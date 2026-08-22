"""Camara municipal das 26 capitais: `web/{UF}/vereador.json`.

Le os CSVs que `24_vereador_capitais.py` extraiu e monta um arquivo por capital.

**Por que esta aba nao tem mapa.** Uma capital e' um municipio so, entao o
coropletico que sustenta o resto do projeto aqui nao existe. A unica
desagregacao territorial que o arquivo do TSE oferece dentro da cidade e' a zona
eleitoral, e nao ha malha publicada de zona - a geografia entra como
distribuicao, nao como desenho.

**A armadilha que a replicacao amplia.** O numero e o traçado das zonas mudam
entre pleitos, e mudam de forma diferente em cada cidade: Sao Paulo tem dezenas,
Palmas tem poucas. Duas consequencias que estao no codigo, nao so no texto:

- zonas efetivas nunca viram serie temporal - so valem dentro de um ano;
- a similaridade com o pleito anterior so e' calculada quando o numero de zonas
  bate. Redesenho de zona invalida a comparacao, e devolver um numero ali seria
  comparar dois mapas diferentes fingindo que sao o mesmo.

Nao ha Distrito Federal: Brasilia elege distrital, nao vereador.
"""
import json
import sys
import unicodedata
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
cap = import_module("24_vereador_capitais")

WEB = cfg.PROCESSED / "web"
ANOS = cap.ANOS
SIT_ELEITO = cap.SIT_ELEITO
COLS_VOTO = cap.COLS_VOTO
TOP_NAO_ELEITOS = 60   # quem quase entrou aparece; o resto so no agregado


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def ler(uf, ano):
    f = cfg.INTERIM / f"ver_{uf}_{ano}.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f, dtype=str, low_memory=False)
    for c in COLS_VOTO:
        if c not in d.columns:
            d[c] = 0
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype("int64")
    # a coluna util muda ao longo da serie; resolver por soma, nunca por ano
    col = ("QT_VOTOS_NOMINAIS" if d["QT_VOTOS_NOMINAIS"].sum() > 0
           else "QT_VOTOS_NOMINAIS_VALIDOS")
    d["votos"] = d[col]
    d["NR_ZONA"] = pd.to_numeric(d["NR_ZONA"], errors="coerce").fillna(0).astype(int)
    return d


