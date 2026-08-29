# FILA — RAS00 (RASTRO)

Decisões pendentes do usuário. A FILA não decide nem prioriza — só registra, estrutura
e apresenta.

Sigla do projeto: **RAS** (`RAS00`), definida pelo usuário em 2026-08-21 via TKT-001.

Tickets criados a partir daqui usam `RAS 00 TKT NNNN`. Os três abaixo **mantêm** os ids
`TKT-NNN` com que nasceram — históricos não são renumerados
(`preserve_historical_numbers: true`, `stable_ticket_id: true`).

---

### TKT-001 — Sigla e entrada no roster

| Campo | Valor |
|---|---|
| `type` | `BLOCKING_DECISION` |
| `criticality` | baixa |
| `work_continues` | sim — o Marco 1 está entregue; isto não travou trabalho técnico |
| `status` | **FECHADO** — respondido pelo usuário em 2026-08-21 |

**decisão do usuário (2026-08-21).** "a sigla é RAS" — opção 2, com sigla própria.
Resposta manual, como a regra exigia: nada foi pré-autorizado nem aplicado por `RT`.

**executado pelo líder na mesma data:**

- `~/.claude/CLAUDE.md` — linha `RAS00` acrescentada ao roster e `RAS00` incluído na
  lista monitorada pelo BEDEL. Arquivo é do **MAESTRO 00**; escrito sob a exceção de
  ordem direta do usuário (DaRulez, "Quem escreve em qual arquivo"), relido antes da
  edição e sem divergência desde 2026-08-10. **MAESTRO 00 precisa ser avisado.**
- `CLAUDE.md` na raiz do projeto — identidade local `[RAS 00]` criada, com as regras
  específicas do projeto e as restrições de ambiente já mapeadas.
- `ROADMAP.md` — item movido de AGUARDANDO para concluído.

**summary (no momento da abertura).** RASTRO nasceu nesta sessão e não constava do
roster em `~/.claude/CLAUDE.md`. Sem sigla, o projeto ficava fora da regência do BEDEL:
nenhum hook de continuidade o monitorava e ele não aparecia nas varreduras de FILA
entre projetos.

**decision_needed.** O RASTRO deve entrar no roster monitorado? Em caso positivo, qual
sigla?

**options.**

1. **Não entrar no roster.** Fica como entrega pontual, fora da regência. O `ROADMAP.md`
   e este arquivo continuam existindo, mas ninguém os varre.
2. **Entrar no roster com sigla escolhida pelo usuário.** Candidatas óbvias a partir do
   nome da pasta: `RAS00`, `RST00`, `RTR00`. Nenhuma foi adotada.
3. **Entrar como subprojeto de outro código já existente**, se o usuário enxergar o
   RASTRO como parte de algo que já está no roster.

**leader_recommendation.** *Nenhuma.* Não por falta de opinião técnica, mas porque a
regra proíbe: DaRulez lista **"inventar código para projeto sem histórico"** entre os
itens que ficam **fora da pré-autorização de progresso** e sobem sempre ao usuário
(`invent_code_for_gap: false`). Por isso o ticket permanece aberto para resposta manual
(`KEEP_TICKET_OPEN_FOR_MANUAL_RESPONSE`) e **a política `RT` não se aplica a ele** — RT
só age sobre ticket com recomendação inequívoca.

**Ação do líder ao receber a resposta.** Registrar a sigla em `CLAUDE.md` (raiz do
projeto), acrescentar a linha no roster de `~/.claude/CLAUDE.md`, e renumerar este
arquivo para o formato `SIGLA 00 TKT NNNN` **apenas nos tickets novos** — os históricos
não são renumerados (`preserve_historical_numbers: true`).

---

### TKT-002 — Estender o painel a outras UFs

| Campo | Valor |
|---|---|
| `type` | `TRACKING_NO_APPROVAL` |
| `criticality` | baixa |
| `work_continues` | sim |
| `status` | **FECHADO** — entregue, 2026-08-23 |

**Fechado por entrega, não por decisão.** RT não alcançou este ticket: ele nunca teve
`leader_recommendation`, e a política não força decisão onde não há recomendação. O que
o fechou foi o fato de o pedido já estar cumprido — as 26 unidades estão no ar, nos
cinco cargos, com Padrões, Cruzamentos, rivais territoriais e vereador nas capitais.

**As três ressalvas do summary original envelheceram, e vale registrar como:**

- *"as correções de nome de município são específicas de Goiás"* — eram nove, de Goiás.
  Hoje são **159**, cobrindo 27 unidades, e a chave virou `(uf, nome)`. A investigação
  que as produziu está em [`docs/MODELO.md`](docs/MODELO.md); ela recuperou 23 milhões
  de votos que sumiam em silêncio.
