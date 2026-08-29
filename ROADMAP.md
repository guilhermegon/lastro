# ROADMAP — RAS00 (RASTRO)

Painel da distribuição espacial do voto para deputado estadual em Goiás, 1998–2022.
Reconstrói o relatório Power BI do TSE/GO (1998–2018), estende a série a 2022 e
produz as inferências sobre padrões.

Sigla **RAS** (`RAS00`), definida pelo usuário em 2026-08-21 (TKT-001). No roster
monitorado pelo BEDEL desde essa data. Identidade local em [`CLAUDE.md`](CLAUDE.md).

## Marco 1 — pipeline e painel  ✅ concluído 2026-08-20

- [x] Esqueleto do projeto e configuração compartilhada (`scripts/00_config.py`)
- [x] Ingestão dos 7 pleitos do TSE, ano a ano, sem acumular zips (`01_ingest.py`)
- [x] Malha municipal do IBGE, simplificação e matriz de adjacência (`04_geo.py`)
- [x] Pareamento TSE↔IBGE: 246/246 municípios, 9 correções manuais
- [x] Modelo estrela e linhagem partidária (`03_normalize.py`)
- [x] Métricas de concentração, domínio, canibalização e dinâmica (`05_metricas.py`)
- [x] Teste-ouro contra o painel original (`06_verifica.py`) — passa
- [x] Apuração dos números das inferências (`07_achados.py`)
- [x] Payload e painel HTML autocontido (`08_payload.py`, `09_build_html.py`)
- [x] Publicação do Artifact
- [x] `docs/MODELO.md` — modelo estrela e medidas DAX
- [x] `docs/ACHADOS.md` — inferências
- [x] Textos de ajuda em todos os termos e critérios do painel (2026-08-21)
- [x] Rivais territoriais por posição ideológica (`10_rivais.py`, 2026-08-21)

## Marco 2 — deputado federal, Senado e cruzamentos  ✅ concluído 2026-08-21

- [x] Ingestão generalizada para os três cargos (`01_ingest.py`), com retentativa e
      validação de zip truncado
- [x] Normalização e métricas parametrizadas por cargo, com cadeiras variáveis
      (Senado renova 1 ou 2 vagas por pleito)
- [x] Teste-ouro reconferido após a generalização — continua passando
- [x] Análise cruzada: escala por cargo, arrasto partidário, duplas territoriais
      (`11_cruzado.py`)
- [x] Abas Estadual / Federal / Senado / Padrões / Cruzamentos no painel
- [x] `docs/ACHADOS.md` seções 10 a 12

## Marco 3 — vereadores de Goiânia  ✅ concluído 2026-08-21

- [x] Pipeline próprio do ciclo municipal 2000–2024 (`12_vereador.py`), separado por ser
      outro ciclo e outra geografia
- [x] Aba Vereador · Goiânia com distribuição por zona eleitoral (não há mapa: Goiânia é
      um município só e não existe malha pública de zona)
- [x] `docs/ACHADOS.md` seções 13 e 14

## Marco 4 — presidente, governador e mapa por seção  ✅ concluído 2026-08-21

- [x] Ingestão dos cinco cargos com os dois turnos, lendo também o membro `_BR` do zip
      (presidente é cargo nacional e não está no arquivo da UF)
- [x] Abas Presidente e Governador, com marcação de "venceu em Goiás" separada de "eleito"
- [x] Mapa de Goiânia por local de votação: 349 pontos com coordenada do TSE, 654.597
      votos mapeados (`13_secoes.py`)
- [x] Escala de disputa nos cruzamentos estendida aos cinco cargos
- [x] `docs/ACHADOS.md` seção 10 e ressalvas 7 a 11 do `MODELO.md`

## Marco 5 — replicação nacional  ✅ concluído 2026-08-21

- [x] Ingestão em modo nacional (`RASTRO_UF=BR`), todas as UFs
- [x] Portão de validação nacional (`15_valida_nacional.py`): o recorte de Goiás dentro
      do arquivo do Brasil tem de bater exatamente com o arquivo de Goiás — 34
      combinações cargo/ano conferidas
- [x] Agregados por UF e malha do Brasil (`14_nacional.py`)
- [x] Payload nacional de 13,2 MB (`16_payload_br.py`) — cabe no teto de 16 MB
- [x] Página `lastro_brasil.html`: gaveta "Qual seu estado?" com as 26 UFs, mesmo
      tratamento para cada uma, e aba de comparativo nacional
