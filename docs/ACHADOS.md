# Padrões no voto para deputado estadual em Goiás, 1998–2022

Todos os números abaixo saem de `scripts/07_achados.py`, que roda sobre as tabelas
de `data/processed/`. Rodar o script de novo é a forma de conferir cada afirmação —
nada aqui foi escrito de memória. O dump bruto fica em `docs/_achados_raw.txt`.

Universo: 7 pleitos gerais (1998–2022) e 246 municípios, mais 7 pleitos municipais
(2000–2024) em Goiânia. Deputado estadual: 4.128 candidaturas e 19,3
milhões de votos nominais — é o cargo das seções 1 a 9. Deputado federal e Senado entram
nas seções 10 a 12, com pipeline idêntico. Salvo indicação, as medidas se referem aos 41 eleitos
de cada pleito e são **medianas**, não médias — a distribuição é assimétrica e a média
é puxada pelos casos extremos.

---

## 1. A dispersão de 24 anos foi revertida em 2022 — mas não por quem se imagina

Três medidas independentes descrevem a mesma curva entre os eleitos:

| Pleito | Municípios efetivos | Maior município | Domínio médio | Contiguidade | Municípios com voto |
|---|---|---|---|---|---|
| 1998 | 3,08 | 55,7% | 22,1% | 69,5% | 163 |
| 2002 | 3,15 | 54,9% | 13,1% | 70,1% | 166 |
| 2006 | 4,18 | 47,5% | 11,7% | 60,5% | 169 |
| 2010 | 4,34 | 42,9% | 9,3% | 59,9% | 195 |
| 2014 | 6,25 | 37,8% | 11,5% | 55,1% | 196 |
| 2018 | 5,28 | 40,0% | 10,6% | 54,2% | 203 |
| **2022** | **4,75** | **42,4%** | **13,5%** | **59,0%** | **213** |

"Municípios efetivos" é 1/HHI: equivale a dizer em quantos municípios *iguais* o
deputado teria de concentrar todos os seus votos para produzir a mesma concentração
observada. De 1998 a 2014 esse número dobrou; desde então recuou.

**A inferência importante é que isso não significa que os deputados fazem votos de
outro jeito.** Entre *todos* os candidatos com 5 mil votos ou mais — 116 em 1998,
151 em 2022 — a concentração é notavelmente estável na série inteira:

| Pleito | 1998 | 2002 | 2006 | 2010 | 2014 | 2018 | 2022 |
|---|---|---|---|---|---|---|---|
| Municípios efetivos (mediana) | 2,68 | 2,80 | 2,69 | 2,96 | 2,72 | 3,21 | 3,12 |
| Maior município | 59,2% | 57,2% | 58,6% | 55,3% | 59,5% | 53,6% | 54,8% |

Ou seja: **a tecnologia eleitoral não mudou — mudou quem passa pelo corte.** O
movimento observado entre os eleitos é efeito de composição. Nos anos de dispersão,
o corte deixou passar mais candidatos de perfil disperso; em 2022, menos.

Note ainda a divergência entre duas colunas da primeira tabela: os eleitos de 2022
recebem votos em **mais** municípios do que nunca (213 dos 246) e ao mesmo tempo
**dependem mais** de poucos deles. Presença ampla e dependência concentrada não são
opostos — a presença capilar é fina, e o voto que decide continua vindo do reduto.

## 2. Um quarto tipo de deputado surgiu, e é recente

Cruzando concentração (municípios efetivos ≤ 10) com domínio (fatia média ≥ 10%),
cada eleito cai numa de quatro células:

| Pleito | Concentrado-Dominante | Concentrado-Compartilhado | Disperso-Dominante | Disperso-Difuso |
|---|---|---|---|---|
| 1998 | 53,7% | 39,0% | 7,3% | **0,0%** |
| 2006 | 48,8% | 34,1% | 14,6% | 2,4% |
| 2014 | 41,5% | 34,1% | 19,5% | 4,9% |
| 2018 | 31,7% | 43,9% | 19,5% | 4,9% |
| 2022 | 43,9% | 29,3% | 14,6% | **12,2%** |

O *Disperso-Difuso* — votos espalhados por muitos municípios sem dominar nenhum,
o deputado sem território — **não existia em 1998 nem em 2002**. Apareceu em 2006 e
chegou a 5 dos 41 eleitos em 2022. É a única célula que cresce de forma consistente
e é o indício mais direto de uma via de eleição que não passa por base municipal.

## 3. A janela de captura municipal — o padrão mais robusto da série

Fatia mediana do maior candidato no total de votos nominais do município, por porte:

| Pleito | até 2 mil | 2–5 mil | 5–10 mil | 10–15 mil | **15–25 mil** | **25–50 mil** | mais de 50 mil |
|---|---|---|---|---|---|---|---|
| 1998 | 38,9 | 33,0 | 41,2 | 47,4 | **52,5** | 35,4 | 23,9 |
| 2002 | 32,0 | 28,2 | 28,1 | 37,4 | **38,8** | 35,3 | 16,4 |
| 2006 | 34,0 | 27,2 | 22,4 | 34,6 | **42,4** | 36,0 | 14,9 |
| 2010 | 27,9 | 26,4 | 24,7 | 29,8 | **37,6** | 37,5 | 15,4 |
| 2014 | 30,5 | 27,7 | 22,3 | 28,0 | **34,5** | 34,1 | 12,5 |
| 2018 | 28,7 | 25,5 | 19,0 | 24,6 | **30,8** | 27,1 | 20,5 |
| 2022 | 35,8 | 26,9 | 19,8 | 21,7 | **41,7** | 35,6 | 21,9 |

**Nas sete eleições, sem exceção, a captura tem um pico na faixa de 15 a 50 mil votos
nominais e o seu mínimo nas cidades grandes.** A correlação linear entre log do porte
e captura é praticamente nula (r entre −0,12 e +0,05), o que faria qualquer regressão
concluir que "tamanho não explica nada" — e esconderia por completo a curva acima.

A leitura: existe um tamanho ótimo de captura. Municípios pequenos demais não sustentam
um candidato próprio e acabam repartidos entre os candidatos dos vizinhos. Municípios
de 15 a 50 mil votos são grandes o bastante para sustentar um quadro nativo — um
ex-prefeito, um vereador com máquina — e pequenos o bastante para que um só o domine.
Acima disso, nenhuma candidatura individual dá conta do território.

Casos de 2022 na faixa de pico: Santo Antônio do Descoberto entregou **75,1%** de todos
os seus votos nominais a um único candidato; Itapuranga 69,4%; Santa Helena de Goiás
66,0%; Jaraguá 61,9%. Nos quatro, 272 a 292 candidatos receberam ao menos um voto — a
concentração não vem de falta de opção.

## 4. Goiânia é o exato oposto de um reduto

| Pleito | Votos nominais | % do estado | Candidatos efetivos | Maior candidato |
|---|---|---|---|---|
| 1998 | 397.324 | 22,7% | 72,2 | 3,46% |
| 2010 | 624.584 | 22,3% | 76,0 | 3,74% |
| 2022 | 674.670 | 21,1% | 95,3 | 3,12% |

O peso de Goiânia no estado é estável há 24 anos, entre 21% e 24%. Mas o número
efetivo de candidatos na capital **subiu para 95,3 em 2022**, o máximo da série, e o
maior candidato individual fica com 3,12%, o mínimo. Um quinto dos votos do estado está
num lugar que ninguém controla.

Isso explica por que a capital não produz deputados: ela é o **complemento** de uma
candidatura, não a sua base. Dos dez mais votados de 2022, seis têm Goiânia como
município de maior votação — e nenhum deles tira de lá mais de 25% do próprio total.

## 5. Dois modelos opostos de vitória coexistem no topo

Os dois maiores votos de 2022:

| | Votos | Municípios com voto | Municípios efetivos | Maior município | Domínio médio | Reduto |
|---|---|---|---|---|---|---|
| Bruno Peixoto (União) | 73.692 | 240 | **23,78** | 17,9% | 14,6% | Goiânia |
| Lucas do Vale (MDB) | 55.747 | 188 | **2,27** | **66,1%** | 29,0% | Rio Verde |

Bruno Peixoto é dez vezes mais disperso que Lucas do Vale e fez 32% mais votos. Não há
um caminho único: a maior votação do estado e a segunda maior foram construídas por
estratégias territorialmente opostas. Qualquer leitura que trate "deputado estadual"
como um tipo homogêneo perde exatamente isso.

## 6. 2022 foi o ano de maior canibalização intrapartidária da série

Semelhança de cosseno média entre os mapas municipais de candidatos do mesmo partido
(0 = territórios disjuntos, 1 = disputam exatamente o mesmo espaço), mediana entre
partidos com 3 ou mais candidatos:

| Pleito | 1998 | 2002 | 2006 | 2010 | 2014 | 2018 | 2022 |
|---|---|---|---|---|---|---|---|
| Semelhança | 0,197 | 0,195 | 0,217 | 0,216 | 0,186 | 0,229 | **0,319** |