- *"o número de cadeiras varia por UF"* — resolvido: `N_CADEIRAS_CARGO` sai do próprio
  dado, contando os eleitos de cada pleito.
- *"o teste-ouro só existe para Goiás, em outra UF não haveria contra o que conferir"* —
  **esta era a ressalva séria, e estava certa.** A resposta foi criar um segundo gate
  que não depende de painel externo: `15_valida_nacional.py` exige que o recorte de
  Goiás dentro dos arquivos do Brasil seja idêntico ao pipeline de Goiás, em 34
  combinações cargo/ano. Não valida as outras 26 diretamente — valida a máquina que as
  produz. E `26_audita_pareamento.py` cobre o flanco que nenhum dos dois via.

**summary (no momento da abertura).** O pipeline é parametrizado por `UF` e `UF_IBGE` em
`scripts/00_config.py` e os zips do TSE já são nacionais, então rodar para outro estado
não exigiria reescrever nada.

---

### TKT-003 — Incorporar o pleito de 2026

| Campo | Valor |
|---|---|
| `type` | `TRACKING_NO_APPROVAL` |
| `criticality` | baixa |
| `work_continues` | não — bloqueado por evento externo |
| `status` | **ABERTO** — espera legítima |

**summary.** A eleição de 2026 ocorre em outubro de 2026 e o TSE só publica
`votacao_candidato_munzona_2026.zip` depois da totalização. Até lá não há o que fazer.

**decision_needed.** Nenhuma. Quando o arquivo existir, basta acrescentar `2026` a
`ANOS` em `scripts/00_config.py` e rerodar o pipeline — o teste-ouro continua válido,
porque ele confere os pleitos antigos.

---

### RAS 00 TKT 0004 — Ordem do porte para React

| Campo | Valor |
|---|---|
| `type` | `BLOCKING_DECISION` |
| `criticality` | média |
| `work_continues` | sim |
| `status` | **FECHADO** — resolvido sem precisar da decisão, 2026-08-22 |

**Fechado porque a pergunta deixou de existir.** O ticket pedia a ordem de porte entre
quatro blocos que competiam por prioridade. Com o modelo completo replicado para as 26
UFs, os cinco cargos, Padrões e Cruzamentos foram portados de uma vez — não havia mais
o que priorizar entre eles. Restam apenas o comparativo nacional, os rivais por UF e o
vereador com mapa por seção, que estão no `ROADMAP.md` sem competir entre si.

**summary (no momento da abertura).** A base do front em React estava entregue:
deputado estadual das 26 UFs, mapa, índices, gaveta de estados, estado na URL, toque.
Restavam quatro blocos do painel antigo para portar, competindo por ordem.

**decision_needed.** Qual bloco vem primeiro?

**options.**

1. **Comparativo nacional** — mapa por UF, rankings, preço da cadeira por estado. É o
   que mostra o produto inteiro numa tela e serve de vitrine.
2. **Demais cargos** — federal, Senado, governador, presidente. Multiplica por cinco o
   que cada estado entrega, mas exige refazer o payload por UF para os outros cargos:
   hoje só o estadual foi fatiado nacionalmente.
3. **Rivais e cruzamentos** — a análise que nenhum concorrente tem. Só existe para Goiás
   e replicá-la nacionalmente é o trabalho mais pesado dos três.
4. **Vereador de Goiânia**, com o mapa por local de votação — o mais fino em geografia,
   e o único que já tem dado de seção pronto.

**leader_recommendation.** **Opção 1.** Não por ser a mais fácil, e sim porque é a única
que fecha um produto coerente com o que já está pronto: hoje o app mostra um estado por
vez e não tem tela que responda "e como está o resto do país". As opções 2 e 3 aprofundam
antes de fechar. A 4 é excelente e é de uma cidade só — vale depois que a moldura
nacional existir.

**Ação do líder ao receber a resposta.** Portar o bloco escolhido e reabrir os demais
como itens de roadmap na ordem definida.

---

### RAS 00 TKT 0005 — Cobertura do mapa municipal do Emendômetro

| Campo | Valor |
|---|---|
| `type` | `BLOCKING_DECISION` |
| `criticality` | alta — decide o que a aba afirma |
| `work_continues` | sim — a base e o casamento já estão prontos |
| `status` | **DECIDIDO** — pré-autorizado pelo líder, 2026-08-23 |

**summary.** O mapa municipal de emendas cobre R$ 14,6 bi de R$ 140 bi
individuais (10,5%), porque 76% do dinheiro está em `MÚLTIPLO` — emenda
espalhada por municípios que o arquivo não nomeia. Existe um campo alternativo,
o município do favorecido, com 100% de cobertura e semântica errada: Brasília
sozinha concentra 36,4%, por ser o endereço do Fundo Nacional de Saúde.