- [x] Marca Lastro aplicada nas duas páginas

## Marco 6 — front end em React  ✅ base entregue 2026-08-21

- [x] Vite + React 19 + TypeScript estrito em `app/`
- [x] Dados fatiados por UF (`18_dados_web.py`): abertura de 305 KB contra 13,3 MB
- [x] Estado da tela na URL (`?uf=&ano=&c=`), link compartilhável
- [x] Mapa, legenda, cartões, índices e gaveta de estados como componentes
- [x] Toque tratado desde o começo, não como remendo
- [x] `app/README.md` com a arquitetura e as escolhas

## Marco 7 — modelo completo em todas as UFs  ✅ concluído 2026-08-22

- [x] Cinco cargos × 7 pleitos × 26 UFs (`19_nacional_completo.py`)
- [x] Adjacência da malha completa, separada da geometria de desenho (`20_adjacencia.py`)
- [x] Padrões e Cruzamentos por UF (`21_padroes_cruzamentos.py`)
- [x] Validado contra o pipeline de Goiás: votos, captura, arrasto, semelhança e escala
- [x] Front React com as sete abas: cinco cargos, Padrões e Cruzamentos

- [x] Rivais territoriais em todas as UFs, estadual e federal (`23_rivais.py`)
- [x] Vereador nas 26 capitais, 2000–2024 (`24_`, `25_`)

### O que ainda não está no React

| Bloco | Situação |
|---|---|
| Comparativo nacional | mapa por UF e rankings; os dados já estão em `indice.json` |
| Vereador com mapa por seção | o mapa por seção existe só para Goiânia (`13_secoes.py`), e depende do arquivo de locais de votação com coordenadas — não replicado |
- [x] Sigla atribuída e entrada no roster monitorado (TKT-001, 2026-08-21)

## AGUARDANDO — sem próximo item seguro

Nada aqui é executável pelo líder. Os três itens estão registrados como ticket em
[`FILA00.md`](FILA00.md) e saíram da lista de execução para não serem lidos como
trabalho pendente.

| Ticket | Item | Por que está parado |
|---|---|---|
| `TKT-002` | Estender a outras UFs | Não foi pedido. O pipeline já é parametrizado por UF; executar sem alvo definido seria trabalho especulativo. |
| `TKT-003` | Incorporar o pleito de 2026 | Espera legítima por evento externo: a eleição ocorre em outubro de 2026 e o TSE só publica os dados após a totalização. |

## Não fazer sem pedido explícito

- Montar o `.pbix`: os CSVs do modelo estrela estão prontos, mas o arquivo do Power BI
  é trabalho manual no Desktop e o usuário optou pelo painel HTML como entrega visual.

## Marco 8 — Emendômetro  ⏳ base pronta 2026-08-23

Mesma pergunta do voto, virada para o dinheiro: onde o deputado manda emenda, e
isso tem a ver com onde ele tirou voto?

- [x] Fonte identificada e baixada: Portal da Transparência, arquivo único
      (`30_emendas_ingest.py`). 78.454 emendas, 2015–2026, R$ 259,5 bi pagos
- [x] Normalização com `cod_ibge`, a **mesma chave** do voto — sem pareamento
      por nome, que é o que custou 23 milhões de votos do outro lado
- [x] Casamento autor ↔ deputado federal eleito: 1.098 de 1.492 autores (74%),
      R$ 108,7 bi (78% do dinheiro individual), com os 9 nomes ambíguos marcados
- [x] Agregados por UF e por município (`31_emendas_agregados.py`): 35 KB
      nacional + 1,2 MB por UF, reconciliando exato nos dois níveis
- [x] Aba **Emendômetro** no artefato: mapa municipal acumulado, filtro por
      exercício e por autor, ranking nacional por UF, cobertura declarada na
      tela. Artefato em **15,2 MB** — o teto de 16 está perto, e é ele que
      decide o que ainda cabe
- [x] Cruzamento voto × emenda (`32_cruzamento_voto_emenda.py`): sim, e o
      efeito sobrevive a toda checagem — cresce quando se exige mais dado
