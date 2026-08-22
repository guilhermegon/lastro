# Modelo de dados — RASTRO

Modelo estrela em `data/processed/`, pronto para importar no Power BI Desktop ou em
qualquer ferramenta que aceite CSV. Todos os arquivos são UTF-8, separados por vírgula.

## Tabelas

### `dim_municipio.csv` — 246 linhas
Uma linha por município de Goiás. Chave: `cod_ibge` (texto de 7 dígitos — **importe como
texto**, não como número, ou o zero à esquerda de outros estados se perde).

| Coluna | Descrição |
|---|---|
| `cod_ibge` | Código IBGE do município (chave) |
| `nome` | Nome oficial do IBGE |
| `nome_norm` | Nome em caixa alta sem acento, usado no pareamento com o TSE |
| `microrregiao`, `mesorregiao` | Recortes do IBGE |
| `n_vizinhos` | Municípios que fazem fronteira, derivado da malha |

### `dim_candidato.csv` — 4.128 linhas
Uma linha por candidatura, ou seja, por par candidato × ano. Chave: `ano` + `sq_candidato`.

| Coluna | Descrição |
|---|---|
| `ano`, `sq_candidato` | Chave composta |
| `nome` | Nome completo — é a identidade estável entre pleitos |
| `nome_urna`, `numero` | Nome e número na urna |
| `sigla_partido` | Sigla **à época do pleito** |
| `partido_norm`, `nome_linhagem` | Sigla e nome depois de resolver fusões e renomeações |
| `federacao` | Federação em 2022; `#NULO#` quando não há |
| `coligacao`, `composicao_coligacao` | Coligação proporcional, até 2014 |
| `situacao` | `ELEITO`, `ELEITO POR QP`, `ELEITO POR MEDIA`, `MEDIA`, `SUPLENTE`, `NAO ELEITO` |
| `eleito` | Booleano já resolvido — use este, não a string |
| `votos_total`, `n_municipios` | Totais do candidato no pleito |

### `fato_votos.csv` — 263.664 linhas
A tabela-fato. Grão: **ano × candidato × município**. Linhas com zero votos foram
descartadas.

| Coluna | Descrição |
|---|---|
| `ano`, `sq_candidato`, `cod_ibge` | Chaves para as três dimensões |
| `votos` | Votos nominais |

### `fato_total_municipio.csv` — 1.718 linhas
Grão: ano × município. Total de votos nominais apurados para deputado estadual no
município — é o **denominador do mapa de Influência**. Existe como tabela separada
porque é uma agregação sobre todos os candidatos, e no Power BI calcular isso como
medida sobre `fato_votos` exige `ALLEXCEPT`, que é fácil de errar.

### `dim_pleito.csv` — 7 linhas
Uma linha por eleição: `total_nominais_uf`, `n_candidatos`, `n_eleitos`,
`votos_ultimo_eleito`, `votos_mais_votado`, `quociente_eleitoral_aprox`,
`n_municipios_com_voto`.

### Tabelas de métricas
`metricas_candidato.csv` (ano × candidato), `metricas_municipio.csv` (ano × município)
e `metricas_partido.csv` (ano × partido) trazem os índices já calculados por
`scripts/05_metricas.py`. Use-as se não quiser reimplementar HHI, Gini e similaridade
de cosseno em DAX — nenhuma delas é confortável em DAX.

### `go_municipios.geojson`
Malha municipal do IBGE simplificada (411 KB, qualidade intermediária, Douglas-Peucker
com tolerância 0,004°). Para o visual de mapa do Power BI (Shape Map ou Azure Maps),
a chave de junção é `cod_ibge`.

### `adjacencia_municipios.json`
`{cod_ibge: [vizinhos]}`, derivado de arestas compartilhadas na malha. Média de 5,3
vizinhos, nenhum município isolado. Insumo das métricas de contiguidade.

## Relacionamentos

```
dim_pleito (ano) ──1:N── fato_votos (ano)
dim_candidato (ano + sq_candidato) ──1:N── fato_votos
dim_municipio (cod_ibge) ──1:N── fato_votos
dim_municipio (cod_ibge) ──1:N── fato_total_municipio
```

No Power BI, `dim_candidato` precisa de uma **chave composta**: crie uma coluna
`ano & "-" & sq_candidato` nas duas pontas e relacione por ela, ou marque o
relacionamento como muitos-para-muitos filtrando por `ano` numa tabela separada.