**decision_needed.** Publicar o mapa municipal com 10,5% de cobertura declarada,
ou trocar pelo campo de favorecido, ou não publicar mapa municipal.

**leader_recommendation.** **Publicar com a cobertura declarada, e nunca usar o
favorecido.** O campo de favorecido não é uma cobertura melhor da mesma
pergunta — é outra pergunta, respondida com aparência de mapa. É exatamente o
"mapa errado com aparência de certo" que a regra de auditoria deste projeto
nomeia, e a mesma razão pela qual não afrouxamos a tolerância do teste-ouro. A
aba abre por UF, onde a cobertura é 97,1%, e o mapa municipal entra rotulado
como o recorte rastreável.

**Aplicado sob a pré-autorização de progresso** (DaRulez, ordem permanente de
2026-08-01): recomendação inequívoca, aplicada na hora, registrada aqui para
revisão posterior.

---

### RAS 00 TKT 0006 — Emendas de deputado estadual

| Campo | Valor |
|---|---|
| `type` | `BLOCKING_DECISION` |
| `criticality` | média — define escopo, não corrige defeito |
| `work_continues` | sim — o Emendômetro federal está no ar |
| `status` | **DECIDIDO** — usuário aprovou o piloto de Goiás, 2026-08-23 |

**Resposta do usuário: fazer o piloto de Goiás.** É a recomendação do líder,
aplicada. O piloto responde "quanto custa cada estado?" antes de qualquer
promessa sobre os outros 25.

**summary.** Emenda de deputado estadual vai para o orçamento **do estado**, não
da União. Não está no Portal da Transparência federal, que é a fonte de todo o
Emendômetro atual. Não existe agregador nacional: são 26 portais estaduais, cada
um com seu formato, e nada garante que o município de destino esteja publicado.

**O que apurei em Goiás**, que é o estado-piloto e um dos portais melhores:

- Existe página dedicada, `transparencia.go.gov.br/emendas-parlamentares-de-goias/`
- A execução completa desde 2021 só sai por **painel Power BI embutido**
  (`reportId=c6b3961c-6932-4e0a-b77e-99cd14acee45`) — sem CSV
- As indicações de 2025/2026 estão noutro sistema, o `sislog.go.gov.br`
- O portal de dados abertos tem três conjuntos com "emenda", e nenhum é o
  conjunto completo: um é de uma secretaria (SERINT), um é de uma universidade
  (UEG), e o terceiro é de **emendas constitucionais**, que são outra coisa —
  alteração de texto de lei, não dinheiro

**decision_needed.** Fazer um piloto só de Goiás por engenharia reversa do painel
Power BI, tentar as 26 unidades, ou não fazer.

**leader_recommendation.** **Piloto de Goiás, e só depois decidir o resto.** O
projeto já fez exatamente isso uma vez — nasceu de engenharia reversa de um
painel Power BI do TSE/GO — então o caminho é conhecido e o custo, estimável.
Prometer as 26 unidades sem ter feito uma é o erro que este projeto evita: cada
portal é um formato, e nem todos publicam município de destino. Um piloto
transforma a pergunta "dá para fazer?" em "quanto custa cada estado?".

Não aplico a pré-autorização aqui: não é destravar progresso de algo em curso, é
abrir uma frente nova de escopo aberto, e isso é decisão de dono.

---

### RAS 00 TKT 0007 — O fork privado impede apagar o repositório antigo

| Campo | Valor |
|---|---|
| `type` | `HUMAN_ACTION` |
| `criticality` | alta — a ação pedida destruiria o repositório novo |
| `work_continues` | sim — o projeto já vive em `guilhermegon/lastro` |
| `status` | **ABERTO** — depende de ação do usuário no GitHub |

**summary.** O usuário pediu para apagar `GTzon/lastro` depois de confirmar o
convite. Ao verificar, `guilhermegon/lastro` é **fork** de `GTzon/lastro`, e os
dois são privados. A documentação do GitHub é literal: *"Deleting a private
repository will delete all forks of the repository."* Apagar o antigo destruiria
o novo. Por isso a exclusão não foi executada.

**decision_needed.** Como separar os dois antes de apagar o antigo.

**options.** (1) Criar repositório independente sob `guilhermegon` — não fork —,
empurrar os commits e só então apagar `GTzon/lastro`. (2) Pedir ao Suporte do
GitHub para retirar o fork da rede. (3) Tornar `GTzon/lastro` público por um
instante, o que faz o fork sobreviver à exclusão.