- [x] Real por habitante e por km² (`33_demografia.py`, Censo 2022 do IBGE)
- [x] "Qual seu estado?" virou subaba: some no Nacional, onde o mapa é o seletor

### O achado do cruzamento

Mediana do país: **60,1% da emenda de um deputado cai nos 10 municípios onde ele
mais votou**, contra **5,7%** que cairia no reduto de outro deputado do mesmo
estado e pleito. Excesso de **+15,9 pp**.

A linha de base é o que dá sentido ao número. Goiânia recebe muito voto *e*
muita emenda de quase todo deputado goiano, porque é grande — sem descontar
isso, qualquer medida de sobreposição sai alta e diz "cidade grande é grande nas
duas contas".

**E o efeito não encolhe quando se exige mais dado — ele cresce:**

| mín. municípios | n | excesso | ponderado por R$ | positivo em |
|---|---|---|---|---|
| 1 | 1.082 | +15,9 pp | +28,9 pp | 66% |
| 3 | 703 | +20,0 pp | +27,2 pp | 77% |
| 5 | 428 | +17,9 pp | +24,9 pp | 83% |
| 10 | 197 | +17,2 pp | **+24,5 pp** | **91%** |

Se fosse artefato de denominador pequeno, sumiria sob filtro. A ressalva que fica
na tela: isso mede o dinheiro rastreável, mediana de 1,9% da carteira de cada
deputado. O sentido é sólido, a magnitude fala do recorte.

### Duas coberturas diferentes, e as duas precisam aparecer

Medidas ao agregar, e não são a mesma coisa:

- **10,5% do dinheiro** individual é rastreável até um município.
- **69% dos municípios** (3.844 de 5.571) receberam alguma emenda rastreável,
  somando 2015–2026.

Por isso o mapa municipal abre **acumulado**, não por ano: em Goiás, 2024 sozinho
tem 17 municípios com emenda e o mapa fica quase vazio; os doze anos juntos dão
uma mancha legível. O filtro por ano continua, como recorte, não como padrão.

### Limitação conhecida do casamento

`eleito` significa "casa com deputado federal eleito entre 2014 e 2022", e não
"é parlamentar". Senadores fazem emenda individual e saem marcados como não
casados — Jorge Kajuru e Damares Alves aparecem assim em Goiás. Casar senador
exige a base de eleitos do Senado, que já temos por UF e ainda não foi ligada
aqui.

### A ressalva que define esta aba, e não pode ser esquecida

**O mapa municipal cobre 10,5% do dinheiro individual.** Não por descuido: 76%
do valor está declarado como `MÚLTIPLO`, uma emenda espalhada por vários
municípios que o arquivo não nomeia. O voto é completo por construção — todo
voto tem município. A emenda não é.

**E existe um atalho falso que precisa ficar fechado.** O arquivo por favorecido
tem município em 100% do dinheiro, e é inútil como mapa: Brasília concentra
36,4% das emendas individuais, porque é o endereço do Fundo Nacional de Saúde e
dos intermediários. Usar esse campo produziria um mapa bonito dizendo que
Brasília recebe um terço das emendas do país — verdade sobre a transferência
bancária, falso sobre onde o dinheiro chegou. **O município vem sempre da
localidade de aplicação.**

Por UF a cobertura é 97,1% do dinheiro, inclusive nas linhas `MÚLTIPLO`. É nesse
nível que o Emendômetro é completo, e é por isso que ele começa por UF.

## Marco 9 — emendas de deputado estadual, piloto em Goiás

Aprovado pelo usuário em 2026-08-23 (`RAS 00 TKT 0006`). Não é extensão do
Emendômetro: é outra fonte — orçamento estadual, 26 portais, sem agregador
nacional. O piloto responde quanto custa um estado antes de prometer 26.

- [x] Capital sinalizada nos mapas municipais (âncora de leitura)
- [x] **Não precisou do Power BI.** O conjunto "Emendas Parlamentares - SERINT"
      dos dados abertos de Goiás é a base da Assembleia, em CSV — eu tinha
      descartado olhando o nome do órgão, sem ler a descrição
- [x] Normalizado com `cod_ibge` (`34_emendas_go_estadual.py`): 22.310 linhas,
      2019–2025, R$ 4,0 bi, 246 municípios em 2022
