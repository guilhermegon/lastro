"""Replica o tratamento para as 27 UFs e monta o comparativo nacional.

O pipeline ja era parametrizado por UF; o que muda aqui e' a escala. Duas
saidas, porque uma so nao cabe:

1. POR UF - deputado estadual, 1998-2022, eleitos, com o mesmo conjunto de
   indices usado em Goias. E' o cargo que o painel original trata e o unico com
   massa suficiente para o mapa municipal fazer sentido em todo estado.

2. NACIONAL - agregados por UF, para comparar estados entre si, mais a malha do
   Brasil por UF (27 poligonos, barato).

Por que nao tudo: o tratamento completo (5 cargos x 7 pleitos x 5.571
municipios) projeta ~89 MB de payload contra um teto de 16 MB por pagina. So a
geometria municipal do Brasil ja sao 8 MB na simplificacao usada em Goias. Aqui
a geometria e' simplificada mais forte e o detalhe fica so nos eleitos.
"""
import gzip
import json
import sys
import unicodedata
import urllib.request
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

MALHA_UF = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
            "?formato=application/vnd.geo+json&intrarregiao=UF&qualidade=minima")
LISTA_UF = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
LISTA_MUN = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

TOL_UF = 0.02        # simplificacao da malha estadual
TOL_MUN = 0.012      # municipal, mais forte que a de Goias (0.004)


def get(url):
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    raw = urllib.request.urlopen(req, timeout=300).read()
    if raw[:2] == bytes([0x1F, 0x8B]):
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def uf_do_municipio(m):
    mi = m.get("microrregiao") or {}
    if mi.get("mesorregiao"):
        return mi["mesorregiao"]["UF"]["sigla"]
    ri = m.get("regiao-imediata") or {}
    rint = ri.get("regiao-intermediaria") or {}
    if rint.get("UF"):
        return rint["UF"]["sigla"]
    return None


def carregar_municipios():
    muns = get(LISTA_MUN)
    linhas = []
    for m in muns:
        uf = uf_do_municipio(m)
        if not uf:
            continue
        linhas.append({"cod_ibge": str(m["id"]), "nome": m["nome"], "uf": uf,
                       "nome_norm": geo.normalizar(m["nome"])})
    d = pd.DataFrame(linhas)
    print(f"IBGE: {len(d)} municipios em {d['uf'].nunique()} UFs")
    return d


def carregar_malha_municipal(dim):
    """Uma malha por UF, simplificada mais forte que a de Goias."""
    saida = {}
    for uf, g in dim.groupby("uf"):
        cod_uf = str(g["cod_ibge"].iloc[0])[:2]
        url = cfg.IBGE_MALHA_URL.format(uf=cod_uf)
        try:
            gj = get(url)
        except Exception as e:
            print(f"  [{uf}] malha falhou: {e}")
            continue
        feats = {}
        for f in gj["features"]:
            cod = str(f["properties"].get("codarea") or f["properties"].get("id"))
            feats[cod] = geo.simplificar_geometria(f["geometry"], tol=TOL_MUN)
        saida[uf] = feats
        print(f"  [{uf}] {len(feats)} municipios")
    return saida


def indices(v):
    """Mesmos indices do painel de Goias, sobre o vetor de votos por municipio."""
    total = v.sum()
    if total <= 0:
        return None
    p = v / total
    hhi = float((p ** 2).sum())
    ordenado = np.sort(v)[::-1]
    return {
        "total": int(total),
        "nmun": int((v > 0).sum()),
        "top1": round(float(ordenado[0] / total * 100), 2),
        "top5": round(float(ordenado[:5].sum() / total * 100), 2),
        "efet": round(1 / hhi if hhi else 0, 2),
        "gini": round(geo_gini(v), 4),
    }