**leader_recommendation.** **Opção 1.** É a única que não depende de terceiro nem
de prazo, e a única que eu consigo executar quase inteira: falta apenas o
usuário criar o repositório vazio e me dar push. A opção 2 leva dias e depende
do Suporte. A opção 3 expõe, ainda que por instantes, dado eleitoral que hoje
está em repositório privado — trocar a política de visibilidade para contornar
uma regra de exclusão é o tipo de atalho que este projeto recusa em toda outra
camada.

**Não aplicável sob a pré-autorização**: a criação do repositório e a exclusão do
antigo são ações na conta do usuário. O ticket fica aberto com o caminho
decidido; a parte técnica está pronta para rodar assim que houver o destino.

---

### RAS 00 TKT 0008 — O Radar não tem controle de acesso

| Campo | Valor |
|---|---|
| `type` | `HUMAN_ACTION` |
| `criticality` | alta — é o que separa produto fechado de produto aberto |
| `work_continues` | sim — o Radar roda local e não é publicado |
| `status` | **ABERTO** — depende da conta Cloudflare do usuário |

**summary.** O Radar é o produto fechado, e hoje o que o fecha é separação de
**build**, não de acesso: `scripts/22_` tira `padroes.json` e `cruzamentos.json`
do build público e `scripts/47_` os publica em `radar/public/dados`, fora do que
a Cloudflare constrói. O site aberto devolve 404 para os dois — verificado. Mas
se o Radar for publicado como está, o dado dele volta a responder 200 para
qualquer um: num site estático não existe premium.

**decision_needed.** Que camada de autenticação usar antes de publicar o Radar.

**options.** (1) Cloudflare Access na frente de um Worker separado. (2) Worker
próprio que valide token antes de servir o JSON. (3) Não publicar: Radar segue
rodando local para uso interno.

**leader_recommendation.** **Opção 1 quando houver cliente; opção 3 até lá.** O
Access resolve autenticação sem escrever código de sessão, e o projeto já está
na Cloudflare — é a menor distância entre onde estamos e um produto entregável.
Enquanto não há cliente, publicar não traz benefício e traz risco: um produto
fechado que responde 200 é pior que um produto não publicado.

**Aplicado o que cabe ao líder**: o Radar não entra no deploy, e `47_` tem gate
que aborta se algum arquivo do Radar reaparecer no build público. A configuração
do Access é ação do usuário.

---

### RAS 00 TKT 0009 — Dois caminhos de publicação, e só um em uso

| Campo | Valor |
|---|---|
| `type` | `APPROVAL_NOW` |
| `criticality` | baixa — dívida de manutenção, não defeito |
| `work_continues` | sim |
| `status` | **DECIDIDO** — pré-autorizado pelo líder, 2026-08-29 |

**summary.** Escrevi `scripts/46_publica_site.py`, que publica o site numa branch
órfã `gh-pages`, antes de descobrir que `guilhermegon` já havia configurado o
deploy por Cloudflare Workers. O script ficou no repositório antigo e nunca foi
portado para o novo.

**decision_needed.** Portar o `46_` para o repositório novo, ou descartá-lo.

**leader_recommendation.** **Descartar.** O deploy por commit na Cloudflare está
funcionando e verificado. Um segundo caminho de publicação não usado é dívida
que envelhece calada: quando alguém precisar dele, estará desatualizado em
relação ao build que de fato roda — e o pior momento para descobrir isso é numa
publicação de emergência. Se um dia o GitHub Pages for necessário, o script está
preservado no histórico de `GTzon/lastro`.

**Aplicado sob a pré-autorização de progresso.** O `46_` não é portado.

---

### RAS 00 TKT 0010 — A cópia antiga do projeto em `Documents\RASTRO`

| Campo | Valor |
|---|---|
| `type` | `TRACKING_NO_APPROVAL` |
| `criticality` | baixa |
| `work_continues` | sim |
| `status` | **ABERTO** — nada a decidir agora, registrado para não se perder |

**summary.** O projeto passou a viver em `Documents\LASTRO\lastro`, ligado ao
repositório novo. A pasta antiga `Documents\RASTRO` segue existindo com a árvore
de trabalho completa, `data/processed` (143 MB), `data/interim` e o remoto
apontando para `GTzon/lastro`.

**Por que fica aberto e não é resolvido agora.** Apagar não é reversível, e a
pasta antiga é hoje a única cópia local de `data/interim` — que não é versionado
por ser grande demais e que o pipeline levaria horas para reconstruir a partir do
TSE. Enquanto o repositório novo não estiver provado em uso, ela é o seguro.

**leader_recommendation.** *Nenhuma ainda.* A decisão depende de um fato que
ainda não existe: o repositório novo ter rodado o pipeline inteiro pelo menos uma
vez. Antes disso, qualquer recomendação seria palpite sobre o próprio seguro.