O salto de 2022 é de 39% sobre 2018 e rompe uma faixa que se manteve estreita por
vinte anos. É o efeito esperado do fim das coligações proporcionais (proibidas a
partir de 2020): sem coligar, cada partido precisa preencher a nominata sozinho, e
passa a lançar candidatos sobre territórios que antes cabiam a um aliado.

O custo disso aparece na comparação entre os partidos de 2022:

| Partido | Candidatos | Eleitos | Votos | Puxador | Semelhança |
|---|---|---|---|---|---|
| MDB | 32 | **6** | 429.320 | **13,0%** | **0,117** |
| União Brasil | 32 | **6** | 401.624 | 18,4% | 0,367 |
| PRTB | 42 | 4 | 279.188 | 11,7% | 0,164 |
| PL | 36 | 3 | 215.252 | 17,5% | 0,435 |
| PT | 32 | 3 | 203.325 | 22,3% | 0,352 |
| Republicanos | 39 | **2** | 148.016 | 21,3% | **0,610** |
| Patriota | 40 | 2 | 128.834 | 23,9% | 0,228 |

O MDB elegeu 6 com a **menor** semelhança interna e o **menor** peso de puxador da
tabela: uma nominata territorialmente complementar, em que os candidatos não disputam
entre si. O Republicanos, com 39 candidatos e semelhança 0,610 — todos brigando pelo
mesmo espaço —, converteu 148 mil votos em 2 cadeiras. Com quase o mesmo número de
candidatos, o MDB converteu 429 mil em 6.

**Montar nominata é um problema de cobertura territorial, não de volume de candidatos.**

## 7. As federações de 2022 quase não pesaram em Goiás

Apenas 102 dos 737 candidatos (13,8%) concorreram em federação, e elas produziram
5 dos 41 eleitos:

| Federação | Candidatos | Eleitos | Votos |
|---|---|---|---|
| PT / PCdoB / PV | 41 | 3 | 217.039 |
| PSDB / Cidadania | 37 | 2 | 122.219 |
| PSOL / Rede | 24 | 0 | **6.039** |

A federação PSOL/Rede somou 6.039 votos no estado inteiro — menos do que qualquer
um dos 41 eleitos obteve sozinho, e cerca de 8% do que fez o primeiro colocado. O
instrumento criado para dar sobrevida a partidos pequenos não teve efeito mensurável
em Goiás.

## 8. As bases são quase imóveis, e a renovação caiu

Semelhança entre o mapa de votos de um mesmo candidato em pleitos consecutivos, mediana:

| Pleito | 2002 | 2006 | 2010 | 2014 | 2018 | 2022 |
|---|---|---|---|---|---|---|
| Todos os reincidentes | 0,980 | 0,987 | 0,986 | 0,990 | 0,982 | 0,982 |
| Somente eleitos | 0,970 | 0,985 | 0,980 | 0,980 | 0,970 | **0,964** |
| Variação mediana de votos | +2,7% | +6,9% | −7,7% | −10,9% | −8,6% | **−13,0%** |

Semelhança acima de 0,96 significa que a geografia da votação de um candidato
praticamente não se move entre eleições — o mapa de 2018 prevê o de 2022. Bases
eleitorais em Goiás são ativos herdados, não conquistados a cada pleito.

Ao mesmo tempo, a proporção de eleitos que já haviam concorrido antes subiu de forma
contínua: 48,8% (2002), 58,5% (2014), 65,9% (2018), **70,7% (2022)** — o máximo da
série. E os reincidentes de 2022 perderam 13% dos votos na mediana, a maior queda
registrada. Mais candidatos disputando o mesmo bolo faz cada um encolher, sem que isso
abra espaço para gente nova.

## 9. O rival de verdade é o vizinho de bloco — mas cada vez menos

Para cada deputado, mediu-se a **pressão** que cada outro candidato exerce sobre ele:
quanto do voto do deputado está em municípios onde o rival também é forte, ponderado
pela força do rival ali. Não é simétrica — um gigante pressiona um pequeno muito mais
do que o contrário. Cada rival foi então classificado como **aliado** (mesma faixa
ideológica ou vizinha) ou **adversário** (duas faixas ou mais de distância).

O resultado bruto é sedutor e quase todo falso: em 2022, o rival nº 1 é um aliado
ideológico para 31 dos 41 eleitos. Parece revelar que a disputa é intrabloco. Não é —
ou não só. Como a maioria das candidaturas de Goiás se concentra do centro à direita,
"aliado" sairia como rival nº 1 por puro acaso na maior parte dos casos:

| Pleito | Esperado por acaso | Observado | Excesso |
|---|---|---|---|
| 1998 | 81,3% | 85,4% | +4,1 pp |
| 2002 | 73,5% | 78,0% | +4,5 pp |
| 2006 | 78,3% | 85,4% | +7,1 pp |
| 2010 | 69,3% | 78,0% | +8,7 pp |
| 2014 | 67,6% | 85,4% | +17,8 pp |
| 2018 | 61,4% | 58,5% | **−2,9 pp** |
| 2022 | 66,8% | 75,6% | +8,8 pp |

O efeito real é o excesso, não o total: entre +4 e +9 pontos na maior parte da série. E
em 2018 ele **desaparece e inverte**.

O teste limpo é o pareado, que elimina a composição por completo: para o **mesmo**
deputado, o principal rival aliado pressiona mais que o principal adversário?

| Pleito | 1998 | 2002 | 2006 | 2010 | 2014 | 2018 | 2022 |
|---|---|---|---|---|---|---|---|
| Diferença mediana | +2,90 pp | +2,55 pp | +2,62 pp | +1,08 pp | +1,66 pp | **+0,45 pp** | +0,89 pp |
| Deputados em que o aliado pressiona mais | 35/41 | 32/41 | 35/41 | 32/41 | 35/41 | **24/41** | 31/41 |

Aí está o achado, e ele é sobre movimento, não sobre nível: **a proximidade ideológica
previa rivalidade territorial e essa ligação vem se dissolvendo.** Em 1998 o aliado
pressionava mais em 35 dos 41 casos, com folga de quase 3 pontos; em 2018 caiu para
24 de 41 e 0,45 ponto — praticamente cara ou coroa. Território e ideologia estão se
desacoplando: onde um candidato disputa voto já não diz de que lado do espectro ele está.

Os pares mais tensos de 2022 mostram como isso se materializa:

| Deputado | Rival | Relação | Pressão | Municípios disputados |
|---|---|---|---|---|
| Dr. José Machado (PSDB) | Renato de Castro (União) | adversário | 26,6% | Goianésia, Barro Alto, Vila Propício |
| Gugu Nader (Agir) | Álvaro Guimarães (União) | aliado | 21,1% | Itumbiara, Cachoeira Dourada, Bom Jesus |
| Gustavo Sebba (PSDB) | Jamil Calife (PP) | aliado | 18,6% | Catalão, Campo Alegre de Goiás, Ipameri |
| Rosângela Rezende (Agir) | Isaac Mendonça (Avante) | aliado | 18,2% | Mineiros, Portelândia, Santa Rita do Araguaia |

O par mais tenso do estado é ideologicamente cruzado — PSDB contra União Brasil, com
afinidade territorial de 0,975, praticamente o mesmo mapa. Já Gugu Nader e Álvaro
Guimarães, do mesmo campo, brigam por Itumbiara com afinidade 0,896.

**Ressalva que não é detalhe.** A separação entre aliado e adversário não sai do dado
eleitoral: vem de uma classificação em cinco faixas gravada em
`data/overrides/partidos_espectro.csv`. É juízo externo e discutível — trocar o arquivo
troca a leitura. Siglas mudam de posição ao longo de 24 anos, e legendas de coalizão
como o MDB têm coesão interna baixa demais para caber num ponto só do espectro. O teste
pareado é o resultado mais robusto justamente porque compara o mesmo deputado consigo,
sob a mesma classificação.

## 10. Há uma escada de territorialidade, e ela vai de cima a baixo da cédula

Municípios efetivos — em quantas cidades equivalentes a votação se concentra. Quanto
menor, mais o voto depende de poucos lugares:

| Pleito | Estadual | Federal | Senado | Governador | Presidente |
|---|---|---|---|---|---|
| 1998 | 3,1 | 12,3 | 17,3 | 11,3 | — |
| 2006 | 4,2 | 16,6 | 15,9 | 15,5 | 15,3 |
| 2014 | 6,3 | 18,0 | 14,9 | 27,6 | 15,2 |
| 2022 | **4,8** | 10,1 | 12,1 | **21,9** | 14,5 |

**Quanto mais alto o cargo, mais uniforme o voto pelo estado.** O deputado estadual é o
extremo territorial — 4,8 municípios efetivos em 2022, de 246 — e o governador o extremo
oposto, com 21,9. Entre eles, federal e Senado. Não é diferença de grau: são lógicas
distintas rodando na mesma urna, no mesmo dia. O eleitor que escolhe governador decide
por razões estaduais; o que escolhe deputado estadual decide por razões de município.

