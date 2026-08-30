"""Traz o Distrito Federal para o painel, equiparando distrital a estadual.

O DF elege **deputado distrital** (cargo 8 no TSE), nao estadual (cargo 7). Como
`cfg.CARGOS` nunca incluiu o 8, o DF era a unica unidade da federacao sem casa
legislativa no painel: tinha presidente, governador, senador e federal, e nao
tinha a assembleia. A Camara Legislativa do DF exerce as competencias de
assembleia estadual E de camara municipal, e os 24 distritais sao o equivalente
funcional dos deputados estaduais — equipara-los e' o que torna o painel
completo.

**Por que um script a parte, e nao mudar `cfg.CARGOS`.** Mudar a constante faria
a ingestao inteira ser refeita: sete anos, 27 UFs, cinco cargos, horas de
download, e o teste-ouro de Goias no meio do caminho. O cargo 8 so existe no DF,
entao o alcance real da mudanca e' uma UF. Este script baixa so o que falta,
produz so o DF, e ANEXA as linhas ao interim existente. Nada do que ja' passou
no teste-ouro e' reprocessado.

**O que o DF nao tem, e a tela precisa dizer.** O DF e' um municipio so. Toda a
geografia deste produto — concentracao municipal, dominio, contiguidade, o mapa
— pressupoe varios municipios, e no DF ela degenera: o candidato tem 100% do
voto no seu unico municipio por construcao, nao por forca politica. O que
continua valendo e' tudo que nao depende de territorio: lista de eleitos,
quociente eleitoral, votos do ultimo eleito, analise partidaria, e a comparacao
nacional de custo da cadeira.

A geografia intra-DF existe por ZONA ELEITORAL, e e' o mesmo caso do vereador de
capital (`24_`): ha' distribuicao por zona e nao ha' malha publicada de zona,
entao ha' numero e nao ha' mapa. Fica para uma camada seguinte.

**O esquema do interim muda de ano para ano, e presumir que nao muda corrompe
o arquivo.** A primeira versao deste script montou a lista de colunas a partir de
2022 — 23 colunas, com os tres campos de federacao — e anexou isso a todos os
anos. Os arquivos de 2002, 2006, 2010 e 2014 tem 20 colunas: a federacao so
existe de 2018 em diante. As linhas entraram desalinhadas em quatro arquivos, e
a leitura com `usecols` mascarou o estrago porque so tocava as primeiras colunas.

O reparo foi remover as linhas com contagem de campos diferente do cabecalho —
eram exatamente as anexadas, contiguas no fim — e o teste-ouro de Goias voltou a
passar identico. A licao virou codigo: agora o alvo e' lido primeiro, e o DF e'
alinhado ao cabecalho DELE.

**Em 1998 o DF nao tem arquivo proprio.** O zip daquele ano traz 26 CSV por UF
mais um `..._1998_BRASIL.csv`, e o Distrito Federal esta' dentro do BRASIL — nao
entre os 26. Procurar so' por `_1998_DF.csv` devolve nada, e "nada" ali se leria
como "o DF nao elegeu distrital em 1998", que e' falso: elegeu 24, com 594
candidatos. O BRASIL tem 44 colunas contra as 23 do arquivo por UF, entao a
selecao das colunas do ano vale igual.

E 1998 traz a armadilha ja' documentada: `QT_VOTOS_NOMINAIS` vem zerada e os
votos estao em `QT_VOTOS_NOMINAIS_VALIDOS` — 872.072 para os distritais. As duas
colunas sao carregadas como estao; quem escolhe por ano e' o `03_normalize`,
arbitrado pelo teste-ouro.

**O CDN do TSE recusa cliente HTTP comum.** So passa em GET simples com o
conjunto completo de cabecalhos de navegador, via `curl.exe` — nao usar `-I` nem
`-r`, que reativam o bloqueio. Os zips sao nacionais (ate' 587 MB) e nao ha'
arquivo por UF; cada um e' apagado logo apos a extracao do CSV do DF.
"""
import shutil
import subprocess
import unicodedata
import sys
import zipfile
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

CD_DISTRITAL = 8
URL = ("https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona"
       "/votacao_candidato_munzona_{ano}.zip")