- [x] Casamento com deputado estadual eleito: 61% dos autores, 76% do dinheiro
- [x] **Fusão, não aba nova** (`35_emendas_estadual_web.py`): seletor de esfera
      dentro do Emendômetro, que só aparece onde há base estadual. Aplicado sob
      a pré-autorização — uma aba vazia em 26 estados é pior que a ausência do
      botão, e a pergunta que interessa é comparativa
- [x] **Decidido: não vale ir para os 25 — vale ir para 2 ou 3**
      (`36_sonda_portais_estaduais.py`). Aplicado sob a pré-autorização, com a
      sondagem em mãos
- [x] **Pernambuco: descartado.** Abri os quinze exercícios: nenhum tem `autor`
      nem `municipio`. São registros de empenho — número, unidade gestora,
      credor, valores. O dicionário "versão 02" descreve um esquema rico com os
      dois campos, e **nenhum arquivo publicado usa esse esquema**. O CSV de
      2026 tem zero bytes e o JSON de 2025 traz o formato antigo
- [x] **Espírito Santo: confirmado**, e melhor que Goiás
- [x] Ingestão do Espírito Santo (`38_emendas_es_estadual.py`): 2021–2026,
      4.620 linhas com pagamento, 51 autores, R$ 291,9 mi, 77 de 78 municípios
- [x] **Bahia: descartada para o mapa.** O ZIP da SEFAZ tem cinco tabelas do
      FIPLAN. `DESPESAS` traz `Nome do Deputado` e `Valor Pago`, mas **nenhuma
      das cinco tem município** — nem `PAGAMENTOS`, que só tem razão social do
      credor e objeto. Renderia ranking por deputado sem geografia, que não é o
      produto

### Placar final do estadual, com todos os candidatos abertos

| estado | autor | município | situação |
|---|---|---|---|
| Goiás | sim | sim, 65,8% do valor | **no ar** |
| Espírito Santo | sim | sim, 82,5% do valor | **no ar** |
| Pernambuco | não | não | descartado — só empenho |
| Bahia | sim | **não** | descartado — sem geografia |
| outros 23 | — | — | sem dado acessível |

**Dois de 27.** E os dois descartes só apareceram abrindo o arquivo: Pernambuco
publica um dicionário que descreve campos que nenhum arquivo tem, e a Bahia tem
o deputado mas não o lugar. Nenhuma das duas coisas se vê pela descrição do
conjunto.

### Espírito Santo, medido

| exercício | emendas | autores | municípios | % do valor com município | pago |
|---|---|---|---|---|---|
| 2021 | 921 | 30 | 76 | 96,8% | R$ 21,8 mi |
| 2022 | 1.323 | 30 | 76 | 98,2% | R$ 28,3 mi |
| 2023 | 964 | 30 | 75 | 98,2% | R$ 30,6 mi |
| 2024 | 1.421 | 30 | 76 | 98,9% | R$ 48,2 mi |
| 2025 | 1.346 | 30 | 78 | 81,5% | R$ 70,2 mi |
| 2026 | 1.684 | 30 | 78 | 61,4% | R$ 92,9 mi |

Esquema estável nos seis exercícios, com `CodigoMunicipio` além do nome — o
pareamento por nome nem é necessário. **A cobertura municipal é de 98% contra
65,8% em Goiás.** 2025 e 2026 aparecem mais baixos porque ainda estão
executando, não porque publiquem pior.

### Duas lições deste levantamento, e as duas são erro meu

**Li o dicionário em vez do dado.** Escrevi a linha do roadmap sobre Pernambuco
a partir da descrição do conjunto e do dicionário v2 — exatamente o que o
`36_sonda_portais_estaduais.py`, escrito no commit anterior, avisa para não
fazer. A regra estava certa e eu a violei uma hora depois.

**O detector de formato de moeda tinha limite de duas casas decimais.** O ES
publica `11250,0000`, com quatro. A vírgula virava separador de milhar e o valor
inflava dez mil vezes: o primeiro cálculo deu R$ 217 bilhões para um estado cujo
orçamento inteiro é fração disso. O número absurdo é que denunciou; um erro de
10% teria passado.

### A sondagem que tornou a decisão possível

Sondados os 27 portais estaduais de dados abertos:

| | |
|---|---|
| respondem CKAN | **10 de 27** |
| têm conjunto com "emenda parlamentar" | 6 |
| em formato tabular | 5 — BA, ES, GO, PB, PE |

E abrindo os cinco, o número real cai de novo: PB só tem "Orçamento" genérico e
SC foi falso positivo (o casamento era com portarias de COVID). **Sobram três
com dado de emenda estadual de verdade: GO, PE e ES.**

Isto responde a pergunta e mata a ambição: **o Emendômetro estadual nacional não
existe como produto uniforme.** Dezessete portais nem respondem API. Os outros
exigiriam raspagem ou engenharia reversa de painel, um por um, sem garantia de
que tragam autor e município.

A ressalva do próprio script continua valendo: achar o conjunto não garante o
conteúdo. Em Goiás o conjunto certo estava lá e foi descartado pelo nome do
órgão. PE e ES precisam ser abertos antes de virarem promessa.

### O que a comparação já mostra em Goiás

| | federal | estadual |
|---|---|---|
| rastreável ao município | R$ 316,2 mi (6,5%) | **R$ 2,61 bi (65%)** |
| municípios alcançados | 170 de 246 | **246 de 246** |
| maior carteira | Major Vitor Hugo, R$ 21,8 mi em 19 municípios | Amilton Filho, R$ 46,1 mi em **73** |

A emenda estadual é mais dinheiro rastreável, mais espalhada e nomeia município
quase sempre. Não por virtude do estado: a emenda federal é maior por unidade e
frequentemente vai para `MÚLTIPLO` ou para o estado inteiro. Área principal nos
dois: saúde.

### O custo real de um estado, medido

O trabalho não está em achar o dado — está em que **o esquema muda todo ano**:
sete arquivos, sete formatos, separador que vira tabulação em 2025, e a coluna
de autor chamada "DEPUTADO AUTOR", "Autor da Emenda" ou "Autor (Deputado)"
conforme o ano. Por isso as colunas são achadas por busca, não por nome fixo.

E o pareamento de município volta, porque aqui o dado vem por **nome**, não por
código IBGE como no federal. Cinco nomes seguem sem par (R$ 1,5 mi) e quatro
deles não são município: "Estado de Goiás", "PMGO", "#N/D" e um nome de pessoa.

## Marco 10 — a aba Sobre

- [x] Aba **Sobre** com a procedência de cada número, as regras de contagem e as
      armadilhas do dado público. Nove seções, três tabelas, dezesseis fatos.

Ela existe por dois motivos, e o segundo é comercial. O primeiro: dado eleitoral
é dado de interesse público sob o olhar de terceiros, e quem publica número tem
de mostrar como contou. O segundo: **o produto não é o mapa, é a confiança no
número** — e confiança que não se demonstra não se vende. A aba transforma o
rigor, que é invisível numa demonstração, em coisa que se lê.

Escrita dentro do gerador, e não num arquivo à parte, de propósito: se o
pipeline mudar e o texto ficar, o texto vira mentira antiga.

## Marco 11 — aba API: o que as assembleias publicam

- [x] Sondagem das 27 casas legislativas (`39_sonda_assembleias.py`)
- [x] Aba **API** com o levantamento e as inferências
- [x] Piloto consumindo a API de fato (`40_alego_verbas.py`): verba
      indenizatória dos deputados de Goiás, 91 dos 96 meses de 2019 a 2026

### O piloto, e os dois achados que saem de uma subtração

R$ 111,8 mi apresentados, R$ 111,4 mi indenizados, **R$ 349 mil glosados —
0,31%**. Nenhum dos dois números abaixo é publicado como indicador em lugar
nenhum; os dois saem de comparar duas colunas que a API já entrega.

**Quase nada é recusado.** A diferença entre apresentado e indenizado mede
decisão administrativa, e a decisão é praticamente sempre aprovar.

**Todo mundo usa o teto.** Entre os 20 deputados com cinco anos ou mais de
série, a média mensal fica entre R$ 25 mil e R$ 32 mil, mediana de R$ 30 mil.
Não há quem gaste pouco — a verba é usada como piso, não como limite. Isso muda
o que "quem gasta mais" significa: ordenar por total ordena por tempo de
mandato, não por comportamento.

### E um defeito que teria virado afirmação falsa

