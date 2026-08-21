"""Teste-ouro: reproduz numeros lidos diretamente do painel original do TSE/GO.

Se qualquer valor divergir, o erro esta na coluna de voto escolhida, no filtro
de cargo/turno, ou na agregacao zona -> municipio. O pipeline nao segue sem isso.
"""
import sys
import unicodedata
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

falhas = []


def checa(rotulo, obtido, esperado, tol=0):
    ok = abs(obtido - esperado) <= tol
    print(f"  {'OK ' if ok else 'FALHA'} {rotulo}: obtido={obtido} esperado={esperado}")
    if not ok:
        falhas.append(rotulo)


def main():
    fato = pd.read_csv(cfg.PROCESSED / "fato_votos.csv", dtype={"cod_ibge": str})
    cand = pd.read_csv(cfg.PROCESSED / "dim_candidato.csv")
    mun = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype={"cod_ibge": str})
    totm = pd.read_csv(cfg.PROCESSED / "fato_total_municipio.csv",
                       dtype={"cod_ibge": str})

    cand["nome_norm"] = cand["nome"].map(geo.normalizar)
    alvo = cand[cand["nome_norm"] == cfg.GOLDEN_NOME]
    print(f"candidato-ouro '{cfg.GOLDEN_NOME}': {len(alvo)} registros "
          f"nos anos {sorted(alvo['ano'].tolist())}")
    if alvo.empty:
        raise SystemExit("candidato do teste-ouro nao encontrado")

    print("\n--- serie historica de votos nominais ---")
    for ano, esperado in cfg.GOLDEN_SERIE.items():
        linha = alvo[alvo["ano"] == ano]
        obtido = int(linha["votos_total"].iloc[0]) if len(linha) else -1
        checa(f"{ano}", obtido, esperado)

    a18 = alvo[alvo["ano"] == 2018]
    if a18.empty:
        raise SystemExit("sem registro de 2018 para o candidato-ouro")
    sq = a18["sq_candidato"].iloc[0]
    print(f"\npartido em 2018: {a18['sigla_partido'].iloc[0]} | "
          f"situacao: {a18['situacao'].iloc[0]}")
    # O card "N. de municipios" do painel original marca 246 para todo deputado:
    # e a contagem do universo exibido no mapa, nao dos municipios com voto.
    # Este deputado teve voto em 190 dos 246 em 2018 - por isso a faixa
    # "1: Nenhum Voto" existe na legenda.
    print(f"municipios com >=1 voto em 2018: {int(a18['n_municipios'].iloc[0])} "
          f"de {cfg.N_MUNICIPIOS} (card do original mostra o universo, 246)")

    v = (fato[(fato["ano"] == 2018) & (fato["sq_candidato"] == sq)]
         .merge(mun[["cod_ibge", "nome"]], on="cod_ibge")
         .merge(totm[totm["ano"] == 2018][["cod_ibge", "total_nominais_municipio"]],
                on="cod_ibge"))
    v["nome_norm"] = v["nome"].map(geo.normalizar)
    total = int(v["votos"].sum())
    v["pct_do_deputado"] = (v["votos"] / total * 100).round(2)
    v["pct_do_municipio"] = (v["votos"] / v["total_nominais_municipio"] * 100).round(2)

    print("\n--- tabela A: concentracao (votos e % do total do deputado) ---")
    for nome, (votos, pct) in cfg.GOLDEN_CONCENTRACAO_2018.items():
        r = v[v["nome_norm"] == nome]
        checa(f"{nome} votos", int(r["votos"].iloc[0]) if len(r) else -1, votos)
        checa(f"{nome} % do deputado",
              float(r["pct_do_deputado"].iloc[0]) if len(r) else -1, pct, tol=0.01)

    # A tabela B depende do DENOMINADOR (total de nominais do municipio), e ai o
    # painel original nao e reproduzivel. Dos 20 municipios que ele lista, 7 batem
    # exatamente com nossa apuracao e os demais divergem em ate ~0,5%, para cima em
    # uns e para baixo em outros (Apore diverge no sentido oposto ao de Itumbiara).
    # Isso descarta a hipotese de categoria de voto faltando e aponta para um
    # extrato mais antigo do TSE, anterior a revisoes de totalizacao. Nosso numero
    # tem confirmacao independente: a soma dos candidatos em
    # votacao_candidato_munzona e a coluna QT_VOTOS_NOMINAIS_VALIDOS de
    # detalhe_votacao_munzona coincidem exatamente. Dai a tolerancia de 1% aqui,
    # contra a exigencia de igualdade exata na tabela A.
    # Por isso a tabela B e REPORTADA, nao exigida: afrouxar a tolerancia ate ela
    # passar seria ajustar o teste ao dado. O portao rigido e a tabela A.
    print("\n--- tabela B: dominancia (comparacao reportada, nao e portao) ---")
    linhas = []
    for nome, (votos, tot_mun, pct) in cfg.GOLDEN_DOMINANCIA_2018.items():
        r = v[v["nome_norm"] == nome]
        obtido = int(r["total_nominais_municipio"].iloc[0]) if len(r) else -1
        linhas.append({"municipio": nome, "denominador_painel": tot_mun,
                       "denominador_nosso": obtido, "dif": obtido - tot_mun,
                       "dif_pct": round((obtido - tot_mun) / tot_mun * 100, 2),
                       "pct_painel": pct,
                       "pct_nosso": float(r["pct_do_municipio"].iloc[0]) if len(r) else -1})
    print(pd.DataFrame(linhas).to_string(index=False))

    print("\n--- top 5 municipios calculados (conferencia visual) ---")
    print(v.nlargest(5, "votos")[["nome", "votos", "pct_do_deputado",
                                  "total_nominais_municipio", "pct_do_municipio"]]
          .to_string(index=False))

    print()
    if falhas:
        raise SystemExit(f"TESTE-OURO FALHOU em {len(falhas)} itens: {falhas}")
    print("TESTE-OURO PASSOU: o pipeline reproduz o painel original.")


if __name__ == "__main__":
    main()