def geo_gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def main():
    dim = carregar_municipios()
    dim.to_csv(cfg.PROCESSED / "nac_dim_municipio.csv", index=False, encoding="utf-8")

    ufs_info = {u["sigla"]: u["nome"] for u in get(LISTA_UF)}

    # ---------- malha estadual ----------
    gj = get(MALHA_UF)
    feats = []
    for f in gj["features"]:
        cod = str(f["properties"].get("codarea") or f["properties"].get("id"))
        feats.append({"cod": cod,
                      "geom": geo.simplificar_geometria(f["geometry"], tol=TOL_UF)})
    (cfg.PROCESSED / "nac_malha_uf.json").write_text(
        json.dumps(feats, separators=(",", ":")), encoding="utf-8")
    print(f"malha por UF: {len(feats)} poligonos, "
          f"{(cfg.PROCESSED / 'nac_malha_uf.json').stat().st_size/1024:.0f} KB")

    # ---------- por UF: deputado estadual ----------
    mapa = {}
    for uf, g in dim.groupby("uf"):
        mapa[uf] = dict(zip(g["nome_norm"], g["cod_ibge"]))
    # As correcoes de grafia foram levantadas para Goias. Aplica-las a qualquer
    # UF injeta codigo errado: "VALPARAISO" existe em GO e em SP, e o override
    # goiano jogava o codigo de Valparaiso de Goias dentro de Sao Paulo. So vale
    # se o codigo pertencer a UF que esta sendo processada.
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    corr = dict(zip(ov["nome_norm_tse"], ov["cod_ibge"]))
    cod_por_uf = {uf: set(g["cod_ibge"]) for uf, g in dim.groupby("uf")}

    linhagem = pd.read_csv(cfg.OVERRIDES / "partidos_linhagem.csv")
    lin = dict(zip(linhagem["sigla_epoca"].map(sem_acento),
                   linhagem["partido_norm"]))

    registros, agregados, orfaos_totais = [], [], {}
    for ano in cfg.ANOS:
        f = cfg.INTERIM / f"votos_br_estadual_{ano}.csv"
        if not f.exists():
            print(f"[{ano}] sem arquivo nacional - pulado")
            continue
        d = pd.read_csv(f, dtype=str, low_memory=False)
        for c in ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"):
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
        col = ("QT_VOTOS_NOMINAIS" if d["QT_VOTOS_NOMINAIS"].sum() > 0
               else "QT_VOTOS_NOMINAIS_VALIDOS")
        d["votos"] = d[col]
        d["situacao"] = d["DS_SIT_TOT_TURNO"].fillna("").map(sem_acento)
        d["eleito"] = (d["situacao"].str.startswith("ELEITO") |
                       d["situacao"].isin(("MEDIA",)))
        d["nome_norm"] = d["NM_MUNICIPIO"].map(geo.normalizar)

        for uf, g in d.groupby("SG_UF"):
            if uf not in mapa:
                continue
            g = g.copy()
            g["cod_ibge"] = g["nome_norm"].map(mapa[uf])
            faltam = g["cod_ibge"].isna()
            if faltam.any():
                sugerido = g.loc[faltam, "nome_norm"].map(corr)
                sugerido = sugerido.where(sugerido.isin(cod_por_uf.get(uf, set())))
                g.loc[faltam, "cod_ibge"] = sugerido
            perdidos = sorted(g.loc[g["cod_ibge"].isna(), "NM_MUNICIPIO"].unique())
            if perdidos:
                orfaos_totais.setdefault(uf, set()).update(perdidos)
                g = g[g["cod_ibge"].notna()]
            if g.empty:
                continue

            codigos = sorted(mapa[uf].values())
            pos = {c: i for i, c in enumerate(codigos)}
            agg = g.groupby(["SQ_CANDIDATO", "cod_ibge"], as_index=False)["votos"].sum()
            info = (g.sort_values("votos", ascending=False)
                      .groupby("SQ_CANDIDATO", as_index=False).first())
            eleitos = info[info["eleito"]]

            for r in eleitos.itertuples():
                sub = agg[agg["SQ_CANDIDATO"] == r.SQ_CANDIDATO]
                v = np.zeros(len(codigos))
                for c, x in zip(sub["cod_ibge"], sub["votos"]):
                    v[pos[c]] = x
                ind = indices(v)
                if not ind:
                    continue
                sigla = sem_acento(r.SG_PARTIDO)
                registros.append({
                    "uf": uf, "ano": ano,
                    "nome": r.NM_URNA_CANDIDATO or r.NM_CANDIDATO,
                    "partido": sigla, "partido_norm": lin.get(sigla, sigla),
                    "reduto": codigos[int(np.argmax(v))],
                    **ind,
                    "mi": [pos[c] for c in sub["cod_ibge"]],
                    "mv": [int(x) for x in sub["votos"]],
                })

            tot_uf = int(agg["votos"].sum())
            agregados.append({
                "uf": uf, "ano": ano, "n_cadeiras": int(len(eleitos)),
                "n_candidatos": int(len(info)),
                "total_nominais": tot_uf,
                "n_municipios": len(codigos),
                "quociente": round(tot_uf / max(len(eleitos), 1), 1),
                "ultimo_eleito": int(eleitos["votos"].groupby(
                    eleitos["SQ_CANDIDATO"]).sum().min()) if len(eleitos) else 0,
            })
        print(f"[{ano}] processado: {len(registros)} eleitos acumulados", flush=True)

    reg = pd.DataFrame(registros)
    agr = pd.DataFrame(agregados)

    # medianas por UF e ano: e' o comparativo nacional
    if len(reg):
        med = (reg.groupby(["uf", "ano"])
                  .agg(efet=("efet", "median"), top1=("top1", "median"),
                       gini=("gini", "median"), nmun=("nmun", "median"),
                       n_eleitos=("nome", "size"))
                  .round(2).reset_index())
        agr = agr.merge(med, on=["uf", "ano"], how="left")
    agr["uf_nome"] = agr["uf"].map(ufs_info)
    agr.to_csv(cfg.PROCESSED / "nac_agregado.csv", index=False, encoding="utf-8")
    reg.drop(columns=["mi", "mv"]).to_csv(cfg.PROCESSED / "nac_eleitos.csv",
                                          index=False, encoding="utf-8")
    reg.to_json(cfg.PROCESSED / "nac_eleitos_detalhe.json", orient="records")

    print(f"\nnac_agregado.csv: {len(agr)} linhas (UF x ano)")
    print(f"nac_eleitos.csv: {len(reg)} eleitos")
    if orfaos_totais:
        print("\nmunicipios sem par no IBGE, por UF:")
        for uf, v in sorted(orfaos_totais.items()):
            print(f"  {uf}: {len(v)} -> {sorted(v)[:4]}")

    print("\n=== municipios efetivos dos eleitos, 2022, dez menores ===")
    u = agr[agr["ano"] == 2022].nsmallest(10, "efet")
    print(u[["uf", "uf_nome", "n_cadeiras", "n_municipios", "efet", "top1"]]
          .to_string(index=False))
    print("\n=== dez maiores ===")
    print(agr[agr["ano"] == 2022].nlargest(10, "efet")[
        ["uf", "uf_nome", "n_cadeiras", "n_municipios", "efet", "top1"]]
        .to_string(index=False))


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


if __name__ == "__main__":
    main()