Nos cargos majoritários a medida usa **o mais votado em Goiás**, não o vencedor da
eleição — para presidente os dois raramente coincidem, e é a geografia goiana que
interessa aqui.

## 10b. Estadual, federal e Senado na comparação direta

Municípios efetivos dos eleitos, mediana por pleito — em quantas cidades equivalentes a
votação se concentra:

| Pleito | Estadual | Federal | Senado |
|---|---|---|---|
| 1998 | 3,1 | 12,3 | 17,3 |
| 2006 | 4,2 | 16,6 | 15,9 |
| 2014 | 6,3 | 18,0 | 14,9 |
| 2018 | 5,3 | 11,2 | 11,2 |
| 2022 | 4,8 | 10,1 | 12,1 |

O deputado estadual disputa um território **três a quatro vezes menor** que o federal.
A fatia do maior município confirma: 42,4% no estadual contra 24,0% no federal e 26,1%
no Senado, em 2022. Não é diferença de grau — são lógicas distintas rodando na mesma
urna, no mesmo dia.

O movimento recente é de convergência: federal e Senado, que estavam em 18,0 e 14,9 em
2014, caíram para 10,1 e 12,1 em 2022. As duas disputas de escala estadual ficaram mais
territorializadas ao mesmo tempo em que o estadual se reconcentrava (seção 1).

## 11. Só os partidos ideológicos têm máquina territorial

Para cada partido e ano, a correlação — sobre os 246 municípios — entre a fatia que ele
tem no deputado estadual e a fatia que tem no federal. Perto de 1, o partido ocupa a
mesma geografia nos dois cargos; perto de 0, as duas disputas correm soltas.

**A mediana entre partidos nunca passou de 0,21 em 24 anos** (0,13 em 1998; 0,15 em
2022). O padrão dominante em Goiás é a legenda que não coordena nada territorialmente.

Mas a média esconde uma separação nítida. Em 2022:

| Partido | Correlação |
|---|---|
| PT | **0,617** |
| PDT | 0,415 |
| PL | 0,377 |
| Podemos | 0,147 |
| MDB | 0,139 |
| PP | 0,036 |
| União Brasil | 0,036 |
| Patriota | 0,035 |

De um lado, partidos de identidade programática — PT, PDT — com geografia coerente entre
os cargos. Do outro, as maiores bancadas do estado, União Brasil e PP, com correlação
praticamente **nula**: seus candidatos a estadual e a federal ocupam territórios que não
têm relação um com o outro. São empreendedores territoriais independentes que dividem
uma legenda, não uma máquina partidária.

E o PT vem subindo de forma contínua: 0,28 (1998), 0,41 (2006), 0,43 (2014), 0,47 (2018),
0,62 (2022). É o único partido que constrói território de forma articulada, e cada vez
mais.

## 12. Sobre "dobradinhas": o que o dado mostra e o que ele não mostra

Para cada deputado estadual, o federal cujo mapa municipal mais se parece com o dele. As
afinidades chegam a **0,9999** — praticamente o mesmo mapa. Em 2022: Gleimo Martins (PMN)
e Leandro Ribeiro (PP) em Anápolis; Anderson Teodoro (Avante) e Giva Felipe
(Solidariedade) em Águas Lindas; Gugu Nader (Agir) e Liliane Costa (PRTB) em Itumbiara.

**Isso não prova campanha casada, e é importante dizer por quê.** Dois candidatos
concentrados na mesma cidade têm mapas quase idênticos por construção geométrica, sem
combinação nenhuma. O cosseno entre dois candidatos quaisquer já é 0,12 na mediana, mas
entre dois candidatos da mesma cidade tende a 1 automaticamente. A tabela mostra
coincidência territorial; a intenção por trás dela o dado eleitoral não revela.

O número que **é** informativo é outro: entre esses pares mais parecidos, a fatia que
divide a mesma legenda caiu de **21,3% (1998) para 7,7% (2022)**. Ou seja: quem divide
território cada vez menos divide partido. Combinado com a seção 11 — as grandes legendas
sem coerência territorial — o quadro é de um sistema em que a coordenação local, quando
existe, se organiza fora da estrutura partidária.

## 13. Câmara de Goiânia: a cadeira mais cara da série é a de agora

Outro ciclo eleitoral (2000 a 2024) e outra geografia — Goiânia é um município só, e a
única desagregação territorial que o arquivo do TSE oferece dentro da cidade é a zona
eleitoral: 10 até 2016, 9 a partir de 2020.

