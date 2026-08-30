"""Vereador em TODOS os municipios de uma UF, 2000 a 2024 — o piloto de Goias.

`24_vereador_capitais.py` extrai UMA cidade por estado: a capital. Foi a escolha
certa enquanto a aba era uma vitrine, e virou o limite da aba no momento em que
ela ganhou a gaveta "Qual sua cidade?" — uma lista de 27 cidades num pais de
5.570 diz mais sobre o que nao servimos do que sobre o que servimos.

Este arquivo tira a capital do centro: a unidade passa a ser o municipio, e a
capital vira um municipio como os outros. Goias e' o piloto — 246 municipios,
que e' escala suficiente para o formato quebrar se estiver errado e pequena o
bastante para consertar.

**O download e' nacional, e isso muda a conta da expansao.** O zip do TSE nao
tem recorte por UF: baixar Goias custa exatamente o que custaria baixar o
Brasil. O que separa piloto de expansao e' CPU e payload, nao rede — e a
consequencia pratica e' que expandir depois exige um novo passe de download.
Nao e' desperdicio escondido, e' o preco de acertar o formato antes de gravar
5.570 arquivos.

**O gate e' de cobertura, e ele ja pegou coisa.** Ao fim de cada ano o script
confere os municipios encontrados contra `dim_municipio.csv`, que tem os 246 de
Goias, e NOMEIA os que faltam. Um municipio ausente do arquivo do TSE e um
municipio que existe e nao foi lido sao indistinguiveis num total agregado — e
o segundo caso apagaria uma cidade inteira do mapa sem mover nenhum numero de
lugar.

**Municipio novo nao e' erro.** Goias tem 246 municipios desde 1998, mas a serie
comeca em 2000 e o pareamento e' por nome: mudanca de grafia no cadastro do TSE
aparece aqui como municipio faltando num ano e sobrando no seguinte. Por isso o
relatorio separa "faltou" de "sobrou" em vez de so contar.
"""
import subprocess
import sys
import unicodedata
import zipfile
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

