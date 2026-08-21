"""Rivais territoriais de cada deputado, separados por posicao ideologica.

A pergunta e' "quem disputa o mesmo chao que este deputado?", e nao "quem teve
votacao parecida em tamanho". Por isso a medida e' a sobreposicao entre os
vetores de votos por municipio, e nao a diferenca de totais.

Duas medidas, que respondem coisas diferentes:

  afinidade (cosseno)  - quanto os dois mapas tem o mesmo FORMATO. E' simetrica:
                         vale o mesmo para os dois lados do par.
  pressao              - quanto do voto DESTE deputado esta em municipios onde o
                         rival tambem e' forte, ponderado pela forca do rival ali.
                         Nao e' simetrica: um gigante pressiona um pequeno muito
                         mais do que o contrario.

A separacao entre aliado e adversario NAO sai do dado eleitoral: vem de
data/overrides/partidos_espectro.csv, uma classificacao em cinco bandas
(esquerda, centro-esquerda, centro, centro-direita, direita). E' juizo externo e
discutivel - trocar o arquivo troca a leitura, sem mexer no codigo.
"""
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

MIN_VOTOS_RIVAL = 1000   # abaixo disso o vetor municipal e' ruido
TOP_RIVAIS = 6           # quantos guardar de cada lado


def carregar_espectro():
    e = pd.read_csv(cfg.OVERRIDES / "partidos_espectro.csv")
    return (dict(zip(e["partido_norm"], e["banda"])),
            dict(zip(e["partido_norm"], e["escore"])))