| Pleito | Cadeiras | Nominais | Quociente | Último eleito | Candidatos | Reeleitos |
|---|---|---|---|---|---|---|
| 2000 | 33 | 485.688 | 14.718 | 1.899 | 537 | — |
| 2008 | 35 | 566.516 | 16.186 | 2.698 | 531 | 68,6% |
| 2012 | 35 | 587.421 | 16.784 | 2.714 | 661 | 77,1% |
| 2016 | 35 | 628.716 | 17.963 | 2.429 | 681 | 68,6% |
| 2020 | 35 | **473.742** | 13.536 | **1.799** | **873** | 65,7% |
| 2024 | **37** | 658.381 | 17.794 | **3.607** | 653 | 67,6% |

**2020 é o ponto fora da curva em todas as colunas**: o maior número de candidaturas da
série (873) disputando o menor volume de votos nominais (473.742), com o corte de entrada
mais barato (1.799). Foi a eleição da pandemia — mais gente concorrendo por um bolo
menor.

**2024 inverteu tudo**: o último eleito precisou de 3.607 votos, o dobro de 2020 e o
maior valor da série, mesmo com duas cadeiras a mais na Câmara. Entrar na Câmara de
Goiânia nunca custou tanto.

A reeleição é alta e estável desde 2008: entre 66% e 77% dos eleitos já haviam concorrido
antes.

## 14. Jorge Kajuru, 2016: um puxador que vale por quatro cadeiras

Em 2016 o mais votado da cidade fez **37.796 votos** — quatro vezes o segundo colocado e
**6,01% de todos os votos nominais de Goiânia**. Nenhum outro pleito da série tem nada
parecido: o teto dos demais anos fica entre 8,5 mil e 15,7 mil.

O efeito sistêmico é o que interessa. O partido dele somou 65.749 votos e elegeu 4 — e
Kajuru sozinho respondeu por **57,5%** desse total. Três vereadores entraram na Câmara
carregados por um nome. É o mecanismo do quociente partidário em estado puro, e a série
municipal de Goiânia oferece o exemplo mais limpo que encontrei em todo o projeto.

Vale notar o contraste territorial: Kajuru teve voto nas 10 zonas, com apenas 20,4% na
maior delas — voto de cidade inteira, não de bairro. No mesmo pleito, Vinícius Cirqueira
(PROS) se elegeu com 63,3% dos votos numa zona só. Os dois extremos convivendo na mesma
Câmara.

## 15. Deputado estadual: a cadeira ficou mais cara, mas o corte de entrada não acompanhou

| Pleito | Nominais no estado | Quociente | Último eleito | Último ÷ quociente | Candidatos por cadeira |
|---|---|---|---|---|---|
| 1998 | 1.752.391 | 42.741 | 8.426 | 19,7% | 9,4 |
| 2006 | 2.545.561 | 62.087 | 11.544 | 18,6% | 11,5 |
| 2010 | 2.795.388 | 68.180 | 14.427 | 21,2% | 13,1 |
| 2014 | 2.877.038 | 70.172 | **8.607** | **12,3%** | 17,5 |
| 2018 | 2.861.366 | 69.789 | 11.616 | 16,6% | **19,4** |
| 2022 | 3.205.075 | 78.173 | **17.484** | **22,4%** | 18,0 |

O quociente eleitoral subiu 83% em 24 anos. O último eleito de 2022 precisou de 17.484
votos — mais que o dobro de 1998 e o maior valor da série, tanto em números absolutos
quanto em proporção do quociente.

2014 é o contraste instrutivo: com o quociente já alto, o último eleito entrou com
8.607 votos, 12,3% do quociente. Naquele ano as coligações proporcionais ainda
existiam e podiam carregar um candidato de votação modesta na esteira de um puxador
de outro partido. Em 2022, sem coligação, o corte de entrada praticamente dobrou.
**O fim das coligações encareceu a cadeira marginal muito mais do que encareceu a
média.**

---

## 16. O custo do Legislativo quase não é o parlamentar

Fonte: `44_cldf_administrativo.py`, folha nominal da CLDF de 07/2026. A Câmara
Legislativa do DF é a única das três casas levantadas que publica a folha **nome
a nome**, com cargo, lotação e remuneração — 107 arquivos mensais, de setembro
de 2017 a julho de 2026.

Em 07/2026, **2.623 pessoas** custaram R$ 59,85 mi de folha bruta. Os
**24 deputados distritais são 1,4%** desse total. O que
custa não é o mandato: é a estrutura em volta dele — 882 pessoas
lotadas em gabinete respondem por 16,2% da folha.

E são 5.052 **linhas de pagamento** para 2.623 pessoas: uma pessoa
aparece em várias folhas no mesmo mês. Contar linhas conta pagamento, não gente
— foi assim que a primeira versão deste levantamento relatou 48 deputados
distritais num Distrito Federal que tem 24.

