# FILA — RAS00 (RASTRO)

Decisões pendentes do usuário. A FILA não decide nem prioriza — só registra, estrutura
e apresenta.

Sigla do projeto: **RAS** (`RAS00`), definida pelo usuário em 2026-08-21 via TKT-001.

Tickets criados a partir daqui usam `RAS 00 TKT NNNN`. Os três abaixo **mantêm** os ids
`TKT-NNN` com que nasceram — históricos não são renumerados
(`preserve_historical_numbers: true`, `stable_ticket_id: true`).

## RT de 2026-08-30

O usuário respondeu `RT`. Aplicada a recomendação do líder a todo ticket aberto
com `leader_recommendation` inequívoca:

| Ticket | Resultado |
|---|---|
| TKT-003 — pleito de 2026 | **segue aberto** — não há recomendação a aplicar: espera o TSE publicar, não uma decisão |
| RAS 00 TKT 0007 — fork privado | **decidido** — opção 1; falta o usuário criar o repositório, o `gh` daqui é de outra conta |
| RAS 00 TKT 0008 — acesso do Radar | **decidido** — opção 3 agora, opção 1 quando houver cliente; vira gatilho |
| RAS 00 TKT 0010 — pasta antiga | **fechado no mesmo dia** — o usuário escolheu o destino logo depois; o move abriu o TKT-0012 |
| RAS 00 TKT 0011 — Distrito Federal | **fechado pelo portão**, não pelo RT: o teste-ouro correu e passou |

Dois ficaram abertos de propósito. RT aplica recomendação inequívoca; ele não
inventa uma onde o próprio líder registrou que a escolha é do usuário.

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
| `status` | **DECIDIDO por RT, 2026-08-30** — caminho fechado na opção 1; execução depende de ação do usuário no GitHub |

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

**RT de 2026-08-30: opção 1 adotada.** E ao tentar executar o que caberia a mim,
apareceu o motivo concreto de por que não cabe: o `gh` desta máquina está
autenticado como **GTzon**, não como `guilhermegon`. Criar repositório sob
`guilhermegon` exige a sessão do outro usuário — não é falta de permissão de
escopo, é conta diferente. Falta um passo, e ele é do usuário:

    gh repo create guilhermegon/lastro --private     # logado como guilhermegon

Feito isso, eu aponto o remoto e empurro. **A exclusão de `GTzon/lastro`
continua fora do RT**: é irreversível e destruiria o fork se a separação falhar,
então exige confirmação explícita depois de o novo repositório estar provado.

---

### RAS 00 TKT 0008 — O Radar não tem controle de acesso

| Campo | Valor |
|---|---|
| `type` | `HUMAN_ACTION` |
| `criticality` | alta — é o que separa produto fechado de produto aberto |
| `work_continues` | sim — o Radar roda local e não é publicado |
| `status` | **DECIDIDO por RT, 2026-08-30** — opção 3 agora; opção 1 quando houver cliente |

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

**RT de 2026-08-30: adotada a recomendação em duas partes.** Vale a opção 3
enquanto não houver cliente — e ela já está em vigor e verificada, sem nada novo
a fazer. A opção 1 fica decidida de antemão para o dia em que houver: não
precisará de nova rodada de decisão, só da configuração do Access.

O ticket sai da fila de decisão e vira **gatilho**: reabre no primeiro cliente.

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
| `status` | **FECHADO** — destino escolhido pelo usuário e movido, 2026-08-30 |

**summary.** O projeto passou a viver em `Documents\LASTRO\lastro`, ligado ao
repositório novo. A pasta antiga `Documents\RASTRO` segue existindo com a árvore
de trabalho completa, `data/processed` (143 MB), `data/interim` e o remoto
apontando para `GTzon/lastro`.

**Por que fica aberto e não é resolvido agora.** Apagar não é reversível, e a
pasta antiga é hoje a única cópia local de `data/interim` — que não é versionado
por ser grande demais e que o pipeline levaria horas para reconstruir a partir do
TSE. Enquanto o repositório novo não estiver provado em uso, ela é o seguro.

**leader_recommendation (formada em 2026-08-30).** **Mover `data/`, nunca
copiar nem apagar.** Medi o que a pasta antiga guarda:

| | tamanho | custo de refazer |
|---|---|---|
| `data/interim` | 5,6 GB | **horas** — exige rebaixar 1,5 GB de zips do TSE |
| `data/processed` | 143 MB | minutos, derivado do interim |
| `data/raw` | 60 MB | transitório por desenho; a ingestão apaga os zips |
| código | — | está no git, em `guilhermegon/lastro` |

Só o `interim` é insubstituível. E o único commit não empurrado da pasta antiga
é o `46_publica_site.py`, que o RAS 00 TKT 0009 já decidiu descartar — não há
nada preso ali.

