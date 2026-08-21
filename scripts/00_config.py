"""Configuracao compartilhada do pipeline RASTRO.

Painel: distribuicao espacial do voto para deputado estadual em Goias, 1998-2022.
Fonte: TSE, dados abertos (votacao_candidato_munzona).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# RASTRO_DATA aponta o diretorio de dados para fora do projeto. Sem a variavel, nada
# muda: continua `data/` aqui dentro.
# Serve para dois casos. (1) Disco apertado: a ingestao chega a ~1,2 GB de pico e os
# dados finais ocupam ~134 MB. (2) Projeto em pasta sincronizada (OneDrive, Dropbox) -
# ai e' obrigatorio: a ingestao grava zips de ate 587 MB e os apaga segundos depois, o
# sincronizador tenta subir cada um, e sincronizacao durante escrita produz copia em
# conflito, que num diretorio de dados vira duplicata silenciosa.
DATA = Path(os.environ.get("RASTRO_DATA") or (ROOT / "data")).resolve()

RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
OVERRIDES = DATA / "overrides"
DOCS = ROOT / "docs"
DIST = ROOT / "dist"

for _d in (RAW, INTERIM, PROCESSED, OVERRIDES, DOCS, DIST):
    _d.mkdir(parents=True, exist_ok=True)

ANOS = [1998, 2002, 2006, 2010, 2014, 2018, 2022]
UF = "GO"
UF_IBGE = 52          # codigo IBGE de Goias
CD_CARGO_DEP_EST = 7  # mantido: o teste-ouro e o painel original sao deste cargo

# Codigos de cargo do TSE. 2 e 4 sao os vices; 8 = distrital, so no DF.
# Presidente e governador sao majoritarios e podem ter segundo turno - por isso
# a ingestao guarda NR_TURNO em vez de filtrar o 1o turno na origem.
CARGOS = {1: "presidente", 3: "governador", 5: "senador",
          6: "federal", 7: "estadual"}
CARGOS_MAJORITARIOS = ("presidente", "governador", "senador")
CARGOS_DOIS_TURNOS = ("presidente", "governador")

# Cadeiras por cargo. O Senado renova alternadamente 1/3 e 2/3, entao o numero
# de vagas muda de pleito para pleito e nao pode ser constante como os outros.
N_CADEIRAS = 41       # tamanho da ALEGO
N_CADEIRAS_CARGO = {
    "presidente": {a: 1 for a in ANOS},
    "governador": {a: 1 for a in ANOS},
    "estadual": {a: 41 for a in (1998, 2002, 2006, 2010, 2014, 2018, 2022)},
    "federal": {a: 17 for a in (1998, 2002, 2006, 2010, 2014, 2018, 2022)},
    "senador": {1998: 1, 2002: 2, 2006: 1, 2010: 2, 2014: 1, 2018: 2, 2022: 1},
}
N_MUNICIPIOS = 246    # Goias, estavel em toda a janela 1998-2022

# Votos por eleitor em cada cargo. No Senado com duas vagas o eleitor vota duas
# vezes, entao o total de votos do cargo chega a quase o dobro dos demais - em
# 2010 foram 4,9 milhoes contra 2,8 do estadual. Comparar "fatia do estado"
# entre cargos sem dividir por isto superestima o Senado pela metade.
VOTOS_POR_ELEITOR = {
    "presidente": {a: 1 for a in ANOS},
    "governador": {a: 1 for a in ANOS},
    "estadual": {a: 1 for a in ANOS},
    "federal": {a: 1 for a in ANOS},
    "senador": {1998: 1, 2002: 2, 2006: 1, 2010: 2, 2014: 1, 2018: 2, 2022: 1},
}

TSE_URL = ("https://cdn.tse.jus.br/estatistica/sead/odsele/"
           "votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip")

IBGE_MALHA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/{uf}"
    "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria"
)

# O CDN do TSE responde 403 a clientes HTTP comuns, a requisicoes HEAD e a
# requisicoes com Range. So passa em GET simples com o conjunto completo de
# cabecalhos de navegador abaixo. Nao adicionar -I nem -r ao curl.
CURL_HEADERS = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language: pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding: gzip, deflate, br",
    'sec-ch-ua: "Chromium";v="124", "Google Chrome";v="124"',
    'sec-ch-ua-platform: "Windows"',
    "Sec-Fetch-Dest: document",
    "Sec-Fetch-Mode: navigate",
    "Sec-Fetch-Site: none",
    "Upgrade-Insecure-Requests: 1",
    "Connection: keep-alive",
]

# Faixas exatas do painel original, mantidas para comparabilidade lado a lado.
FAIXAS_VOTACAO = [0, 200, 500, 1500, 5000, 15000]
FAIXAS_INFLUENCIA = [0.0, 1.5, 5.0, 10.0, 25.0, 50.0]

# Teste-ouro extraido do painel original (ALVARO GUIMARAES, DEM).
GOLDEN_SERIE = {1998: 12160, 2002: 12398, 2006: 18646,
                2010: 27074, 2014: 35660, 2018: 23788}
# Casamos pelo nome completo: o nome de urna varia na serie e em 2006 o
# proprio TSE registrou com erro de digitacao ("ALAVARO GUIMARAES").
GOLDEN_NOME = "ALVARO SOARES GUIMARAES"
GOLDEN_CONCENTRACAO_2018 = {   # municipio -> (votos, % do total do deputado)
    "ITUMBIARA": (6559, 27.57),
    "GOIANIA": (1607, 6.76),
    "GOIATUBA": (1346, 5.66),
    "BOM JESUS DE GOIAS": (1272, 5.35),
    "CACHOEIRA DOURADA": (1060, 4.46),
}
GOLDEN_DOMINANCIA_2018 = {     # municipio -> (votos, total do municipio, %)
    "AGUA LIMPA": (554, 1532, 36.16),
    "PANAMA": (553, 1563, 35.38),
    "NOVA AURORA": (339, 1280, 26.48),
    "CACHOEIRA DOURADA": (1060, 4080, 25.98),
}
