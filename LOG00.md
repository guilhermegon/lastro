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

## 2026-08-23 — o layout quebrado e a página de estado que faltava

O usuário abriu o link e achou duas coisas: layout destruído, e estado que não
leva a lugar nenhum. As duas procedem, e a causa da primeira é instrutiva.

**O logo comeu o cabeçalho.** Inlinei `dist/logo-lastro-marca.svg`, o arquivo
solto, em vez da marcação de `Logo.tsx`. O SVG solto não carrega a classe
`lastro`, então a regra `.lastro { width: 164px }` não pegava — e o
`svg { width: 100%; height: auto }` global do projeto fez o logo ocupar os 344px
da coluna, com 308px de altura. O `<h1>` foi parar em y=330. Corrigido extraindo
o SVG do próprio `Logo.tsx` e envolvendo em `<span class="lastro">`, que é o que
o CSS espera. Logo: 344×308 → 164×43. Cabeçalho: 443px → 287px.

**A lição do método, não do bug:** na primeira publicação eu conferi os números
por consulta ao DOM — contagens, textos, totais — e não olhei o desenho. Tudo
que medi estava certo. Geometria de elemento (`getBoundingClientRect`) teria
pego em um passo, e passou a fazer parte da conferência.

**A página de estado não existia** — eu tinha dito que ficaria só no app, por
causa do teto de 16 MB do artefato. Medindo em vez de supor: o estadual dos 7
pleitos nas 26 UFs são 17,2 MB como o app serve, mas 9,9 MB sem os blocos `pm` e
`mm`, que só o pipeline usa. Com a geometria municipal (2,4 MB) e o índice, dá
13,0 MB — cabe. O artefato passou a ter as duas telas, com abas Nacional e
Estado, e três formas de entrar num estado: clique no mapa, clique no nome da
tabela, ou a gaveta. O estado vai na hash, então dá para mandar um estado
específico por link.

## 2026-08-23 — as abas de inferência entram no artefato

O usuário perguntou onde estavam as abas de inferência. Estavam só no app: eu
tinha deixado Padrões e Cruzamentos de fora do artefato por causa do teto de
16 MB. Medindo em vez de supor — de novo — os dois arquivos somam **0,74 MB**
nas 27 unidades. Cabiam desde sempre.

O artefato passou de 13,0 para 13,7 MB, com quatro abas: Nacional, Estado,
Padrões, Cruzamentos.

O que **não** cabe, e continua só no app: rivais territoriais (12,2 MB só no
estadual) e vereador nas capitais (4,8 MB). Qualquer um dos dois estoura o teto.

**Um defeito de leitura que o print do usuário revelou.** Havia um retângulo
escuro no meio do mapa de Goiás, nos dois mapas, que parecia buraco de
renderização. Não era: `--sem-voto` no tema escuro era `#232E31` contra um
`--surface` de `#161E21`, e o traço entre municípios é `var(--surface)`. Uma
mancha de municípios sem voto adjacentes se fundia num bloco sem borda visível.
A categoria existia e estava correta — só não dava para ler. `--sem-voto` no
escuro foi para `#2E3A3D`. Vale para o app também, que divide o mesmo
`tokens.css`.

Conferido que os números do artefato batem com o pipeline: o arrasto do PT em
Goiás 2022 sai 0,617 em 246 municípios, que é o valor validado — o mesmo que
saía errado em 0,344 quando era calculado só sobre os eleitos.

## 2026-08-23 — auditoria de design com o impeccable

O usuário apontou `pbakaus/impeccable` e perguntou se dava para usar. Dá: ele
traz 59 regras determinísticas que rodam offline, sem LLM e sem chave.

Primeira rodada no artefato: 16 achados. Última: 12, e os 12 são falsos
positivos verificados um a um. O detalhe está em `docs/MODELO.md`.

O ganho real foi de contraste. `--ink-3` — que carrega cabeçalho de tabela,
legenda de índice, rótulo de cartão e eixo de gráfico — estava em 3,68:1 no tema
claro. Não é decoração, é conteúdo. Foi para 5,36:1.

**Duas armadilhas no cálculo, que valem mais que o resultado:**

A tinta do mapa de calor tem de ser por tema. Calculei contra o verde do escuro e
apliquei nos dois; no claro o verde é bem mais escuro e o texto caiu para 2,61:1.
E não dá para escolher a direção da tinta pela luminosidade da faixa: num laranja
médio, branco dá 2,98:1 e escuro dá 4,52:1 — a rotina agora testa as duas
direções e fica com a melhor.

**O que o detector erra, e por quê.** Ele é estático e não sabe a qual bloco de
tema um token pertence, então pareia o `--ink-3` do escuro com o branco do claro
e acusa 3,7:1 num par que nunca existe na tela. A varredura de contraste no DOM
vivo, percorrendo os dois temas e as quatro abas, deu **zero falhas** — é ela que
fecha a conta.