### 16a. Livre nomeação é maioria por cabeça, minoria por dinheiro

Há **993 comissionados para 871 concursados** — o cargo de livre
nomeação é a maior categoria da Casa em número de pessoas. Em dinheiro a ordem
se inverte: os concursados custam R$ 31,00 mi contra R$ 10,79 mi, porque o
concursado individual custa **3,3×** o comissionado individual
(R$ 35.594 contra R$ 10.866 por mês).

Um total agregado de "despesa de pessoal" não deixaria ver nem uma coisa nem a
outra.

### 16b. Quem já saiu pesa mais que todo o quadro de livre nomeação

**448 inativos custam R$ 15,28 mi; 993 comissionados em atividade custam
R$ 10,79 mi.** O inativo médio custa R$ 34.104 por mês, praticamente o
mesmo que o concursado da ativa — são carreiras no topo, aposentadas com
proventos integrais.

### 16c. A folha cresce mais rápido que o quadro, e só um dos dois números é sólido

Comparando julho com julho, de 2018 a 2026: o quadro foi de
1.919 para 2.623 pessoas (**+37%**) e a folha
de R$ 30,11 mi para R$ 59,85 mi (**+99%**).

**Os dois números não têm o mesmo peso probatório.** O crescimento do quadro é
contagem e não depende de inflação. O da folha está em reais correntes, sem
deflacionar — boa parte dele é a moeda valendo menos. Não deflacionamos porque
escolher um índice exigiria justificar a escolha, e o que interessa aqui — o
descolamento entre as duas curvas — não vem da inflação, que atinge as duas.

Julho é escolhido de propósito: dezembro carrega décimo terceiro.

### 16d. Duas fontes independentes que poderiam divergir e não divergem

A folha bruta de 07/2026 dá R$ 59,85 mi. A despesa total paga pela Casa naquele
mês, publicada por caminho separado, dá R$ 77,82 mi. A folha é **77%** do que a
CLDF pagou no mês, e o resto cabe em custeio, terceirizado e investimento. É a
checagem de consistência que o levantamento do DF permite e o de Goiás não.

### 16e. Uma ressalva que sobrevive: o bruto é piso

Só a folha principal detalha os créditos. As secundárias trazem as colunas de
crédito zeradas e apenas o líquido — **R$ 4,98 mi pagos em 07/2026 cujo valor
bruto o arquivo não informa**. Somar as colunas de crédito não duplica (as
secundárias somam zero), mas também não alcança tudo. Todo número de folha aqui
é mínimo, não total.

## Seis ressalvas de método

**O denominador do mapa de Influência.** O painel original informa, para cada município,
um total de votos nominais que não é reproduzível a partir da base atual do TSE. Dos 20
municípios que ele lista para Álvaro Guimarães em 2018, 7 batem exatamente com a nossa
apuração e os demais divergem em até 0,5%, para cima em uns e para baixo em outros
(Aporé diverge no sentido oposto ao de Itumbiara) — o que descarta a hipótese de uma
categoria de voto faltando e aponta para um extrato anterior a revisões de totalização.
Os números daqui têm confirmação independente: a soma dos candidatos em
`votacao_candidato_munzona` e a coluna `QT_VOTOS_NOMINAIS_VALIDOS` de
`detalhe_votacao_munzona` coincidem exatamente entre si. A **votação de cada deputado
por município**, que é o numerador de tudo, bate exatamente com o painel original.

**Presidente é cargo nacional, e Goiás vota contra a maré com frequência.** Em 2022 o
mais votado no estado foi Jair Bolsonaro; quem se elegeu foi Lula. Em 2006, Alckmin
liderou em Goiás e Lula venceu. Por isso a aba de presidente marca "venceu em Goiás" em
vez de fingir que o vencedor nacional é o retrato local. Some-se a isso que em **2006 e
2010 o TSE deixou o campo de resultado em branco** neste arquivo, e que **1998 não tem
membro nacional no zip** — presidente cobre 2002 a 2022, seis pleitos, não sete.

**Semelhança não se compara entre escalas.** A canibalização intrapartidária é medida
por cosseno sobre o vetor territorial. No estadual esse vetor tem 246 posições; na Câmara
de Goiânia tem 9. Com menos dimensões, dois candidatos quaisquer parecem mais próximos
por construção — o 0,685 do MDB em 2024 na cidade **não** é comparável ao 0,319 estadual.
Dentro de cada escala a medida ordena bem; entre escalas, não significa nada.