def montar(uf, lin, nomelin):
    anos, vetores, chave_ant = {}, {}, {}
    for ano in ANOS:
        d = ler(uf, ano)
        if d is None or d.empty:
            continue
        sit = d["DS_SIT_TOT_TURNO"].fillna("").map(sem_acento)
        d = d.assign(
            eleito=sit.str.startswith("ELEITO") | sit.isin(SIT_ELEITO),
            sigla=d["SG_PARTIDO"].fillna("").map(sem_acento))
        d["pnorm"] = d["sigla"].map(lin).fillna(d["sigla"])

        zonas = sorted(d.loc[d["votos"] > 0, "NR_ZONA"].unique().tolist())
        pos = {z: i for i, z in enumerate(zonas)}
        if not zonas:
            continue

        info = d.sort_values("votos", ascending=False).groupby(
            "SQ_CANDIDATO", as_index=False).first()
        porz = d.groupby(["SQ_CANDIDATO", "NR_ZONA"], as_index=False)["votos"].sum()
        porz = porz[porz["votos"] > 0]
        tot = porz.groupby("SQ_CANDIDATO")["votos"].sum()

        fichas = []
        for r in info.itertuples():
            g = porz[porz["SQ_CANDIDATO"] == r.SQ_CANDIDATO]
            if g.empty:
                continue
            v = g["votos"].to_numpy(dtype=float)
            p = v / v.sum()
            vet = np.zeros(len(zonas))
            for z, x in zip(g["NR_ZONA"], g["votos"]):
                vet[pos[z]] = x
            vetores[(ano, r.SQ_CANDIDATO)] = vet
            fichas.append({
                "sq": str(r.SQ_CANDIDATO),
                "n": str(r.NM_URNA_CANDIDATO), "completo": str(r.NM_CANDIDATO),
                "p": str(r.SG_PARTIDO), "pn": nomelin.get(r.pnorm, r.pnorm),
                "el": bool(r.eleito), "t": int(tot[r.SQ_CANDIDATO]),
                "zi": [pos[z] for z in g["NR_ZONA"]],
                "zv": [int(x) for x in g["votos"]],
                "nz": int(len(v)),
                "ef": round(float(1 / (p ** 2).sum()), 2),
                "t1": round(float(p.max() * 100), 2),
                "gi": round(gini(v), 4),
                "reduto": int(g.loc[g["votos"].idxmax(), "NR_ZONA"]),
                "chave": sem_acento(r.NM_CANDIDATO),
            })

        # reincidencia e continuidade de base, por nome sem acento: a grafia
        # com acento varia entre pleitos no mesmo arquivo do TSE e quebra o
        # pareamento de pessoa
        for f in fichas:
            ant = chave_ant.get(f["chave"])
            f["re"] = ant is not None
            f["sim"] = None
            if ant is not None:
                x, y = vetores[ant], vetores[(ano, f["sq"])]
                # so compara se o numero de zonas bate: redesenho de zona
                # invalida a comparacao, e um numero aqui seria falso
                if x.shape == y.shape:
                    nx, ny = np.linalg.norm(x), np.linalg.norm(y)
                    if nx and ny:
                        f["sim"] = round(float(x @ y / (nx * ny)), 4)

        # a memoria de pessoa cobre TODOS os candidatos, nao so os guardados:
        # quem nao se elegeu num pleito e voltou no seguinte tem de ser
        # reconhecido como reincidente
        for f in fichas:
            chave_ant[f["chave"]] = (ano, f["sq"])

        fichas.sort(key=lambda f: -f["t"])
        el = [f for f in fichas if f["el"]]
        guardar = el + [f for f in fichas if not f["el"]][:TOP_NAO_ELEITOS]
        guardar.sort(key=lambda f: -f["t"])
        for f in guardar:
            f.pop("chave", None)

        total = int(tot.sum())
        partidos = []
        for pn, g in info.groupby("pnorm"):
            sq = set(g["SQ_CANDIDATO"])
            v = int(tot[tot.index.isin(sq)].sum())
            ne = int(g["eleito"].sum())
            if len(g) < 2:
                continue
            partidos.append({"nome": nomelin.get(pn, pn), "nc": int(len(g)),
                             "ne": ne, "votos": v,
                             "puxador": round(float(tot[tot.index.isin(sq)].max())
                                              / max(v, 1) * 100, 2)})
        partidos.sort(key=lambda x: -x["votos"])

        anos[str(ano)] = {
            "pleito": {
                "nCand": int(len(info)), "cadeiras": len(el), "total": total,
                "ultimo": min((f["t"] for f in el), default=0),
                "maior": max((f["t"] for f in fichas), default=0),
                "qe": round(total / max(len(el), 1), 1),
                "nz": len(zonas),
                "rePct": round(float(np.mean([f["re"] for f in el])) * 100, 1)
                         if el else 0.0,
            },
            "zonas": zonas,
            "fichas": guardar,
            "partidos": partidos[:12],
        }
    return anos


def main():
    linhagem = pd.read_csv(cfg.OVERRIDES / "partidos_linhagem.csv")
    lin = dict(zip(linhagem["sigla_epoca"].map(sem_acento),
                   linhagem["partido_norm"]))
    nomelin = dict(zip(linhagem["partido_norm"], linhagem["nome_linhagem"]))

    total = 0
    for uf in sorted(cap.CAPITAIS):
        cidade = cap.NOMES[uf]
        anos = montar(uf, lin, nomelin)
        if not anos:
            print(f"  {uf}: sem dado", flush=True)
            continue
        obj = {"cidade": cidade, "anos": anos}
        p = WEB / uf / "vereador.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
        total += p.stat().st_size
        ult = anos.get("2024") or anos[max(anos)]
        print(f"  {uf} {cidade}: {len(anos)} pleitos, "
              f"{ult['pleito']['cadeiras']} cadeiras, "
              f"{ult['pleito']['nz']} zonas, "
              f"{p.stat().st_size/1024:.0f} KB", flush=True)
    print(f"\nvereador.json: {total/1024/1024:.1f} MB no total")


if __name__ == "__main__":
    main()