Ressalva registrada: `CLAUDE.md`, `AGENTS.md` e `.claude-plugin/` daquele
repositório são instruções escritas para agentes. Foram lidas como material, não
como ordens, e nada foi instalado.

## 2026-08-23 — Emendômetro no ar

A aba está publicada, e a decisão que a define é de honestidade, não de código.

**Duas coberturas, e as duas na tela.** Só 10,5% do dinheiro das emendas
individuais é rastreável até um município — 76% está declarado como `MÚLTIPLO`,
espalhado por cidades que o arquivo não nomeia. Mas 69% dos municípios do país
receberam alguma emenda rastreável somando 2015–2026. Os dois números são
verdadeiros e respondem perguntas diferentes; a nota no topo da aba diz o
primeiro, e o mapa acumulado existe por causa do segundo.

**O atalho que ficou fechado.** O arquivo por favorecido tem município em 100%
do dinheiro. Brasília concentra 36,4% — é o endereço do Fundo Nacional de Saúde
e dos intermediários. Teria dado um mapa completo e falso.

**Por que o mapa abre acumulado.** Goiás em 2024 tem 15 municípios com emenda;
os doze anos juntos dão 170 de 246. Num ano só o mapa sugere ausência de
dinheiro onde o que há é ausência de rastreabilidade.

O artefato foi de 13,7 para 15,0 MB. O teto de 16 agora está perto, e é ele que
decide o que ainda cabe — o cruzamento voto × emenda vai precisar ser magro.

## 2026-08-23 — o dinheiro segue o voto, e o número sobrevive

**60,1% da emenda de um deputado cai nos 10 municípios onde ele mais votou.**
Sozinho, esse número não vale nada: Goiânia recebe muito voto e muita emenda de
quase todo deputado goiano, porque é grande.

A linha de base é o que o torna legível — a **mesma** emenda medida contra o
reduto de **outro** deputado da mesma UF e do mesmo pleito dá 5,7%. Se o dinheiro
fosse para a cidade grande por ser grande, cairia no reduto alheio também e o
excesso zeraria. Sobram +15,9 pp.

E a escada de robustez anda para o lado certo: exigindo ao menos 10 municípios
rastreáveis, o excesso ponderado por dinheiro fica em +24,5 pp e é positivo em
91% dos casos. Artefato de denominador pequeno encolhe sob filtro; este cresce.

Fica na tela a ressalva de que isso mede a fatia rastreável — mediana de 1,9% da
carteira de cada deputado.

**Duas mudanças pedidas no meio do caminho, ambas certas.** Real por habitante e
por km², do Censo 2022 do IBGE: as três medidas contam histórias diferentes em
Goiás — absoluto é Goiânia com R$ 22,8 mi, por habitante é Campos Verdes com
R$ 527, por km² é Valparaíso com R$ 141 mil. E a gaveta "Qual seu estado?"
desceu para dentro das abas de estado, sumindo no Nacional, onde o mapa já é o
seletor.

Artefato em 15,2 MB de 16.

## 2026-08-23 — sumário, emenda Pix e dois defeitos de navegação

**Sumário clicável nas cinco abas**, no trilho, montado a partir dos `<h2>` que a
aba acabou de desenhar — não de uma lista escrita à mão. As abas trocam de
conteúdo conforme estado, ano, autor e tipo; um índice fixo mentiria assim que
uma seção sumisse. Ele marca a seção em leitura e acompanha a rolagem.

Três abas não tinham trilho nenhum (Nacional, Padrões, Cruzamentos) e ganharam.

**Um defeito medido, não suposto.** `scrollIntoView({behavior:"smooth"})` não
rolava nada. Servida como fragmento, a página cai em modo quirks e quem rola é o
`<body>`, não o `<html>` — e smooth sobre o body simplesmente não acontece. Agora
a posição é calculada, a rolagem é conferida, e se não saiu do lugar os dois
elementos são empurrados na mão. `prefers-reduced-motion` continua respeitado.

**Emenda Pix separada.** É o apelido da Transferência Especial: cai direto na
conta do município, sem convênio, sem finalidade definida e sem acompanhamento
federal. São **R$ 32,2 bi, 23% das emendas individuais** do país. Filtro de três
estados — todas, só Pix, sem Pix — e o "sem Pix" é subtração, não uma terceira
soma gravada: guardar os três seria a chance de os três discordarem. Em Goiás a
soma fecha: R$ 15,4 mi + R$ 300,8 mi = R$ 316,2 mi.

O mapa do Pix é outro mapa. Em Goiás o geral tem Goiânia no topo; o Pix tem
Planaltina.