**O Senado não é comparável de forma ingênua.** Nos anos de duas vagas — 2002, 2010 e
2018 — cada eleitor vota duas vezes, e o total do cargo chega a quase o dobro dos demais:
4,9 milhões em 2010 contra 2,8 milhões do estadual. Comparar "fatia do estado" entre
cargos sem levar isso em conta superestima o Senado pela metade. As medidas usadas nas
seções 10 a 12 são todas internas ao cargo — concentração, correlação —, que não sofrem
com isso. E o Senado é majoritário: não tem quociente eleitoral, e o painel suprime essa
coluna ali em vez de exibir um número sem significado legal.

**A posição ideológica dos partidos é camada externa.** A seção 9 depende de
`data/overrides/partidos_espectro.csv`, uma classificação em cinco faixas que não deriva
de nenhum dado do TSE. É contestável por construção: partidos migram de posição ao longo
de 24 anos e legendas de coalizão têm coesão baixa demais para um ponto único. Trocar o
arquivo troca a leitura — por isso o teste pareado, que compara cada deputado consigo
mesmo sob a mesma classificação, é o resultado a levar a sério.

**Identidade de pessoas ao longo da série.** Candidatos são pareados entre pleitos pelo
nome completo sem acento, porque o TSE grava o mesmo nome ora com acento ora sem, e o
`SQ_CANDIDATO` muda a cada eleição. Isso funde eventuais homônimos — um risco pequeno
num universo de 4.128 candidaturas, mas real. Os números de reincidência e de
semelhança entre pleitos carregam essa margem.

## Território e ideologia são pouco acoplados

*Reproduz por `scripts/23_rivais.py`, que imprime a tabela abaixo ao final.*

Calculado o rival territorial mais pressionante de cada eleito em todas as
unidades, no estadual e no federal, 1998–2022, a leitura tentadora é: **o rival
nº 1 costuma ser um aliado ideológico**. Em Goiás 2022 ele é aliado para 69,8%
dos eleitos; em Minas 1998, para 81,1%.

O número não sobrevive sozinho. Se a maior parte das candidaturas já está na
mesma faixa ideológica do eleito, "aliado" vence por acaso — e é o que acontece:

| UF | ano | acaso | observado | pareado |
|---|---|---|---|---|
| GO | 2022 | 71,0% | 69,8% | +1,21 pp |
| SP | 2010 | 54,4% | 48,2% | −0,11 pp |
| MG | 1998 | 74,3% | 81,1% | +2,27 pp |
| RR | 2022 | 75,0% | 51,7% | +0,25 pp |

`observado` acompanha `esperado` de perto, e às vezes fica **abaixo** dele. O
achado aparente é, em boa medida, composição do campo — não comportamento.

O que resta é o teste pareado, que compara aliado e adversário **dentro do mesmo
eleito** e por isso controla a composição por completo. Ele é positivo em quase
todos os pleitos das 27 unidades, mas pequeno: ordem de +1 a +3 pontos
percentuais de pressão a mais. A conclusão defensável é a mais fraca e a mais
interessante: **a geografia do voto proporcional é quase independente da posição
ideológica**. Quem disputa o mesmo chão disputa por estar ali, não por pensar
parecido.

Uma unidade fica de fora por construção: o Distrito Federal é um município só, e
lá o cosseno entre dois candidatos quaisquer dá exatamente 1,000. A medida não é
calculada, e a tela diz por quê em vez de mostrar um ranking de tamanho de
votação disfarçado de território.

## Câmaras municipais: a mesma cadeira custa coisas muito diferentes

*Reproduz por `scripts/25_vereador_web.py`.*

Nas 26 capitais, 2000–2024, o vereador mais votado da cidade tira múltiplos
muito diferentes do último eleito. Em São Paulo 2024, Lucas Pavanato fez 161.386
votos contra 22.306 do último a entrar — **7,2 vezes**. E a base dele não é um
reduto: 54,83 zonas efetivas de 57, Gini 0,112 entre zonas. É votação grande e
espalhada, o oposto do padrão de reduto que domina o interior nos estaduais.

São Paulo teve 979 candidatos para 55 cadeiras — 17,8 por cadeira — e 67,3% dos
eleitos já haviam concorrido antes.

A comparação entre capitais para na escala: Rio de Janeiro tem 49 zonas e São
Paulo 57, mas Macapá, Boa Vista e Vitória têm 2, e **Palmas tem 1 nos sete
pleitos**. Onde há uma zona só não existe geografia interna, e a tela diz isso em
vez de desenhar uma barra de 100% que fingiria distribuição.