def main():
    fato = pd.read_csv(cfg.PROCESSED / "fato_votos.csv", dtype={"cod_ibge": str})
    met = pd.read_csv(cfg.PROCESSED / "metricas_candidato.csv")
    mun = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype={"cod_ibge": str})
    banda, escore = carregar_espectro()

    codigos = sorted(mun["cod_ibge"])
    pos = {c: i for i, c in enumerate(codigos)}
    nomes_mun = dict(zip(mun["cod_ibge"], mun["nome"]))

    faltam = sorted(set(met["partido_norm"].dropna()) - set(banda))
    if faltam:
        print(f"AVISO partidos sem posicao no espectro (tratados como centro): {faltam}")

    linhas = []
    for ano in cfg.ANOS:
        m = met[(met["ano"] == ano) & (met["votos_total"] >= MIN_VOTOS_RIVAL)].copy()
        f = fato[fato["ano"] == ano]
        idx = {sq: i for i, sq in enumerate(m["sq_candidato"])}

        # matriz candidatos x municipios
        M = np.zeros((len(m), len(codigos)))
        for r in f.itertuples():
            i = idx.get(r.sq_candidato)
            if i is not None:
                M[i, pos[r.cod_ibge]] = r.votos

        totais = M.sum(axis=1, keepdims=True)
        norma = np.linalg.norm(M, axis=1, keepdims=True)
        norma[norma == 0] = 1.0
        U = M / norma
        AFIN = U @ U.T                       # cosseno, simetrico
        np.fill_diagonal(AFIN, 0.0)

        # forca do rival em cada municipio = fatia dele no total apurado ali
        total_mun = M.sum(axis=0)
        total_mun[total_mun == 0] = 1.0
        FORCA = M / total_mun                # candidato x municipio

        # pressao[a, b] = fracao do voto de A que esta em chao onde B e' forte
        PESO = M / totais                    # distribuicao propria de A
        PRESSAO = PESO @ FORCA.T
        np.fill_diagonal(PRESSAO, 0.0)

        info = m.reset_index(drop=True)
        bandas = info["partido_norm"].map(banda).fillna("centro")
        escores = info["partido_norm"].map(escore).fillna(3).astype(int)

        eleitos = info[info["eleito"]]
        for r in eleitos.itertuples():
            i = idx[r.sq_candidato]
            meu_escore = escores.iloc[i]
            dist = (escores - meu_escore).abs()
            # aliado = mesma banda ou banda vizinha; adversario = 2 ou mais de distancia
            aliado = dist <= 1
            adversario = dist >= 2

            for lado, mascara in (("aliado", aliado), ("adversario", adversario)):
                cand = np.where(mascara.values)[0]
                cand = cand[cand != i]
                if not len(cand):
                    continue
                ordem = cand[np.argsort(-PRESSAO[i, cand])][:TOP_RIVAIS]
                for rank, j in enumerate(ordem, 1):
                    if PRESSAO[i, j] <= 0:
                        continue
                    # municipios onde os dois mais se encostam
                    contato = M[i] * FORCA[j]
                    top = np.argsort(-contato)[:3]
                    linhas.append({
                        "ano": ano,
                        "sq_candidato": r.sq_candidato,
                        "deputado": r.nome_urna,
                        "partido": r.sigla_partido,
                        "banda": bandas.iloc[i],
                        "lado": lado,
                        "rank": rank,
                        "rival": info["nome_urna"].iloc[j],
                        "rival_partido": info["sigla_partido"].iloc[j],
                        "rival_banda": bandas.iloc[j],
                        "rival_eleito": bool(info["eleito"].iloc[j]),
                        "rival_votos": int(info["votos_total"].iloc[j]),
                        "afinidade": round(float(AFIN[i, j]), 4),
                        "pressao": round(float(PRESSAO[i, j]) * 100, 2),
                        "municipios_disputados": " | ".join(
                            nomes_mun[codigos[k]] for k in top if contato[k] > 0),
                    })
        print(f"[{ano}] {len(m)} candidatos comparados")

    out = pd.DataFrame(linhas)
    out.to_csv(cfg.PROCESSED / "rivais.csv", index=False, encoding="utf-8")
    print(f"\nrivais.csv: {len(out)} linhas")

    print("\n=== pressao mediana sofrida pelos eleitos, por lado ===")
    p = out[out["rank"] == 1].groupby(["ano", "lado"])["pressao"].median().unstack()
    print(p.round(2).to_string())

    print("\n=== o rival numero 1 e' aliado ou adversario ideologico? ===")
    mais = (out.sort_values("pressao", ascending=False)
              .groupby(["ano", "sq_candidato"]).first().reset_index())
    print((mais.groupby(["ano", "lado"]).size().unstack(fill_value=0)).to_string())

    # ---- o rival n.1 ser aliado e' achado ou artefato? ----
    # Se a maioria das candidaturas ja esta na mesma faixa ideologica, "aliado"
    # sairia como rival n.1 por acaso. Comparamos com a expectativa e, sobretudo,
    # com o teste pareado: para o MESMO deputado, o aliado pressiona mais que o
    # adversario? Esse segundo controla a composicao por completo.
    print("\n=== rival n.1 aliado: observado vs esperado por acaso ===")
    base = []
    for ano in cfg.ANOS:
        m = met[(met["ano"] == ano) & (met["votos_total"] >= MIN_VOTOS_RIVAL)].copy()
        m["esc"] = m["partido_norm"].map(escore).fillna(3).astype(int)
        el = m[m["eleito"]]
        fr = [float((( m.loc[m["sq_candidato"] != e.sq_candidato, "esc"] - e.esc)
                     .abs() <= 1).mean()) for e in el.itertuples()]
        r1 = (out[out["ano"] == ano].sort_values("pressao", ascending=False)
                 .groupby("sq_candidato").first())
        base.append({"ano": ano,
                     "esperado_pct": round(float(np.mean(fr)) * 100, 1),
                     "observado_pct": round(float((r1["lado"] == "aliado").mean()) * 100, 1)})
    b = pd.DataFrame(base)
    b["excesso_pp"] = (b["observado_pct"] - b["esperado_pct"]).round(1)
    print(b.to_string(index=False))

    print("\n=== teste pareado: aliado pressiona mais que adversario? ===")
    for ano in cfg.ANOS:
        r = out[(out["ano"] == ano) & (out["rank"] == 1)]
        piv = r.pivot_table(index="sq_candidato", columns="lado",
                            values="pressao").dropna()
        dif = piv["aliado"] - piv["adversario"]
        print(f"  {ano}: mediana {dif.median():+.2f} pp | aliado pressiona mais "
              f"em {int((dif > 0).sum())} de {len(dif)} eleitos")

    print("\n=== 2022: os dez pares de maior pressao ===")
    d = out[out["ano"] == 2022].nlargest(10, "pressao")
    print(d[["deputado", "partido", "lado", "rival", "rival_partido",
             "pressao", "afinidade", "municipios_disputados"]].to_string(index=False))


if __name__ == "__main__":
    main()
