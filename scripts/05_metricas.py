"""Indices de concentracao, dominancia, competicao intrapartidaria e dinamica
temporal das bases eleitorais.

Grava tres tabelas em data/processed/:
  metricas_candidato.csv  - um registro por candidato x ano
  metricas_municipio.csv  - um registro por municipio x ano
  metricas_partido.csv    - um registro por partido x ano
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

MIN_VOTOS_SIMILARIDADE = 500   # abaixo disso o vetor municipal e ruido


def gini(x):
    """Gini do vetor de votos sobre os 246 municipios (zeros incluidos)."""
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * (idx * x).sum()) / (n * x.sum()) - (n + 1) / n)


def cosseno(m):
    """Matriz de similaridade de cosseno entre as linhas de m."""
    norm = np.linalg.norm(m, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    u = m / norm
    return u @ u.T


def main(cargo="estadual"):
    sfx = "" if cargo == "estadual" else f"_{cargo}"
    fato = pd.read_csv(cfg.PROCESSED / f"fato_votos{sfx}.csv",
                       dtype={"cod_ibge": str})
    cand = pd.read_csv(cfg.PROCESSED / f"dim_candidato{sfx}.csv")
    mun = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype={"cod_ibge": str})
    totm = pd.read_csv(cfg.PROCESSED / f"fato_total_municipio{sfx}.csv",
                       dtype={"cod_ibge": str})
    adj = json.loads((cfg.PROCESSED / "adjacencia_municipios.json").read_text())

    codigos = sorted(mun["cod_ibge"])
    pos = {c: i for i, c in enumerate(codigos)}
    n_mun = len(codigos)

    f = fato.merge(totm, on=["ano", "cod_ibge"], how="left")
    f["share_mun"] = f["votos"] / f["total_nominais_municipio"]

    # ---------------- metricas por candidato ----------------
    regs = []
    vetores = {}          # (ano, sq) -> vetor de votos por municipio
    for (ano, sq), g in f.groupby(["ano", "sq_candidato"], sort=False):
        v = np.zeros(n_mun)
        for cod, votos in zip(g["cod_ibge"], g["votos"]):
            v[pos[cod]] = votos
        vetores[(ano, sq)] = v

        total = v.sum()
        p = v / total
        ordenado = np.sort(v)[::-1]
        hhi = float((p ** 2).sum())
        n_efetivo = 1.0 / hhi if hhi > 0 else 0.0

        # dominancia: media do share municipal ponderada pelos proprios votos
        dom_pond = float((g["votos"] * g["share_mun"]).sum() / total)

        # contiguidade: fatia dos votos no reduto e nos municipios que o tocam
        reduto = codigos[int(np.argmax(v))]
        viz = set(adj.get(reduto, [])) | {reduto}
        votos_contig = float(sum(v[pos[c]] for c in viz if c in pos))

        regs.append({
            "ano": ano, "sq_candidato": sq,
            "votos_total": int(total),
            "n_municipios": int((v > 0).sum()),
            "top1_share": round(float(ordenado[0] / total * 100), 2),
            "top5_share": round(float(ordenado[:5].sum() / total * 100), 2),
            "hhi": round(hhi, 5),
            "n_municipios_efetivo": round(n_efetivo, 2),
            "gini_municipal": round(gini(v), 4),
            "dominancia_ponderada": round(dom_pond * 100, 2),
            "dominancia_max": round(float(g["share_mun"].max() * 100), 2),
            "n_mun_dominio_25": int((g["share_mun"] >= 0.25).sum()),
            "n_mun_dominio_50": int((g["share_mun"] >= 0.50).sum()),
            "reduto": reduto,
            "contiguidade": round(votos_contig / total * 100, 2),
            "votos_por_municipio": round(float(total / max((v > 0).sum(), 1)), 1),
        })

    met = pd.DataFrame(regs)

    # tipologia 2x2: concentracao (n. efetivo de municipios) x dominancia
    concentrado = met["n_municipios_efetivo"] <= 10
    dominante = met["dominancia_ponderada"] >= 10
    met["tipologia"] = np.select(
        [concentrado & dominante, concentrado & ~dominante,
         ~concentrado & dominante],
        ["Concentrado-Dominante", "Concentrado-Compartilhado",
         "Disperso-Dominante"], default="Disperso-Difuso")

    nomes_mun = dict(zip(mun["cod_ibge"], mun["nome"]))
    met["reduto_nome"] = met["reduto"].map(nomes_mun)

    met = met.merge(
        cand[[c for c in ("ano", "sq_candidato", "nome", "nome_urna",
                          "sigla_partido", "partido_norm", "nome_linhagem",
                          "federacao", "situacao", "eleito", "venceu_go")
              if c in cand.columns]],
        on=["ano", "sq_candidato"], how="left")

    # ---------------- dinamica temporal ----------------
    # Um mesmo candidato reaparece com SQ_CANDIDATO diferente a cada pleito;
    # a identidade estavel na serie e o nome completo.
    # O TSE grava o mesmo nome ora com acento ora sem (ALVARO SOARES GUIMARAES
    # em 1998/2018, ALVARO SOARES GUIMARAES com acentos nos demais anos). Usar o
    # nome cru como chave partiria a mesma pessoa em duas trajetorias e zeraria
    # a reincidencia dela. A chave estavel e o nome sem acento.
    met["chave_pessoa"] = met["nome"].astype(str).map(geo.normalizar)
    met = met.sort_values(["chave_pessoa", "ano"])
    sim_prev, delta_prev = [], []
    anterior = {}
    for r in met.itertuples():
        k = r.chave_pessoa
        ant = anterior.get(k)
        if ant is None:
            sim_prev.append(np.nan)
            delta_prev.append(np.nan)
        else:
            a, b = vetores[ant], vetores[(r.ano, r.sq_candidato)]
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            sim_prev.append(round(float(a @ b / (na * nb)), 4) if na and nb else np.nan)
            va = a.sum()
            delta_prev.append(round(float((b.sum() - va) / va * 100), 1) if va else np.nan)
        anterior[k] = (r.ano, r.sq_candidato)
    met["similaridade_pleito_anterior"] = sim_prev
    met["variacao_votos_pct"] = delta_prev
    met["reincidente"] = met["similaridade_pleito_anterior"].notna()

    met.to_csv(cfg.PROCESSED / f"metricas_candidato{sfx}.csv", index=False, encoding="utf-8")
    print(f"[{cargo}] metricas_candidato{sfx}.csv: {len(met)} linhas")

    # ---------------- metricas por municipio ----------------
    regs_m = []
    for (ano, cod), g in f.groupby(["ano", "cod_ibge"], sort=False):
        tot = g["votos"].sum()
        p = (g["votos"] / tot).values
        ordenado = np.sort(p)[::-1]
        hhi = float((p ** 2).sum())
        regs_m.append({
            "ano": ano, "cod_ibge": cod,
            "total_nominais": int(tot),
            "n_candidatos_com_voto": int(len(g)),
            "hhi_candidatos": round(hhi, 5),
            "n_candidatos_efetivo": round(1 / hhi if hhi else 0, 2),
            "top1_share": round(float(ordenado[0] * 100), 2),
            "top3_share": round(float(ordenado[:3].sum() * 100), 2),
            "capturado_25": bool(ordenado[0] >= 0.25),
            "capturado_50": bool(ordenado[0] >= 0.50),
        })
    met_mun = pd.DataFrame(regs_m).merge(
        mun[["cod_ibge", "nome", "microrregiao", "mesorregiao"]],
        on="cod_ibge", how="left")
    met_mun.to_csv(cfg.PROCESSED / f"metricas_municipio{sfx}.csv", index=False,
                   encoding="utf-8")
    print(f"[{cargo}] metricas_municipio{sfx}.csv: {len(met_mun)} linhas")

    # ---------------- metricas por partido ----------------
    regs_p = []
    for (ano, part), g in met.groupby(["ano", "partido_norm"], sort=False):
        g = g.sort_values("votos_total", ascending=False)
        tot = g["votos_total"].sum()
        fortes = g[g["votos_total"] >= MIN_VOTOS_SIMILARIDADE]
        sim_media = np.nan
        if len(fortes) >= 2:
            m = np.vstack([vetores[(ano, sq)] for sq in fortes["sq_candidato"]])
            s = cosseno(m)
            iu = np.triu_indices(len(fortes), k=1)
            sim_media = round(float(s[iu].mean()), 4)
        regs_p.append({
            "ano": ano, "partido_norm": part,
            "nome_linhagem": g["nome_linhagem"].iloc[0],
            "n_candidatos": int(len(g)),
            "n_eleitos": int(g["eleito"].sum()),
            "votos_total": int(tot),
            "share_puxador": round(float(g["votos_total"].iloc[0] / tot * 100), 2)
                             if tot else 0.0,
            "similaridade_media_intrapartido": sim_media,
            "n_pares_comparados": int(len(fortes) * (len(fortes) - 1) / 2),
        })
    met_part = pd.DataFrame(regs_p)
    met_part.to_csv(cfg.PROCESSED / f"metricas_partido{sfx}.csv", index=False,
                    encoding="utf-8")
    print(f"[{cargo}] metricas_partido{sfx}.csv: {len(met_part)} linhas")

    print(f"\n=== [{cargo}] tipologia dos ELEITOS por ano ===")
    t = (met[met["eleito"]].groupby(["ano", "tipologia"]).size()
         .unstack(fill_value=0))
    print(t.to_string())

    print(f"\n=== [{cargo}] concentracao media dos eleitos ===")
    s = met[met["eleito"]].groupby("ano").agg(
        n_mun_efetivo=("n_municipios_efetivo", "mean"),
        top1_share=("top1_share", "mean"),
        dominancia=("dominancia_ponderada", "mean"),
        gini=("gini_municipal", "mean"),
        contiguidade=("contiguidade", "mean"),
        n_municipios=("n_municipios", "mean")).round(2)
    print(s.to_string())


if __name__ == "__main__":
    alvos = sys.argv[1:] or list(cfg.CARGOS.values())
    for c in alvos:
        main(c)
