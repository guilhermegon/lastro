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
