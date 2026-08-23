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
- [ ] Aba do Emendômetro estadual, ou fusão com a federal
- [ ] Decidir, com o custo medido, se vale ir para os outros 25

### O custo real de um estado, medido

O trabalho não está em achar o dado — está em que **o esquema muda todo ano**:
sete arquivos, sete formatos, separador que vira tabulação em 2025, e a coluna
de autor chamada "DEPUTADO AUTOR", "Autor da Emenda" ou "Autor (Deputado)"
conforme o ano. Por isso as colunas são achadas por busca, não por nome fixo.

E o pareamento de município volta, porque aqui o dado vem por **nome**, não por
código IBGE como no federal. Cinco nomes seguem sem par (R$ 1,5 mi) e quatro
deles não são município: "Estado de Goiás", "PMGO", "#N/D" e um nome de pessoa.
