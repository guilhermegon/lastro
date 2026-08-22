"""Vereadores das 26 capitais, 2000 a 2024.

Generaliza `12_vereador.py`, que fazia so Goiania, mantendo as duas restricoes
que vem da natureza do dado municipal e nao some por replicar:

1. **Outro ciclo.** Municipal e' 2000, 2004, ... 2024. Nao ha um unico ano em
   comum com os pleitos gerais, entao esta aba nunca cruza com as outras.
2. **Outra geografia.** Uma capital e' um municipio so. O coropletico por
   municipio, que e' a espinha do resto do projeto, aqui nao existe: a unica
   desagregacao territorial que o arquivo do TSE oferece dentro da cidade e' a
   ZONA ELEITORAL. Nao ha malha publicada de zona, entao nao ha mapa - a
   geografia entra como distribuicao por zona.

E a armadilha que a replicacao amplia: **o numero e o desenho das zonas mudam
entre pleitos**, e mudam de forma diferente em cada cidade. Comparar a zona 1 de
Sao Paulo em 2000 com a de 2024 nao e' comparar a mesma coisa, e comparar "zona
media" entre capitais e' pior ainda, porque Sao Paulo tem dezenas e Palmas tem
poucas. Por isso as medidas por zona so valem dentro de um ano e de uma cidade,
e o arquivo carrega `nz` para que a tela possa dizer isso ao leitor.

O Distrito Federal nao entra: Brasilia nao elege vereador, elege distrital.
"""
import json
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
SIT_ELEITO = ("ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA", "MEDIA")
COLS_VOTO = ["QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]

# Duas coisas diferentes, e misturar as duas colocava "GOIANIA" no rotulo da
# aba: CAPITAIS e' chave de pareamento com o TSE (maiuscula, sem acento) e
# NOMES e' o que o leitor ve.
CAPITAIS = {
    "AC": "RIO BRANCO", "AL": "MACEIO", "AP": "MACAPA", "AM": "MANAUS",
    "BA": "SALVADOR", "CE": "FORTALEZA", "ES": "VITORIA", "GO": "GOIANIA",
    "MA": "SAO LUIS", "MT": "CUIABA", "MS": "CAMPO GRANDE",
    "MG": "BELO HORIZONTE", "PA": "BELEM", "PB": "JOAO PESSOA",
    "PR": "CURITIBA", "PE": "RECIFE", "PI": "TERESINA",
    "RJ": "RIO DE JANEIRO", "RN": "NATAL", "RS": "PORTO ALEGRE",
    "RO": "PORTO VELHO", "RR": "BOA VISTA", "SC": "FLORIANOPOLIS",
    "SP": "SAO PAULO", "SE": "ARACAJU", "TO": "PALMAS",
}

NOMES = {
    "AC": "Rio Branco", "AL": "Maceió", "AP": "Macapá", "AM": "Manaus",
    "BA": "Salvador", "CE": "Fortaleza", "ES": "Vitória", "GO": "Goiânia",
    "MA": "São Luís", "MT": "Cuiabá", "MS": "Campo Grande",
    "MG": "Belo Horizonte", "PA": "Belém", "PB": "João Pessoa",
    "PR": "Curitiba", "PE": "Recife", "PI": "Teresina",
    "RJ": "Rio de Janeiro", "RN": "Natal", "RS": "Porto Alegre",
    "RO": "Porto Velho", "RR": "Boa Vista", "SC": "Florianópolis",
    "SP": "São Paulo", "SE": "Aracaju", "TO": "Palmas",
}


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
    cmd = ["curl.exe", "-sS", "--fail", "--max-time", "3600", "-o", str(zp)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(cfg.TSE_URL.format(ano=ano))
    for t in range(1, 4):
        print(f"[{ano}] baixando... (tentativa {t})", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        # validar abrindo o zip, e nao pelo tamanho: um download truncado de
        # 554 MB ja passou por um teste que so olhava bytes
        if r.returncode == 0 and zp.exists():
            try:
                with zipfile.ZipFile(zp):
                    return zp
            except zipfile.BadZipFile:
                pass
        zp.unlink(missing_ok=True)
    raise RuntimeError(f"[{ano}] download falhou em 3 tentativas")


def extrair(ano):
    """Um CSV por capital. O zip e' nacional: le-se o membro de cada UF."""
    pendentes = [uf for uf in CAPITAIS
                 if not (cfg.INTERIM / f"ver_{uf}_{ano}.csv").exists()]
    if not pendentes:
        print(f"[{ano}] ja extraido", flush=True)
        return

    zp = baixar(ano)
    try:
        with zipfile.ZipFile(zp) as zf:
            nomes = zf.namelist()
            for uf in pendentes:
                alvo = [n for n in nomes if n.upper().endswith(f"_{ano}_{uf}.CSV")]
                if not alvo:
                    print(f"  [{ano}/{uf}] sem membro no zip", flush=True)
                    continue
                with zf.open(alvo[0]) as fh:
                    df = pd.read_csv(fh, sep=";", encoding="latin-1", quotechar='"',
                                     dtype=str, low_memory=False)
                df.columns = [c.strip().upper() for c in df.columns]
                for c in COLS_VOTO:
                    if c not in df.columns:
                        df[c] = 0
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
                df["NM_NORM"] = df["NM_MUNICIPIO"].map(sem_acento)
                d = df[(df["NM_NORM"] == CAPITAIS[uf]) &
                       (pd.to_numeric(df["CD_CARGO"], errors="coerce") == CD_VEREADOR) &
                       (pd.to_numeric(df["NR_TURNO"], errors="coerce") == 1)].copy()
                if d.empty:
                    print(f"  [{ano}/{uf}] nenhuma linha em {CAPITAIS[uf]}", flush=True)
                    continue
                cols = [c for c in ("ANO_ELEICAO", "NR_ZONA", "SQ_CANDIDATO",
                                    "NM_CANDIDATO", "NM_URNA_CANDIDATO",
                                    "NR_CANDIDATO", "SG_PARTIDO", "NM_PARTIDO",
                                    "NM_COLIGACAO", "DS_SIT_TOT_TURNO",
                                    "SG_FEDERACAO", "DS_SITUACAO_CANDIDATURA")
                        if c in d.columns]
                agg = d.groupby(cols, dropna=False, as_index=False)[COLS_VOTO].sum()
                agg.to_csv(cfg.INTERIM / f"ver_{uf}_{ano}.csv", index=False,
                           encoding="utf-8")
                print(f"  [{ano}/{uf}] {CAPITAIS[uf]}: {len(agg)} linhas, "
                      f"{agg['SQ_CANDIDATO'].nunique()} cand, "
                      f"{agg['NR_ZONA'].nunique()} zonas", flush=True)
    finally:
        # o zip sai antes do proximo ano: sao ate ~1 GB e ha 31 GB livres
        zp.unlink(missing_ok=True)


def main():
    for ano in ANOS:
        extrair(ano)
    print("\nextracao concluida", flush=True)


if __name__ == "__main__":
    main()
