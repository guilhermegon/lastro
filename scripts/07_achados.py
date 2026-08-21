"""Apura os numeros citados em docs/ACHADOS.md.

Cada bloco impresso corresponde a uma afirmacao do documento de inferencias.
Rodar de novo e a forma de conferir que nenhum numero do texto foi inventado.
"""
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

pd.set_option("display.width", 200)


def sec(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def main():
    met = pd.read_csv(cfg.PROCESSED / "metricas_candidato.csv")
    mm = pd.read_csv(cfg.PROCESSED / "metricas_municipio.csv",
                     dtype={"cod_ibge": str})
    mp = pd.read_csv(cfg.PROCESSED / "metricas_partido.csv")
    ple = pd.read_csv(cfg.PROCESSED / "dim_pleito.csv")
    el = met[met["eleito"]].copy()

    sec("1. GEOGRAFIA: dispersao 1998-2018 e reversao em 2022")
    print(el.groupby("ano").agg(
        mun_efetivo=("n_municipios_efetivo", "median"),
        top1_share=("top1_share", "median"),
        dominancia=("dominancia_ponderada", "median"),
        contiguidade=("contiguidade", "median"),
        mun_com_voto=("n_municipios", "median")).round(2).to_string())
    print("\nmesma leitura para TODOS os candidatos com >= 5.000 votos:")
    g = met[met["votos_total"] >= 5000]
    print(g.groupby("ano").agg(
        n=("sq_candidato", "size"),
        mun_efetivo=("n_municipios_efetivo", "median"),
        top1_share=("top1_share", "median")).round(2).to_string())

    sec("2. TIPOLOGIA dos eleitos (share %)")
    t = el.groupby(["ano", "tipologia"]).size().unstack(fill_value=0)
    print((t.div(t.sum(axis=1), axis=0) * 100).round(1).to_string())

    sec("3. CUSTO DO VOTO: quociente e margem de corte")
    p = ple.copy()
    p["custo_por_cadeira"] = (p["total_nominais_uf"] / cfg.N_CADEIRAS).round(0)
    p["ultimo_eleito_vs_QE"] = (p["votos_ultimo_eleito"] /
                                p["quociente_eleitoral_aprox"] * 100).round(1)
    print(p[["ano", "total_nominais_uf", "n_candidatos", "quociente_eleitoral_aprox",
             "votos_ultimo_eleito", "ultimo_eleito_vs_QE",
             "votos_mais_votado"]].to_string(index=False))
    print("\ncandidatos por cadeira:")
    print((p["n_candidatos"] / cfg.N_CADEIRAS).round(1).tolist())

    sec("4. EFICIENCIA: eleitos de base estreita vs ampla")
    el["base_estreita"] = el["top1_share"] >= 40
    print(el.groupby("ano").agg(
        pct_base_estreita=("base_estreita", lambda s: round(s.mean() * 100, 1)),
        votos_por_municipio=("votos_por_municipio", "median"),
        mun_dominio_25=("n_mun_dominio_25", "median"),
        mun_dominio_50=("n_mun_dominio_50", "sum")).to_string())

    sec("5. PODER MUNICIPAL: captura")
    print(mm.groupby("ano").agg(
        n_municipios=("cod_ibge", "size"),
        pct_capturado_25=("capturado_25", lambda s: round(s.mean() * 100, 1)),
        pct_capturado_50=("capturado_50", lambda s: round(s.mean() * 100, 1)),
        cand_efetivo_mediano=("n_candidatos_efetivo", "median"),
        top1_share_mediano=("top1_share", "median")).to_string())

    sec("5b. captura x porte do municipio (2022)")
    m22 = mm[mm["ano"] == 2022].copy()
    m22["faixa"] = pd.cut(m22["total_nominais"],
                          [0, 2000, 5000, 15000, 50000, 10 ** 9],
                          labels=["ate 2k", "2k-5k", "5k-15k", "15k-50k", "50k+"])
    print(m22.groupby("faixa", observed=True).agg(
        n=("cod_ibge", "size"),
        top1_share=("top1_share", "median"),
        cand_efetivo=("n_candidatos_efetivo", "median"),
        pct_capturado_25=("capturado_25", lambda s: round(s.mean() * 100, 1))
    ).round(2).to_string())
    print("\ncorrelacao log(porte) x top1_share, por ano:")
    for ano, g2 in mm.groupby("ano"):
        r = np.corrcoef(np.log(g2["total_nominais"]), g2["top1_share"])[0, 1]
        print(f"  {ano}: r = {r:.3f}")

    sec("5d. JANELA DE CAPTURA: top1_share mediano por porte, todos os anos")
    faixas = [0, 2000, 5000, 10000, 15000, 25000, 50000, 10 ** 9]
    rot = ["<2k", "2-5k", "5-10k", "10-15k", "15-25k", "25-50k", ">50k"]
    mm2 = mm.assign(faixa=pd.cut(mm["total_nominais"], faixas, labels=rot))
    print(mm2.pivot_table(index="ano", columns="faixa", values="top1_share",
                          aggfunc="median", observed=True).round(1).to_string())
    print("\n% de municipios capturados (top1 >= 25%):")
    print(mm2.pivot_table(index="ano", columns="faixa", values="capturado_25",
                          aggfunc="mean", observed=True).mul(100).round(0).to_string())
    print("\nn. de municipios por faixa (2022):")
    print(mm2[mm2["ano"] == 2022].groupby("faixa", observed=True).size().to_string())

    sec("5c. maiores dominios municipais de 2022")
    print(el[el["ano"] == 2022].nlargest(10, "dominancia_max")[
        ["nome_urna", "sigla_partido", "votos_total", "reduto_nome",
         "dominancia_max", "top1_share", "n_municipios_efetivo"]]
          .rename(columns={"reduto": "cod"}).to_string(index=False))

    sec("6. PARTIDOS: puxador e canibalizacao (partidos com >=3 candidatos)")
    f = mp[(mp["n_candidatos"] >= 3) & mp["similaridade_media_intrapartido"].notna()]
    print(f.groupby("ano").agg(
        n_partidos=("partido_norm", "size"),
        similaridade_mediana=("similaridade_media_intrapartido", "median"),
        share_puxador_mediano=("share_puxador", "median")).round(3).to_string())
    print("\n2022, partidos por n. de eleitos:")
    print(mp[mp["ano"] == 2022].nlargest(8, "n_eleitos")[
        ["nome_linhagem", "n_candidatos", "n_eleitos", "votos_total",
         "share_puxador", "similaridade_media_intrapartido"]].to_string(index=False))

    sec("7. FEDERACOES em 2022")
    m22c = met[met["ano"] == 2022]
    # Candidatos fora de federacao aparecem como "#NULO#"/"#NE", nao como vazio.
    marca = m22c["federacao"].astype(str).str.upper()
    fed = m22c[~marca.isin(["#NULO#", "#NE", "NAN", ""])]
    print(f"candidatos em federacao: {len(fed)} de {len(m22c)} "
          f"({len(fed)/len(m22c)*100:.1f}%)")
    print(f"eleitos por federacao: {int(fed['eleito'].sum())} de "
          f"{int(m22c['eleito'].sum())}")
    if len(fed):
        print(fed.groupby("federacao").agg(
            n=("sq_candidato", "size"), eleitos=("eleito", "sum"),
            votos=("votos_total", "sum")).to_string())

    sec("8. DINAMICA: estabilidade das bases entre pleitos consecutivos")
    r = met[met["reincidente"]]
    print(r.groupby("ano").agg(
        n_reincidentes=("sq_candidato", "size"),
        similaridade_mediana=("similaridade_pleito_anterior", "median"),
        variacao_mediana_pct=("variacao_votos_pct", "median")).round(3).to_string())
    print("\nsomente eleitos:")
    re = el[el["reincidente"]]
    print(re.groupby("ano").agg(
        n=("sq_candidato", "size"),
        similaridade_mediana=("similaridade_pleito_anterior", "median")
    ).round(3).to_string())

    sec("9. RENOVACAO: quantos eleitos ja tinham concorrido antes")
    print(el.groupby("ano").agg(
        n_eleitos=("sq_candidato", "size"),
        pct_reincidentes=("reincidente", lambda s: round(s.mean() * 100, 1))
    ).to_string())

    sec("10. OS 10 MAIS VOTADOS DE 2022 e seu perfil territorial")
    print(el[el["ano"] == 2022].nlargest(10, "votos_total")[
        ["nome_urna", "sigla_partido", "votos_total", "n_municipios",
         "n_municipios_efetivo", "top1_share", "dominancia_ponderada",
         "reduto_nome", "tipologia"]].to_string(index=False))

    sec("11. GOIANIA: peso e fragmentacao")
    goi = mm[mm["nome"].str.startswith("Goiânia", na=False)]
    tot_uf = ple.set_index("ano")["total_nominais_uf"]
    goi = goi.assign(peso_uf=(goi["total_nominais"] /
                              goi["ano"].map(tot_uf) * 100).round(2))
    print(goi[["ano", "total_nominais", "peso_uf", "n_candidatos_com_voto",
               "n_candidatos_efetivo", "top1_share"]].to_string(index=False))


if __name__ == "__main__":
    main()