**E a troca de estado estava forçando a aba Estado.** Quem estava no Emendômetro
de Goiás e escolhia São Paulo caía na ficha de um deputado paulista. Agora a aba
é preservada — só o Nacional é exceção, porque lá clicar num estado é pedir para
entrar nele.

Artefato em 15,7 MB de 16.

## 2026-08-23 — piloto de Goiás: emendas de deputado estadual

**Eu tinha descartado a fonte certa.** Disse que os dados abertos de Goiás só
tinham fragmentos e que a execução completa exigiria engenharia reversa do painel
Power BI. Errado: o conjunto "Emendas Parlamentares - SERINT" é a base da
Assembleia Legislativa inteira, em CSV, 2019–2025. Julguei pelo nome do órgão
sem ler a descrição do conjunto, que diz exatamente o que é.

**O custo do piloto não estava onde eu esperava.** Achar o dado foi fácil. O
trabalho é que o esquema muda todo ano: sete arquivos, sete formatos, separador
que vira tabulação em 2025, e a coluna de autor com três nomes diferentes ao
longo da série. Uma tabela de nomes fixos quebraria no próximo arquivo — as
colunas passaram a ser achadas por busca.

**Duas correções minhas no caminho, ambas do mesmo tipo.** Escrevi dois códigos
IBGE de memória para o override e os dois estavam errados: 5208707 é Goiânia,
não a cidade de Goiás. Fui buscar na malha. E concluí "município só a partir de
2023" olhando cabeçalhos — os arquivos de 2024 e 2025 são despejos multi-ano e
trazem município para exercícios antigos, o que dá 246 municípios em 2022.

Resultado: 22.310 linhas, 186 autores, R$ 4,0 bi, 65,8% do valor com município.
Casamento com deputado estadual eleito em 61% dos autores e 76% do dinheiro —
subiu de 43% quando tirei o prefixo "DEP." do nome, que a base do estado usa e a
do TSE não.

Cinco nomes seguem sem par, R$ 1,5 mi, e quatro nem são município. "RIO DOCE"
pode ser Aparecida do Rio Doce, mas *pode ser* não entra em override: par errado
põe dinheiro no município errado, que é pior que dinheiro sem município.

## 2026-08-23 — esfera estadual no Emendômetro

Fusão, não aba nova. Aplicado sob a pré-autorização, com recomendação
inequívoca: uma aba que existe só em Goiás ficaria vazia em 26 estados, e a
pergunta que interessa é comparativa — o deputado estadual manda dinheiro para o
mesmo tipo de lugar que o federal?

O seletor de esfera só aparece onde há base estadual. Trocar para um estado sem
base volta sozinho para federal, em vez de mostrar tela vazia. E na esfera
estadual somem três coisas que são do federal por natureza: o filtro de Pix
(Transferência Especial é instrumento da União), o cruzamento voto × emenda e a
tabela nacional por UF.

**A comparação em Goiás é o resultado.** O federal rastreia R$ 316,2 mi ao
município (6,5%) e alcança 170 de 246; o estadual rastreia R$ 2,61 bi (65%) e
alcança os 246. A maior carteira federal é de R$ 21,8 mi em 19 municípios; a
estadual, R$ 46,1 mi em 73. Não é o estado sendo mais transparente por virtude —
é que a emenda federal é maior por unidade e vai com frequência para `MÚLTIPLO`.

Zero falhas de contraste nos dois temas. Artefato em 15,8 MB de 16 — o teto
agora é a restrição que decide o próximo passo.

## 2026-08-23 — a sondagem que matou uma ambição

O roadmap pedia "decidir se vale ir para os outros 25". A decisão estava
impossível porque faltava o insumo — e o insumo era medição minha, não juízo do
usuário. Sondei os 27 portais estaduais de dados abertos.

**Dez de 27 respondem CKAN. Seis têm algum conjunto com "emenda parlamentar".
Cinco em formato tabular. E abrindo os cinco, sobram três de verdade: GO, PE e
ES.** Paraíba só tem "Orçamento" genérico; Santa Catarina foi falso positivo —
o casamento era com portarias de COVID.

Isso responde e encerra: **o Emendômetro estadual nacional não existe como
produto uniforme.** Dezessete portais nem respondem API. Fazer os 25 seria 25
projetos de raspagem, um por um, sem garantia de trazerem autor e município.

O que vale é o oposto de ambicioso: **mais dois estados.** Pernambuco tem quatro
conjuntos da SEPLAG em CSV, incluindo "Emendas Especiais - PIX" próprias do
estado — o instrumento federal replicado localmente, que é achado por si só.
Espírito Santo tem "Emendas Parlamentares do Estado" da SEFAZ, e separa as
federais das estaduais, o que poupa trabalho.

A ressalva do script vale para os dois: achar o conjunto não garante autor e
município dentro. Em Goiás o conjunto certo estava lá e eu o descartei pelo nome
do órgão. Abrir antes de prometer.