A primeira varredura trouxe **37 dos 96 meses**, e 2022 e 2023 apareciam
completamente vazios — quando eu mesmo já tinha testado 2023/02 à mão, com 41
registros. Requisição que falha, lida como ausência de dado, não parece erro:
parece resultado. Com três tentativas por mês, foram 91 meses, 2,4× mais dado.

**19 de 27 respondem** algum portal de dado aberto; **4 têm API confirmada** por
abertura manual (GO, MG, PE, DF); 8 não devolveram nada nos caminhos testados —
o que não é prova de ausência.

### A inferência que importa

**Nenhuma assembleia publica emenda parlamentar.** O que elas publicam é a si
mesmas: folha, diárias, verbas indenizatórias, licitações, contratos, e a
execução do próprio orçamento da Casa. A assembleia como empregadora e
compradora, não como poder que direciona orçamento.

E isso é coerência institucional, não omissão: a emenda é indicação de deputado
sobre o orçamento do **Executivo**, executada pelas secretarias. Por isso o
Emendômetro estadual sai dos portais do governo do estado.

**O legislativo é mais opaco que o executivo neste recorte:** dos portais do
Executivo, cinco tinham conjunto de emenda em formato tabular; das assembleias,
nenhuma.

### Dois defeitos meus na sonda, corrigidos antes de publicar

A primeira versão deu **zero APIs** — num levantamento em que eu já tinha testado
a da ALEGO funcionando. Ela mora em `/api/transparencia/{recurso}`, dois níveis
abaixo do que eu sondava. E a lógica de subdomínio cortava `ale.am.gov.br` para
`am.gov.br`, levando a sonda ao **Executivo** num levantamento sobre o
Legislativo. Corrigidos, o resultado foi de 0 para 4 APIs e de achados
contaminados para achados da casa certa.

### Segundo piloto: Distrito Federal (`41_cldf_verbas.py`)

A CLDF publica a **mesma** verba indenizatória em outro grão: nota a nota, com
fornecedor, CNPJ e categoria. 20.572 comprovantes, 2013–2024, R$ 25,5 mi.

**O que só o DF responde:** no que a verba é gasta. Entre o que tem categoria,
**divulgação de atividade parlamentar é 27,7%** — o maior item da verba de
gabinete é publicidade do próprio mandato. Veículos, somando as duas grafias que
o arquivo usa, dão 28,9%.

**Duas ressalvas medidas, e a segunda recusa uma comparação:**

- **68,3% do valor não tem categoria.** A tabela fala de R$ 8,1 mi dos R$ 25,5 mi.
- **A CLDF tem 24 distritais e o arquivo traz de 3 a 26 por ano.** Não é
  rotatividade, é publicação parcial. **Não comparamos gasto por deputado com
  Goiás**: o cálculo roda e dá "um terço", e esse número descreveria a política
  de publicação de cada casa achando que descreve comportamento.

### Onde os dois pilotos param

| | Goiás (ALEGO) | DF (CLDF) |
|---|---|---|
| grão | mês, por deputado | comprovante |
| revela | **glosa** (apresentado − indenizado) | **no que gasta** (categoria, fornecedor) |
| não revela | destino do gasto | valor pedido, logo nem glosa |

Cada casa responde o que a outra não responde. Pernambuco tem API REST
(`/api/v1/`) com `parlamentares` e `remuneracao`, que é outro conceito — não
verba de gabinete. Minas tem Swagger, mas não achei a especificação por
tentativa e parei de caçar.

## Marco 12 — gasto administrativo das Casas, e uma correção

- [x] **Gasto administrativo da ALEGO** (`42_alego_administrativo.py`):
  orçamento da Casa, diárias, terceirizados, contratos
- [x] **Gasto administrativo da CLDF** (`44_cldf_administrativo.py`): folha
  nominal, despesa, duodécimo, terceirizados
- [x] **Correção de uma afirmação publicada** (`45_emenda_nas_assembleias.py`)
- [x] Delta-encoding do vetor municipal: 15,9 → 13,9 MB, round-trip verificado

- [x] **Verba indenizatória da ALMG** (`43_almg_verbas.py`): 141.781 notas,
  77 deputados, 2019–2026. Bruto em parquet; `--cache` reanalisa em segundos.

### O total de Minas era o número redondo e falso da vez