Então a operação certa é **mover o diretório de dados** para um lugar que o
projeto novo assuma, apontar `RASTRO_DATA` para ele de forma documentada, rodar
o pipeline uma vez para provar, e só então o resto da pasta antiga pode ir. Mover
não perde nada; copiar duplicaria 5,6 GB; apagar antes de mover perderia horas.

**Fora da pré-autorização, e por isso segue aberto:** *onde* os dados devem
morar é escolha do usuário — envolve disco, backup e talvez pasta sincronizada,
que o `00_config` documenta como caso em que `RASTRO_DATA` é obrigatório. A
recomendação está formada; o destino é a decisão que falta.

**Nota de 2026-08-30:** esta sessão rodou o pipeline do repositório novo contra
os dados da pasta antiga, via `RASTRO_DATA`, e funcionou. Isso prova que o
arranjo serve — mas não satisfaz a condição original do ticket, porque o
repositório novo continua sem `data/` próprio. A distinção importa: o que foi
provado é o caminho, não a mudança.

**RT de 2026-08-30: este ticket NÃO fecha, e a política é que manda.** A
recomendação é inequívoca sobre o **método** — mover, nunca copiar nem apagar —
e silenciosa sobre o **destino**, que ela própria declara ser escolha do
usuário. Aplicar "mover" sem destino é impossível, e RT não força decisão onde
não há recomendação (`on_missing_recommendation`). O método fica registrado como
aceito; o destino segue aberto.

Para que a próxima palavra baste, o destino que eu recomendo é
`C:\Users\Administrador\Documents\LASTRO\dados`: irmão do repositório e fora
dele (o `.gitignore` não precisa saber que existe), no **mesmo volume** da pasta
antiga — mover 5,6 GB dentro do mesmo volume é renomear, instantâneo e
reversível —, e fora de qualquer pasta sincronizada, que é o caso que o
`00_config` documenta como perigoso porque a ingestão grava e apaga zips de
587 MB em segundos.

Um "sim" a esse caminho fecha o ticket; outro destino também fecha, e aí só
troco o alvo do `move`.

**Fechamento (2026-08-30).** O usuário escolheu `Documents\LASTRO\dados`. Movido
com `Move-Item`: **0,02 s**, porque mesmo volume é renomear — 814 arquivos e
5.835,7 MB antes e depois, contagem e soma de bytes idênticas, origem inexistente
ao fim. Provado com o teste-ouro rodando contra o caminho novo: passou.

**E o fechamento revelou o que o ticket não sabia: há DUAS árvores de dados, não
uma.** O repositório novo tem `data/` próprio, e ele não está vazio — outra
sessão vem escrevendo lá porque não define `RASTRO_DATA` e o `00_config` cai no
`ROOT/data`. No momento do move:

| | `LASTRO\dados` (movido) | `lastro/data` (interno) |
|---|---|---|
| `interim` | 5.634 MB, 272 arquivos | 27,9 MB, 7 arquivos |
| `processed` | 142 MB, 505 arquivos | 160 MB, **779 arquivos** |
| `raw` | 58,9 MB | 212,7 MB (download em curso) |
| `overrides` | 7 arquivos | 3 arquivos |

As duas divergiram e **cada uma tem conteúdo que a outra não tem**. O `interim`
insubstituível está no movido; o `processed` com mais arquivos está no interno.

Unificar as duas é decisão nova, criada pela concorrência entre sessões, e não
cabe neste ticket — nem se resolve enquanto a outra sessão estiver escrevendo.
Registrado como **RAS 00 TKT 0012**. Nada foi mesclado: mesclar duas árvores
`processed` divergentes é exatamente como se publica um site silenciosamente
errado.

**A pasta `Documents\RASTRO` continua existindo** com código, `.git` e o remoto
antigo — só os dados saíram. Apagar o resto é irreversível e não foi pedido.

---

### RAS 00 TKT 0012 — Duas árvores de dados, e as duas em uso

| Campo | Valor |
|---|---|
| `type` | `BLOCKING_DECISION` |
| `criticality` | alta — é de onde sai o número que vai para o site |
| `work_continues` | sim, com risco: cada sessão publica a partir da sua |
| `status` | **ABERTO** — aberto em 2026-08-30, ao fechar o TKT-0010 |

**summary.** O pipeline lê e escreve em `cfg.DATA`, que é `RASTRO_DATA` quando a
variável existe e `ROOT/data` quando não existe. Hoje as duas coisas existem e
as duas têm dado real: `Documents\LASTRO\dados` (canônico, com o `interim` de
5,6 GB) e `Documents\LASTRO\lastro\data` (interno, com um `processed` de 779
arquivos contra 505 do outro). Quem define a variável usa uma; quem esquece usa
a outra, e nada avisa.

**Por que isso é pior que desperdício de disco.** O `22_publicar_web.py` apaga e
reconstrói `app/public/dados` inteiro a partir de `cfg.PROCESSED`. Duas sessões
publicando de árvores diferentes produzem um site em que metade dos arquivos vem
de uma apuração e metade de outra — sem erro em lugar nenhum, porque cada arquivo
é individualmente válido. É o modo de falha que este projeto mais recusa: número
errado com aparência de certo.