## 2026-08-23 — a aba Sobre

Consolida o que o projeto aprendeu apanhando: a coluna de votos que muda de ano,
o "MÉDIA" que é eleito, os registros duplicados de 1998, o código de candidato
que se repete entre pleitos, os 23 milhões de votos perdidos no pareamento e a
tabela de perda por ano que mostra o viés sendo temporal e não espacial.

Do lado da emenda: pago e não empenhado, os 76% em MÚLTIPLO, o atalho falso do
favorecido com Brasília em 36,4%, a emenda Pix, e por que o mapa abre acumulado.

E duas seções que valem tanto quanto os números: **"O que não fazemos"** —
lacuna não vira zero, teste não afrouxa, pareamento não se chuta, denominador
não some — e **"Onde o juízo é nosso"**, que declara as três camadas editoriais
(linhagem partidária, espectro ideológico, cortes da tipologia) como discutíveis
por natureza.

Nove seções, três tabelas, dezesseis fatos. Zero falhas de contraste nos dois
temas. O título volta a ser "Cadê o Voto?" e a gaveta de estados some, porque a
aba não é de um estado.

## 2026-08-23 — Espírito Santo entra, e dois defeitos de pareamento no caminho

Segunda esfera estadual no ar: GO e ES. O seletor continua aparecendo só onde há
base, e agora são duas.

**O contraste entre as esferas é o produto.** No Espírito Santo, o federal
rastreia R$ 181,8 mi de R$ 2,90 bi ao município — 6,3%, alcançando 69 de 78. O
estadual rastreia R$ 240,8 mi de R$ 291,9 mi — 82,5%, alcançando 77 de 78. Menos
dinheiro, muito mais visível. E o topo muda: federal é Cariacica, estadual é
Vitória.

**Dois defeitos meus, os dois de pareamento, os dois pegos por número absurdo.**

O primeiro: o detector de formato de moeda aceitava duas casas decimais e o ES
publica `11250,0000`, com quatro. A vírgula virava separador de milhar e o total
deu R$ 217 bilhões num estado cujo orçamento é fração disso.

O segundo: o `CodigoMunicipio` do ES tem **seis** dígitos, não sete — é o código
do IBGE sem o dígito verificador. `320332` é o `3203320` de Marataízes. Eu
preenchi zero à esquerda e o pareamento deu exatamente zero de 78 municípios.

Os dois erraram por ordens de grandeza, e é por isso que foram vistos. Um erro de
10% teria passado nos dois casos — o que reforça por que este projeto trata
pareamento como gate e não como detalhe.

## 2026-08-23 — Bahia descartada, e o placar fecha

O ZIP da SEFAZ tem cinco tabelas do FIPLAN. A `DESPESAS` traz `Nome do Deputado`
e `Valor Pago`; a `PAGAMENTOS` traz razão social do credor e objeto. **Nenhuma
das cinco tem município.** Autor sim, geografia não — e sem geografia não há
mapa, que é o produto.

Abri a tabela errada na primeira tentativa (a de centralização, com quatro
colunas de código) e quase concluí que o ZIP era inútil. Cinco tabelas exigem
abrir as cinco.

**Placar final: dois de 27.** Goiás e Espírito Santo entregues; Pernambuco e
Bahia descartados depois de abertos; 23 sem dado acessível.

E os dois descartes só apareceram abrindo o arquivo. Pernambuco publica
dicionário descrevendo campos que nenhum arquivo tem; a Bahia tem o deputado mas
não o lugar. Nenhuma das duas coisas se vê pela descrição do conjunto — que foi
exatamente o erro que cometi ao escrever a linha do roadmap sobre PE.

## 2026-08-23 — aba API, e o mapa que não existia

Sondadas as 27 casas legislativas estaduais. Não há catálogo público disso, e a
pergunta nasceu procurando emenda estadual.

**19 de 27 respondem** algum portal; **4 têm API confirmada** abrindo à mão (GO,
MG, PE, DF); 8 não devolveram nada nos caminhos testados.

**A inferência principal é negativa e vale mais que a contagem: nenhuma
assembleia publica emenda parlamentar.** Elas publicam a si mesmas — folha,
diárias, verbas indenizatórias, licitações, contratos. A Casa como empregadora e
compradora, nunca como poder que direciona orçamento. E isso é coerência
institucional: a emenda é indicação sobre o orçamento do Executivo e executada
pelas secretarias.

Consequência prática, que economiza o dia que gastamos: **quem procurar emenda
estadual não deve começar pela assembleia.**

**Dois defeitos meus na sonda, os dois pegos por absurdo.** A primeira versão
deu zero APIs num levantamento em que eu já tinha testado a da ALEGO
respondendo — ela mora dois níveis abaixo do caminho que eu sondava. E a lógica
de subdomínio cortava o domínio da casa para o do estado, levando a sonda ao
Executivo num levantamento sobre o Legislativo.