A série por ano dava **+182%** de 2020 a 2025. É artefato: a varredura consulta
`deputados/em_exercicio` — os 77 de hoje — e só 48 deles já eram deputados em
2020. Quando a legislatura virou, a cobertura pulou de 49 para 74 e o total pulou
junto. **Por deputado o crescimento é +78%**, e os 104 pontos de diferença são
cobertura, não gasto.

A série publicada é por deputado, com o +182% na tela ao lado, rotulado como o
número falso — mesmo tratamento dado ao mapa de favorecido e à comparação
DF × Goiás.

**A ressalva que sobrevive:** 2020–2022 cobre só os 48 que continuam em
exercício hoje, não os ~77 de então. Sobreviventes de três mandatos tendem a ter
estrutura maior, o que faz de +78% um piso. Corrigir exigiria varrer
`que_exerceram_mandato` por legislatura — não feito, e declarado na tela.

### O erro da janela de Minas, e por que ele importa mais que parece

Escrevi que a ALMG mantinha uma **janela móvel de ~18 meses** por política de
publicação. Amostrei **um** deputado, vi 18 meses e generalizei para os 77.

Medindo os 77: **mediana de 88 meses**, máximo 91, mínimo 18 — e o mínimo era
justamente o deputado que amostrei. O arquivo começa em **2019-02**, início da
legislatura 2019–2022, e a janela de cada um acompanha o tempo dele de mandato:
48 têm série desde 2019, 22 desde fevereiro de 2023, o resto entrou por
substituição.

**Errei nas duas metades, e a consequência não foi cosmética.** Com base na
limitação que inventei, eu tinha me *recusado a publicar a série temporal* —
escrevi na tela que uma série ali "descreveria a política de retenção da ALMG
achando que descreve gasto". A série existe, cobre duas legislaturas, e a
recusa era o único obstáculo.

A frase não chegou a nenhum leitor: a seção retornava vazio por falta do JSON
quando o artefato foi publicado. Mas é o terceiro erro da mesma família nesta
frente — presumir padrão a partir do que vi e não do que testei — depois de
`\d{4}-\d{2}` ter apagado cinco anos do DF e de "nenhuma assembleia publica
emenda" ter ido ao ar. A diferença entre os três é só quanto tempo levou até
alguma coisa denunciar.

### Minas: o grão mais completo dos três

A ALMG tem API v2 documentada (a especificação está em
`/api/ajuda/swagger/endpoints/lastest`, que só se acha olhando o que a página
carrega — as tentativas por endereço plausível davam 500). São 108 endpoints.

O de verba indenizatória devolve **deputado × mês × categoria**, com detalhe
nota a nota dentro: `valorDespesa` e `valorReembolsado` (a glosa, que só Goiás
dava), `descTipoDespesa` (a categoria, que só o DF dava) e `nomeEmitente` +
`cpfCnpj` (o fornecedor). **É a união dos três**, e a única das casas onde dá
para perguntar qual fornecedor atende quantos deputados.

**A janela é móvel e isso não é comportamento:** cerca de 18 meses por
deputado, de fevereiro de 2025 em diante. É política de publicação, não início
da verba — série longa ali descreveria a retenção da ALMG achando que descreve
gasto.

**O limite de requisição é publicado e obedecido:** a ALMG declara no site duas
requisições simultâneas e um segundo entre elas, sob pena de bloqueio sem
aviso. São dois workers com pausa de um segundo. A varredura leva o tempo que
levar.

## Marco 13 — o site sai do artefato, e nasce o terceiro produto

- [x] Repositório novo (`guilhermegon/lastro`) com o dado versionado
- [x] **Um arquivo por pleito**: 69% a menos na primeira tela
- [x] Três abas portadas do artefato para o app: Emendômetro, API, Sobre
- [x] Marcas de produto: Cadê o Voto?, Emendômetro, Radar
- [x] **Radar** (`radar/`), o produto fechado, com a aba Projeção
- [x] `47_publica_radar.py` e o gate que impede o dado do Radar de vazar

### O que fazia o site não funcionar, e não era o que eu achava

O site estava no ar como **casca vazia**: o HTML carregava e todo dado dava 404,
porque `app/public/dados` estava no `.gitignore` e a Cloudflare constrói a partir
do clone. Deploy por commit não podia funcionar assim.