## Medidas equivalentes em DAX

```dax
Votos = SUM ( fato_votos[votos] )

Total do Município =
    CALCULATE (
        SUM ( fato_total_municipio[total_nominais_municipio] ),
        REMOVEFILTERS ( dim_candidato )
    )

-- eixo do mapa VOTAÇÃO do painel original
Votos do Deputado = [Votos]

-- eixo do mapa INFLUÊNCIA: fatia do deputado no total apurado no município
Influência % = DIVIDE ( [Votos], [Total do Município] )

-- coluna "% do total do deputado" da tabela de Concentração
Concentração % =
    DIVIDE ( [Votos], CALCULATE ( [Votos], REMOVEFILTERS ( dim_municipio ) ) )

Municípios com Voto = DISTINCTCOUNT ( fato_votos[cod_ibge] )

Quociente Eleitoral =
    DIVIDE ( CALCULATE ( [Votos], REMOVEFILTERS ( dim_candidato ) ), 41 )

-- concentração: some sobre municípios o quadrado da fatia de cada um
HHI =
    SUMX (
        VALUES ( dim_municipio[cod_ibge] ),
        VAR fatia =
            DIVIDE ( [Votos], CALCULATE ( [Votos], REMOVEFILTERS ( dim_municipio ) ) )
        RETURN fatia * fatia
    )

Municípios Efetivos = DIVIDE ( 1, [HHI] )
```

As faixas do painel original, para reproduzir a legenda:

- **Votação** (votos nominais): nenhum / até 200 / 200–500 / 500–1.500 / 1.500–5.000 / 5.000–15.000
- **Influência** (% do município): nenhum / até 1,5% / 1,5–5% / 5–10% / 10–25% / 25–50%

## Armadilhas conhecidas nesta base

Documentadas aqui porque nenhuma delas é visível no dado e todas alteram resultados:

1. **A coluna de votos muda de ano para ano.** Em 1998, `QT_VOTOS_NOMINAIS` vem
   inteiramente **zerada** e os votos reais estão em `QT_VOTOS_NOMINAIS_VALIDOS`. Em
   2002 a coluna `_VALIDOS` sequer existe. `scripts/03_normalize.py` escolhe por ano a
   coluna cuja soma estadual é maior que zero.

2. **`MÉDIA` é uma situação de eleito.** Até 2010 o TSE marcava o eleito por média
   apenas como `MEDIA`; de 2014 em diante passou a `ELEITO POR MÉDIA`. Filtrar por
   `situacao = "ELEITO"` devolve 35 a 38 eleitos em vez de 41.

3. **1998 tem candidatos duplicados.** Quatro números de urna aparecem com dois
   `SQ_CANDIDATO` — um com a candidatura superada (`INDEFERIDO`/`RENÚNCIA`) e outro
   `DEFERIDO` — repetindo os **mesmos** votos nas duas linhas. Somar tudo infla o ano
   em 3.352 votos e cria candidatos fantasmas.

4. **Nomes de município do TSE não são os do IBGE.** Nove grafias divergem em 1998 e
   2002 (`AGUAS LINDAS`, `BOM JESUS`, `CESARINA`, `MUNDO NOVO DE GOIAS`,
   `SAO LUIS DOS MONTES BELOS`, `TEREZINHA DE GOIAS`, `VALPARAIZO`…). O pareamento é
   por nome normalizado com correções em `data/overrides/municipios_tse_ibge.csv`.

5. **O mesmo nome aparece com e sem acento** conforme o ano, e o `SQ_CANDIDATO` muda a
   cada pleito. A chave de pessoa é o nome completo sem acento.

6. **O dado bruto é por município *e zona eleitoral*.** Sem agregar zona → município,
   um município com duas zonas vira duas linhas.

7. **`SQ_CANDIDATO` não é único entre anos.** O TSE reaproveita o sequencial: Frederico
   Nassif tem o mesmo `SQ_CANDIDATO` em 2010, quando foi suplente, e em 2014, quando se
   elegeu por quociente. Qualquer chave que use só o SQ mistura as duas candidaturas —
   no nosso caso a bancada federal passou a ter 19 nomes em vez de 17, com "eleitos" de
   699 votos. A chave é sempre **(ano, SQ_CANDIDATO)**.

