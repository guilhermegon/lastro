"""Malha municipal de Goias: baixa do IBGE, simplifica, casa com os nomes do TSE
e deriva a matriz de adjacencia usada nas metricas de contiguidade.

Sem geopandas: a malha e consumida como GeoJSON puro.
"""
import gzip
import io
import json
import sys
import unicodedata
import urllib.request
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

GEOJSON_BRUTO = cfg.RAW / "malha_go_bruta.geojson"
GEOJSON_FINAL = cfg.PROCESSED / "go_municipios.geojson"
ADJ_JSON = cfg.PROCESSED / "adjacencia_municipios.json"


def normalizar(nome):
    """Chave de pareamento: sem acento, maiuscula, sem pontuacao, espaco colapsado."""
    s = unicodedata.normalize("NFKD", str(nome))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("-", " ").replace("'", " ").replace("`", " ")
    s = "".join(c if (c.isalnum() or c.isspace()) else " " for c in s)
    return " ".join(s.split())


def _get(url):
    """GET que lida com a resposta gzipada que a API do IBGE devolve."""
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read()
    if raw[:2] == bytes([0x1F, 0x8B]):
        raw = gzip.decompress(raw)
    return raw.decode("utf-8")


def baixar_malha():
    if GEOJSON_BRUTO.exists():
        print(f"malha ja presente ({GEOJSON_BRUTO.stat().st_size/1024:.0f} KB)")
        return json.loads(GEOJSON_BRUTO.read_text(encoding="utf-8"))
    url = cfg.IBGE_MALHA_URL.format(uf=cfg.UF_IBGE)
    print("baixando malha do IBGE...")
    data = json.loads(_get(url))
    GEOJSON_BRUTO.write_text(json.dumps(data), encoding="utf-8")
    print(f"malha baixada: {len(data['features'])} feicoes")
    return data


def nomes_ibge():
    """Nomes oficiais dos municipios de GO, para casar com os codigos da malha."""
    url = (f"https://servicodados.ibge.gov.br/api/v1/localidades/"
           f"estados/{cfg.UF_IBGE}/municipios")
    muns = json.loads(_get(url))
    out = {}
    for m in muns:
        micro = (m.get("microrregiao") or {}).get("nome", "")
        meso = ((m.get("microrregiao") or {}).get("mesorregiao") or {}).get("nome", "")
        out[str(m["id"])] = {"nome": m["nome"], "microrregiao": micro,
                            "mesorregiao": meso, "nome_norm": normalizar(m["nome"])}
    print(f"IBGE lista {len(out)} municipios em {cfg.UF}")
    return out


# ---------- simplificacao de geometria (Douglas-Peucker) ----------

def _dist_perp(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    px, py = x1 + t * dx, y1 + t * dy
    return ((x - px) ** 2 + (y - py) ** 2) ** 0.5


def simplificar_anel(pts, tol):
    if len(pts) <= 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    pilha = [(0, len(pts) - 1)]
    while pilha:
        i, j = pilha.pop()
        if j <= i + 1:
            continue
        pior, idx = 0.0, -1
        for k in range(i + 1, j):
            d = _dist_perp(pts[k], pts[i], pts[j])
            if d > pior:
                pior, idx = d, k
        if pior > tol:
            keep[idx] = True
            pilha += [(i, idx), (idx, j)]
    out = [p for p, k in zip(pts, keep) if k]
    return out if len(out) >= 4 else pts


def simplificar_geometria(geom, tol):
    def anel(a):
        r = simplificar_anel([tuple(round(c, 5) for c in pt) for pt in a], tol)
        if r[0] != r[-1]:
            r.append(r[0])
        return [list(p) for p in r]
    t = geom["type"]
    if t == "Polygon":
        return {"type": t, "coordinates": [anel(a) for a in geom["coordinates"]]}
    if t == "MultiPolygon":
        return {"type": t, "coordinates": [[anel(a) for a in poly]
                                           for poly in geom["coordinates"]]}
    return geom


# ---------- adjacencia por aresta compartilhada ----------

def arestas(geom):
    """Conjunto de arestas nao-direcionadas, arredondadas para tolerar ruido."""
    out = set()
    polys = ([geom["coordinates"]] if geom["type"] == "Polygon"
             else geom["coordinates"])
    for poly in polys:
        for ring in poly:
            for a, b in zip(ring, ring[1:]):
                pa = (round(a[0], 4), round(a[1], 4))
                pb = (round(b[0], 4), round(b[1], 4))
                if pa != pb:
                    out.add((pa, pb) if pa < pb else (pb, pa))
    return out


def main():
    bruto = baixar_malha()
    info = nomes_ibge()

    feats = []
    adj_src = {}
    for f in bruto["features"]:
        cod = str(f["properties"].get("codarea") or f["properties"].get("id"))
        meta = info.get(cod)
        if meta is None:
            raise RuntimeError(f"codigo {cod} da malha nao encontrado na lista do IBGE")
        adj_src[cod] = arestas(f["geometry"])
        feats.append({
            "type": "Feature",
            "properties": {"cod_ibge": cod, "nome": meta["nome"],
                           "nome_norm": meta["nome_norm"],
                           "microrregiao": meta["microrregiao"],
                           "mesorregiao": meta["mesorregiao"]},
            "geometry": simplificar_geometria(f["geometry"], tol=0.004),
        })

    GEOJSON_FINAL.write_text(
        json.dumps({"type": "FeatureCollection", "features": feats},
                   separators=(",", ":")), encoding="utf-8")
    print(f"geojson simplificado: {GEOJSON_FINAL.stat().st_size/1024:.0f} KB, "
          f"{len(feats)} municipios")

    codigos = list(adj_src)
    adj = {c: set() for c in codigos}
    for i, a in enumerate(codigos):
        for b in codigos[i + 1:]:
            if adj_src[a] & adj_src[b]:
                adj[a].add(b)
                adj[b].add(a)
    ADJ_JSON.write_text(json.dumps({k: sorted(v) for k, v in adj.items()}),
                        encoding="utf-8")
    isolados = [c for c, v in adj.items() if not v]
    print(f"adjacencia: media {sum(len(v) for v in adj.values())/len(adj):.1f} "
          f"vizinhos, {len(isolados)} isolados")
    if isolados:
        print("  ISOLADOS:", [info[c]['nome'] for c in isolados])

    dim = pd.DataFrame([{"cod_ibge": f["properties"]["cod_ibge"],
                         "nome": f["properties"]["nome"],
                         "nome_norm": f["properties"]["nome_norm"],
                         "microrregiao": f["properties"]["microrregiao"],
                         "mesorregiao": f["properties"]["mesorregiao"],
                         "n_vizinhos": len(adj[f["properties"]["cod_ibge"]])}
                        for f in feats]).sort_values("nome")
    dim.to_csv(cfg.PROCESSED / "dim_municipio_base.csv", index=False, encoding="utf-8")
    print(f"dim_municipio_base.csv: {len(dim)} linhas")


if __name__ == "__main__":
    main()