**decision_needed.** Qual árvore é a única, e como o código passa a garantir isso.

**options.** (1) `00_config` prefere `../dados` quando existe, e imprime na
importação qual árvore escolheu — acaba com o "esqueci a variável" sem depender
de disciplina. (2) `00_config` **falha** se `RASTRO_DATA` não estiver definida,
tornando a escolha sempre explícita. (3) Manter como está e combinar por fora.

**leader_recommendation.** **Opção 1.** Um padrão que acerta sozinho vale mais que
uma regra que exige lembrar, e imprimir a árvore escolhida transforma um erro
silencioso em uma linha visível. A opção 2 é mais rígida e quebraria todo script
já escrito que não define a variável; a 3 é a situação atual, que já se mostrou
insuficiente.

**Fora da pré-autorização, e por isso aberto:** antes de trocar o padrão é
preciso decidir **o que fazer com o conteúdo único de cada árvore** — e há uma
sessão escrevendo numa delas agora. Mudar o padrão com trabalho em voo faria a
próxima execução dela trocar de árvore no meio de uma feature.

---

### RAS 00 TKT 0011 — Distrito Federal equiparado a estado

| Campo | Valor |
|---|---|
| `type` | `TRACKING_NO_APPROVAL` |
| `criticality` | alta — mexe na camada de apuração |
| `work_continues` | sim |
| `status` | **FECHADO** — o gate correu e passou, 2026-08-30 |

**summary.** O DF elege deputado **distrital** (cargo 8 do TSE) e o pipeline só
ingeria o cargo 7, então ele era a única unidade da federação sem casa
legislativa no painel. `49_df_distrital.py` traz os sete pleitos, equiparando
distrital a estadual: **24 eleitos em cada ano**, batendo com as cadeiras da
CLDF em sete pleitos independentes.

**Por que é ticket e não só roadmap.** Mexe em apuração, que é onde a regra de
auditoria deste projeto manda parar e olhar (DaRulez 3). E o gate ainda não
correu: o teste-ouro de Goiás decide se a inclusão fica.

**Três armadilhas encontradas, e uma delas eu criei:**

1. **Corrompi quatro arquivos do interim.** Montei a lista de colunas a partir
   de 2022 — 23 colunas, com federação — e anexei a todos os anos; 2002 a 2014
   têm 20. Só apareceu quando tentei ler um arquivo inteiro e o pandas falhou.
   A leitura de verificação anterior usava `usecols` e mascarava o desalinhamento.
   Reparado removendo exatamente as linhas anexadas, e o teste-ouro voltou a
   passar idêntico. O script agora alinha ao cabeçalho do ano e aborta se a
   contagem divergir.
2. **`contains("ELEITO")` casa com "NÃO ELEITO".** Relatei 286 eleitos numa Casa
   de 24. O pipeline publicado não tem esse defeito — usa `startswith` mais uma
   lista fechada que inclui `MEDIA` —, era só o meu diagnóstico.
3. **Em 1998 o DF não tem arquivo próprio** no zip do TSE: está dentro do
   `BRASIL.csv`, e naquele ano `QT_VOTOS_NOMINAIS` vem zerada, com os 872.072
   votos na `_VALIDOS`.

**O que a tela precisa continuar dizendo.** O DF é um município só: concentração,
domínio, contiguidade e o mapa degeneram lá — 100% do voto no único município
por construção, não por força política. O aviso está escrito em `VistaCargo`. A
geografia intra-DF existe por zona eleitoral e não há malha publicada de zona,
mesmo caso do vereador de capital.

**work_continues** enquanto o pipeline roda. Se o teste-ouro de Goiás mudar um
dígito, a inclusão volta atrás.

**Fechamento (2026-08-30).** O gate correu e não mudou um dígito: Álvaro Guimarães
12.160 / 12.398 / 18.646 / 27.074 / 35.660 / 23.788, Itumbiara 6.559 e 27,57%,
idênticos ao painel do TSE/GO. O `15_valida_nacional` confirmou que o recorte de
GO no arquivo do Brasil segue igual ao arquivo de GO nas 34 combinações
cargo/ano — que era exatamente o risco do append. Publicado e verificado no ar:
índice com 27 UFs e 189 linhas de agregado, aba **Distrital** no DF, 24 eleitos.

O DF obrigou a corrigir três exibições degeneradas que passavam por medida — os
dois coropléticos, a tipologia e a semelhança partidária — e revelou um defeito
antigo: a aba de Vereador ligava por `capital` e não pelo arquivo, então ficava
clicável no DF para cair num 404. Detalhe no ROADMAP, Marco 14.

Este ticket **não** foi fechado por RT: foi fechado pelo portão. RT não decide
gate — gate se decide rodando.