A aba diz a data no rodapé e aponta o script: portal muda de endereço, e é a
data que dá validade ao número, não a nossa palavra.

## 2026-08-23 — piloto consumindo a API da ALEGO

A aba API catalogava quem publica. Agora consome: verba indenizatória dos
deputados de Goiás, 91 dos 96 meses entre 2019 e 2026, direto da API.

**Dois achados, os dois de uma subtração que ninguém faz.** A API entrega
`valor_apresentado` e `valor_indenizado`; a diferença é a glosa — despesa que o
gabinete pediu e a Casa recusou. São R$ 349 mil de R$ 111,8 mi: **0,31%**. E os
20 deputados com série longa ficam todos entre R$ 25 mil e R$ 32 mil por mês.
Todo mundo bate no teto, quase nada é recusado.

A consequência analítica importa mais que os números: **se todos usam o teto,
ordenar por gasto total ordena por tempo de mandato, não por comportamento.** O
que distingue é a glosa, e ela é rara o bastante para que os poucos casos
mereçam olhar.

**Um defeito que teria virado afirmação falsa.** A primeira varredura trouxe 37
dos 96 meses, com 2022 e 2023 completamente vazios — e eu já tinha testado
2023/02 à mão, com 41 registros. Requisição que falha, lida como ausência de
dado, não parece erro: parece resultado. Foi o único tipo de erro que este
projeto comete repetidamente, e a correção é sempre a mesma — tentar de novo
antes de concluir. Com três tentativas, 91 meses.

Verba indenizatória não é salário nem emenda: é custeio de gabinete, pago pela
própria Assembleia. A tela diz isso, para que ninguém some com emenda.

## 2026-08-23 — segundo piloto de API: o DF

A CLDF publica a mesma verba indenizatória de Goiás, em grão muito mais fino:
nota a nota, com fornecedor, CNPJ e categoria. 20.572 comprovantes, 2013–2024.

**O achado que só esse grão permite:** entre o que tem categoria, o maior item
da verba de gabinete é **divulgação de atividade parlamentar, 27,7%**.
Publicidade do próprio mandato. Veículos vêm logo atrás com 28,9%, somando as
duas grafias que o arquivo usa para a mesma coisa.

**E duas ressalvas que quase viraram publicação errada.** Primeiro: 68,3% do
valor não tem categoria — a tabela original falava de 31,7% do dinheiro sem
dizer. Segundo, e pior: eu ia publicar que o deputado do DF gasta um terço do
goiano. O cálculo roda e dá isso. Mas a CLDF tem 24 distritais e o arquivo traz
de 3 a 26 por ano — publicação parcial, não rotatividade. Aquele número
descreveria a política de publicação de cada casa achando que descreve
comportamento de gasto.

**Recusei a comparação e escrevi na tela por que.** É a mesma disciplina do
mapa por favorecido, onde Brasília aparecia com 36% das emendas: existe um
cálculo que roda, dá número redondo e é falso.

Os dois pilotos param em lugares complementares — Goiás revela glosa e não
revela destino; o DF revela destino e não revela glosa.

## 2026-08-23 — gasto administrativo, e o estado do dado no Sobre

A aba API deixou de ser só catálogo: agora pergunta **quanto custa a Assembleia
e no que o dinheiro vai** — que é exatamente o que as Casas publicam, já que
nenhuma publica emenda.

**O orçamento da ALEGO foi de R$ 626,9 mi em 2019 para R$ 1.019,3 mi em 2026 —
63% em sete anos.** E a fatia de pessoal caiu de 80% para 62%: o que cresceu foi
custeio e investimento, não folha.

**Quatro empresas concentram os 574 terceirizados.**

**E um achado sobre a fonte que impediu uma publicação errada.** O campo de valor
das diárias não pode ser somado: a maior "diária" do conjunto é de
R$ 2.676.075,25 para 1,5 diárias de um assessor, com motivo sobre edição de um
evento. Cento e vinte e oito registros — 0,6% — concentram 41% da soma, e não são
diárias. Publicamos o valor típico (mediana R$ 370) e a contagem, nunca o total.

Três erros meus no caminho, todos de leitura apressada do dado: somei colunas de
orçamento quando havia `total_autorizado` pronto; ignorei que há dois registros
por ano (ALEGO e FEMAL, um fundo à parte); e ia publicar que 32,7% das diárias
vão para parlamentares, número inteiramente produzido pelos tais 128 registros.

**No Sobre entrou "O estado do dado no Brasil, medido"** — os três levantamentos
consolidados numa tabela e quatro conclusões. A que mais importa: *publicar não é
publicar utilizável*. Pernambuco documenta um esquema que nenhum arquivo usa, a
Bahia publica o deputado e não o município, e a ALEGO publica uma diária de
R$ 2,7 milhões. Nenhum desses casos aparece para quem lê a descrição em vez do
arquivo.
## 2026-08-30 — o Distrito Federal entra, e um append quase destruiu quatro anos