ANOS = [2000, 2004, 2008, 2012, 2016, 2020, 2024]
CD_VEREADOR = 13
COLS_VOTO = ["QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]


# O nome do municipio e' chave de pareamento, e o TSE grafa o mesmo municipio de
# dois jeitos em dois arquivos do mesmo ano: `eleitorado_local_votacao` escreve
# "SAO JOAO D'ALIANCA" e `votacao_secao` escreve "SAO JOAO D ALIANCA". Por isso
# a normalizacao vem de `04_geo`, que tira pontuacao e colapsa espaco, e nao de
# um `sem_acento` que so' tira acento: com o segundo, duas cidades de Goias
# sairam sem mapa nenhum.

def sem_acento(t):
    """So' acento: e' a chave de NOME DE PESSOA, verificada pelo teste-ouro."""
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def chave_mun(t):
    """Chave de NOME DE MUNICIPIO - ver nota acima."""
    return geo.normalizar(t)


def baixar(ano):
    zp = cfg.RAW / f"votacao_candidato_munzona_{ano}.zip"
    if zp.exists():
        try:
            with zipfile.ZipFile(zp):
                return zp
        except zipfile.BadZipFile:
            zp.unlink()
    cmd = ["curl.exe", "-sS", "--fail", "--max-time", "3600", "-o", str(zp)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(cfg.TSE_URL.format(ano=ano))
    for t in range(1, 4):
        print(f"[{ano}] baixando... (tentativa {t})", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        # validar abrindo o zip, nunca pelo tamanho: um download truncado de
        # 554 MB ja passou por um teste que so' olhava bytes
        if r.returncode == 0 and zp.exists():
            try:
                with zipfile.ZipFile(zp):
                    return zp
            except zipfile.BadZipFile:
                pass
        zp.unlink(missing_ok=True)
    raise RuntimeError(f"[{ano}] download falhou em 3 tentativas")


def extrair(uf, ano, esperados):
    saida = cfg.INTERIM / f"veruf_{uf}_{ano}.csv"
    if saida.exists():
        print(f"[{ano}] ja extraido", flush=True)
        return None

    zp = baixar(ano)
    try:
        with zipfile.ZipFile(zp) as zf:
            alvo = [n for n in zf.namelist()
                    if n.upper().endswith(f"_{ano}_{uf}.CSV")]
            if not alvo:
                print(f"  [{ano}/{uf}] sem membro no zip", flush=True)
                return None
            with zf.open(alvo[0]) as fh:
                df = pd.read_csv(fh, sep=";", encoding="latin-1", quotechar='"',
                                 dtype=str, low_memory=False)
    finally:
        zp.unlink(missing_ok=True)

    df.columns = [c.strip().upper() for c in df.columns]
    for c in COLS_VOTO:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    d = df[(pd.to_numeric(df["CD_CARGO"], errors="coerce") == CD_VEREADOR)
           & (pd.to_numeric(df["NR_TURNO"], errors="coerce") == 1)].copy()
    if d.empty:
        print(f"  [{ano}/{uf}] nenhuma linha de vereador", flush=True)
        return None

    d["NM_NORM"] = d["NM_MUNICIPIO"].map(chave_mun)
    cols = [c for c in ("ANO_ELEICAO", "CD_MUNICIPIO", "NM_MUNICIPIO", "NM_NORM",
                        "NR_ZONA", "SQ_CANDIDATO", "NM_CANDIDATO",
                        "NM_URNA_CANDIDATO", "NR_CANDIDATO", "SG_PARTIDO",
                        "NM_PARTIDO", "NM_COLIGACAO", "DS_SIT_TOT_TURNO",
                        "SG_FEDERACAO", "DS_SITUACAO_CANDIDATURA")
            if c in d.columns]
    agg = d.groupby(cols, dropna=False, as_index=False)[COLS_VOTO].sum()
    agg.to_csv(saida, index=False, encoding="utf-8")

    achados = set(agg["NM_NORM"])
    falta = sorted(esperados - achados) if esperados else []
    sobra = sorted(achados - esperados) if esperados else []
    print(f"  [{ano}/{uf}] {len(agg):,} linhas | "
          f"{agg['SQ_CANDIDATO'].nunique():,} candidaturas | "
          f"{len(achados)} municipios" + (f" de {len(esperados)}" if esperados else ""), flush=True)
    if falta:
        print(f"     FALTAM {len(falta)}: {', '.join(falta[:12])}"
              f"{' ...' if len(falta) > 12 else ''}", flush=True)
    if sobra:
        print(f"     SOBRAM {len(sobra)}: {', '.join(sobra[:12])}"
              f"{' ...' if len(sobra) > 12 else ''}", flush=True)
    return {"ano": ano, "falta": falta, "sobra": sobra, "achados": len(achados)}


def main():
    uf = (sys.argv[1] if len(sys.argv) > 1 else "GO").upper()
    # `dim_municipio.csv` e' a malha de GOIAS, com os 246 ja' pareados ao
    # IBGE. Usa-la como referencia de outra UF diria "faltam 246" em toda
    # linha, e um alarme falso ensina a ignorar alarme: fora de GO o gate se
    # cala, e diz que se calou.
    if uf == "GO":
        dim = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype=str)
        esperados = set(dim["nome_norm"].map(chave_mun))
        print(f"{uf}: {len(esperados)} municipios esperados\n", flush=True)
    else:
        esperados = set()
        print(f"{uf}: sem malha de referencia — extrai sem gate de "
              "cobertura", flush=True)

    rel = []
    for ano in ANOS:
        r = extrair(uf, ano, esperados)
        if r:
            rel.append(r)

    print("\n=== cobertura por pleito ===", flush=True)
    for r in rel:
        print(f"  {r['ano']}: {r['achados']:>3} municipios"
              f"{'  (faltam ' + str(len(r['falta'])) + ')' if r['falta'] else ''}",
              flush=True)


if __name__ == "__main__":
    main()