COLS = ["ANO_ELEICAO", "CD_CARGO", "NR_TURNO", "SG_UF", "SQ_CANDIDATO",
        "CD_MUNICIPIO", "NM_MUNICIPIO", "NM_CANDIDATO", "NM_URNA_CANDIDATO",
        "NR_CANDIDATO", "SG_PARTIDO", "NR_PARTIDO", "NM_PARTIDO",
        "NM_COLIGACAO", "DS_COMPOSICAO_COLIGACAO", "DS_SIT_TOT_TURNO",
        "CD_SIT_TOT_TURNO", "SG_FEDERACAO", "NM_FEDERACAO",
        "DS_COMPOSICAO_FEDERACAO", "DS_SITUACAO_CANDIDATURA",
        "QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def baixa(ano, destino):
    """GET simples com os cabecalhos completos — ver docstring."""
    cmd = ["curl.exe", "-sS", "-L", "--max-time", "1800",
           "-o", str(destino)] + [x for h in cfg.CURL_HEADERS for x in ("-H", h)]
    cmd.append(URL.format(ano=ano))
    r = subprocess.run(cmd, capture_output=True)
    return r.returncode == 0 and destino.exists() and destino.stat().st_size > 1e6


def extrai_df(zipe, ano):
    """So o CSV do DF sai do zip nacional. O resto nem toca o disco.

    Em 1998 nao ha' arquivo do DF: ele esta' dentro do BRASIL — ver docstring.
    Nesse caso le o BRASIL inteiro e recorta a UF."""
    with zipfile.ZipFile(zipe) as z:
        nomes = z.namelist()
        alvo = next((n for n in nomes
                     if n.upper().endswith(f"_{ano}_DF.CSV")), None)
        recorta = False
        if not alvo:
            alvo = next((n for n in nomes
                         if n.upper().endswith(f"_{ano}_BRASIL.CSV")), None)
            recorta = True
        if not alvo:
            return None
        with z.open(alvo) as f:
            d = pd.read_csv(f, sep=";", encoding="latin-1", quotechar='"',
                            low_memory=False)
    if recorta:
        print(f"   (sem arquivo do DF; recortando de {alvo.split('/')[-1]})",
              flush=True)
        d = d[d["SG_UF"] == "DF"]
    return d


def main():
    inter = cfg.INTERIM
    inter.mkdir(parents=True, exist_ok=True)
    raw = cfg.RAW
    raw.mkdir(parents=True, exist_ok=True)

    resumo = []
    for ano in cfg.ANOS:
        alvo = inter / f"votos_br_estadual_{ano}.csv"
        if not alvo.exists():
            print(f"{ano}: {alvo.name} não existe — rode 01_ingest.py antes")
            continue
        # O cabecalho DO ANO manda: ver docstring. Le so a primeira linha.
        colsAno = list(pd.read_csv(alvo, nrows=0).columns)
        ja = pd.read_csv(alvo, usecols=["SG_UF"], low_memory=False)
        if "DF" in set(ja["SG_UF"]):
            print(f"{ano}: DF já está no interim, pulando")
            continue

        zipe = raw / f"munzona_{ano}.zip"
        print(f"{ano}: baixando o zip nacional...", flush=True)
        if not baixa(ano, zipe):
            print(f"   FALHOU o download de {ano}")
            zipe.unlink(missing_ok=True)
            continue
        mb = zipe.stat().st_size / 1e6
        print(f"   {mb:.0f} MB, extraindo o DF...", flush=True)
        try:
            d = extrai_df(zipe, ano)
        finally:
            # o disco e' apertado: o zip sai assim que o CSV do DF esta' em memoria
            zipe.unlink(missing_ok=True)
        if d is None:
            print(f"   sem CSV do DF em {ano}")
            continue

        for c in ("CD_CARGO", "NR_TURNO"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d = d[(d["CD_CARGO"] == CD_DISTRITAL) & (d["NR_TURNO"] == 1)]
        if d.empty:
            print(f"   nenhum distrital em {ano}")
            continue

        # equiparado: entra no arquivo do estadual com o codigo do estadual.
        # A equiparacao e' feita AQUI e uma vez, para o resto do pipeline nao
        # precisar saber que o DF e' diferente.
        d["CD_CARGO"] = cfg.CD_CARGO_DEP_EST
        for c in colsAno:
            if c not in d.columns:
                d[c] = pd.NA      # coluna que o ano do TSE nao traz
        d = d[colsAno]            # ordem e numero exatos do arquivo alvo

        # o grao do interim e' municipio, nao zona: agrega antes de anexar
        chaves = [c for c in colsAno if c not in
                  ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS")]
        d = (d.groupby(chaves, dropna=False, as_index=False)
             [["QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]].sum())

        cand = d["SQ_CANDIDATO"].nunique()
        votos = int(d["QT_VOTOS_NOMINAIS"].sum())
        # A MESMA regra do 19_: `startswith` mais a lista fechada. Um
        # `contains("ELEITO")` casaria com "NAO ELEITO" — foi o que a primeira
        # versao fez, e relatou 286 eleitos numa Casa de 24.
        SIT_OK = ("ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA", "MEDIA")
        sit = d["DS_SIT_TOT_TURNO"].astype(str).map(sem_acento)
        eleitos = d[sit.str.startswith("ELEITO") | sit.isin(SIT_OK)][
            "SQ_CANDIDATO"].nunique()

        # Gate: o numero de campos tem de bater com o cabecalho do ano. Sem
        # isto, o append corrompe em silencio e so' se descobre quando o pandas
        # falha ao ler o arquivo inteiro, muito depois.
        if len(d.columns) != len(colsAno):
            print(f"   ABORTADO: {len(d.columns)} colunas contra "
                  f"{len(colsAno)} do arquivo")
            continue
        d.to_csv(alvo, mode="a", header=False, index=False)

        resumo.append((ano, cand, eleitos, votos))
        print(f"   {cand} candidatos, {eleitos} eleitos, {votos:,} votos "
              f"anexados a {alvo.name}", flush=True)

    if resumo:
        print("\n=== distritais do DF, equiparados a estaduais ===")
        print("   ano   candidatos  eleitos       votos")
        for ano, c, e, v in resumo:
            print(f"   {ano}   {c:>9}  {e:>7}  {v:>11,}")
        print("\nAgora rode, nesta ordem:")
        print("   03_normalize.py estadual")
        print("   19_nacional_completo.py")
        print("   22_publicar_web.py")
        print("   06_verifica.py    <- o teste-ouro de Goiás, que NÃO pode mudar")
    else:
        print("\nNada anexado.")


if __name__ == "__main__":
    main()