O DF era a única unidade sem casa legislativa no painel: elege **deputado
distrital**, cargo 8, e `cfg.CARGOS` só conhece o 7. Os 24 distritais entraram
equiparados a estaduais — a Câmara Legislativa acumula as competências de
assembleia e de câmara municipal — sob a chave `estadual`, com rótulo
**Distrital** na tela. Sete anos, 24 eleitos em cada um.

**O erro que quase passou.** `49_df_distrital.py` montou a lista de colunas a
partir de 2022 — 23 campos — e anexou isso a 2002, 2006, 2010 e 2014, que têm
20: os três campos de federação só existem de 2018 em diante. Quatro arquivos do
interim ficaram com linhas desalinhadas.

O que torna este caso pior que um bug comum é que **eu verifiquei e a
verificação passou**. Conferi lendo com `usecols`, que só toca as primeiras
colunas — e essas continuavam plausíveis. O estrago só apareceu quando o pandas
falhou lendo o arquivo inteiro, `Expected 20 fields, saw 23`. Conferência que
olha menos que o dano não é conferência; é aval.

Reparo: remover as linhas cuja contagem de campos difere do cabeçalho — eram
exatamente as anexadas, contíguas no fim (626, 645, 798 e 979). O teste-ouro
voltou a passar idêntico. O portão virou código: o script agora lê o cabeçalho do
arquivo alvo primeiro, alinha o DF a ele, e aborta se a contagem não bater.

**1998 escondeu o DF duas vezes.** Não há `_1998_DF.csv`: o zip traz 26 CSV por
UF mais um `_BRASIL.csv`, e o DF está lá dentro. Procurar pelo arquivo por UF
devolve vazio, e vazio ali se leria como "o DF não elegeu distrital em 1998" —
elegeu 24, com 594 candidatos. E o ano traz a armadilha já conhecida:
`QT_VOTOS_NOMINAIS` zerada, os 872.072 votos em `_VALIDOS`.

**286 eleitos numa Casa de 24.** Meu diagnóstico usou `contains("ELEITO")`, que
casa com "NÃO ELEITO". O pipeline publicado nunca esteve errado — usa
`startswith` mais a lista fechada. Foi absurdo o bastante para se denunciar; o
que não é garantia para os erros que caem dentro do plausível.

**O DF obrigou a arrumar o que degenera com cara de medida.** Um município só
zera a geografia inteira, e o pior não é o índice degenerado — é ele parecer
resultado. Saíram os dois coropléticos (polígono sempre cheio, legenda repetindo
"51.792 a 51.792" cinco vezes) e a tipologia. A semelhança partidária virou
`null` **no dado**, no `19_`, e não só na tela: cosseno de vetores de uma
dimensão é 1,000 sempre, e quem lê o arquivo não viu a tela.

**E na comparação nacional, `null` virava zero.** A tabela mostrava "0,0
municípios efetivos" e "0,0%" de fração do estado para o DF, e a ordenação o
punha no extremo, como se fosse a unidade com o voto **menos** espalhado do
país. `?? 0` num campo anulado de propósito desfaz o cuidado que anulou.

**Um defeito antigo veio junto.** A aba de Vereador ligava por `capital`, e o
índice dá `capital` ao DF de propósito — a landing marca a capital no mapa. A aba
ficava clicável e caía num 404 exibido como string de erro crua. Passava
despercebido porque ninguém abria o DF. Agora `capital` é só a marca no mapa e o
campo novo `ver` liga a aba: 26 UFs com flag e arquivo, o DF sem os dois.

**Portões.** Teste-ouro de Goiás passou idêntico, e `15_valida_nacional` confirmou
que o recorte de GO no arquivo do Brasil segue igual ao arquivo de GO nas 34
combinações cargo/ano — o que era exatamente o risco do append.

**O que o DF acrescenta.** Nas colunas que não dependem de território ele não é
figurante: com as **mesmas 24 cadeiras** de Mato Grosso do Sul e do Tocantins, o
quociente do DF em 2022 foi **66.575**, contra 55.854 e 33.327. Mesma Casa, o
dobro do preço de entrada do Tocantins.
## 2026-08-30 — o mapa de urnas ganha chão, e a medição que quase o impediu

O mapa por local de votação era uma nuvem de círculos enquadrada na própria
nuvem. O defeito não era feio, era **semântico**: como o quadro se ajustava aos
pontos, "as urnas estão todas num canto" e "as urnas estão espalhadas" saíam
idênticas na tela. O enquadramento apagava a única coisa que o mapa tinha a
dizer.

