"""Vereadores de Goiania, 2000 a 2024.

Pipeline proprio, separado do de eleicao geral, por dois motivos que nao sao de
organizacao e sim de natureza do dado:

1. Outro ciclo. Municipal e' 2000, 2004, ... 2024 - nao ha interseccao com os
   pleitos gerais.
2. OUTRA GEOGRAFIA. Goiania e' um municipio so: o mapa coropletico por municipio,
   que e' a espinha do resto do projeto, aqui nao existe. A unica desagregacao
   territorial dentro da cidade que este arquivo do TSE oferece e' a ZONA
   ELEITORAL - nove em 2024. Nao ha malha publicada de zona eleitoral, entao nao
   ha mapa: a geografia entra como distribuicao por zona, nao como desenho.

Cuidado central: o numero e o desenho das zonas MUDAM entre pleitos. Comparar a
zona 135 de 2000 com a de 2024 nao e' comparar a mesma coisa. Por isso as medidas
de concentracao por zona so sao usadas dentro de cada ano, nunca como serie.
"""
import subprocess
import sys
import unicodedata
import zipfile
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

ANOS = [2000, 2004, 2008, 2012, 2016, 2020, 2024]
CD_VEREADOR = 13
CIDADE = "GOIANIA"
SIT_ELEITO = ("ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA", "MEDIA")

