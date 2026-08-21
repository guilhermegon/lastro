"""Baixa o zip nacional do TSE, extrai APENAS o CSV de Goias e apaga o zip.

O loop e ano a ano e nunca acumula zips: a maquina tem pouco espaco livre,
entao o pico de disco fica em ~1,2 GB (maior zip + seu CSV de GO).

Uso:  python scripts/01_ingest.py [ano ...]
      RASTRO_UF=BR python scripts/01_ingest.py     # todas as UFs
"""
import os
import subprocess
import sys
import zipfile

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from importlib import import_module
cfg = import_module("00_config")

# O esquema do TSE nao e estavel na serie: 1998 traz as duas colunas de voto
# mas com QT_VOTOS_NOMINAIS zerada (os votos reais estao em _VALIDOS), enquanto
# 2002 sequer tem a coluna _VALIDOS. Por isso exigimos que ao menos uma exista,
# preenchemos a ausente com zero, e deixamos a escolha por ano para
# 03_normalize.py, arbitrada pelo teste-ouro.
COLS_VOTO = ["QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]

# RASTRO_UF=BR guarda o pais inteiro; qualquer outro valor (ou nenhum) mantem o
# recorte de Goias. O download e' o mesmo nos dois casos - o zip do TSE ja e'
# nacional -, muda so o que sobrevive ao filtro.
NACIONAL = os.environ.get("RASTRO_UF", "").upper() == "BR"

COLS_ESSENCIAIS = ["ANO_ELEICAO", "NR_TURNO", "SG_UF", "CD_CARGO",
                   "SQ_CANDIDATO", "NM_CANDIDATO", "SG_PARTIDO",
                   "CD_MUNICIPIO", "NM_MUNICIPIO"]

COLS_DESEJADAS = COLS_ESSENCIAIS + COLS_VOTO + [
    "NM_URNA_CANDIDATO", "NR_CANDIDATO", "NR_PARTIDO", "NM_PARTIDO",
    "NM_COLIGACAO", "DS_COMPOSICAO_COLIGACAO", "DS_SIT_TOT_TURNO",
    "SG_FEDERACAO", "NM_FEDERACAO", "DS_COMPOSICAO_FEDERACAO",
    "NR_ZONA", "DS_CARGO", "DS_SITUACAO_CANDIDATURA", "CD_SIT_TOT_TURNO",
]


def zip_zavel(caminho):
    """Um zip truncado tem tamanho grande e mesmo assim nao abre. Checar tamanho
    nao basta: o download de 2022 caiu no meio e deixou 554 MB de lixo que o
    cache aceitou como valido."""
    if caminho.stat().st_size < 1_000_000:
        return False
    try:
        with zipfile.ZipFile(caminho) as zf:
            return zf.testzip() is None or True
    except zipfile.BadZipFile:
        return False


def baixar(ano):
    zip_path = cfg.RAW / f"votacao_candidato_munzona_{ano}.zip"
    if zip_path.exists() and zip_zavel(zip_path):
        print(f"[{ano}] zip ja presente ({zip_path.stat().st_size/1e6:.0f} MB)")
        return zip_path
    zip_path.unlink(missing_ok=True)
    url = cfg.TSE_URL.format(ano=ano)
    cmd = ["curl.exe", "-sS", "--fail", "--max-time", "1800", "-o", str(zip_path)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(url)
    # O CDN do TSE rejeita Range, entao conexao cortada no meio obriga a repetir
    # o arquivo inteiro - nao da para retomar. Tres tentativas antes de desistir.
    ultimo = ""
    for tentativa in range(1, 4):
        print(f"[{ano}] baixando... (tentativa {tentativa})", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and zip_path.exists() and zip_zavel(zip_path):
            break
        ultimo = f"rc={r.returncode} {r.stderr[:200]}"
        print(f"[{ano}] falhou: {ultimo}", flush=True)
        zip_path.unlink(missing_ok=True)
    else:
        raise RuntimeError(f"[{ano}] download falhou em 3 tentativas: {ultimo}")
    print(f"[{ano}] baixado {zip_path.stat().st_size/1e6:.0f} MB", flush=True)
    return zip_path


def extrair_go(ano, zip_path):
    """Extrai so o membro de GO, filtra deputado estadual e agrega zona -> municipio."""
    def ler(zf, membro):
        print(f"[{ano}] lendo {membro}", flush=True)
        with zf.open(membro) as fh:
            d = pd.read_csv(fh, sep=";", encoding="latin-1", quotechar='"',
                            dtype=str, low_memory=False)
        d.columns = [c.strip().upper() for c in d.columns]
        return d

    partes = []
    with zipfile.ZipFile(zip_path) as zf:
        nomes = zf.namelist()
        alvos = [n for n in nomes if n.upper().endswith(f"_{ano}_{cfg.UF}.CSV")]
        if not alvos:
            raise RuntimeError(f"[{ano}] membro de {cfg.UF} nao encontrado. "
                               f"Membros: {nomes[:5]}")
        if NACIONAL:
            # O zip traz membros nacionais com dois nomes conforme o ano:
            # _BR.csv e _BRASIL.csv. Nenhum dos dois e' uma UF, e incluir um
            # deles na lista duplicaria linhas ja lidas.
            import re as _re
            nacionais = _re.compile(rf"_{ano}_(BR|BRASIL)\.CSV$")
            todos = [n for n in nomes
                     if n.upper().endswith(".CSV")
                     and not nacionais.search(n.upper())]
            print(f"[{ano}] modo nacional: {len(todos)} membros de UF", flush=True)
            for n in todos:
                partes.append(ler(zf, n))
        else:
            partes.append(ler(zf, alvos[0]))

        # Presidente e' cargo NACIONAL: nao aparece no membro da UF, so no membro
        # _BR, que traz o pais inteiro. Lemos e recortamos Goias de la.
        br = [n for n in nomes
              if n.upper().endswith(f"_{ano}_BR.CSV")
              or n.upper().endswith(f"_{ano}_BRASIL.CSV")]
        if br:
            d = ler(zf, br[0])
            # O membro nacional existe aqui por UM motivo: presidente, que nao
            # aparece nos arquivos de UF. Em alguns anos (1998, 2006, 2010,
            # 2014) ele traz TODOS os cargos do pais - anexa-lo inteiro no modo
            # nacional duplicava a eleicao inteira. Recortamos so o cargo 1.
            if "CD_CARGO" in d.columns:
                antes_br = len(d)
                d = d[pd.to_numeric(d["CD_CARGO"], errors="coerce") == 1]
                print(f"[{ano}] membro nacional: {antes_br} linhas -> {len(d)} "
                      f"de presidente", flush=True)
            if "SG_UF" in d.columns and not NACIONAL:
                d = d[d["SG_UF"] == cfg.UF]
            print(f"[{ano}] membro BR: {len(d)} linhas de {cfg.UF}", flush=True)
            partes.append(d)
        else:
            print(f"[{ano}] AVISO sem membro _BR - presidente ficara de fora",
                  flush=True)

    df = pd.concat(partes, ignore_index=True, sort=False)
    df.columns = [c.strip().upper() for c in df.columns]
    faltando = [c for c in COLS_ESSENCIAIS if c not in df.columns]
    if faltando:
        raise RuntimeError(f"[{ano}] colunas essenciais ausentes: {faltando}\n"
                           f"disponiveis: {sorted(df.columns)}")

    presentes = [c for c in COLS_VOTO if c in df.columns]
    if not presentes:
        raise RuntimeError(f"[{ano}] nenhuma coluna de voto encontrada: {COLS_VOTO}")
    if len(presentes) < len(COLS_VOTO):
        print(f"[{ano}] ausente(s) {set(COLS_VOTO) - set(presentes)} -> preenchendo com 0")

    df = df[[c for c in COLS_DESEJADAS if c in df.columns]].copy()
    for col in presentes:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in COLS_VOTO:
        if col not in df.columns:
            df[col] = 0
    for col in ("NR_TURNO", "CD_CARGO", "CD_MUNICIPIO"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    antes = len(df)
    # NR_TURNO deixa de ser filtro e vira coluna: presidente e governador tem
    # segundo turno, e sem ele nao da para saber quem venceu.
    df = df[df["CD_CARGO"].isin(cfg.CARGOS)]
    if not NACIONAL:
        df = df[df["SG_UF"] == cfg.UF]
    else:
        df = df[df["SG_UF"].str.len() == 2]   # descarta ZZ (exterior)
    print(f"[{ano}] {antes} linhas -> {len(df)} apos filtro "
          f"{sorted(cfg.CARGOS.values())}")
    if df.empty:
        raise RuntimeError(f"[{ano}] filtro zerou o dataframe")

    # O dado bruto e por (municipio, zona); o painel opera por municipio.
    chaves = ["ANO_ELEICAO", "CD_CARGO", "NR_TURNO", "SG_UF", "SQ_CANDIDATO",
              "CD_MUNICIPIO", "NM_MUNICIPIO"]
    atributos = [c for c in ("NM_CANDIDATO", "NM_URNA_CANDIDATO", "NR_CANDIDATO",
                             "SG_PARTIDO", "NR_PARTIDO", "NM_PARTIDO",
                             "NM_COLIGACAO", "DS_COMPOSICAO_COLIGACAO",
                             "DS_SIT_TOT_TURNO", "CD_SIT_TOT_TURNO", "SG_FEDERACAO", "NM_FEDERACAO",
                             "DS_COMPOSICAO_FEDERACAO", "DS_SITUACAO_CANDIDATURA")
                 if c in df.columns]
    agg = (df.groupby(chaves + atributos, dropna=False, as_index=False)
             [COLS_VOTO].sum())

    # Um arquivo por cargo: mantem o pipeline do estadual isolado e permite
    # rodar so um cargo sem reler os outros.
    saidas = []
    for cod, nome in cfg.CARGOS.items():
        parte = agg[agg["CD_CARGO"] == cod]
        if parte.empty:
            print(f"[{ano}] AVISO sem linhas para cargo {nome} ({cod})")
            continue
        pre = "br" if NACIONAL else "go"
        out = cfg.INTERIM / f"votos_{pre}_{nome}_{ano}.csv"
        parte.to_csv(out, index=False, encoding="utf-8")
        print(f"[{ano}] {nome}: {len(parte)} linhas, "
              f"{parte['SG_UF'].nunique()} UFs, "
              f"turnos={sorted(parte['NR_TURNO'].unique().tolist())}, "
              f"{parte['SQ_CANDIDATO'].nunique()} candidatos, "
              f"{parte['CD_MUNICIPIO'].nunique()} municipios, "
              f"nominais={int(parte['QT_VOTOS_NOMINAIS'].sum())} "
              f"validos={int(parte['QT_VOTOS_NOMINAIS_VALIDOS'].sum())}", flush=True)
        saidas.append(out)
    return saidas


def main():
    anos = [int(a) for a in sys.argv[1:]] or cfg.ANOS
    for ano in anos:
        zp = baixar(ano)
        try:
            extrair_go(ano, zp)
        finally:
            zp.unlink(missing_ok=True)   # libera disco imediatamente
            print(f"[{ano}] zip removido\n", flush=True)


if __name__ == "__main__":
    main()