E o argumento com que eu tinha defendido não versionar o dado estava errado.
Disse que o histórico cresceria ~17 MB por regeração. Não cresce: **git guarda
por conteúdo**, então reescrever arquivo idêntico não cria objeto novo. Custo
medido: 82,6 MB em disco, **18,2 MB como objeto**, uma vez.

A linha divisória passou a ser: **o que o site serve é versionado; o que o
pipeline usa para chegar lá não é.**

### A redução que valia, e a que não valia

Medi as duas. Espremer bytes — delta-encoding, desduplicação, arredondamento —
rendia **4%**, porque o gzip do servidor já corta 79%. O que valia era outra
coisa: a tela mostra um pleito e o arquivo trazia os sete.

Partido por ano, São Paulo (pior caso do país) caiu de **4.815 KB para 1.401 KB**
na primeira tela — 343 KB pela rede, com brotli. Os outros seis pleitos entram em
pré-busca a partir dos 144 ms, depois do caminho crítico; trocar de ano faz zero
requisições.

Verificação: 1.299 blocos comparados contra a origem, **zero divergentes**, e o
teste-ouro reproduz pelo caminho novo (Itumbiara 6.559, 27,57%).

**E a mudança criou um defeito que quase passou:** `28_build_landing.py` lia o
monolito `estadual.json`, que deixou de existir. O `exists()` daria falso, `anos`
viria vazio e o artefato sairia **sem voto nenhum, com aparência de pronto**.
Agora lê a divisão, e o gate é no total de UFs — porque uma UF vazia é legítima
(o DF elege distrital) e todas vazias é regressão.

### O 2024 que faltava era um seletor a mais

Na aba de vereador havia duas faixas de ano. A global parava em 2022 e não
governava nada ali; a da própria vista ia até 2024. Quem olhasse a de cima lia
"falta 2024" — e a leitura estava certa sobre a tela. A global saiu de onde não
manda: vereador (tem a própria) e padrões (mostra a série inteira).

### Radar, e por que ele é uma aplicação à parte

Lastro é a casa — no sentido de **respaldo**, como o ouro que lastreia moeda.
Cadê o Voto? e Emendômetro são a vitrine. Radar recebe o que eles produzem e lê
para a frente; Padrões e Cruzamentos saíram do site aberto e viraram o conteúdo
dele.

**A separação é de arquivo, não de tela.** Antes da mudança,
`/dados/GO/padroes.json` respondia 200 no site — tirar a aba esconderia o botão e
não o arquivo. Hoje o build público devolve 404 para os dois, verificado, e o
`47_` aborta se algum deles reaparecer lá.

**Isso ainda não é controle de acesso** (RAS 00 TKT 0008): é separação de build.
Publicar para cliente exige Cloudflare Access ou Worker com token.

A aba **Projeção** nunca entrega o número sozinho: sai sempre com R², desvio
típico e número de pontos, e abaixo de 50% de ajuste a tela escreve que a série
não tem tendência que se sustente. Goiás provou o valor disso na estreia — o
ajuste da estabilidade de base é de **3%**, e o painel diz que o projetado vale
como referência, não como previsão.

### Marcas

As três compartilham a mesma construção e só ela: régua vertical em x=12, linha
de base em y=52, só retângulos arredondados, hierarquia por opacidade, `--accent`.
O Radar ganhou o único elemento novo do sistema — a quarta barra é **contorno**,
não preenchimento, e vem adiante das outras: é projeção, não observação.

## AGUARDANDO — espera decisão do usuário ou evento externo

O BEDEL lê o **título da seção** para saber que não há próximo item seguro
aqui: a palavra AGUARDANDO precisa estar no cabeçalho, não só ao lado de cada
item. Sem ela, o hook cobra estes três como se fossem executáveis — e nenhum
é: os dois primeiros dependem de ação nas contas do usuário, e o terceiro do
TSE publicar.

- [ ] **AGUARDANDO** — separar `guilhermegon/lastro` da rede de fork antes de
  apagar o antigo (RAS 00 TKT 0007). Espera ação do usuário no GitHub.
- [ ] **AGUARDANDO** — autenticação do Radar antes de publicá-lo
  (RAS 00 TKT 0008). Espera a conta Cloudflare do usuário.
- [ ] **AGUARDANDO** — pleito de 2026 (TKT-003). Espera o TSE publicar.