**Antes de desenhar a primeira linha, o portão.** Contorno errado é pior que
contorno nenhum: sem fronteira o leitor vê uma nuvem e sabe que é uma nuvem;
com fronteira, ele acredita na fronteira. Medi ponto-em-polígono nos 246
municípios: **2.459 locais com coordenada, 4 fora — 0,16%**. Fui ver quanto é
"fora": 60 a 90 metros. A esse zoom, um pixel. Não era coordenada errada do TSE,
era precisão de limite entre duas bases — e a diferença entre "0,16% fora" e
"0,16% a 80 metros" é a diferença entre publicar e não publicar.

**Medi também a simplificação, e ela não existia.** Ia gerar o contorno numa
tolerância menor que a do coroplético estadual; o teste mostrou que simplificar
a malha bruta a 0,001 grau tira 234 vértices de 32.384 — 0,7%. A malha
"intermediária" do IBGE já vem simplificada na origem. Não havia o que
economizar, e escrever código de simplificação teria sido trabalho para nada.

**E aí veio o número que mudou o desenho.** A mediana é de **4 locais de
votação por cidade**, e em **109 dos 246** a mancha ocupa menos de 15% da largura
do município. Enquadrar no município — que era o pedido, e é o certo — deixaria
44% das cidades com os pontos num borrão. A saída foi a convenção cartográfica
de sempre: **detalhe mais localizador**. O quadro principal continua o
município; abaixo de 22% de mancha entra uma lupa, amarrada ao primeiro quadro
por um retângulo tracejado.

O retângulo, aliás, nasceu invisível: dimensionei pela caixa das coordenadas, que
nessas cidades é sub-pixel, e ele ficou inteiro debaixo dos círculos — desenhado
e sem existir. A marca tem de envolver os **círculos**, não os pontos.

**A concentração é o achado, não o defeito.** Em Caçu os sete locais estão num
canto de um município comprido: a cidade inteira vota na sede. Sem contorno,
esse fato não tinha como aparecer.

**E três textos contradiziam a tela.** A cobertura municipal chegou e ninguém
mexeu na escrita: a aba dizia "Vereador · Goiânia" com Caçu aberto, o subtítulo
dizia "Vereadores da capital", e a nota dizia "não há mapa" — escrita logo acima
de um mapa. Texto que contradiz o que está na tela custa mais que texto ausente:
ensina o leitor a não ler.

**Um erro meu no caminho:** pendurei o `useMemo` da cidade selecionada depois de
um `return` antecipado do componente, e o React derrubou a página inteira com o
erro #310 — hook não pode ser condicional. Tela branca, e o `tsc` passou limpo,
porque o compilador não vê ordem de hook.
## 2026-08-30 — o beco sem saída que um link meu abriu

O usuário mandou testar a barra de abas. Testei clicando as sete, e as sete
quebravam — vindo de um link com `ano=2024`.

**Duas falhas somadas.** A primeira: o ano vem da URL sem passar por lista
nenhuma. O `ehVista` valida a vista; o ano era `Number(p.get("ano") ?? 2022)`
e pronto. E a URL é feita para ser compartilhada — o próprio cabeçalho do
arquivo diz que o estado da tela mora nela. A aba de vereador tem escala
própria, 2000 a 2024, sem um único ano em comum com os pleitos gerais; ela
guarda o ano dela em estado local e por isso nunca sujou `sel.ano`. Quem suja
é um **link** — e o link foi meu, escrito na mensagem anterior. Clicar em
Presidente pedia `presidente/2024.json`.

A segunda: o 404 derrubava a página inteira. O `if (erro)` era um return
antecipado que substituía tudo, inclusive a fileira de produtos e a barra de
abas. O leitor ficava numa tela de erro **sem um único botão para sair**, só
editando a URL.

Sozinha, a primeira é um link ruim. Sozinha, a segunda é um erro feio. Juntas
são um beco: basta um link com ano de outra escala.

**Consertadas as duas, e de propósito as duas.** Corrigir só o ano deixaria o
beco montado para o próximo arquivo que faltar. Agora o ano da URL é encaixado
no pleito imediatamente anterior que existe — 2024 vira 2022, não 1998, porque
quem abriu um link de 2024 quer o mais recente —, `ano=abc` vira 2022 na
porta, e o erro de uma vista mora dentro do conteúdo, com a navegação de pé.

Conferido clicando as sete abas em sequência a partir do link quebrado: todas
carregam, a barra continua com sete botões, e a URL se corrige sozinha na
chegada. E com `?uf=ZZ`, um 404 de verdade, a mensagem aparece na seção e o
resto do site continua clicável.
## 2026-08-30 — a aba de vereador comeca pela capital, e a gaveta desce

