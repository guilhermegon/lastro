# LOG — RASTRO

## 2026-08-20 — Marco 1

Origem: usuário apontou o painel Power BI público do TSE/GO ("Distribuição Espacial do
Desempenho Eleitoral dos Deputados Estaduais, 1998 a 2018") e pediu análise, painel
semelhante para a última eleição, e inferências sobre padrões. Decisões: Goiás, série
completa 1998–2022, entrega dupla (Artifact HTML + dataset Power BI), quatro dimensões
de análise.

Descobertas que custaram tempo e que ficam registradas para não se repetirem:

- **CDN do TSE bloqueia cliente HTTP comum.** 403 em `Invoke-WebRequest`, em `HEAD` e em
  requisição com `Range`. Passa em GET simples via `curl.exe` com o conjunto completo de
  cabeçalhos de navegador. Está em `CURL_HEADERS` no `00_config.py`. Não usar `-I` nem `-r`.
- **Não existe arquivo por UF** em `votacao_candidato_munzona`: o zip é nacional (até
  587 MB) com um CSV por UF dentro. Com 26 GB livres em disco, a ingestão precisa apagar
  cada zip logo após extrair o CSV de GO.
- **O esquema do TSE não é estável na série.** 1998 traz `QT_VOTOS_NOMINAIS` zerada com
  os votos em `QT_VOTOS_NOMINAIS_VALIDOS`; 2002 não tem a coluna `_VALIDOS`.
- **`MÉDIA` conta como eleito** até 2010 — sem isso a contagem dá 35–38 em vez de 41.
- **1998 tem 4 candidatos com registro duplicado** (mesmo número de urna, dois SQ, votos
  repetidos): 3.352 votos inflados.
- **O mesmo nome aparece com e sem acento** conforme o ano. Usar o nome cru como chave de
  pessoa partia trajetórias ao meio e subestimava a reincidência (61% em vez de 70,7% em 2022).

Divergência não resolvida, documentada: o **denominador** do mapa de Influência do painel
original não é reproduzível a partir da base atual do TSE. Dos 20 municípios listados
para Álvaro Guimarães em 2018, 7 batem exatamente e os demais divergem em até 0,5% em
ambos os sentidos. Duas fontes independentes do TSE confirmam o nosso número. Optou-se
por não afrouxar a tolerância do teste até passar: a tabela A (votos do próprio
candidato, que bate 100%) é o portão rígido; a tabela B é comparação reportada.

Artifact publicado: https://claude.ai/code/artifact/60c14ca5-bff2-4693-bc23-3eca535f3944

## 2026-08-20 — Encerramento do Marco 1 (BEDEL)

O hook `Stop` apontou item aberto no `ROADMAP.md` (atribuir sigla / entrar no roster).
Verificado contra o DaRulez: o item **não** é resolvível pelo líder. A pré-autorização
de progresso não o cobre — "inventar código para projeto sem histórico" está na lista
explícita do que sobe sempre ao usuário, junto com reativar projeto pausado e expandir
ownership. Como não é possível formar `leader_recommendation` sem violar essa regra, o
ticket fica em `KEEP_TICKET_OPEN_FOR_MANUAL_RESPONSE` e `RT` não se aplica a ele.

Ação: aberta a `FILA00.md` com TKT-001 (sigla/roster, `BLOCKING_DECISION`), TKT-002
(outras UFs, rastreio) e TKT-003 (pleito de 2026, espera por evento externo). Os três
saíram da lista de execução do `ROADMAP.md` para a seção AGUARDANDO, com o motivo de
cada um. Sem próximo item seguro — encerramento legítimo.

## 2026-08-21 — TKT-001 respondido: sigla RAS

Usuário definiu a sigla **RAS**. O projeto entra no roster como `RAS00` e passa a ser
monitorado pelo BEDEL.

Executado: linha no roster e inclusão na lista monitorada em `~/.claude/CLAUDE.md`
(arquivo do MAESTRO 00, escrito sob a exceção de ordem direta do usuário — relido antes,
sem divergência desde 2026-08-10; **MAESTRO 00 a avisar**); `CLAUDE.md` na raiz com a
identidade `[RAS 00]` e as regras específicas do projeto; TKT-001 fechado na FILA;
ROADMAP atualizado.

Tickets novos passam a usar `RAS 00 TKT NNNN`. TKT-001 a TKT-003 mantêm os ids originais.

Restam TKT-002 (outras UFs, rastreio) e TKT-003 (pleito de 2026, espera por evento
externo) — nenhum executável. Sem próximo item seguro.

## 2026-08-21 — Pasta base movida para o OneDrive

Ordem direta do usuário. `C:\Users\Administrador\Documents\RASTRO` →
`C:\Users\Administrador\OneDrive\RASTRO`. A pasta de destino estava **vazia**: o usuário
mudou o diretório de trabalho da sessão, mas os arquivos não tinham sido movidos. Movidos
os 45 arquivos (134 MB) e conferidos na origem e no destino. A pasta antiga ficou vazia e
não pôde ser removida (handle preso por outro processo) — sem conteúdo, é inócua.

Nenhuma alteração de código foi necessária: nenhum script tem caminho absoluto, tudo
resolve a partir de `Path(__file__)`. Teste-ouro rodado no destino: passa.

Adequações feitas:

- roster em `~/.claude/CLAUDE.md` — caminho atualizado (arquivo do MAESTRO 00);
- roster em `~/.kimi-code/AGENTS.md` — `RAS00` acrescentado à tabela e à lista do BEDEL;
- `scripts/00_config.py` — passa a aceitar `RASTRO_DATA` para tirar `data/` de dentro da
  pasta sincronizada, sem mudar o padrão;
- `MSG-RAS00-sigla-e-mudanca-de-pasta.md` no CORREIO do MAESTRO.

**Divergência encontrada e NÃO corrigida:** a cópia do roster em `~/.kimi-code/AGENTS.md`
está sem o **EST00** desde 2026-08-08 — tanto na tabela quanto na lista monitorada pelo
BEDEL. Não é efeito desta mudança e não é projeto deste líder; corrigir seria mexer no
registro de outro projeto. Reportado ao usuário e no CORREIO.

## 2026-08-21 — Mudança para o OneDrive desfeita

Ordem direta do usuário: voltar a pasta base para `C:\Users\Administrador\Documents\RASTRO`.
Como na ida, o diretório de trabalho da sessão tinha mudado mas os arquivos não — os 45
arquivos (134 MB) ainda estavam no OneDrive. Movidos de volta e conferidos nas duas
pontas; `OneDrive\RASTRO` removida. Teste-ouro rodado no destino: passa.

Revertido:

- roster em `~/.claude/CLAUDE.md` e em `~/.kimi-code/AGENTS.md` — caminho de volta ao
  original, sem a nota sobre a mudança;
- `CLAUDE.md` do projeto — pasta base e a nota sobre sincronização;
- `MSG-RAS00-...md` no CORREIO — corrigida no lugar, e não por anexo, porque o MAESTRO
  está suspenso e ainda não a leu; deixar duas versões do fato num canal que ele vai ler
  de uma vez só criaria ambiguidade.

**Mantido de propósito:** `RASTRO_DATA` em `scripts/00_config.py`. O comentário foi
reescrito, porque a justificativa original era o OneDrive e ela caducou. A variável
continua útil por outro motivo: C: tem ~26 GB livres e a ingestão chega a ~1,2 GB de
pico. Padrão inalterado — sem a variável, `data/` continua dentro do projeto.

Lição que vale registrar: nas duas vezes, o aviso de mudança de diretório de trabalho
**não** significou que os arquivos tivessem sido movidos. Conferir o filesystem antes de
agir, sempre.

## 2026-08-21 — Ajuda contextual e rivais territoriais

**Ajuda.** 29 pontos de "?" no painel, cobrindo cada termo, critério e escolha de método.
Abrem por hover e também por foco de teclado, com fechamento por Escape — não é tooltip
só de mouse. Os textos dizem o que a medida é, como foi calculada e como ler o número,
incluindo onde o corte é escolha analítica e não do TSE.

**Rivais.** `scripts/10_rivais.py`. Duas medidas: afinidade (cosseno entre os mapas,
simétrica) e pressão (quanto do voto do deputado está em chão onde o rival é forte,
assimétrica). A separação aliado/adversário vem de `partidos_espectro.csv`, camada
externa e discutível, registrada como tal.

Achado que quase virou erro: o rival nº 1 é um aliado ideológico em 31 de 41 casos em
2022 — número que sozinho não significa nada, porque por acaso já se esperariam 66,8%,
dada a concentração das candidaturas do centro à direita. O efeito real é o excesso sobre
o acaso (+8,8 pp) e, sobretudo, o teste pareado: para o mesmo deputado, o aliado pressiona
mais que o adversário em 35 de 41 casos em 1998 e só 24 de 41 em 2018. A conclusão que
sobrevive é sobre movimento — território e ideologia estão se desacoplando —, não sobre
nível. A checagem de linha de base ficou dentro do script, não em rascunho.

## 2026-08-21 — Marco 2: federal, Senado e cruzamentos

Os intermediários só guardavam deputado estadual, então foi preciso rebaixar os 7 pleitos
(~2 GB) para extrair também os cargos 5 (Senado) e 6 (federal). Três defeitos no caminho,
todos registrados porque voltariam a morder:

- coluna `CD_CARGO` duplicada na lista de seleção fez `df["CD_CARGO"]` virar DataFrame;
- o `chaves` do groupby não recebeu o patch (o comentário-âncora tinha acento diferente do
  que eu supus) e a coluna sumia na agregação — falha silenciosa;
- o download de 2022 truncou em 554 MB e o cache aceitou pelo tamanho. O CDN do TSE rejeita
  `Range`, então não há retomada: agora há três tentativas e a validação abre o zip em vez
  de olhar só o tamanho.

Cadeiras por cargo entraram em `N_CADEIRAS_CARGO`: o Senado renova 1 ou 2 vagas
alternadamente, então não pode ser constante. O gate de contagem confirmou 1/2/1/2/1/2/1 no
Senado e 17 em todos os anos no federal.

Dois cuidados de método que ficaram no código, não só no texto: no Senado com duas vagas o
eleitor vota duas vezes e o total do cargo quase dobra — comparar fatias entre cargos sem
isso superestima o Senado; e o Senado é majoritário, então o painel suprime a coluna de
quociente em vez de exibir total÷vagas como se fosse um.

Achado mais forte: a correlação entre a geografia do partido no estadual e no federal é
mediana 0,15, mas PT 0,62 contra União Brasil 0,036 e PP 0,036. As duas maiores bancadas do
estado não têm máquina territorial — têm candidatos independentes dividindo uma legenda.

Achado que exigiu freio: as "dobradinhas" chegam a afinidade 0,9999, mas isso é geometria,
não prova de campanha casada — dois candidatos concentrados na mesma cidade têm o mesmo mapa
por construção. O painel diz isso em nota junto da tabela. O número informativo é a queda das
duplas do mesmo partido, de 21,3% (1998) para 7,7% (2022).

## 2026-08-21 — Marco 3: vereadores de Goiânia

Ciclo municipal 2000–2024, cargo 13. Pipeline próprio (`12_vereador.py`) em vez de forçar
no da eleição geral, por duas razões de natureza do dado: o ciclo não tem interseção com
os pleitos gerais, e a geografia é outra.

**A limitação central, que define o formato da aba:** Goiânia é um município só. A malha
municipal que sustenta todas as outras abas não desagrega nada dentro da cidade. A única
divisão interna que o `votacao_candidato_munzona` oferece é a zona eleitoral — 10 até 2016,
9 a partir de 2020 — e não existe malha pública com o desenho das zonas. Logo, **não há
mapa nesta aba**, e isso está dito na própria interface em vez de disfarçado. A geografia
entra como distribuição por zona.

Como o desenho das zonas muda entre pleitos, a comparação de distribuição entre anos
distantes é inválida; o script só calcula similaridade entre pleitos quando o número de
zonas coincide.

Achado a registrar como ressalva de método: a semelhança de cosseno **não se compara entre
escalas**. Sobre 9 zonas ela é mecanicamente muito maior que sobre 246 municípios — o 0,685
do MDB em 2024 não é o mesmo tipo de número que o 0,319 estadual. Anotado na aba e em
`ACHADOS.md`.

Dois achados substantivos: 2020 foi o ponto fora da curva em todas as colunas (873
candidaturas, o maior número da série, disputando o menor volume de votos, com o corte de
entrada mais barato — eleição da pandemia); e 2024 inverteu, com o último eleito precisando
de 3.607 votos, o dobro de 2020 e o maior da série mesmo com duas cadeiras a mais. Jorge
Kajuru em 2016 é o exemplo mais limpo de puxador de legenda do projeto inteiro: 6,01% dos
votos da cidade sozinho, 57,5% do total do partido, que elegeu 4.

## 2026-08-21 — Marco 4 e abertura do nacional

**Presidente e governador.** Cinco cargos e dois turnos. Três defeitos encontrados, todos
registrados em `docs/MODELO.md` porque nenhum é visível no dado:

- **Presidente não está no arquivo da UF.** É cargo nacional: fica no membro `_BR.csv`
  (ou `_BRASIL.csv`, o nome varia por ano) do mesmo zip. O de 1998 não tem membro
  nacional, então presidente cobre 2002–2022.
- **`SQ_CANDIDATO` não é único entre anos.** O TSE reaproveita o sequencial: Frederico
  Nassif tem o mesmo SQ como suplente em 2010 e eleito em 2014. Com chave só de SQ, o
  "eleito" de 2014 vazou para 2010 e a bancada federal passou a ter 19 nomes, com
  "eleitos" de 699 votos. A chave é (ano, SQ).
- **`DS_SIT_TOT_TURNO` vem `#NULO` em 2006 e 2010** para presidente. Não dá para derivar
  o vencedor dali, nem dos votos de Goiás — presidente é nacional e Goiás votou no
  derrotado nos dois anos. Daí a coluna `venceu_go`, que é derivável e é a leitura útil
  num painel sobre Goiás.

**Mapa de Goiânia por seção.** Eu tinha afirmado que não havia mapa possível; estava
estreito. Não há polígono de zona eleitoral, mas o TSE publica coordenada por seção em
`eleitorado_local_votacao`. Juntando com `votacao_secao` saem 349 pontos e 654.597 votos
mapeados. Duas armadilhas: coordenada ausente vem como −1 (plotar sem filtrar joga pontos
no Golfo da Guiné) e o arquivo de seção mistura branco, nulo e legenda com candidatos —
sem filtrar, "VOTO BRANCO" vira o mais votado da cidade.

**Nacional.** Ingestão ganhou modo `RASTRO_UF=BR`. Primeira execução saiu com **tudo
dobrado**: o membro `_BRASIL.csv` contém o país inteiro e estava sendo lido como se fosse
mais uma UF. Pegou na validação contra Goiás — GO 2002 deu 4.660.688, exatamente 2× o
valor conhecido de 2.330.344. Corrigido e revalidado: bate exato, 26 UFs (o DF não elege
deputado estadual).

**Limite de escala medido, não estimado.** Tratamento completo das 27 UFs num único
arquivo projeta ~89 MB, sendo 8 MB só de geometria municipal. O teto de página do
artefato é 16 MB. Por isso o nacional entra como comparativo agregado por UF (< 1 MB) e a
replicação por estado fica no cargo principal.

## 2026-08-21 — Marca: Lastro, Inteligência Política

Primeira proposta (prumo: haste vertical com peso sobre linha de base) foi
descartada pelo usuário com razão — a silhueta tinha leitura obscena evidente, e
logo não sobrevive a isso. Descartada, não ajustada: o problema era a forma, não
o acabamento.

Conceito mantido, forma refeita. **Estratos**: camadas horizontais que engrossam
em direção à base, apoiadas numa haste vertical. Faz três leituras sem forçar
nenhuma — um L (a inicial), um gráfico de barras horizontal (o produto) e uma
fundação (o nome, lastro é o que dá estabilidade e respaldo).

Arquivos em `dist/`: `logo-lastro.svg` (lockup), `logo-lastro-marca.svg` (marca
isolada) e `logo-lastro-mono.svg` — esta última sem opacidades, com a hierarquia
das camadas vindo só da espessura, para impressão em uma cor e fundos onde
transparência não é confiável. Todos usam `currentColor`.

Aplicado no cabeçalho do painel e no rodapé. No painel a marca usa `--accent` e
o texto usa `--ink`, então acompanha o tema.

## 2026-08-21 — Marco 5: replicação nacional entregue

Duas duplicações silenciosas no caminho, ambas pegas por validação e não por erro:

1. O membro `_BRASIL.csv` do zip entrou na lista de UFs e dobrou o país inteiro.
2. Corrigido isso, o mesmo membro continuou sendo anexado inteiro pelo bloco que busca
   presidente — e em 1998, 2006, 2010 e 2014 ele traz todos os cargos, não só o cargo 1.
   Dobrou de novo, mas só nesses quatro anos, o que é pior: parecia plausível.

As duas apareceram como número grande, nunca como exceção. Por isso ficou o
`15_valida_nacional.py`: exige que o recorte de Goiás dentro do arquivo nacional seja
idêntico ao arquivo de Goiás, em todas as combinações de cargo e ano. Passa em 34.

Tamanho medido, não estimado: geometria municipal do Brasil a 2,3 MB (tolerância 0,012),
detalhe dos eleitos dos 7 pleitos empacotado a 9,6 MB, total do payload 13,2 MB. Cabe nos
16 MB, então **não houve corte de anos** — as 26 UFs receberam os sete pleitos.

Ressalva que virou desenho de interface: municípios efetivos não se comparam entre
estados. Roraima tem 15 municípios, Minas tem 853 — o índice está limitado pelo porte. O
mapa nacional colore pela *fração* do estado ocupada, que é comparável, e a nota explica
por quê.

## 2026-08-21 — Adaptação ao celular

O painel do navegador desta sessão não desce abaixo de 980 px, então não foi possível
renderizar a 390. A análise foi feita sobre o CSS, que é determinístico, e o
comportamento de toque foi verificado com `TouchEvent` sintético.

Três defeitos reais, nenhum cosmético:

1. **Abas inalcançáveis.** `.abas` é flex sem wrap e sem overflow. Com 8 abas a 380 px,
   "Vereador" e "Cruzamentos" ficavam fora da tela e sem como chegar nelas. Agora a
   barra rola horizontalmente.
2. **Trilho antes do conteúdo.** Abaixo de 900 px a grade virava uma coluna e o trilho
   inteiro subia: cerca de 700 px de controle antes do primeiro número. Agora o trilho
   usa `display: contents` no celular, o bloco de lista fica em primeiro (`rail-primario`)
   e os controles secundários vão para depois do conteúdo.
3. **Mapa mudo no toque.** Os mapas informavam por `mousemove`. Em tela de toque não há
   hover, então dava para ver a mancha e não dava para saber qual município era. Agora
   `ligarInspecao` liga os dois caminhos — hover no desktop, `touchstart` no celular — e
   um toque fora fecha. O balão passa a se posicionar acima do dedo no celular, senão a
   própria mão cobriria a informação.

## 2026-08-21 — Marco 6: front end em React

Decisão do usuário: React para entrega de produto, daqui em diante. Escolhas
confirmadas com ele: hospedagem estática e TypeScript.

A mudança que importa não é React, é o **fatiamento dos dados**. A página anterior
embutia 13,3 MB e carregava tudo antes de mostrar qualquer coisa. Agora: app 212 KB +
índice 93 KB = 305 KB na abertura, e o estado escolhido vem sob demanda (Goiás 533 KB,
Minas 2,3 MB). Isso resolve o problema de celular que eu tinha sinalizado como não
resolvido.

O pipeline Python não foi tocado. Ele é a camada de dado e está validado — `06_verifica`
e `15_valida_nacional` continuam sendo os portões. `18_dados_web.py` só fatia o que
`16_payload_br.py` já produzia.

Portado, não reescrito: o `tokens.css` veio inteiro do painel anterior. Ele já tinha sido
validado nos três estados de tema e carregava os tokens de tinta sobre cada passo da
rampa — reescrever reintroduziria bugs de contraste já resolvidos.

Sem D3, sem Leaflet, sem Redux. A projeção são 40 linhas e o coroplético é um `path` por
município; o estado da tela são três variáveis e mora na URL, o que também torna o link
compartilhável. Biblioteca entra quando aparecer exigência que justifique — zoom, tiles,
rotação.

`noUncheckedIndexedAccess` ligado de propósito: o código faz `municipios[i]` o tempo todo
com índice vindo do dado, e é exatamente aí que se quer o compilador reclamando.

Verificado no navegador: SP com 645 municípios e 94 deputados, troca de estado e de ano,
URL sincronizando, toque abrindo o balão com dado real. Zero erro de console, `tsc`
limpo em modo estrito.

## 2026-08-21 — Repositório

`https://github.com/GTzon/lastro` — **privado**. Convite de escrita enviado a
`guilhermegon`, pendente de aceite. Commit autorado como
`Guilherme <guilhermegon@hotmail.com>`, conforme pedido.

65 arquivos, 0,4 MB. O que ficou de fora e por quê:

- `data/interim/` tem **5,3 GB** — só `votos_br_estadual_2022.csv` são 960 MB. É
  derivado e refazível pela ingestão.
- `data/raw/` é transitório por desenho: a ingestão apaga cada zip logo após extrair.
- `data/processed/`, `app/public/dados/` e os HTML montados são gerados.
- `app/node_modules/`, 71 MB, vem do `package-lock.json`.

Entram os três CSV de `data/overrides/` — correções de grafia de município, linhagem
partidária e posição no espectro. Não saem de lugar nenhum: foram levantados à mão e
perdê-los custaria refazer o trabalho.

Varredura de segredo antes do commit: os primeiros positivos eram "de**senha**do" e
"de**senha**r". Refeita com padrão estrito (chave de API, token entre aspas, bloco de
chave privada, credencial de nuvem): nada.

## 2026-08-21 — Nome do produto: Cadê o Voto?

Ordem do usuário. A casa é **Lastro — Inteligência Política**; o produto passa a ser
**Cadê o Voto?**. `RASTRO`/`RAS00` seguem como código interno no roster do Overhead e
não aparecem para o usuário final.

Nome funciona porque é uma pergunta, e o painel existe exatamente para respondê-la —
não é rótulo de categoria, é a coisa que o produto faz.

Aplicado nas duas páginas, no app React e nos README. As duas precisam de nomes
distinguíveis numa galeria, então:

- página nacional, o produto: **Cadê o Voto?**
- recorte profundo de Goiás: **Cadê o Voto em Goiás?**

## 2026-08-22 — Modelo completo replicado para as 26 UFs

Os cinco cargos, os sete pleitos, todos os estados, mais Padrões e Cruzamentos por UF.
54 MB, fatiados em `data/processed/web/{UF}/{cargo}.json`.

**Um arquivo por UF *e por cargo*, não um por UF.** Assim o front baixa só o cargo na
tela: São Paulo no estadual são 2,7 MB e não os 7,9 MB dos cinco somados.

Três defeitos encontrados, e nenhum deu erro:

1. **Adjacência calculada sobre a geometria de desenho.** A malha da web é simplificada
   a 0,012 e isso apaga vértices: Goiás caía de 5,3 para 3,7 vizinhos por município. Um
   índice de contiguidade assim mede o desenho, não o território. Separei em
   `20_adjacencia.py`, que deriva da malha completa — Goiás volta a 5,5 e o único
   município sem vizinho no país é Ilhabela, que é ilha.

2. **Chave de tipo trocado.** `vetores` era indexado pelo `sq` cru do groupby e a ficha
   guardava `str(sq)`. Nenhuma consulta casava, em silêncio: a janela de captura saía
   com 0 municípios de 246 e a semelhança entre partidos saía zero.

3. **Arrasto somando só eleitos.** Os cargos proporcionais guardam ficha só de quem se
   elegeu, para caber. Somar o partido por essas fichas subestima quem tem muita gente
   sem eleger — o PT saía 0,344 contra os 0,617 conhecidos. Passou a usar um agregado
   por partido sobre todos os candidatos, gravado no próprio arquivo do cargo.

Mais um ajuste de leitura: o arrasto exige presença em metade dos municípios do estado.
Sem isso a Unidade Popular, presente em 76 de 246, correlacionava 0,73 e aparecia acima
do PT sem dizer nada sobre máquina territorial.

Validação contra o pipeline de Goiás, tudo exato: Bruno Peixoto 73.692 e 23,78
municípios efetivos; janela de captura com pico de 41,66 na faixa de 15–25 mil; arrasto
do PT 0,617; semelhança do Republicanos 0,6103; escala governador 21,91 > presidente
14,46 > senador 12,14 > federal 10,12 > estadual 4,75.

Roraima virou o contraexemplo útil da ressalva de escala: com 15 municípios, todos os
cargos ficam entre 2,2 e 3,0 efetivos, e o estadual (3,0) fica **acima** do presidente
(2,2). Não é que o voto estadual seja mais disperso lá — é que o teto é 15.

## 2026-08-22 — Front React com o modelo completo

As sete abas no ar: presidente, governador, Senado, federal, estadual, Padrões e
Cruzamentos — para qualquer uma das 26 UFs, nos sete pleitos.

Carregamento por aba, não por estado. Trocar de aba busca um arquivo; trocar de estado
busca a base mais o cargo aberto. Abertura em 328 KB; a maior requisição do sistema é
`SP/estadual.json` com 2,7 MB, e só quem abrir São Paulo no estadual paga por ela.

Dois acertos que vieram de graça por causa do desenho:

- **O Distrito Federal aparece com a aba Estadual desabilitada**, porque ele elege
  distrital. Não há caso especial no código: a lista de cargos vem por UF no índice, e
  a aba se desabilita sozinha.
- **Roraima escancara a ressalva de escala na própria tela.** Os cinco cargos ficam
  entre 2,2 e 3,0 municípios efetivos, com o estadual acima do presidente. A nota da
  aba de Cruzamentos diz o motivo — o teto é 15 municípios — e a coluna de fração dá o
  número comparável.

`TKT-0004`, que pedia a ordem de porte entre quatro blocos, foi fechado sem precisar da
decisão: com a replicação completa, portou-se tudo de uma vez e não havia mais o que
priorizar.

## 2026-08-22 — as duas abas que faltavam

O usuário apontou que faltava algo, e faltava: a versão completa de Goiás tinha
**oito** abas, não sete. Faltavam os rivais territoriais e o vereador.

Os dois foram replicados para o país — rivais em 27 unidades (estadual e
federal, 1998–2022) e vereador nas 26 capitais (2000–2024, 182 arquivos
extraídos sem um aviso sequer).

**Um susto que não era defeito.** O arquivo do estadual de 2014 tem 4,26 milhões
de linhas contra 791 mil em 2010 — cinco vezes, no mesmo cargo. Parecia a
duplicação que já mordeu este projeto antes. Não era: 717 candidatos × 246
municípios em Goiás dá 176.382 exatamente, e não há duplicata em
`(uf, sq, município)`. A partir de 2014 o arquivo do TSE é **denso** — traz a
linha do município mesmo com zero voto.

**Um defeito que era real, e sério.** No Distrito Federal o painel de rivais
mostrava afinidade 1,000 com todo mundo e "disputam Brasília". O DF é um
município só: o cosseno entre dois candidatos quaisquer é exatamente 1, e a
lista estava ordenando por tamanho de votação com aparência de território. É o
risco que a regra de auditoria deste projeto nomeia — mapa errado com aparência
de certo. Corrigido nos dois lados: `23_rivais.py` não produz o arquivo abaixo
de três municípios, e a tela explica a ausência em vez de simplesmente não
mostrar o painel.

**Duas coisas que estavam misturadas.** O nome da capital servia ao mesmo tempo
de chave de pareamento com o TSE (maiúscula, sem acento) e de rótulo — a aba
dizia "Vereador · GOIANIA". Separadas em `CAPITAIS` e `NOMES`.

Tamanho: os rivais saíram primeiro com 28,9 MB porque cada ficha repetia o
**nome** dos municípios disputados. Trocado por índice em `base.json` (22,6 MB) e
cortado por cargo — São Paulo no estadual caiu de 3,97 MB para 1,54 MB.

## 2026-08-22 — o título pergunta pelo estado aberto

`Cadê o Voto em Goiás?`, `no Rio de Janeiro?`, `na Bahia?` — e a aba do
navegador junto, que é por ela que a pessoa acha a tela entre dez abertas e é o
que vai no link compartilhado.

A preposição é tabela, não regra derivável: "Goiás" e "Pará" terminam igual e
pedem *em* e *no*; "Bahia" e "Paraná" parecem o mesmo caso e pedem *na* e *no*.
Fica em `app/src/lib/uf.ts`, chaveada por sigla e não por nome — o nome vem do
IBGE e pode mudar de grafia. Mato Grosso e Mato Grosso do Sul vão sem artigo,
que é o uso oficial.

O subtítulo perdia o sentido dizendo "em todas as unidades da federação" sob um
título que nomeia uma: passou a descrever o estado aberto, e omite "município a
município" onde isso não quer dizer nada — o Distrito Federal é um município só.

## 2026-08-22 — a tela nacional vira a entrada, e o buraco que ela revelou

O usuário mostrou a tela nacional do artefato antigo e pediu que fosse a landing
page, com Nacional à esquerda e o estado à direita. A tela nunca tinha sido
portada para o React — só existia no `lastro_brasil.html`. Portada em
`VistaNacional.tsx`, virou a aba mais à esquerda e a vista padrão. Clicar num
estado no mapa, ou no nome dele na tabela, abre a tela daquele estado.

Ela não custa requisição: sai inteira do `indice.json`, os mesmos 96 KB que já
são baixados para desenhar qualquer tela.

**E foi conferindo os números dela que apareceu o defeito grande.** O artefato
antigo dava "último eleito" 6.603 em São Paulo; o pipeline dava 45.093. Contra o
dado bruto do TSE, 45.094 — o pipeline estava certo. Mas o **total** de São Paulo
divergia em 6.496 votos, e voto que some sem aviso é o defeito que este projeto
trata como gate.

`26_audita_pareamento.py`, escrito para isso, achou 23.063.701 votos e 153
municípios fora do mapa. Detalhe em `docs/MODELO.md`. O que importa aqui: **não
era um mapa com buraco, era uma série temporal com viés** — o TSE mudou a grafia
dos nomes ao longo dos anos, então os pleitos antigos perdiam e os recentes não.
Pernambuco perdia 10% em 2002 e 0,1% em 2022. Uma série de concentração lida
assim mostraria crescimento que é puro artefato.

Corrigido para 47.535 votos sem par, três municípios, todos só em 1998. Os dois
gates continuam passando: teste-ouro de Goiás e validação nacional.

O link público é `dist/cade_o_voto.html`, gerado por `28_build_landing.py`: a
tela nacional sozinha, 117 KB, autocontida. O app com os 27 estados e as oito
abas serve 80 MB sob demanda e precisa de hospedagem — não cabe em artefato, e
foi por isso que ele deixou de ser página única.