COLS_VOTO = ["QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def baixar(ano):
    zp = cfg.RAW / f"votacao_candidato_munzona_{ano}.zip"
    if zp.exists():
        try:
            with zipfile.ZipFile(zp):
                return zp
        except zipfile.BadZipFile:
            zp.unlink()
    cmd = ["curl.exe", "-sS", "--fail", "--max-time", "1800", "-o", str(zp)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(cfg.TSE_URL.format(ano=ano))
    for t in range(1, 4):
        print(f"[{ano}] baixando... (tentativa {t})", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and zp.exists():
            try:
                with zipfile.ZipFile(zp):
                    return zp
            except zipfile.BadZipFile:
                pass
        zp.unlink(missing_ok=True)
    raise RuntimeError(f"[{ano}] download falhou em 3 tentativas")


def extrair(ano):
    saida = cfg.INTERIM / f"vereador_goiania_{ano}.csv"
    if saida.exists():
        print(f"[{ano}] ja extraido")
        return saida
    zp = baixar(ano)
    try:
        with zipfile.ZipFile(zp) as zf:
            m = [n for n in zf.namelist()
                 if n.upper().endswith(f"_{ano}_{cfg.UF}.CSV")][0]
            with zf.open(m) as fh:
                df = pd.read_csv(fh, sep=";", encoding="latin-1", quotechar='"',
                                 dtype=str, low_memory=False)
    finally:
        zp.unlink(missing_ok=True)

    df.columns = [c.strip().upper() for c in df.columns]
    for c in COLS_VOTO:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["NM_NORM"] = df["NM_MUNICIPIO"].map(sem_acento)
    d = df[(df["NM_NORM"] == CIDADE) &
           (pd.to_numeric(df["CD_CARGO"], errors="coerce") == CD_VEREADOR) &
           (pd.to_numeric(df["NR_TURNO"], errors="coerce") == 1)].copy()
    if d.empty:
        raise RuntimeError(f"[{ano}] nenhuma linha de vereador em {CIDADE}")

    cols = [c for c in ("ANO_ELEICAO", "NR_ZONA", "SQ_CANDIDATO", "NM_CANDIDATO",
                        "NM_URNA_CANDIDATO", "NR_CANDIDATO", "SG_PARTIDO",
                        "NM_PARTIDO", "NM_COLIGACAO", "DS_SIT_TOT_TURNO",
                        "SG_FEDERACAO", "DS_SITUACAO_CANDIDATURA") if c in d.columns]
    agg = d.groupby(cols, dropna=False, as_index=False)[COLS_VOTO].sum()
    agg.to_csv(saida, index=False, encoding="utf-8")
    print(f"[{ano}] {len(agg)} linhas, {agg['SQ_CANDIDATO'].nunique()} candidatos, "
          f"{agg['NR_ZONA'].nunique()} zonas", flush=True)
    return saida


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def main():
    quadros = []
    for ano in ANOS:
        d = pd.read_csv(extrair(ano), dtype=str, low_memory=False)
        for c in COLS_VOTO:
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype("int64")
        somas = {c: int(d[c].sum()) for c in COLS_VOTO}
        col = ("QT_VOTOS_NOMINAIS" if somas["QT_VOTOS_NOMINAIS"] > 0
               else "QT_VOTOS_NOMINAIS_VALIDOS")
        d["votos"] = d[col]
        d["ano"] = ano
        print(f"[{ano}] coluna de voto: {col} (somas={somas})")
        quadros.append(d)
    df = pd.concat(quadros, ignore_index=True)

    linhagem = pd.read_csv(cfg.OVERRIDES / "partidos_linhagem.csv")
    mapa_lin = dict(zip(linhagem["sigla_epoca"].map(sem_acento),
                        linhagem["partido_norm"]))
    mapa_nome = dict(zip(linhagem["partido_norm"], linhagem["nome_linhagem"]))

    df["situacao"] = df["DS_SIT_TOT_TURNO"].fillna("").map(sem_acento)
    df["eleito"] = (df["situacao"].str.startswith("ELEITO") |
                    df["situacao"].isin(SIT_ELEITO))
    df["sigla"] = df["SG_PARTIDO"].fillna("").map(sem_acento)
    df["partido_norm"] = df["sigla"].map(mapa_lin).fillna(df["sigla"])
    df["nome_linhagem"] = df["partido_norm"].map(mapa_nome).fillna(df["partido_norm"])

    # ---- fato por zona ----
    fato = (df.groupby(["ano", "SQ_CANDIDATO", "NR_ZONA"], as_index=False)["votos"]
              .sum().rename(columns={"SQ_CANDIDATO": "sq", "NR_ZONA": "zona"}))
    fato = fato[fato["votos"] > 0]
    fato.to_csv(cfg.PROCESSED / "ver_fato_zona.csv", index=False, encoding="utf-8")

    # ---- candidatos ----
    cand = (df.sort_values("votos", ascending=False)
              .groupby(["ano", "SQ_CANDIDATO"], as_index=False).first())
    tot = fato.groupby(["ano", "sq"], as_index=False)["votos"].sum() \
              .rename(columns={"votos": "votos_total", "sq": "SQ_CANDIDATO"})
    cand = cand.merge(tot, on=["ano", "SQ_CANDIDATO"], how="left")
    cand["votos_total"] = cand["votos_total"].fillna(0).astype("int64")

    # concentracao entre as zonas daquele ano
    regs = []
    for (ano, sq), g in fato.groupby(["ano", "sq"]):
        v = g["votos"].values.astype(float)
        p = v / v.sum()
        regs.append({"ano": ano, "SQ_CANDIDATO": sq,
                     "n_zonas": int(len(v)),
                     "zonas_efetivas": round(float(1 / (p ** 2).sum()), 2),
                     "top1_zona": round(float(p.max() * 100), 2),
                     "gini_zona": round(gini(v), 4),
                     "zona_reduto": g.loc[g["votos"].idxmax(), "zona"]})
    cand = cand.merge(pd.DataFrame(regs), on=["ano", "SQ_CANDIDATO"], how="left")

    cand["chave"] = cand["NM_CANDIDATO"].astype(str).map(sem_acento)
    cand = cand.sort_values(["chave", "ano"])
    sim, var = [], []
    ant = {}
    vetores = {}
    for ano, g in fato.groupby("ano"):
        zonas = sorted(g["zona"].unique())
        pos = {z: i for i, z in enumerate(zonas)}
        for sq, gg in g.groupby("sq"):
            v = np.zeros(len(zonas))
            for z, x in zip(gg["zona"], gg["votos"]):
                v[pos[z]] = x
            vetores[(ano, sq)] = v
    for r in cand.itertuples():
        a = ant.get(r.chave)
        # so compara quando as zonas do ano batem em numero com as do anterior;
        # redesenho de zona invalida a comparacao
        if a is None or vetores[a].shape != vetores[(r.ano, r.SQ_CANDIDATO)].shape:
            sim.append(np.nan)
        else:
            x, y = vetores[a], vetores[(r.ano, r.SQ_CANDIDATO)]
            nx, ny = np.linalg.norm(x), np.linalg.norm(y)
            sim.append(round(float(x @ y / (nx * ny)), 4) if nx and ny else np.nan)
        va = cand.loc[(cand["ano"] == a[0]) & (cand["SQ_CANDIDATO"] == a[1]),
                      "votos_total"].sum() if a else 0
        var.append(round(float((r.votos_total - va) / va * 100), 1) if va else np.nan)
        ant[r.chave] = (r.ano, r.SQ_CANDIDATO)
    cand["similaridade_anterior"] = sim
    cand["variacao_pct"] = var
    cand["reincidente"] = cand.groupby("chave").cumcount() > 0

    cand = cand.rename(columns={"SQ_CANDIDATO": "sq", "NM_CANDIDATO": "nome",
                                "NM_URNA_CANDIDATO": "nome_urna",
                                "NM_COLIGACAO": "coligacao"})
    cand.to_csv(cfg.PROCESSED / "ver_candidato.csv", index=False, encoding="utf-8")

    # ---- pleitos ----
    ple = []
    for ano, g in cand.groupby("ano"):
        el = g[g["eleito"]]
        total = int(g["votos_total"].sum())
        ple.append({"ano": ano, "n_candidatos": int(len(g)),
                    "n_eleitos": int(len(el)),
                    "total_nominais": total,
                    "votos_ultimo_eleito": int(el["votos_total"].min()) if len(el) else 0,
                    "votos_mais_votado": int(g["votos_total"].max()),
                    "quociente_aprox": round(total / max(len(el), 1), 1),
                    "n_zonas": int(fato[fato["ano"] == ano]["zona"].nunique()),
                    "reincidentes_pct": round(float(el["reincidente"].mean()) * 100, 1)})
    dp = pd.DataFrame(ple)
    dp.to_csv(cfg.PROCESSED / "ver_pleito.csv", index=False, encoding="utf-8")

    # ---- partidos ----
    pr = []
    for (ano, part), g in cand.groupby(["ano", "partido_norm"]):
        g = g.sort_values("votos_total", ascending=False)
        t = int(g["votos_total"].sum())
        fortes = g[g["votos_total"] >= 300]
        s = np.nan
        if len(fortes) >= 2:
            M = np.vstack([vetores[(ano, sq)] for sq in fortes["sq"]])
            n = np.linalg.norm(M, axis=1, keepdims=True)
            n[n == 0] = 1
            U = M / n
            S = U @ U.T
            iu = np.triu_indices(len(fortes), k=1)
            s = round(float(S[iu].mean()), 4)
        pr.append({"ano": ano, "partido": part,
                   "nome_linhagem": g["nome_linhagem"].iloc[0],
                   "n_candidatos": int(len(g)), "n_eleitos": int(g["eleito"].sum()),
                   "votos": t,
                   "share_puxador": round(g["votos_total"].iloc[0] / t * 100, 2) if t else 0,
                   "similaridade": s})
    pp = pd.DataFrame(pr)
    pp.to_csv(cfg.PROCESSED / "ver_partido.csv", index=False, encoding="utf-8")

    print("\n=== CAMARA DE GOIANIA ===")
    print(dp.to_string(index=False))
    print("\n=== zonas por pleito (mudanca de desenho invalida serie por zona) ===")
    for ano in ANOS:
        z = sorted(fato[fato["ano"] == ano]["zona"].unique())
        print(f"  {ano}: {len(z)} zonas -> {z}")
    print("\n=== concentracao entre zonas, eleitos (mediana) ===")
    el = cand[cand["eleito"]]
    print(el.groupby("ano").agg(
        zonas_efetivas=("zonas_efetivas", "median"),
        top1_zona=("top1_zona", "median"),
        n_zonas=("n_zonas", "median")).round(2).to_string())
    print("\n=== 2024: dez mais votados ===")
    print(el[el["ano"] == 2024].nlargest(10, "votos_total")[
        ["nome_urna", "sigla", "votos_total", "top1_zona", "zonas_efetivas",
         "zona_reduto"]].to_string(index=False))


if __name__ == "__main__":
    main()