8. **Presidente não está no arquivo da UF.** É cargo nacional: no zip de
   `votacao_candidato_munzona`, os votos para presidente estão no membro `_BR.csv`, e
   não no `_GO.csv`. É preciso ler os dois e recortar Goiás do nacional. O zip de 1998
   não tem membro `_BR`, então presidente cobre 2002 a 2022.

9. **`DS_SIT_TOT_TURNO` vem vazio em alguns anos.** Em 2006 e 2010, todas as linhas de
   presidente trazem `#NULO`. Não dá para derivar o vencedor dali, e tampouco dos votos:
   presidente é cargo nacional e Goiás pode ter votado no derrotado — o que de fato
   ocorreu nos dois anos.

10. **`votacao_secao` mistura candidatos com branco, nulo e legenda.** `SQ_CANDIDATO`
    igual a `-1` é branco/nulo e `-3` é voto de legenda, um por partido. Sem filtrar,
    "VOTO BRANCO" aparece como o candidato mais votado da cidade.

11. **Coordenada ausente vem como `-1.0`**, não como vazio, em
    `eleitorado_local_votacao`. Plotar sem filtrar joga pontos no Golfo da Guiné.

12. **O card "Nº de municípios" do painel original é sempre 246**: conta o universo
   exibido no mapa, não os municípios em que o deputado teve voto (Álvaro Guimarães
   teve voto em 190 dos 246 em 2018).


## Rivais territoriais (`web/{UF}/rivais_{cargo}.json`)

Um arquivo por UF e por cargo, e só nos proporcionais. Nos majoritários cada
partido lança um nome e a disputa não se dá dentro de uma lista: ali "rival"
seria o próprio adversário da eleição, que a tela do cargo já mostra inteiro.

| Campo | O que é |
|---|---|
| `pr` | **pressão** — % do voto do eleito que está em municípios onde o rival também é forte, ponderado pela força do rival ali. **Assimétrica**: um gigante pressiona um pequeno muito mais do que o contrário |
| `af` | **afinidade** — cosseno entre os dois vetores municipais. Simétrica; mede formato do mapa, não tamanho |
| `mun` | índices, em `base.json`, dos três municípios onde os dois mais se encostam |
| `b` | banda ideológica, de `partidos_espectro.csv` |

Corte de mil votos: abaixo disso o vetor municipal é ruído, não geografia.

### A aferição, e por que ela está no arquivo

O achado aparente é "o rival nº 1 costuma ser um aliado ideológico". Ele não
sobrevive sozinho: se a maioria das candidaturas já está na mesma faixa, aliado
venceria por acaso. Por isso cada pleito carrega três números:

- `esperado` — fração média de candidaturas na mesma banda do eleito. É o acaso.
- `observado` — fração de eleitos cujo rival nº 1 é de fato aliado.
- `pareado` — **o único que sobrevive sozinho**: para o MESMO eleito, quanto o
  aliado mais pressionante pressiona a mais que o adversário mais pressionante.
  Controla a composição por completo.

Medido nas 27 unidades, `observado` acompanha `esperado` de perto — o achado
aparente é, em boa parte, composição do campo. O pareado é positivo em quase
todos os pleitos, mas pequeno (ordem de +1 a +3 pp). A leitura honesta é
**território e ideologia são pouco acoplados**, não "aliados se canibalizam".

## Vereador nas capitais (`web/{UF}/vereador.json`)

26 capitais, 2000 a 2024. Brasília não entra: elege distrital, não vereador.

**Não há mapa, e não é omissão.** Uma capital é um município só — o coroplético
que sustenta o resto do projeto aqui não existe. A única desagregação territorial
que o arquivo do TSE oferece dentro da cidade é a zona eleitoral, e não há malha
pública de zona: a geografia entra como distribuição, não como desenho.

Duas armadilhas que a replicação amplia, tratadas no código e não só no texto:

- **O número e o traçado das zonas mudam entre pleitos**, e de forma diferente
  em cada cidade. Zonas efetivas nunca viram série temporal — só valem dentro de
  um ano — e a similaridade com o pleito anterior só é calculada quando o número
  de zonas bate. Devolver um número sobre zonas redesenhadas seria comparar dois
  mapas diferentes fingindo que são o mesmo.
- **A escala não se compara entre capitais.** Rio de Janeiro tem 49 zonas e São
  Paulo 57; Macapá, Boa Vista e Vitória têm 2. **Palmas tem 1 nos sete pleitos** —
  lá não há geografia interna nenhuma, e a tela diz isso em vez de desenhar uma
  barra de 100%.
