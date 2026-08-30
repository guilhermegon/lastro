# Cadê o Voto? — front end

Produto de **Lastro — Inteligência Política**.

React 19 + TypeScript + Vite. Build estático: sai um `dist/` que roda em qualquer
hospedagem de arquivo, sem servidor de aplicação.

```bash
npm install
npm run dev      # desenvolvimento, porta 5180
npm run check    # só o TypeScript, sem gerar nada
npm run build    # tsc + vite build -> dist/
npm run preview  # serve o dist/ como em produção
```

## A decisão que define a arquitetura

A versão anterior era um HTML único de 13,3 MB com todos os dados embutidos. Abria
tudo antes de mostrar qualquer coisa — inviável no celular e desconfortável no
desktop.

Aqui os dados são **fatiados por UF** e buscados sob demanda:

Os dados são fatiados **por UF e por cargo**, e o front baixa só o que a aba
aberta precisa:

| | Tamanho |
|---|---|
| App (JS + CSS) | 233 KB |
| `dados/indice.json` | 95 KB |
| **Abertura** | **328 KB** |
| `+ GO/base.json + GO/estadual.json` | 847 KB |
| `+ SP/estadual.json` (a maior) | 2,7 MB |
| `+ qualquer padroes.json` | 3 KB |

Um arquivo por UF seria pior: em São Paulo, os cinco cargos somam 7,9 MB, e
trocar de aba não deveria custar isso.

O usuário paga só pelo estado que abrir, e o cache em `lib/dados.ts` guarda a
*promessa*, não o resultado — dois pedidos simultâneos do mesmo estado viram uma
requisição só, e uma falha não fica presa no cache.

Os arquivos de `public/dados/` são **gerados**, não editados à mão:

```bash
python ../scripts/19_nacional_completo.py    # 5 cargos x 7 pleitos x 27 unidades
python ../scripts/20_adjacencia.py           # vizinhança, da malha completa
python ../scripts/21_padroes_cruzamentos.py  # padrões e cruzamentos por UF
python ../scripts/22_publicar_web.py         # publica em public/dados
```

## Estado na URL

`?uf=GO&ano=2022&v=estadual&c=0` — unidade da federação, pleito, aba e índice do candidato.

Não é preciosismo. Num produto de inteligência política a ação mais frequente é
mandar a tela para outra pessoa; com o estado na URL, copiar o endereço compartilha
exatamente o que está sendo visto, o botão voltar funciona e recarregar não perde
nada. Sai de graça, sem biblioteca de rotas.

## Estrutura

```
src/
  tipos.ts              formas do dado servido; espelham 18_dados_web.py
  lib/
    dados.ts            fetch + cache por UF
    projecao.ts         lat/long -> caminho SVG
    escalas.ts          quantis, faixas, rampa de cor
    formato.ts          pt-BR num lugar só
  componentes/          Mapa, Legenda, Cartoes, Indices, SeletorEstado, Dica,
                        Logo, Abas, Barras, Linha
  vistas/               VistaCargo, VistaPadroes, VistaCruzamentos
  estilos/tokens.css    sistema de tokens, claro e escuro
  App.tsx               composição e estado
```

## Escolhas que valem explicação

**Sem biblioteca de gráfico ou mapa.** A projeção são 40 linhas em `projecao.ts` e o
coroplético é um `<path>` por município. D3 ou Leaflet resolveriam o mesmo e
custariam centenas de KB, tempo de aprendizado e uma camada a mais entre o dado e o
pixel. Quando aparecer algo que exija projeção de verdade — zoom, tiles, rotação —
aí sim vale a biblioteca.

**Sem gerenciador de estado.** São três variáveis (UF, ano, candidato) e elas moram
na URL. Redux ou Zustand aqui seria cerimônia sem contrapartida.

**CSS portado, não reescrito.** `estilos/tokens.css` veio do painel anterior, que já
tinha sido validado em tema claro, escuro e no estado sem carimbo, incluindo os
tokens de tinta sobre cada passo da rampa. Reescrever reintroduziria bugs de
contraste que já custaram trabalho.

**`noUncheckedIndexedAccess` ligado.** Índice de array devolve `T | undefined` e o
compilador obriga a tratar. É chato e é exatamente o que se quer num código que faz
`municipios[i]` o tempo todo com índices vindos do dado.

## Toque

Os mapas informam por `mousemove` **e** `touchstart`. Em tela de toque não existe
hover: sem o segundo caminho, o mapa vira desenho mudo — dá para ver a mancha e não
dá para saber que município é. O balão aparece acima do dedo, senão a própria mão
cobre a informação.

## Publicar

`npm run build` e suba `dist/` — GitHub Pages, Netlify, Vercel, S3, servidor de
órgão. `base: "./"` no `vite.config.ts` faz os caminhos serem relativos, então
funciona em subpasta sem reconfigurar.

Não abra o `dist/index.html` com duplo clique: o navegador bloqueia `fetch` em
`file://` e os dados não carregam. Use `npm run preview` ou qualquer servidor
estático.
