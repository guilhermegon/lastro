# Cadê o Voto?

Produto de **Lastro — Inteligência Política**.

Geografia do voto sobre os dados abertos do TSE: onde cada candidato tirou voto,
município a município, de 1998 a 2024.

Reconstrói o painel Power BI público do TSE/GO — *Distribuição Espacial do Desempenho
Eleitoral dos Deputados Estaduais (1998 a 2018)* — a partir dos dados abertos do TSE,
estende a série ao pleito de 2022 e acrescenta os índices de concentração e domínio que
o painel original não calcula.

- **Painel interativo:** https://claude.ai/code/artifact/60c14ca5-bff2-4693-bc23-3eca535f3944
- **Inferências:** [`docs/ACHADOS.md`](docs/ACHADOS.md)
- **Modelo de dados e medidas DAX:** [`docs/MODELO.md`](docs/MODELO.md)

## Rodar o pipeline

Requer Python 3 com `pandas` e `numpy`, e `curl.exe` no PATH. A ingestão baixa cerca de
2 GB do CDN do TSE, um pleito de cada vez, apagando cada arquivo assim que extrai a
parte de Goiás — o pico de uso de disco fica em torno de 1,2 GB.

```bash
python scripts/01_ingest.py     # baixa os 7 pleitos e extrai Goiás (etapa longa)
python scripts/04_geo.py        # malha do IBGE, simplificação e adjacência
python scripts/03_normalize.py  # modelo estrela + linhagem partidária
python scripts/05_metricas.py   # índices de concentração, domínio e dinâmica
python scripts/06_verifica.py   # teste-ouro contra o painel original
python scripts/07_achados.py    # números citados em docs/ACHADOS.md
python scripts/08_payload.py    # JSON compacto do painel
python scripts/09_build_html.py # HTML autocontido em dist/
```

`06_verifica.py` é o portão: ele reproduz números lidos diretamente do painel original
(a série de Álvaro Guimarães e as suas tabelas de 2018) e sai com erro se algum divergir.
Rode-o depois de qualquer mudança em `03_normalize.py`.

## Como está organizado ?

```
scripts/     pipeline numerado, na ordem de execução
data/raw/    transitório — nada aqui é preservado entre execuções
data/interim/     votos_go_{ano}.csv, já filtrados para deputado estadual em GO
data/processed/   modelo estrela + geojson + métricas
data/overrides/   correções manuais: nomes de município e linhagem partidária
docs/        ACHADOS.md (inferências) e MODELO.md (esquema e DAX)
dist/        template.html, dados.json e o painel construído
```

## O que o painel acrescenta ao original

O original é uma consulta caso a caso: escolha um deputado, veja dois mapas e duas
tabelas. Este acrescenta os índices por deputado (número efetivo de municípios, Gini,
domínio ponderado, contiguidade, tipologia), a alternância entre as faixas fixas do
original e quantis, o pleito de 2022, e uma aba de padrões agregados que responde
perguntas que o original não formula — como a captura municipal se distribui por porte
de município, quanto os candidatos de um mesmo partido se canibalizam, e quanto custa a
cadeira marginal em cada pleito.

## Ressalva principal

A votação de cada deputado por município é reproduzida **exatamente**. Já o total de
votos nominais do município — denominador do mapa de Influência — não é reproduzível a
partir da base atual do TSE: o painel original foi construído sobre um extrato anterior
a revisões de totalização. Detalhes em [`docs/ACHADOS.md`](docs/ACHADOS.md).