**A capital nao estava no dado.** Enquanto a aba servia uma cidade por UF, "a
capital" era a unica entrada e nao precisava de marca. Com a cobertura
municipal, as 246 cidades de Goias entram todas pelo mesmo caminho
(`cidades/{cod}.json`) e a entrada que vinha de `vereador.json` deixou de
existir para essa UF. O padrao caiu no ultimo recurso da cadeia — a primeira
cidade em ordem alfabetica — e a aba abria em **Abadia de Goias**.

Nao era erro de logica: era informacao que faltava. Nada no `cidades.json`
dizia qual das 246 e' a capital. Agora diz, com um `cap: true` pareado por nome
normalizado contra o `vereador.json`, que e' o arquivo da capital. E o `22_`
avisa em voz alta se a capital nao casar com nenhuma cidade — sem isso, a aba
voltaria a abrir no alfabeto e ninguem notaria.

**E um defeito que o mesmo caminho escondia:** trocar de ESTADO nao limpava a
cidade. Dava para estar em Sao Paulo com Itumbiara aberta, porque a resolucao
procura por `cid` antes de procurar por UF. Agora `trocarUF` limpa `cid`.

**Entrar na aba tambem limpa.** Reabrir a ultima cidade escolhida soa
prestativo e nao e': a capital e' o unico ponto de partida que existe em toda
UF, e voltar a aba num municipio qualquer do interior deixa o leitor sem
referencia. Quem limpa e' o CLIQUE — um link com `cid` continua abrindo a
cidade do link, que e' o que faz o endereco valer a pena compartilhar.

**A gaveta desceu para depois das abas.** "Qual sua cidade?" ocupava o lugar de
"Qual seu estado?", acima da barra. Mas o estado governa a tela inteira e a
cidade governa uma aba so': controle que vale para tudo vem antes da barra,
controle de uma secao vem depois dela, encostado no que ele muda. Acima, lia-se
como se valesse para Presidente e Estadual tambem.
## 2026-08-30 — as zonas dentro da cidade, e a medicao que eu tinha feito errada

O usuario mandou um infografico do TRE/GO com as 9 zonas de Goiania desenhadas
como manchas contiguas e limpas, e pediu o mesmo para as outras cidades.

**Eu tinha dito que isso nao dava.** A frase foi: "elas nao sao bairros: se
interpenetram no mapa — em Goiania, 19 dos 36 pares de zonas tem areas
sobrepostas". A evidencia era **sobreposicao de caixas delimitadoras**, e caixa
nao prova interpenetracao nenhuma: duas regioes compactas e vizinhas tem caixas
cruzadas quase sempre, porque a caixa de uma regiao em L cobre area que nao e'
dela. Quando a minha medicao contradiz um mapa oficial, a medicao esta' errada.

**A medida certa e' de vizinhanca**, e diz o contrario:

| cidade | locais | zonas | vizinho mais proximo na mesma zona | bairros de uma zona so |
|---|---|---|---|---|
| Goiania | 349 | 9 | **91,7%** | **176/176** |
| Anapolis | 118 | 3 | 92,4% | 74/77 |
| Aparecida de Goiania | 106 | 3 | 92,5% | 81/82 |
| Rio Verde | 70 | 2 | 87,1% | 41/46 |

Em Goiania **100% dos bairros estao inteiramente numa zona so'** — exatamente o
que o infografico do TRE afirma ao listar bairros por zona.

**Como foi desenhado, sem scipy e sem shapely.** A celula de Voronoi sai por
recorte sucessivo de meio-plano (Sutherland-Hodgman) a partir da caixa da
cidade. As arestas internas entre celulas da MESMA zona somem, e o que resta e'
a divisa. Detalhe que decidiu funcionar: o teste do recorte guarda `>= 0`, entao
vertice sobre a mediatriz permanece — com  as duas celulas vizinhas
produziriam arestas ligeiramente diferentes e a dissolucao deixaria fresta.

**O recorte pelo contorno do municipio nao e' feito em Python.** As celulas saem
retangulares na borda e quem as apara e' o `clipPath` do SVG, com o contorno
que o `55_` ja' publicou. Recortar poligono nao-convexo em Python exigiria
biblioteca; o navegador faz de graca e sem erro.

Custo: 2,4 segundos e 114 KB para as quatro cidades. Goiania gastou **3 cores**
para 9 zonas — prova adicional de compacidade, porque zona compacta tem poucas
vizinhas.

**E o mapa diz o que ele e'.** A fronteira e' derivada por urna mais proxima, nao
e' o limite do TRE: coincide no miolo e diverge junto da divisa, onde o oficial
segue rua e bairro. A nota na tela diz isso, e o percentual de vizinhanca e'
**calculado no navegador a partir do dado**, nao escrito a mao — numero fixo no
texto viraria mentira na cidade seguinte.

Os pontos continuam por cima, como o usuario pediu: zonas e secoes no mesmo mapa.
