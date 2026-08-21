"""Consolida os CSVs anuais no modelo estrela e roda o teste-ouro.

Resolve tres coisas que o dado bruto do TSE nao entrega prontas:
  1. qual coluna de voto vale em cada ano (o esquema varia na serie);
  2. o pareamento dos municipios do TSE com os codigos do IBGE;
  3. a linhagem partidaria, para que a serie 1998-2022 seja comparavel.
"""
import json
import sys
import unicodedata
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")
normalizar = geo.normalizar

# Ate 2010 o TSE marcava o eleito por media apenas como "MEDIA"; de 2014 em
# diante passou a "ELEITO POR MEDIA"/"ELEITO POR QP". Sem tratar as duas formas
# a contagem de eleitos fica abaixo das 41 cadeiras da ALEGO.
SIT_ELEITO = ("ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA", "MEDIA")


def sem_acento(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).upper().strip()


def escolher_coluna_voto(df, ano):
    """O TSE preenche ora QT_VOTOS_NOMINAIS, ora QT_VOTOS_NOMINAIS_VALIDOS."""
    somas = {c: int(df[c].sum()) for c in
             ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS") if c in df.columns}
    validas = {c: s for c, s in somas.items() if s > 0}
    if not validas:
        raise RuntimeError(f"[{ano}] nenhuma coluna de voto tem soma > 0: {somas}")
    col = ("QT_VOTOS_NOMINAIS" if "QT_VOTOS_NOMINAIS" in validas
           else "QT_VOTOS_NOMINAIS_VALIDOS")
    print(f"[{ano}] coluna de voto: {col} (somas={somas})")
    return col


def carregar_ano(ano, mapa_mun, cargo="estadual"):
    df = pd.read_csv(cfg.INTERIM / f"votos_go_{cargo}_{ano}.csv",
                     dtype=str, low_memory=False)
    for c in ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int64")
    col = escolher_coluna_voto(df, ano)
    df["votos"] = df[col]

    df["nome_norm"] = df["NM_MUNICIPIO"].map(normalizar)
    df["cod_ibge"] = df["nome_norm"].map(mapa_mun)
    orfaos = sorted(df.loc[df["cod_ibge"].isna(), "NM_MUNICIPIO"].unique())
    if orfaos:
        raise RuntimeError(f"[{ano}] municipios sem par no IBGE: {orfaos}")

    df["ano"] = ano
    return remover_registros_duplicados(df, ano)


def remover_registros_duplicados(df, ano):
    """Em 1998 o TSE registra 4 candidatos duas vezes: o mesmo numero de urna
    aparece com dois SQ_CANDIDATO - um com a candidatura ja superada
    (INDEFERIDO/RENUNCIA) e outro DEFERIDO - repetindo os MESMOS votos nas duas
    linhas. Somar as duas inflaria o total do ano em 3.352 votos e criaria
    candidatos fantasmas. Mantemos o registro deferido.
    """
    n_sq = df.groupby("NR_CANDIDATO")["SQ_CANDIDATO"].transform("nunique")
    if (n_sq > 1).sum() == 0:
        return df

    situacao = df.get("DS_SITUACAO_CANDIDATURA", pd.Series("", index=df.index))
    df = df.assign(_ok=situacao.fillna("").str.upper().str.startswith(("DEFERIDO", "APTO")))
    escolhido = (df[n_sq > 1]
                 .sort_values(["_ok", "SQ_CANDIDATO"], ascending=[False, False])
                 .groupby("NR_CANDIDATO")["SQ_CANDIDATO"].first())
    manter = df["SQ_CANDIDATO"].isin(escolhido) | (n_sq == 1)
    removidos = int((~manter).sum())
    print(f"[{ano}] {len(escolhido)} numeros de urna com registro duplicado -> "
          f"{removidos} linhas descartadas")
    return df[manter].drop(columns="_ok")


def sufixo(cargo):
    """O estadual mantem os nomes originais: e' o cargo que o teste-ouro valida."""
    return "" if cargo == "estadual" else f"_{cargo}"


def main(cargo="estadual"):
    base = pd.read_csv(cfg.PROCESSED / "dim_municipio_base.csv", dtype={"cod_ibge": str})
    mapa_mun = dict(zip(base["nome_norm"], base["cod_ibge"]))

    ov = cfg.OVERRIDES / "municipios_tse_ibge.csv"
    if ov.exists():
        extra = pd.read_csv(ov, dtype=str)
        mapa_mun.update(dict(zip(extra["nome_norm_tse"], extra["cod_ibge"])))
        print(f"overrides de municipio aplicados: {len(extra)}")

    linhagem = pd.read_csv(cfg.OVERRIDES / "partidos_linhagem.csv")
    mapa_lin = dict(zip(linhagem["sigla_epoca"].map(sem_acento),
                        linhagem["partido_norm"]))
    mapa_nome_lin = dict(zip(linhagem["partido_norm"], linhagem["nome_linhagem"]))

    anos = [a for a in cfg.ANOS
            if (cfg.INTERIM / f"votos_go_{cargo}_{a}.csv").exists()]
    if len(anos) < len(cfg.ANOS):
        print(f"[{cargo}] sem dado para {sorted(set(cfg.ANOS) - set(anos))}")
    partes = [carregar_ano(a, mapa_mun, cargo) for a in anos]
    df = pd.concat(partes, ignore_index=True)

    # Presidente e governador podem ter 2o turno. Quem venceu so se sabe no
    # ultimo turno realizado, mas a GEOGRAFIA interessante e a do 1o, que tem
    # todos os candidatos - no 2o sobram dois. Entao: vencedor vem de todos os
    # turnos, vetor de votos vem do 1o.
    df["NR_TURNO"] = pd.to_numeric(df["NR_TURNO"], errors="coerce").fillna(1).astype(int)
    # ATENCAO: SQ_CANDIDATO NAO e' unico entre anos - o TSE reaproveita o
    # sequencial. Frederico Nassif tem o mesmo SQ em 2010 (suplente) e 2014
    # (eleito por QP); com chave so de SQ, o "eleito" de 2014 vaza para 2010 e a
    # bancada federal passa a ter 19 nomes. A chave tem de ser (ano, SQ).
    _venc = df.loc[df["DS_SIT_TOT_TURNO"].fillna("").map(sem_acento)
                   .str.startswith("ELEITO"), ["ano", "SQ_CANDIDATO"]]
    venceu = set(zip(_venc["ano"], _venc["SQ_CANDIDATO"]))
    turnos_por_ano = df.groupby("ano")["NR_TURNO"].max().to_dict()
    df = df[df["NR_TURNO"] == 1].copy()

    # ---- fato ----
    fato = (df.groupby(["ano", "SQ_CANDIDATO", "cod_ibge"], as_index=False)["votos"]
              .sum()
              .rename(columns={"SQ_CANDIDATO": "sq_candidato"}))
    fato = fato[fato["votos"] > 0]

    # Quem foi o mais votado EM GOIAS. Para governador coincide com o eleito;
    # para presidente nao necessariamente - e e' justamente essa a leitura util
    # num painel sobre Goias, ainda mais nos anos em que o TSE nao informa o
    # vencedor neste arquivo.
    _tg = fato.groupby(["ano", "sq_candidato"], as_index=False)["votos"].sum()
    _mx = _tg.loc[_tg.groupby("ano")["votos"].idxmax()]
    vencedor_go = set(zip(_mx["ano"], _mx["sq_candidato"]))


    # ---- dimensao candidato ----
    cand = (df.sort_values("votos", ascending=False)
              .groupby(["ano", "SQ_CANDIDATO"], as_index=False)
              .first())
    cand = cand.rename(columns={
        "SQ_CANDIDATO": "sq_candidato", "NM_CANDIDATO": "nome",
        "NM_URNA_CANDIDATO": "nome_urna", "NR_CANDIDATO": "numero",
        "SG_PARTIDO": "sigla_partido", "NM_PARTIDO": "nome_partido",
        "NM_COLIGACAO": "coligacao", "DS_COMPOSICAO_COLIGACAO": "composicao_coligacao",
        "DS_SIT_TOT_TURNO": "situacao", "SG_FEDERACAO": "federacao",
        "DS_SITUACAO_CANDIDATURA": "situacao_candidatura"})
    cols_cand = ["ano", "sq_candidato", "nome", "nome_urna", "numero",
                 "sigla_partido", "nome_partido", "coligacao",
                 "composicao_coligacao", "situacao", "federacao",
                 "situacao_candidatura"]
    cand = cand[[c for c in cols_cand if c in cand.columns]].copy()

    cand["situacao"] = cand["situacao"].fillna("").map(sem_acento)
    venceu_par = pd.Series(list(zip(cand["ano"], cand["sq_candidato"]))
                           ).isin(venceu).values
    cand["eleito"] = (cand["situacao"].str.startswith("ELEITO") |
                      cand["situacao"].isin(SIT_ELEITO) |
                      venceu_par)
    cand["venceu_go"] = pd.Series(list(zip(cand["ano"], cand["sq_candidato"]))
                                  ).isin(vencedor_go).values
    cand["houve_2o_turno"] = (cand["ano"].map(turnos_por_ano)
                              .fillna(1).astype(int) > 1)
    cand["sigla_partido"] = cand["sigla_partido"].fillna("").map(sem_acento)
    cand["partido_norm"] = cand["sigla_partido"].map(mapa_lin)
    faltam = sorted(cand.loc[cand["partido_norm"].isna(), "sigla_partido"].unique())
    if faltam:
        print(f"AVISO siglas sem linhagem (mantidas como estao): {faltam}")
        cand["partido_norm"] = cand["partido_norm"].fillna(cand["sigla_partido"])
    cand["nome_linhagem"] = cand["partido_norm"].map(mapa_nome_lin).fillna(
        cand["partido_norm"])

    tot = fato.groupby(["ano", "sq_candidato"], as_index=False)["votos"].sum() \
              .rename(columns={"votos": "votos_total"})

    nmun = fato.groupby(["ano", "sq_candidato"], as_index=False)["cod_ibge"].nunique() \
               .rename(columns={"cod_ibge": "n_municipios"})
    cand = cand.merge(tot, on=["ano", "sq_candidato"], how="left") \
               .merge(nmun, on=["ano", "sq_candidato"], how="left")
    cand[["votos_total", "n_municipios"]] = \
        cand[["votos_total", "n_municipios"]].fillna(0).astype("int64")

    # ---- dimensao pleito ----
    cadeiras = cfg.N_CADEIRAS_CARGO[cargo]
    pleitos = []
    for ano, g in cand.groupby("ano"):
        eleitos = g[g["eleito"]]
        total_nom = int(g["votos_total"].sum())
        pleitos.append({
            "ano": ano,
            "cargo": cargo,
            "n_cadeiras": cadeiras[ano],
            "total_nominais_uf": total_nom,
            "n_candidatos": int(len(g)),
            "n_eleitos": int(len(eleitos)),
            "votos_ultimo_eleito": int(eleitos["votos_total"].min()) if len(eleitos) else 0,
            "votos_mais_votado": int(g["votos_total"].max()),
            "quociente_eleitoral_aprox": round(total_nom / cadeiras[ano], 1),
            "n_municipios_com_voto": int(
                fato.loc[fato["ano"] == ano, "cod_ibge"].nunique()),
        })
    dim_pleito = pd.DataFrame(pleitos)

    # ---- totais por municipio (denominador da "influencia") ----
    tot_mun = fato.groupby(["ano", "cod_ibge"], as_index=False)["votos"].sum() \
                  .rename(columns={"votos": "total_nominais_municipio"})

    cfg.PROCESSED.mkdir(exist_ok=True)
    sfx = sufixo(cargo)
    fato.to_csv(cfg.PROCESSED / f"fato_votos{sfx}.csv", index=False, encoding="utf-8")
    cand.to_csv(cfg.PROCESSED / f"dim_candidato{sfx}.csv", index=False, encoding="utf-8")
    dim_pleito.to_csv(cfg.PROCESSED / f"dim_pleito{sfx}.csv", index=False,
                      encoding="utf-8")
    tot_mun.to_csv(cfg.PROCESSED / f"fato_total_municipio{sfx}.csv", index=False,
                   encoding="utf-8")
    base.to_csv(cfg.PROCESSED / "dim_municipio.csv", index=False, encoding="utf-8")

    print(f"\n=== dim_pleito [{cargo}] ===")
    print(dim_pleito.to_string(index=False))

    ruins = dim_pleito[dim_pleito["n_eleitos"] != dim_pleito["n_cadeiras"]]
    if len(ruins):
        # Em 2006 e 2010 o TSE deixou DS_SIT_TOT_TURNO como "#NULO" em todas as
        # linhas de presidente, entao o vencedor nao e' derivavel deste arquivo.
        # Nao da para inferir dos votos: presidente e' cargo nacional e Goias
        # pode ter votado no perdedor. Em vez de inventar o resultado ou de
        # travar o pipeline, o ano fica sem vencedor marcado e a coluna
        # "venceu_go" - essa sim derivavel - carrega a leitura util aqui.
        if cargo == "presidente":
            print(f"[{cargo}] AVISO sem vencedor no arquivo do TSE para "
                  f"{ruins['ano'].tolist()} - ver coluna venceu_go")
        else:
            raise RuntimeError(
                f"[{cargo}] anos em que n_eleitos nao bate com as cadeiras:\n"
                f"{ruins[['ano', 'n_eleitos', 'n_cadeiras']].to_string(index=False)}")
    print(f"\nfato_votos: {len(fato)} linhas | dim_candidato: {len(cand)} linhas")
    return fato, cand, tot_mun, base


if __name__ == "__main__":
    alvos = sys.argv[1:] or list(cfg.CARGOS.values())
    for c in alvos:
        main(c)
