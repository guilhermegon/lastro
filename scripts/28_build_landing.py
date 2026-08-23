"""Monta `dist/cade_o_voto.html`: nacional + detalhe de cada estado, num arquivo.

Por que existe, se o app React ja tem essas telas: o app serve 80 MB sob demanda
e precisa de hospedagem. Este arquivo se abre em qualquer lugar e se manda por
link.

**O que cabe, e por que.** O teto do artefato e' 16 MB. Medido:

    estadual, os 7 pleitos, 26 UFs, como o app serve   17,2 MB   nao cabe
    o mesmo, sem os blocos que so' o pipeline usa        9,9 MB
    geometria municipal das 27 unidades                  2,4 MB
    padroes + cruzamentos das 27 unidades                0,7 MB
    indice nacional                                      0,1 MB
                                                       --------
                                                        13,1 MB   cabe

Rivais territoriais (12,2 MB so' no estadual) e vereador nas capitais (4,8 MB)
NAO cabem junto - continuam so' no app.

Os blocos descartados sao `pm` (vetores por partido sobre TODOS os candidatos,
insumo do arrasto em `21_`) e `mm` (perfil por municipio, insumo da janela de
captura). Nenhum dos dois e' lido por esta tela.

Fica de fora, e e' so' no app: os outros quatro cargos, os rivais territoriais e
o vereador nas capitais.

**A marca vem de `Logo.tsx`**, extraida do proprio componente, e nao do SVG
solto em `dist/`. Motivo concreto: o SVG solto nao carrega a classe `lastro`,
entao a regra que o limita a 164px nao pega, e o `svg { width: 100% }` global
faz o logo ocupar a largura toda do cabecalho - foi o que quebrou o layout da
primeira versao desta pagina.
"""
import json
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

APP = cfg.ROOT / "app"
DADOS = APP / "public" / "dados"
SAIDA = cfg.ROOT / "dist" / "cade_o_voto.html"
TETO_MB = 16
FONTES = ("https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700"
          "&family=IBM+Plex+Mono:wght@400;500"
          "&family=IBM+Plex+Sans:wght@400;500;600&display=swap")

# o que a tela usa de cada eleito; o resto do arquivo do app fica para tras
FICHA = ["sq", "n", "completo", "p", "pn", "el", "t", "nm", "t1", "t5", "ef",
         "gi", "dom", "dom25", "contig", "r", "tipo", "mi", "mv"]


def logo_do_componente():
    """Mesmo SVG que o app usa, com o invólucro que o CSS espera."""
    tsx = (APP / "src" / "componentes" / "Logo.tsx").read_text(encoding="utf-8")
    m = re.search(r"(<svg[\s\S]*?</svg>)", tsx)
    if not m:
        raise SystemExit("não achei o <svg> em Logo.tsx")
    svg = m.group(1).replace("className=", "class=")
    return ('<span class="lastro" role="img" '
            'aria-label="Lastro — Inteligência Política">' + svg + "</span>")


def aneis(geom):
    """GeoJSON -> lista de anéis, o mesmo formato de base.json."""
    polys = ([geom["coordinates"]] if geom["type"] == "Polygon"
             else geom["coordinates"])
    return [p[0] for p in polys]


def montar_dados():
    indice = json.loads((DADOS / "indice.json").read_text(encoding="utf-8"))
    estados = {}
    for u in indice["ufs"]:
        uf = u["s"]
        base = json.loads((DADOS / uf / "base.json").read_text(encoding="utf-8"))
        est = DADOS / uf / "estadual.json"
        anos = {}
        if est.exists():
            d = json.loads(est.read_text(encoding="utf-8"))
            for ano, b in d.items():
                anos[ano] = {
                    "totalMun": b["totalMun"],
                    "pleito": b["pleito"],
                    "partidos": b.get("partidos", [])[:12],
                    "fichas": [{k: f[k] for k in FICHA if k in f}
                               for f in b["fichas"]],
                }
        def ler(nome):
            f = DADOS / uf / nome
            return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        estados[uf] = {"m": [x["n"] for x in base["municipios"]],
                       "g": base["geo"], "a": anos,
                       "p": ler("padroes.json"), "c": ler("cruzamentos.json"),
                       "e": ler("emendas.json"), "d": ler("demografia.json"),
                       "ve": ler("voto_emenda.json"),
                       "ee": ler("emendas_estadual.json"),
                       "vb": ler("alego_verbas.json")}
    return {
        "anos": indice["anos"],
        "ufs": indice["ufs"],
        "agregado": indice["agregado"],
        # a malha do Brasil vira anéis também: uma projeção só serve as duas telas
        "malhaBR": [{"cod": f["cod"], "g": aneis(f["geom"])}
                    for f in indice["malhaUF"]],
        "estados": estados,
        "emendasBR": json.loads((DADOS / "emendas_br.json").read_text(encoding="utf-8"))
                     if (DADOS / "emendas_br.json").exists() else None,
        "assembleias": json.loads((DADOS / "assembleias.json").read_text(encoding="utf-8"))
                       if (DADOS / "assembleias.json").exists() else None,
    }


PAGINA = r"""<title>Cadê o Voto?</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="@FONTES@">
<style>
@CSS@
</style>

<div class="topo"><div class="wrap">
  <div class="topo-in">
    <div class="marca">
      @LOGO@
      <h1 id="titulo">Cadê o Voto?</h1>
      <p id="sub">Distribuição espacial do voto para deputado estadual em cada
        unidade da federação, de 1998 a 2022, município a município.</p>
    </div>
    <div class="seg" role="group" aria-label="Pleito" id="anos"></div>
  </div>

  <div class="abas" role="tablist" id="abas">
    <button role="tab" data-v="nacional" aria-selected="true">Nacional</button>
    <button role="tab" data-v="estado" aria-selected="false">Estado</button>
    <button role="tab" data-v="padroes" aria-selected="false">Padrões</button>
    <button role="tab" data-v="cruzamentos" aria-selected="false">Cruzamentos</button>
    <button role="tab" data-v="emendas" aria-selected="false">Emendômetro</button>
    <button role="tab" data-v="api" aria-selected="false">API</button>
    <button role="tab" data-v="sobre" aria-selected="false">Sobre</button>
  </div>

  <!-- Escolher estado só faz sentido nas abas de estado. No Nacional o mapa
       é o seletor: clicar num estado abre a tela dele. -->
  <details class="gaveta" id="gaveta">
    <summary><span class="seta">&#9656;</span> Qual seu estado?
      <span class="atual" id="atual"></span></summary>
    <div class="estados" id="estados"></div>
  </details>
</div></div>

<main class="wrap">
  <div id="v-nacional">
    <div class="painel">
      <aside class="rail"><div class="rail-bloco sumario">
        <p class="rail-titulo">Nesta aba</p><ol id="sum-nacional"></ol></div></aside>
      <div class="conteudo">
        <div class="cartaz">
          <h2>Concentração do voto por estado</h2>
          <p class="cap">Cada estado colorido pela <strong>fração dos seus
            municípios</strong> que a votação mediana dos eleitos efetivamente
            ocupa. <span class="swatch" style="display:inline-block;vertical-align:-2px;background:var(--s1)"></span>
            vermelho = voto concentrado em poucos municípios;
            <span class="swatch" style="display:inline-block;vertical-align:-2px;background:var(--s5)"></span>
            verde = espalhado pelo estado. <strong>Clique num estado para abrir a tela dele.</strong></p>
          <div id="mapaBR"></div>
          <div class="legenda" id="legBR"></div>
          <div class="rolagem" style="margin-top:16px"><table id="tconc"></table></div>
          <div class="nota" style="margin-top:14px">
            <strong>Municípios efetivos não se comparam entre estados sem
            cuidado.</strong> Roraima tem 15 municípios e Minas tem 853 — um
            estado com 15 não pode ter 16 municípios efetivos. O índice está
            limitado pelo tamanho do estado. Por isso a tabela traz também a
            <em>fração</em> do estado efetivamente usada, que é comparável, e o
            mapa colore por ela.
          </div>
          <p class="cap">O Distrito Federal fica sem cor: elege deputado
            distrital, não estadual. São 26 unidades.</p>
        </div>

        <div class="cartaz">
          <h2>O preço da cadeira em cada estado</h2>
          <p class="cap">Total de votos nominais dividido pelas cadeiras, e a
            votação do último eleito — o corte real de entrada na assembleia.
            Ordenado pelo corte.</p>
          <div class="rolagem"><table id="tpreco"></table></div>
        </div>
      </div>
    </div>
  </div>

  <div id="v-estado" class="oculto">
    <div class="painel">
      <aside class="rail">
        <div class="rail-bloco rail-primario">
          <p class="rail-titulo" id="rotLista">Eleito(a)</p>
          <input class="busca" type="search" id="busca" placeholder="Buscar pelo nome"
                 aria-label="Buscar eleito">
          <div class="lista" id="lista"></div>
        </div>
        <div class="rail-bloco sumario">
          <p class="rail-titulo">Nesta aba</p><ol id="sum-estado"></ol></div>
      </aside>
      <div class="conteudo" id="detalhe"></div>
    </div>
  </div>

  <div id="v-padroes" class="oculto"><div class="painel">
    <aside class="rail"><div class="rail-bloco sumario">
      <p class="rail-titulo">Nesta aba</p><ol id="sum-padroes"></ol></div></aside>
    <div class="conteudo" id="padroes"></div></div></div>

  <div id="v-cruzamentos" class="oculto"><div class="painel">
    <aside class="rail"><div class="rail-bloco sumario">
      <p class="rail-titulo">Nesta aba</p><ol id="sum-cruzamentos"></ol></div></aside>
    <div class="conteudo" id="cruzamentos"></div></div></div>

  <div id="v-api" class="oculto"><div class="painel">
    <aside class="rail"><div class="rail-bloco sumario">
      <p class="rail-titulo">Nesta aba</p><ol id="sum-api"></ol></div></aside>
    <div class="conteudo" id="api"></div>
  </div></div>

  <div id="v-sobre" class="oculto"><div class="painel">
    <aside class="rail"><div class="rail-bloco sumario">
      <p class="rail-titulo">Nesta aba</p><ol id="sum-sobre"></ol></div></aside>
    <div class="conteudo" id="sobre"></div>
  </div></div>

  <div id="v-emendas" class="oculto">
    <div class="painel">
      <aside class="rail">
        <div class="rail-bloco rail-primario">
          <p class="rail-titulo" id="rotAutores">Autor(a)</p>
          <div class="seg" role="group" aria-label="Esfera" id="emEsfera"
               style="margin-bottom:8px"></div>
          <div class="seg" role="group" aria-label="Tipo de emenda" id="emTipo"
               style="margin-bottom:8px">
            <button data-t="todas" aria-pressed="true">Todas</button>
            <button data-t="pix">Só Pix</button>
            <button data-t="def">Sem Pix</button>
          </div>
          <div class="seg" role="group" aria-label="Medida" id="emMedida"
               style="margin-bottom:8px">
            <button data-m="abs" aria-pressed="true">R$</button>
            <button data-m="hab">por hab.</button>
            <button data-m="km">por km²</button>
          </div>
          <div class="seg" role="group" aria-label="Exercício" id="emAnos"
               style="margin-bottom:8px"></div>
          <div class="lista" id="listaAutores"></div>
        </div>
        <div class="rail-bloco sumario">
          <p class="rail-titulo">Nesta aba</p><ol id="sum-emendas"></ol></div>
      </aside>
      <div class="conteudo" id="emendas"></div>
    </div>
  </div>
</main>

<footer class="wrap">
  <p><strong>Lastro — Inteligência Política.</strong> Fonte: Tribunal Superior
     Eleitoral, dados abertos, arquivo
     <span class="num">votacao_candidato_munzona</span>, 1º turno. Malha
     municipal e estadual: IBGE.</p>
  <p>Esta página traz deputado estadual nas 26 unidades, de 1998 a 2022, com as
     duas análises. Os outros quatro cargos, os rivais territoriais e a câmara
     das capitais estão no aplicativo, que carrega os dados sob demanda — não
     cabem aqui: só os rivais do estadual são 12,2 MB.</p>
  <p>O pareamento entre os nomes de município do TSE e a malha do IBGE tem 159
     correções manuais; 47.535 votos de 1998, em três municípios, seguem sem par
     e estão fora destes números.</p>
</footer>

<div class="dica" id="dica" aria-hidden="true"></div>

<script>
const D = @DADOS@;
const RAMPA = ["--s1","--s2","--s3","--s4","--s5"];
const COD = {"11":"RO","12":"AC","13":"AM","14":"RR","15":"PA","16":"AP",
 "17":"TO","21":"MA","22":"PI","23":"CE","24":"RN","25":"PB","26":"PE",
 "27":"AL","28":"SE","29":"BA","31":"MG","32":"ES","33":"RJ","35":"SP",
 "41":"PR","42":"SC","43":"RS","50":"MS","51":"MT","52":"GO","53":"DF"};
const PREP = {AC:"no",AL:"em",AP:"no",AM:"no",BA:"na",CE:"no",DF:"no",ES:"no",
 GO:"em",MA:"no",MT:"em",MS:"em",MG:"em",PA:"no",PB:"na",PR:"no",PE:"em",
 PI:"no",RJ:"no",RN:"no",RS:"no",RO:"em",RR:"em",SC:"em",SE:"em",SP:"em",TO:"no"};

const nomeUF = new Map(D.ufs.map(u => [u.s, u.n]));
const esc = s => String(s).replace(/[&<>"]/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const num = v => (v||0).toLocaleString("pt-BR");
const dec = (v,n) => (v||0).toLocaleString("pt-BR",
  {minimumFractionDigits:n, maximumFractionDigits:n});
const pct = (v,n=2) => dec(v,n) + "%";

/* ---------- projeção ----------
   Equirretangular com correção de longitude por cos(latitude média). Não é
   projeção cartográfica séria; nesta escala a distorção é invisível e não
   depende de biblioteca. O cosseno importa: sem ele o Norte estica. */
function projetar(feicoes, L) {
  let x0=1/0,x1=-1/0,y0=1/0,y1=-1/0;
  for (const f of feicoes) { if(!f) continue;
    for (const a of f) for (const p of a) {
      if(p[0]<x0)x0=p[0]; if(p[0]>x1)x1=p[0];
      if(p[1]<y0)y0=p[1]; if(p[1]>y1)y1=p[1]; } }
  if (!isFinite(x0)) return {L, H:100, d: feicoes.map(()=>"")};
  const k = Math.cos((y0+y1)/2*Math.PI/180), e = L/((x1-x0)*k||1);
  const px = p => [(p[0]-x0)*k*e, (y1-p[1])*e];
  /* Centro do maior anel, não de todos: um município com ilhas teria o centro
     puxado para o mar pela média de tudo. */
  const centro = f => {
    if (!f || !f.length) return null;
    const a = f.reduce((m,x) => x.length > m.length ? x : m, f[0]);
    let sx = 0, sy = 0;
    for (const p of a) { const q = px(p); sx += q[0]; sy += q[1]; }
    return [sx/a.length, sy/a.length];
  };
  return {L, H: Math.max(120, Math.round((y1-y0)*e)),
    c: feicoes.map(centro),
    d: feicoes.map(f => !f ? "" : f.map(a => "M"+a.map(p =>
      ((p[0]-x0)*k*e).toFixed(1)+","+((y1-p[1])*e).toFixed(1)).join("L")+"Z").join(" "))};
}

/* Quantis, não faixas fixas: com faixas iguais quase todo estado cai na classe
   de baixo e o mapa vira monocromático. */
function quantis(v, n=5) {
  const s = v.filter(x=>x>0).sort((a,b)=>a-b);
  if (!s.length) return [1,2,3,4,5];
  return Array.from({length:n}, (_,i) =>
    s[Math.min(s.length-1, Math.ceil(s.length*(i+1)/n)-1)]);
}
const faixa = (v,c) => { if(!(v>0)) return -1;
  for(let i=0;i<c.length;i++) if(v<=c[i]) return i; return c.length-1; };
const corDe = (v,c) => { const i = faixa(v,c);
  return "var(" + (i<0 ? "--sem-voto" : RAMPA[Math.min(i,4)]) + ")"; };

function legenda(el, cortes, sufixo, zero) {
  el.innerHTML = `<span class="item"><span class="swatch" style="background:var(--sem-voto)"></span>${zero}</span>` +
    cortes.map((v,i) => `<span class="item"><span class="swatch" style="background:var(${RAMPA[i]})"></span>` +
      (i===0 ? "até " + (sufixo? pct(v,1):num(Math.round(v)))
             : (sufixo? pct(cortes[i-1],1):num(Math.round(cortes[i-1]))) + " a " +
               (sufixo? pct(v,1):num(Math.round(v)))) + "</span>").join("");
}

function tabela(el, cab, linhas, rodape) {
  el.innerHTML = "<thead><tr>" + cab.map(h=>`<th>${h}</th>`).join("") +
    "</tr></thead><tbody>" + linhas.map(r => "<tr>" + r.map((v,i) =>
      i===0 ? `<td>${v}</td>` : `<td class="n">${v}</td>`).join("") + "</tr>").join("") +
    "</tbody>" + (rodape ? "<tfoot><tr>" + rodape.map((v,i) =>
      i===0 ? `<td>${v}</td>` : `<td class="n">${v}</td>`).join("") + "</tr></tfoot>" : "");
}

/* ---------- marca da capital ----------
   Serve de âncora: num mapa de 246 manchas coloridas sem nenhum rótulo, o
   leitor não sabe onde está olhando. A capital é o ponto de referência que
   quase todo mundo reconhece.

   Desenhada com um halo da cor da superfície por baixo: o marcador cai sobre
   qualquer uma das cinco cores da rampa, e sem o halo ele some no verde-escuro
   e some de novo no vermelho. */
function marcaCapital(P) {
  const r = D.ufs.find(u => u.s === uf);
  if (!r || r.capIdx == null) return "";
  const c = P.c && P.c[r.capIdx];
  if (!c) return "";
  const [x, y] = c;
  const nome = esc(r.capital || "");
  return `<g class="capital" aria-hidden="true">` +
    `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5.2" fill="var(--surface)" opacity=".85"/>` +
    `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="var(--ink)"/>` +
    `<text x="${(x+7).toFixed(1)}" y="${(y+3.5).toFixed(1)}" font-size="11"` +
    ` font-family="IBM Plex Sans, sans-serif" font-weight="600"` +
    ` stroke="var(--surface)" stroke-width="3" paint-order="stroke"` +
    ` fill="var(--ink)">${nome}</text></g>`;
}

/* ---------- balão ---------- */
const dica = document.getElementById("dica");
function mostrarDica(html, x, y) {
  dica.innerHTML = html;
  dica.style.opacity = "1";
  const b = dica.getBoundingClientRect();
  let px = x + 14, py = y + 14;
  if (px + b.width > innerWidth - 8) px = x - b.width - 14;
  if (py + b.height > innerHeight - 8) py = y - b.height - 14;
  dica.style.left = Math.max(8,px) + "px";
  dica.style.top = Math.max(8,py) + "px";
}
const esconderDica = () => { dica.style.opacity = "0"; };

function ligarMapa(svg, descrever, aoClicar) {
  svg.addEventListener("mousemove", e => {
    const p = e.target.closest("path[data-i]");
    if (!p) return esconderDica();
    mostrarDica(descrever(+p.dataset.i), e.clientX, e.clientY);
  });
  svg.addEventListener("mouseleave", esconderDica);
  svg.addEventListener("touchstart", e => {
    const p = e.target.closest("path[data-i]");
    if (!p) return;
    const t = e.touches[0];
    mostrarDica(descrever(+p.dataset.i), t.clientX, t.clientY);
  }, {passive:true});
  if (aoClicar) svg.addEventListener("click", e => {
    const p = e.target.closest("path[data-i]");
    if (p) aoClicar(+p.dataset.i);
  });
}

/* ---------- estado da tela, na hash para poder mandar por link ---------- */
let vista = "nacional", uf = "GO", ano = D.anos[D.anos.length-1], sel = 0, filtro = "";

function lerHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  if (VISTAS.includes(p.get("v"))) vista = p.get("v");
  if (p.get("uf") && D.estados[p.get("uf")]) uf = p.get("uf");
  if (D.anos.includes(+p.get("ano"))) ano = +p.get("ano");
  sel = Math.max(0, +p.get("c") || 0);
}
function gravarHash() {
  const p = new URLSearchParams({v:vista, uf, ano:String(ano), c:String(sel)});
  history.replaceState(null, "", "#" + p);
}

/* ---------- nacional ---------- */
const PROJ_BR = projetar(D.malhaBR.map(f => f.g), 760);
const SIG_BR = D.malhaBR.map(f => COD[f.cod] || f.cod);

function pintarNacional() {
  const m = new Map();
  for (const a of D.agregado) if (a.ano === ano) m.set(a.uf, a);
  const val = SIG_BR.map(s => (m.get(s)||{}).fr || 0);
  const c = quantis(val);

  document.getElementById("mapaBR").innerHTML =
    `<svg viewBox="0 0 ${PROJ_BR.L} ${PROJ_BR.H}" role="img" aria-label="Fração do estado ocupada pelo voto">` +
    PROJ_BR.d.map((d,i) =>
      `<path d="${d}" class="uf" data-i="${i}" fill="${corDe(val[i],c)}"></path>`).join("") +
    "</svg>";
  legenda(document.getElementById("legBR"), c, true, "Sem deputado estadual");

  ligarMapa(document.querySelector("#mapaBR svg"), i => {
    const s = SIG_BR[i], u = m.get(s);
    return `<strong>${esc(nomeUF.get(s)||s)}</strong>` + (u
      ? `Fração do estado: <span class="num">${pct(u.fr||0,1)}</span><br>` +
        `${dec(u.ef||0,1)} municípios efetivos de ${num(u.nmun)}<br>` +
        `<span style="color:var(--accent)">clique para abrir</span>`
      : "elege deputado distrital, não estadual");
  }, i => { const s = SIG_BR[i]; if (m.has(s)) trocarUF(s); });

  const linhas = [...m.values()].map(a => ({...a, nome: nomeUF.get(a.uf)||a.uf}));
  tabela(document.getElementById("tconc"),
    ["Estado","Munic.","Cadeiras","Mun. efetivos","Fração do estado","Maior município"],
    linhas.slice().sort((a,b)=>(b.fr||0)-(a.fr||0)).map(d => [
      `<button class="ligacao" data-uf="${d.uf}">${esc(d.nome)}</button>`,
      num(d.nmun), d.cad, dec(d.ef||0,1), pct(d.fr||0,1), pct(d.t1||0,1)]));
  tabela(document.getElementById("tpreco"),
    ["Estado","Nominais","Cadeiras","Quociente","Último eleito","Candidatos","Por cadeira"],
    linhas.slice().sort((a,b)=>b.ult-a.ult).map(d => [
      `<button class="ligacao" data-uf="${d.uf}">${esc(d.nome)}</button>`,
      num(d.tot), d.cad, num(Math.round(d.qe)), num(d.ult), num(d.cand),
      dec(d.cand/Math.max(d.cad,1),1)]));
}

document.querySelector("main").addEventListener("click", e => {
  const b = e.target.closest("button.ligacao");
  if (b) trocarUF(b.dataset.uf);
});

/* Trocar de estado preserva a aba aberta. Só o Nacional é exceção: lá o clique
   num estado é um pedido para entrar nele, e "entrar" quer dizer a tela do
   estado. Das outras abas, quem troca de estado quer a MESMA leitura noutro
   lugar — o Emendômetro de São Paulo, não a ficha de um deputado paulista. */
function trocarUF(novo) {
  if (!novo || !D.estados[novo]) return;
  uf = novo; sel = 0; emAutor = -1; filtro = "";
  const busca = document.getElementById("busca");
  if (busca) busca.value = "";
  irPara(vista === "nacional" ? "estado" : vista);
}

/* ---------- estado ---------- */
const projCache = new Map();
function projDe(u) {
  if (!projCache.has(u)) projCache.set(u, projetar(D.estados[u].g, 560));
  return projCache.get(u);
}

function fichasVisiveis() {
  const b = D.estados[uf].a[String(ano)];
  if (!b) return [];
  const f = filtro.trim().toLowerCase();
  return f ? b.fichas.filter(x => x.n.toLowerCase().includes(f)) : b.fichas;
}

function pintarEstado() {
  const est = D.estados[uf], b = est.a[String(ano)];
  const alvo = document.getElementById("detalhe");
  document.getElementById("rotLista").textContent =
    `Eleito(a) · ${nomeUF.get(uf)||uf}`;

  if (!b) {
    document.getElementById("lista").innerHTML = "";
    alvo.innerHTML = `<p class="indice exp">Sem dado de deputado estadual em ${ano}.</p>`;
    return;
  }
  const lista = fichasVisiveis();
  document.getElementById("lista").innerHTML = lista.length
    ? lista.map((f,i) => `<button data-i="${i}"${i===sel?' aria-pressed="true"':''}>` +
        `<span>${esc(f.n)}</span><span class="lv">${num(f.t)}</span></button>`).join("")
    : `<p class="indice exp">Ninguém com esse nome neste pleito.</p>`;

  const f = lista[sel] || lista[0];
  if (!f) { alvo.innerHTML = ""; return; }

  const n = est.m.length;
  const votos = new Array(n).fill(0);
  f.mi.forEach((idx,k) => votos[idx] = f.mv[k]);
  const infl = votos.map((v,i) => {
    const t = b.totalMun[i] || 0; return v>0 && t>0 ? v/t*100 : 0; });
  const cv = quantis(votos), ci = quantis(infl);
  const P = projDe(uf);

  const mapa = (id, vals, cortes, rot) =>
    `<svg viewBox="0 0 ${P.L} ${P.H}" role="img" aria-label="${rot}" data-m="${id}">` +
    P.d.map((d,i) => d ? `<path d="${d}" class="mun" data-i="${i}" fill="${corDe(vals[i],cortes)}"></path>` : "").join("") +
    marcaCapital(P) + "</svg>";

  const top = f.mi.map((idx,k) => ({
      nome: est.m[idx] || "—", v: f.mv[k],
      pd: f.mv[k]/f.t*100,
      pm: (b.totalMun[idx]||0) > 0 ? f.mv[k]/b.totalMun[idx]*100 : 0}))
    .sort((a,x)=>x.v-a.v).slice(0,20);

  alvo.innerHTML = `
    <div class="cartoes">
      ${cartao("Eleito(a)", esc(f.n), f.completo && f.completo!==f.n ? esc(f.completo):"", true)}
      ${cartao("Partido", esc(f.p), f.pn && f.pn!==f.p ? "hoje "+esc(f.pn):"", true)}
      ${cartao("Municípios com voto", num(f.nm), "de "+num(n))}
      ${cartao("Votos nominais", num(f.t), "")}
      ${cartao("Do estado", pct(f.t/b.pleito.totalUF*100), num(b.pleito.totalUF)+" no total")}
      ${cartao("Perfil", esc(f.tipo), "", true)}
    </div>

    <div class="mapas">
      <div class="cartaz"><h2>Votação</h2>
        <p class="cap">Votos nominais recebidos em cada município.</p>
        <div id="m-votos">${mapa("votos", votos, cv, "Votação")}</div>
        <div class="legenda" id="leg-votos"></div></div>
      <div class="cartaz"><h2>Influência</h2>
        <p class="cap">Quanto representa do total de votos nominais apurados no município.</p>
        <div id="m-infl">${mapa("infl", infl, ci, "Influência")}</div>
        <div class="legenda" id="leg-infl"></div></div>
    </div>

    <div class="cartaz"><h2>Perfil territorial</h2>
      <p class="cap">Os mesmos índices em todos os estados.</p>
      <div class="indices">
        ${ind("Municípios efetivos", dec(f.ef,1), "de "+num(n)+" — equivale a concentrar tudo nesse tanto de municípios iguais")}
        ${ind("Fração do estado", pct(f.ef/Math.max(n,1)*100,1), "é o número comparável entre estados de portes diferentes")}
        ${ind("Maior município", pct(f.t1,1), f.r>=0 ? esc(est.m[f.r]||"") : "")}
        ${ind("Cinco maiores", pct(f.t5,1), "do total do eleito")}
        ${ind("Domínio médio", pct(f.dom,1), "fatia dele nos municípios onde tem voto")}
        ${ind("Municípios dominados", num(f.dom25), "onde tem 25% ou mais do total apurado")}
        ${ind("Contiguidade", pct(f.contig,1), "votos no reduto e nos municípios que fazem fronteira com ele")}
        ${ind("Gini municipal", dec(f.gi,3), "0 = espalhado por igual, 1 = tudo num lugar")}
      </div></div>

    <div class="duas">
      <div class="cartaz"><h2>Concentração</h2>
        <p class="cap">Os 20 municípios que mais renderam votos.</p>
        <div class="rolagem"><table id="tconc-e"></table></div></div>
      <div class="cartaz"><h2>Partidos</h2>
        <p class="cap">Partidos com três candidaturas ou mais. A semelhança mede
          quanto os candidatos do mesmo partido disputam o mesmo território — não
          se compara entre estados de portes diferentes.</p>
        <div class="rolagem"><table id="tpart"></table></div></div>
    </div>`;

  legenda(document.getElementById("leg-votos"), cv, false, "Nenhum voto");
  legenda(document.getElementById("leg-infl"), ci, true, "Nenhum voto");

  tabela(document.getElementById("tconc-e"),
    ["Município","Votos","% do eleito","% do município"],
    top.map(r => [esc(r.nome), num(r.v), pct(r.pd), pct(r.pm)]),
    ["Total", num(f.t), "100,00%", ""]);
  tabela(document.getElementById("tpart"),
    ["Partido","Cand.","Eleitos","Votos","Puxador","Semelhança"],
    (b.partidos||[]).map(p => [esc(p.nome), p.nc, p.ne, num(p.votos),
      pct(p.puxador,1), p.sim==null ? "—" : dec(p.sim,3)]));

  ligarMapa(document.querySelector("#m-votos svg"), i =>
    `<strong>${esc(est.m[i]||"")}</strong>Votos: <span class="num">` +
    (votos[i]>0 ? num(votos[i]) : "sem voto") + "</span>");
  ligarMapa(document.querySelector("#m-infl svg"), i =>
    `<strong>${esc(est.m[i]||"")}</strong>Influência: <span class="num">` +
    (infl[i]>0 ? pct(infl[i]) : "sem voto") + "</span>");
}

const cartao = (rot, val, sub, txt) =>
  `<div class="cartao"><div class="rot">${rot}</div>` +
  `<div class="val${txt?" txt":""}">${val}</div>` +
  (sub ? `<div class="sub">${sub}</div>` : "") + "</div>";
const ind = (rot, val, exp) =>
  `<div class="indice"><div class="rot">${rot}</div><div class="val">${val}</div>` +
  `<div class="exp">${exp}</div></div>`;

document.getElementById("lista").addEventListener("click", e => {
  const b = e.target.closest("button[data-i]");
  if (!b) return;
  sel = +b.dataset.i; gravarHash(); pintarEstado(); montarSumario("estado"); observarSecoes("estado");
});
document.getElementById("busca").addEventListener("input", e => {
  filtro = e.target.value; sel = 0; pintarEstado(); montarSumario("estado"); observarSecoes("estado");
});

/* ---------- série temporal ----------
   Um eixo só, sempre. Duas medidas de escalas diferentes viram dois gráficos,
   nunca um com dois eixos — é o erro de gráfico mais comum que existe. */
function linha(series, eixoX, casas, altura) {
  altura = altura || 190;
  const L=620, ml=40, mr=14, mt=14, mb=26;
  const vals = series.flatMap(s=>s.pontos).filter(v=>v!=null);
  if (!vals.length) return `<p class="indice exp">Sem dado para o período.</p>`;
  const hi = Math.max(...vals)*1.1;
  const px = i => ml + (L-ml-mr)*i/Math.max(eixoX.length-1,1);
  const py = v => mt + (altura-mt-mb)*(1 - v/(hi||1));
  let out = `<svg viewBox="0 0 ${L} ${altura}" role="img" aria-label="série temporal">`;
  for (const v of [0, hi/2, hi])
    out += `<line x1="${ml}" x2="${L-mr}" y1="${py(v)}" y2="${py(v)}" stroke="var(--line)" stroke-width="1"/>`
        +  `<text x="${ml-6}" y="${py(v)+3}" text-anchor="end" font-size="11" fill="var(--ink-3)" font-family="IBM Plex Mono, monospace">${v.toFixed(casas)}</text>`;
  for (const s of series) {
    const pts = s.pontos.map((v,i)=> v==null?null:[px(i),py(v)]).filter(Boolean);
    if (!pts.length) continue;
    out += `<path d="M${pts.map(q=>q[0].toFixed(1)+","+q[1].toFixed(1)).join("L")}" fill="none" stroke="var(${s.cor})" stroke-width="2.5" stroke-linejoin="round"/>`;
    pts.forEach((q,i)=> out += `<circle cx="${q[0]}" cy="${q[1]}" r="${i===pts.length-1?5:3.5}" fill="var(${s.cor})" stroke="var(--surface)" stroke-width="2"/>`);
  }
  eixoX.forEach((r,i)=> out += `<text x="${px(i)}" y="${altura-8}" text-anchor="middle" font-size="11" fill="var(--ink-3)" font-family="IBM Plex Mono, monospace">${r}</text>`);
  return out + "</svg>";
}
const chip = (cor, txt) =>
  `<span class="item"><span class="swatch" style="background:var(${cor})"></span>${txt}</span>`;

/* ---------- Padrões ---------- */
const TIPOS = {"Concentrado-Dominante":"--s1","Disperso-Dominante":"--s3",
  "Concentrado-Compartilhado":"--s4","Disperso-Difuso":"--s5"};

function pintarPadroes() {
  const alvo = document.getElementById("padroes");
  const p = D.estados[uf].p, n = D.estados[uf].m.length;
  const nome = esc(nomeUF.get(uf)||uf);
  if (!p || !p.serie.length) {
    alvo.innerHTML = `<p class="indice exp">Sem análise de padrões para ${nome}.</p>`;
    return; }
  const anos = p.serie.map(s=>s.ano), capt = p.captura;

  alvo.innerHTML = `
  <div class="cartaz">
    <h2>Como as bases mudaram, ${anos[0]} a ${anos[anos.length-1]}</h2>
    <p class="cap">Medianas entre os eleitos de cada pleito, não médias: a
      distribuição é assimétrica e a média seria puxada pelos casos extremos.</p>
    ${linha([{rotulo:"Municípios efetivos",cor:"--accent",pontos:p.serie.map(s=>s.ef)}],anos,1)}
    <p class="cap" style="margin-top:10px">Municípios efetivos — quanto menor, mais a
      votação depende de poucas cidades. Em ${nome} o teto é ${num(n)}.</p>
    ${linha([{rotulo:"Maior município",cor:"--s1",pontos:p.serie.map(s=>s.t1)},
             {rotulo:"Domínio médio",cor:"--s5",pontos:p.serie.map(s=>s.dom)}],anos,1)}
    <div class="legenda">${chip("--s1","Maior município, % do total do eleito")}
      ${chip("--s5","Domínio médio, % que ele detém onde atua")}</div>
  </div>

  <div class="cartaz">
    <h2>Que tipo de deputado o estado elege</h2>
    <p class="cap">Cruzamento de concentração (10 ou menos municípios efetivos) com
      domínio (10% ou mais em média). Os cortes são escolha analítica, não do TSE.</p>
    <div class="rolagem"><table id="ttipo"></table></div>
  </div>

  <div class="cartaz">
    <h2>A janela de captura municipal</h2>
    <p class="cap">Fatia do maior candidato no total de votos nominais do município,
      por porte do eleitorado. Valores medianos; cor mais quente significa mais capturado.</p>
    <div class="rolagem"><table id="tcapt"></table></div>
    <div class="nota" style="margin-top:12px">
      <strong>Existe um tamanho ótimo de captura.</strong> Município pequeno demais não
      sustenta candidato próprio e acaba repartido entre os vizinhos; grande demais,
      ninguém domina. O pico costuma ficar numa faixa intermediária — em estados com
      poucos municípios o padrão some, porque não há faixas suficientes.
    </div>
  </div>

  <div class="cartaz">
    <h2>O preço da cadeira</h2>
    <p class="cap">Quociente eleitoral aproximado — total de nominais dividido pelas
      cadeiras — e a votação do último eleito, que é o corte real de entrada.</p>
    <div class="rolagem"><table id="tcusto"></table></div>
  </div>`;

  tabela(document.getElementById("ttipo"), ["Pleito", ...Object.keys(TIPOS)],
    p.tipologia.map(l => [l.ano, ...Object.keys(TIPOS).map(t => {
      const q = l.tipos[t] || 0;
      return `${q} <span style="color:var(--ink-3);font-size:.7rem">(${pct(q/l.n*100,0)})</span>`;
    })]));

  /* A escala de cor da captura é por LINHA, não pela tabela toda: cada pleito
     tem seu próprio nível, e uma escala global esconderia a forma da curva
     dentro do ano, que é justamente o que interessa aqui. */
  const el = document.getElementById("tcapt");
  el.innerHTML = "<thead><tr>" + ["Pleito", ...capt.faixas].map(h=>`<th>${h}</th>`).join("") +
    "</tr></thead><tbody>" + capt.anos.map(a => {
      const vs = a.t1.filter(v=>v!=null);
      const lo = Math.min(...vs,0), hi = Math.max(...vs,1);
      return `<tr><td class="n">${a.ano}</td>` + a.t1.map(v => {
        if (v == null) return `<td class="n">—</td>`;
        const c = RAMPA[Math.min(4, Math.max(0, Math.floor((v-lo)/((hi-lo)||1)*5)))];
        return `<td class="n" style="background:var(${c});color:var(${c.replace("--s","--tinta-s")})">${dec(v,1)}</td>`;
      }).join("") + "</tr>";
    }).join("") + "</tbody><tfoot><tr><td>Municípios</td>" +
    ((capt.anos[capt.anos.length-1]||{}).n||[]).map(q=>`<td class="n">${q}</td>`).join("") +
    "</tr></tfoot>";

  tabela(document.getElementById("tcusto"),
    ["Pleito","Cadeiras","Nominais","Quociente","Último eleito","Candidatos","Por cadeira"],
    p.custo.map(c => [c.ano, c.cad, num(c.tot), num(Math.round(c.qe)), num(c.ult),
      c.cand, dec(c.cand/Math.max(c.cad,1),1)]));
}

/* ---------- Cruzamentos ---------- */
const CARGOS = ["presidente","governador","senador","federal","estadual"];
const NOME_CARGO = {presidente:"Presidente",governador:"Governador",
  senador:"Senado",federal:"Federal",estadual:"Estadual"};
const COR_CARGO = {presidente:"--s5",governador:"--s3",senador:"--s4",
  federal:"--s2",estadual:"--s1"};

function pintarCruzamentos() {
  const alvo = document.getElementById("cruzamentos");
  const c = D.estados[uf].c, n = D.estados[uf].m.length;
  const nome = esc(nomeUF.get(uf)||uf);
  if (!c || !c.escala.length) {
    alvo.innerHTML = `<p class="indice exp">Sem análise de cruzamentos para ${nome}.</p>`;
    return; }
  const anos = [...new Set(c.escala.map(e=>e.ano))].sort();
  const arr = c.arrasto.filter(a=>a.ano===ano).sort((a,b)=>b.r-a.r).slice(0,14);
  const dup = c.duplas.filter(d=>d.ano===ano).slice(0,15);

  alvo.innerHTML = `
  <div class="cartaz">
    <h2>Cada cargo se disputa numa escala diferente</h2>
    <p class="cap">Municípios efetivos, mediana por pleito. Nos cargos majoritários
      usa-se o mais votado no estado, não o vencedor da eleição — para presidente os
      dois raramente coincidem, e é a geografia local que interessa aqui.</p>
    ${linha(CARGOS.map(cg => ({rotulo:NOME_CARGO[cg], cor:COR_CARGO[cg],
      pontos: anos.map(a => { const e = c.escala.find(x=>x.cargo===cg&&x.ano===a);
        return e ? e.ef : null; })})), anos, 1)}
    <div class="legenda">${CARGOS.map(cg=>chip(COR_CARGO[cg],NOME_CARGO[cg])).join("")}</div>
    <div class="nota" style="margin-top:12px">
      <strong>O teto é o número de municípios do estado.</strong> ${nome} tem ${num(n)},
      e nenhum cargo pode passar disso. Em estados pequenos os cinco cargos se aproximam
      por limitação aritmética, não porque a disputa seja parecida — por isso a coluna
      de fração, abaixo, é a comparável.
    </div>
    <div class="rolagem" style="margin-top:12px"><table id="tescala"></table></div>
  </div>

  <div class="cartaz">
    <h2>O partido anda junto entre os cargos?</h2>
    <p class="cap">Correlação, entre os municípios do estado, da fatia do partido no
      deputado estadual e no federal em ${ano}. Perto de 1, o partido tem a mesma
      geografia nos dois cargos — máquina coordenada. Perto de 0, as duas disputas
      correm soltas: candidatos independentes dividindo só a legenda.</p>
    ${arr.length ? `<div class="rolagem"><table id="tarr"></table></div>`
      : `<p class="indice exp">Nenhum partido com presença em pelo menos metade dos
         municípios nos dois cargos neste pleito.</p>`}
    <p class="cap" style="margin-top:10px">Só entram partidos presentes em metade dos
      municípios ou mais, nos dois cargos. Sem esse corte, uma legenda com voto em
      poucas cidades correlaciona alto por acaso e aparece no topo sem dizer nada
      sobre território.</p>
  </div>

  <div class="cartaz">
    <h2>Duplas estadual e federal com o mesmo mapa</h2>
    <p class="cap">Para cada deputado estadual, o federal cujo mapa municipal mais se
      parece com o dele em ${ano}.</p>
    <div class="rolagem"><table id="tdup"></table></div>
    <div class="nota" style="margin-top:12px">
      <strong>Isto não prova campanha casada.</strong> Dois candidatos concentrados na
      mesma cidade têm mapas quase idênticos por geometria, sem combinação nenhuma —
      por isso as afinidades chegam perto de 1. A tabela mostra coincidência
      territorial; a intenção o dado não revela. O número informativo é o de baixo.
    </div>
    ${c.mesmoPartido.length ? `<p class="cap" style="margin-top:14px">Entre as duplas
      mais parecidas, quantas dividem a mesma legenda:</p>` +
      linha([{rotulo:"Mesmo partido",cor:"--accent",pontos:c.mesmoPartido.map(m=>m.pct)}],
            c.mesmoPartido.map(m=>m.ano), 0, 150) : ""}
  </div>`;

  tabela(document.getElementById("tescala"),
    ["Cargo","Municípios efetivos","Fração do estado","Maior município"],
    CARGOS.map(cg => { const e = c.escala.find(x=>x.cargo===cg&&x.ano===ano);
      return e ? [NOME_CARGO[cg], dec(e.ef,1), pct(e.fr,1), pct(e.t1,1)] : null;
    }).filter(Boolean));
  if (arr.length) tabela(document.getElementById("tarr"),
    ["Partido","Correlação","Municípios"],
    arr.map(a => [esc(a.partido), dec(a.r,3), a.nm]));
  tabela(document.getElementById("tdup"),
    ["Estadual","Federal","Mesmo partido","Afinidade"],
    dup.map(d => [`${esc(d.e)} <span style="color:var(--ink-3)">${esc(d.ep)}</span>`,
      `${esc(d.f)} <span style="color:var(--ink-3)">${esc(d.fp)}</span>`,
      d.mp ? "sim" : "não", dec(d.af,4)]));
}

/* ---------- Emendômetro ----------
   Duas coberturas diferentes, e as duas aparecem na tela porque respondem a
   perguntas diferentes: 10,5% do DINHEIRO individual é rastreável até um
   município, mas 69% dos MUNICÍPIOS receberam alguma emenda somando 2015–2026.
   O mapa abre acumulado por causa do segundo número — num ano só, um estado
   como Goiás mostra 17 municípios e o mapa sugere ausência de dinheiro onde o
   que há é ausência de rastreabilidade. */
let emAno = "todos", emAutor = -1, emMedida = "abs", emTipo = "todas";
let emEsfera = "federal";

/* Federal e estadual são orçamentos diferentes com o mesmo nome. O seletor só
   aparece onde existe a base estadual — hoje, Goiás — porque um botão que leva
   a uma tela vazia em 26 estados é pior que a ausência do botão. */
function fonteEmendas() {
  return emEsfera === "estadual" ? D.estados[uf].ee : D.estados[uf].e;
}

/* "Emenda Pix" é o apelido da Transferência Especial: o dinheiro cai direto na
   conta do município, sem convênio, sem finalidade definida no orçamento e sem
   que o governo federal acompanhe a aplicação. Não é uma subcategoria contábil
   — é a diferença entre dinheiro com destino declarado e dinheiro sem, e por
   isso vale um filtro próprio e não uma linha numa tabela. */
const NOME_TIPO = {todas: "todas as emendas individuais",
                   pix: "só emendas Pix", def: "só emendas com finalidade definida"};

/* Reais absolutos, por habitante e por km2 respondem coisas diferentes, e
   nenhuma e' a leitura certa sozinha. O mapa em reais e' quase um mapa de
   populacao — cidade grande recebe mais porque e' grande. Por habitante inverte
   o retrato; por km2 inverte de novo, favorecendo o pequeno e denso. */
const MEDIDA = {
  abs: {rot: "Valor pago", un: "", fmt: v => reais(v)},
  hab: {rot: "Valor pago por habitante", un: " por hab.",
        fmt: v => "R$ " + dec(v, v < 100 ? 2 : 0)},
  km:  {rot: "Valor pago por km²", un: " por km²",
        fmt: v => "R$ " + dec(v, v < 100 ? 2 : 0)},
};

/* Divide elemento a elemento pelo denominador demográfico. Município sem dado
   no Censo vira null e some do mapa como "sem dado" — nunca zero, que
   dividiria e daria infinito. */
function normalizar(vals, medida) {
  if (medida === "abs") return vals;
  const d = D.estados[uf].d;
  if (!d) return vals;
  const den = medida === "hab" ? d.pop : d.area;
  return vals.map((v, i) => {
    const q = den[i];
    return (q == null || q <= 0) ? 0 : v / q;
  });
}

const reais = v => v >= 1e9 ? "R$ " + dec(v/1e9,2) + " bi"
              : v >= 1e6 ? "R$ " + dec(v/1e6,1) + " mi"
              : v >= 1e3 ? "R$ " + dec(v/1e3,0) + " mil"
              : "R$ " + dec(v,0);

function emBlocos() {
  const e = fonteEmendas();
  if (!e) return null;
  return emAno === "todos" ? Object.values(e.anos)
                           : (e.anos[emAno] ? [e.anos[emAno]] : []);
}

function emAgregado() {
  /* Soma os anos escolhidos num único vetor municipal e numa lista de autores.
     Somar aqui, e não no pipeline, é o que deixa o filtro de exercício ser
     recorte e não outro arquivo. */
  const e = fonteEmendas(), n = D.estados[uf].m.length;
  const bl = emBlocos();
  if (!bl || !bl.length) return null;
  const tot = new Array(n).fill(0), totPix = new Array(n).fill(0);
  const por = new Map();
  let pago = 0, pagoPix = 0, emendas = 0, emendasPix = 0, cortados = 0;
  for (const b of bl) {
    b.totalMun.forEach((v,i) => tot[i] += v);
    (b.totalPix || []).forEach((v,i) => totPix[i] += v);
    pago += b.pleito.pago; pagoPix += b.pleito.pix || 0;
    emendas += b.pleito.nEmendas; emendasPix += b.pleito.nPix || 0;
    cortados += b.pleito.cortados || 0;
    for (const f of b.fichas) {
      let a = por.get(f.n);
      if (!a) { a = {n:f.n, t:0, pix:0, ne:0, el:f.el, ufEl:f.ufEl, amb:f.amb,
                     fn:f.fn, mun:new Map(), munPix:new Map()}; por.set(f.n, a); }
      a.t += f.t; a.pix += f.pix || 0; a.ne += f.ne;
      f.mi.forEach((idx,k) => a.mun.set(idx, (a.mun.get(idx)||0) + f.mv[k]));
      (f.pxi || []).forEach((idx,k) => a.munPix.set(idx, (a.munPix.get(idx)||0) + f.pxv[k]));
    }
  }
  /* "Sem Pix" é subtração, não uma terceira soma: o arquivo guarda o total e a
     parte Pix, e o resto é a diferença. Guardar os três seria a chance de os
     três discordarem. */
  const recorte = (todos, pix) => emTipo === "pix" ? pix
    : emTipo === "def" ? todos.map((v,i) => Math.max(0, v - pix[i])) : todos;
  const autores = [...por.values()].map(a => {
    const m = new Map();
    for (const [i,x] of a.mun) {
      const px = a.munPix.get(i) || 0;
      const val = emTipo === "pix" ? px : emTipo === "def" ? Math.max(0, x - px) : x;
      if (val > 0) m.set(i, val);
    }
    const v = [...m.values()], soma = v.reduce((x,y)=>x+y,0) || 1;
    const p = v.map(x => x/soma);
    return {...a, mun: m, nm: v.length,
      total: emTipo === "pix" ? a.pix
           : emTipo === "def" ? Math.max(0, a.t - a.pix) : a.t,
      ef: v.length ? +(1/p.reduce((x,y)=>x+y*y,0)).toFixed(2) : 0,
      t1: v.length ? +(Math.max(...p)*100).toFixed(2) : 0};
  }).filter(a => a.total > 0).sort((a,b)=>b.total-a.total);
  const vals = recorte(tot, totPix);
  return {tot: vals, totTodas: tot, totPix, autores, cortados,
          pago: emTipo === "pix" ? pagoPix
              : emTipo === "def" ? Math.max(0, pago - pagoPix) : pago,
          pagoTodas: pago, pagoPix,
          emendas: emTipo === "pix" ? emendasPix
                 : emTipo === "def" ? Math.max(0, emendas - emendasPix) : emendas,
          nMun: vals.filter(v=>v>0).length, cobertura: e.cobertura};
}

function pintarEmendas() {
  const alvo = document.getElementById("emendas");
  const est = D.estados[uf], nome = esc(nomeUF.get(uf)||uf);
  const n = est.m.length;

  /* Trocar de estado pode tirar o chão da esfera estadual: se o novo estado
     não tem base própria, volta para federal em vez de mostrar tela vazia. */
  if (emEsfera === "estadual" && !est.ee) emEsfera = "federal";
  const fonte = fonteEmendas();
  document.getElementById("emEsfera").innerHTML = est.ee
    ? `<button data-s="federal"${emEsfera==="federal"?' aria-pressed="true"':''}>Federal</button>` +
      `<button data-s="estadual"${emEsfera==="estadual"?' aria-pressed="true"':''}>Estadual</button>`
    : "";
  // Transferência Especial é instrumento federal: o filtro não faz sentido aqui
  document.getElementById("emTipo").classList.toggle("oculto", emEsfera === "estadual");
  if (emEsfera === "estadual") emTipo = "todas";
  const anosEm = fonte ? Object.keys(fonte.anos).sort() : [];
  document.getElementById("emAnos").innerHTML = est.e
    ? [`<button data-a="todos"${emAno==="todos"?' aria-pressed="true"':''}>Todos</button>`]
        .concat(anosEm.map(a=>`<button data-a="${a}"${a===emAno?' aria-pressed="true"':''}>${a}</button>`)).join("")
    : "";
  document.getElementById("rotAutores").textContent = `Autor(a) · ${nomeUF.get(uf)||uf}`;

  const ag = emAgregado();
  if (!ag) {
    document.getElementById("listaAutores").innerHTML = "";
    alvo.innerHTML = `<p class="indice exp">Sem emenda com município identificado
      ${emAno==="todos" ? `em ${nome}` : `em ${nome} no exercício de ${emAno}`}.</p>`;
    return;
  }

  document.getElementById("listaAutores").innerHTML =
    `<button data-i="-1"${emAutor<0?' aria-pressed="true"':''}>` +
    `<span>Todos os autores</span><span class="lv">${reais(ag.pago)}</span></button>` +
    ag.autores.map((a,i) => `<button data-i="${i}"${i===emAutor?' aria-pressed="true"':''}>` +
      `<span>${esc(a.n)}${a.el?'':' <span class="lv">·</span>'}</span>` +
      `<span class="lv">${reais(a.total)}</span></button>`).join("");

  const a = emAutor >= 0 ? ag.autores[emAutor] : null;
  const brutos = a ? (() => { const v = new Array(n).fill(0);
      for (const [i,x] of a.mun) v[i] = x; return v; })() : ag.tot;
  for (const b of document.querySelectorAll("#emTipo button"))
    b.setAttribute("aria-pressed", String(b.dataset.t === emTipo));
  const med = MEDIDA[emMedida] || MEDIDA.abs;
  const vals = normalizar(brutos, emMedida);
  const cortes = quantis(vals);
  for (const b of document.querySelectorAll("#emMedida button"))
    b.setAttribute("aria-pressed", String(b.dataset.m === emMedida));
  const P = projDe(uf);
  const pctMun = ag.cobertura.pago > 0 ? ag.cobertura.pagoMun/ag.cobertura.pago*100 : 0;

  const top = vals.map((v,i)=>({i,v,bruto:brutos[i]})).filter(x=>x.v>0)
    .sort((x,y)=>y.v-x.v).slice(0,20);
  const somaBrutos = brutos.reduce((x,y)=>x+y,0);

  alvo.innerHTML = `
  <div class="nota">
    ${emEsfera === "estadual" ? `
      <strong>Emendas de deputado estadual, orçamento de ${nome}.</strong>
      Outra fonte e outro orçamento: vem dos dados abertos do estado, não do
      Portal da Transparência federal. Aqui
      <span class="num">${pct(pctMun,1)}</span> do valor nomeia um município —
      muito mais que no federal, e não por virtude: a emenda estadual é menor e
      quase sempre aponta uma cidade, enquanto a federal vai com frequência
      para <em>MÚLTIPLO</em> ou para o estado inteiro.
      ${reais(ag.cobertura.pagoMun)} de ${reais(ag.cobertura.pago)}.
    ` : `
      <strong>Esta aba mostra o que é rastreável até o município, e isso é uma
      fatia.</strong> Em ${nome}, ${reais(ag.cobertura.pagoMun)} dos
      ${reais(ag.cobertura.pago)} pagos em emendas individuais têm um município
      declarado — <span class="num">${pct(pctMun,1)}</span>. O resto está em
      <em>MÚLTIPLO</em> ou dirigido ao estado inteiro, e o arquivo do Portal da
      Transparência não diz para onde foi. O valor é o que saiu do caixa
      (pago + restos a pagar pagos), nunca o empenhado.
    `}
  </div>

  <div class="cartoes">
    ${cartao("Rastreável ao município", reais(a ? a.total : ag.pago), a ? esc(a.n) : `de ${reais(ag.cobertura.pago)} no estado`)}
    ${cartao("Emendas", num(a ? a.ne : ag.emendas), emAno==="todos" ? "2015–2026" : `exercício ${emAno}`)}
    ${emTipo === "todas" && emEsfera !== "estadual" ? cartao("Sendo Pix",
        pct(ag.pagoTodas > 0 ? (a ? a.pix/Math.max(a.t,1) : ag.pagoPix/ag.pagoTodas)*100 : 0, 1),
        reais(a ? a.pix : ag.pagoPix) + " em transferência especial") : ""}
    ${cartao("Municípios alcançados", num(a ? a.nm : ag.nMun), "de "+num(n))}
    ${cartao("Autores", num(ag.autores.length), a ? "" : "com emenda no estado")}
    ${a ? cartao("Municípios efetivos", dec(a.ef,1), "concentração da carteira") : ""}
    ${a ? cartao("Casa com eleito", a.el ? "Sim" : "Não", a.el ? (a.ufEl||"").replace(/\|/g,", ") : "senador ou fora de 2014–2022", true) : ""}
  </div>

  <div class="cartaz">
    <h2>Para onde foi o dinheiro${a ? " de "+esc(a.n) : ""}</h2>
    ${emTipo !== "todas" ? `<div class="nota" style="margin-bottom:12px">
      <strong>${emTipo === "pix" ? "Só emendas Pix." : "Sem as emendas Pix."}</strong>
      A Transferência Especial — o apelido é "Pix" — cai direto na conta do
      município, sem convênio, sem finalidade definida no orçamento e sem que o
      governo federal acompanhe a aplicação. ${emTipo === "pix"
        ? "É o dinheiro sobre o qual se sabe menos: quem mandou e para onde, e mais nada."
        : "O que sobra aqui é o dinheiro que tem destino declarado."}
    </div>` : ""}
    <p class="cap">${med.rot} em cada município${emAno==="todos" ? ", somando 2015 a 2026" : `, exercício de ${emAno}`}.
      ${emMedida === "abs"
        ? "Em reais absolutos o mapa é quase um mapa de população — cidade grande recebe mais porque é grande. Troque a medida à esquerda para inverter o retrato."
        : `População e área do Censo 2022 (IBGE).${emMedida==="km" ? " Por quilômetro quadrado favorece o município pequeno e denso." : " Por habitante favorece o município pequeno que recebeu bem."}`}
      ${a ? "" : "Clique num autor à esquerda para ver só a carteira dele."}</p>
    <div id="m-emendas">
      <svg viewBox="0 0 ${P.L} ${P.H}" role="img" aria-label="Emendas por município">
        ${P.d.map((d,i)=> d ? `<path d="${d}" class="mun" data-i="${i}" fill="${corDe(vals[i],cortes)}"></path>` : "").join("")}
        ${marcaCapital(P)}
      </svg>
    </div>
    <div class="legenda" id="leg-emendas"></div>
  </div>

  <div class="duas">
    <div class="cartaz"><h2>Municípios que mais receberam</h2>
      <p class="cap">Os 20 maiores${a ? " na carteira deste autor" : ""}.</p>
      <div class="rolagem"><table id="tmun"></table></div></div>
    <div class="cartaz"><h2>Quem manda</h2>
      <p class="cap">Autores com emenda rastreável em ${nome}. O ponto marca quem
        casa com um deputado federal eleito entre 2014 e 2022 — senadores também
        fazem emenda individual e não casam por aqui.</p>
      <div class="rolagem"><table id="tautores"></table></div></div>
  </div>

  <div class="cartaz" id="c-cruz"></div>

  <div class="cartaz${emEsfera === "estadual" ? " oculto" : ""}">
    <h2>O país inteiro, por unidade da federação</h2>
    <p class="cap">Aqui a cobertura é outra: <strong>97,1% do dinheiro</strong>
      individual tem UF, inclusive o que está em <em>MÚLTIPLO</em>. É o nível em
      que o Emendômetro está completo.</p>
    <div class="rolagem"><table id="tbr"></table></div>
  </div>`;

  const legFmt = document.getElementById("leg-emendas");
  legFmt.innerHTML =
    `<span class="item"><span class="swatch" style="background:var(--sem-voto)"></span>Sem emenda rastreável</span>` +
    cortes.map((v,i) => `<span class="item"><span class="swatch" style="background:var(${RAMPA[i]})"></span>` +
      (i===0 ? "até " + med.fmt(v) : med.fmt(cortes[i-1]) + " a " + med.fmt(v)) + "</span>").join("");

  const dem = D.estados[uf].d;
  ligarMapa(document.querySelector("#m-emendas svg"), i => {
    if (!(brutos[i] > 0)) return `<strong>${esc(est.m[i]||"")}</strong>sem emenda rastreável`;
    let txt = `<strong>${esc(est.m[i]||"")}</strong><span class="num">${reais(brutos[i])}</span>`;
    if (emMedida !== "abs" && dem) {
      const q = emMedida === "hab" ? dem.pop[i] : dem.area[i];
      txt += q == null ? "<br>sem dado no Censo 2022"
           : `<br><span class="num">${med.fmt(vals[i])}</span>${med.un}` +
             `<br>${num(Math.round(q))}${emMedida==="hab" ? " habitantes" : " km²"}`;
    }
    return txt;
  });

  // em reais absolutos a coluna normalizada seria a mesma; nao repetir
  tabela(document.getElementById("tmun"),
    emMedida === "abs"
      ? ["Município", "Valor pago", "% do total"]
      : ["Município", med.rot, "Valor pago", "% do total"],
    top.map(x => emMedida === "abs"
      ? [esc(est.m[x.i]||"—"), reais(x.bruto), pct(x.bruto/somaBrutos*100)]
      : [esc(est.m[x.i]||"—"), med.fmt(x.v), reais(x.bruto),
         pct(x.bruto/somaBrutos*100)]));

  tabela(document.getElementById("tautores"),
    ["Autor(a)","Emendas","Valor pago","Munic.","Área principal"],
    ag.autores.slice(0,20).map(x => [
      esc(x.n) + (x.el ? ' <span style="color:var(--accent)">●</span>' : ""),
      x.ne, reais(x.t), x.nm, esc(x.fn||"—")]));

  const cx = document.getElementById("c-cruz");
  if (cx) cx.classList.toggle("oculto", emEsfera === "estadual");
  if (emEsfera !== "estadual") pintarCruzamento();

  if (D.emendasBR && emEsfera !== "estadual") {
    const m = new Map();
    for (const r of D.emendasBR.uf) {
      if (emAno !== "todos" && String(r.ano) !== emAno) continue;
      const q = m.get(r.uf) || {pago:0, n:0, pagoMun:0, aut:0};
      q.pago += r.pago; q.n += r.n; q.pagoMun += r.pagoMun;
      q.aut = Math.max(q.aut, r.aut); m.set(r.uf, q);
    }
    tabela(document.getElementById("tbr"),
      ["UF","Pago (todas as emendas individuais)","Emendas","Autores","Rastreável ao município"],
      [...m.entries()].sort((x,y)=>y[1].pago-x[1].pago).map(([s,q]) => [
        `<button class="ligacao" data-uf="${s}">${esc(nomeUF.get(s)||s)}</button>`,
        reais(q.pago), num(q.n), num(q.aut),
        pct(q.pago>0 ? q.pagoMun/q.pago*100 : 0, 1)]));
  }
}

document.getElementById("emEsfera").addEventListener("click", e => {
  const b = e.target.closest("button[data-s]");
  if (!b) return;
  emEsfera = b.dataset.s; emAutor = -1; emAno = "todos";
  pintarEmendas(); montarSumario("emendas"); observarSecoes("emendas");
});
document.getElementById("emTipo").addEventListener("click", e => {
  const b = e.target.closest("button[data-t]");
  if (!b) return;
  emTipo = b.dataset.t; emAutor = -1;
  pintarEmendas(); montarSumario("emendas"); observarSecoes("emendas");
});
document.getElementById("emMedida").addEventListener("click", e => {
  const b = e.target.closest("button[data-m]");
  if (!b) return;
  emMedida = b.dataset.m; pintarEmendas(); montarSumario("emendas"); observarSecoes("emendas");
});
document.getElementById("emAnos").addEventListener("click", e => {
  const b = e.target.closest("button[data-a]");
  if (!b) return;
  emAno = b.dataset.a; emAutor = -1; pintarEmendas(); montarSumario("emendas"); observarSecoes("emendas");
});
document.getElementById("listaAutores").addEventListener("click", e => {
  const b = e.target.closest("button[data-i]");
  if (!b) return;
  emAutor = +b.dataset.i; pintarEmendas(); montarSumario("emendas"); observarSecoes("emendas");
});

/* ---------- o dinheiro segue o voto? ----------
   A medida ingênua não serve: Goiânia recebe muito voto E muita emenda de quase
   todo deputado goiano, porque é grande. Por isso cada deputado é comparado com
   uma linha de base pareada — o MESMO dinheiro dele medido contra o reduto dos
   OUTROS deputados da mesma UF e do mesmo pleito. Se a emenda vai para a cidade
   grande por ser grande, ela cai no reduto dos outros também e o excesso zera. */
function pintarCruzamento() {
  const alvo = document.getElementById("c-cruz");
  if (!alvo) return;
  const ve = D.estados[uf].ve, nome = esc(nomeUF.get(uf)||uf);
  if (!ve || !ve.afericao || !ve.afericao.n) {
    alvo.innerHTML = `<h2>O dinheiro segue o voto?</h2>
      <p class="cap">Sem pares suficientes em ${nome} para medir.</p>`;
    return;
  }
  const a = ve.afericao;
  const firmes = ve.deputados.filter(d => d.nm >= (ve.minMun || 3));
  alvo.innerHTML = `
    <h2>O dinheiro segue o voto?</h2>
    <p class="cap">Para cada deputado federal eleito, quanto da emenda dele caiu
      nos ${ve.topReduto} municípios onde ele mais votou — e quanto cairia no
      reduto de <em>outro</em> deputado do mesmo estado e pleito. A segunda
      medida é a linha de base: ela carrega o efeito do tamanho da cidade, e é
      contra ela que a primeira tem de ser lida.</p>
    <div class="indices">
      ${ind("No próprio reduto", pct(a.obs,1), "mediana em "+nome)}
      ${ind("No reduto alheio", pct(a.nulo,1), "a mesma emenda, outro mapa de voto")}
      ${ind("Excesso", (a.exc>=0?"+":"")+dec(a.exc,1)+" pp", "o que sobra depois de descontar o acaso")}
      ${ind("Acima de zero", `${a.acima} de ${a.n}`, "deputados com excesso positivo")}
    </div>
    ${ve.escada && ve.escada.length ? `
    <p class="cap" style="margin-top:14px"><strong>O efeito encolhe quando se
      exige mais dado?</strong> No país inteiro, não — ele cresce. É o contrário
      do que aconteceria se fosse artefato de denominador pequeno.</p>
    <div class="rolagem"><table id="tescada"></table></div>` : ""}
    <div class="nota" style="margin-top:14px">
      <strong>Isto mede ${pct(a.cob,1)} do dinheiro, na mediana.</strong> Só a
      emenda cuja localidade de aplicação nomeia um município entra na conta, e
      em ${nome} isso é uma fração pequena da carteira de cada deputado. O
      sentido do resultado é sólido; a magnitude fala do que é rastreável, não
      do orçamento inteiro.
    </div>
    ${firmes.length ? `<p class="cap" style="margin-top:14px">Os que mais
      concentraram no próprio reduto, entre os que têm ao menos
      ${ve.minMun} municípios rastreáveis:</p>
      <div class="rolagem"><table id="tcruz"></table></div>` : ""}`;

  if (ve.escada && ve.escada.length) tabela(document.getElementById("tescada"),
    ["Mín. de municípios","Deputados","No reduto","Base","Excesso","Ponderado por R$","Positivo"],
    ve.escada.map(e => [e.minMun, num(e.n), pct(e.obs,1), pct(e.nulo,1),
      (e.exc>=0?"+":"")+dec(e.exc,1)+" pp", (e.pond>=0?"+":"")+dec(e.pond,1)+" pp",
      pct(e.acima/e.n*100,0)]));

  if (firmes.length) tabela(document.getElementById("tcruz"),
    ["Deputado(a)","Pleito","Reduto","No reduto","Base","Excesso","Munic.","Rastreado"],
    firmes.slice(0,12).map(d => [
      `${esc(d.n)} <span style="color:var(--ink-3)">${esc(d.p)}</span>`,
      d.ano, esc(d.reduto), pct(d.obs,0), pct(d.nulo,0),
      (d.exc>=0?"+":"")+dec(d.exc,0)+" pp", d.nm,
      d.cob == null ? "—" : pct(d.cob,1)]));
}

/* ---------- sumário ----------
   Montado a partir dos <h2> que a aba acabou de desenhar, e não de uma lista
   escrita à mão: as abas trocam de conteúdo conforme estado, ano e autor, e um
   índice fixo ficaria mentindo assim que uma seção sumisse. */
function montarSumario(vista) {
  const ol = document.getElementById("sum-" + vista);
  const cx = document.querySelector("#v-" + vista + " .conteudo");
  if (!ol || !cx) return;
  const titulos = [...cx.querySelectorAll(".cartaz > h2")]
    .filter(h => !h.parentElement.classList.contains("oculto")
                 && h.parentElement.offsetParent !== null);
  ol.innerHTML = titulos.map((h, i) => {
    h.id = h.id || `s-${vista}-${i}`;
    return `<li><button data-alvo="${h.id}">${esc(h.textContent)}</button></li>`;
  }).join("");
  if (ol.dataset.ligado) return;
  ol.dataset.ligado = "1";
  ol.addEventListener("click", e => {
    const b = e.target.closest("button[data-alvo]");
    if (!b) return;
    rolarAte(document.getElementById(b.dataset.alvo));
  });
}

/* Rolagem própria em vez de scrollIntoView({behavior:"smooth"}).
   Motivo medido, não preferência: dependendo de como a página é servida, quem
   rola é o <body> e não o <html>, e o smooth sobre o body simplesmente não
   acontece — o clique não saía do lugar. Aqui calculamos o destino, tentamos
   rolar e conferimos se saiu; se não saiu, empurramos os dois elementos na mão.
   E respeitamos prefers-reduced-motion, que é o único caso em que não animar
   é o comportamento certo. */
function rolarAte(alvo) {
  if (!alvo) return;
  const topo = () => window.pageYOffset || document.documentElement.scrollTop
                     || document.body.scrollTop || 0;
  const antes = topo();
  const y = Math.max(0, alvo.getBoundingClientRect().top + antes - 12);
  const suave = !matchMedia("(prefers-reduced-motion: reduce)").matches;
  try { window.scrollTo({top: y, behavior: suave ? "smooth" : "auto"}); }
  catch (_) { window.scrollTo(0, y); }
  setTimeout(() => {
    if (Math.abs(topo() - antes) < 2 && Math.abs(y - antes) > 2) {
      document.documentElement.scrollTop = y;
      document.body.scrollTop = y;
    }
  }, 60);
}

/* Marca no sumário a seção que está sendo lida. Um índice sem posição atual
   diz para onde ir e não diz onde se está, que é metade do serviço. */
const observador = "IntersectionObserver" in window
  ? new IntersectionObserver(entradas => {
      for (const en of entradas) {
        if (!en.isIntersecting) continue;
        const b = document.querySelector(`.sumario button[data-alvo="${en.target.id}"]`);
        if (!b) continue;
        for (const o of b.closest("ol").querySelectorAll("button"))
          o.removeAttribute("aria-current");
        b.setAttribute("aria-current", "true");
      }
    }, {rootMargin: "-10% 0px -75% 0px"})
  : null;

function observarSecoes(vista) {
  if (!observador) return;
  observador.disconnect();
  const cx = document.querySelector("#v-" + vista + " .conteudo");
  if (cx) for (const h of cx.querySelectorAll(".cartaz > h2"))
    if (!h.parentElement.classList.contains("oculto")) observador.observe(h);
}

/* ---------- Sobre ----------
   Conteúdo fixo, e de propósito: é a única aba que não depende de estado nem de
   ano. Escrita aqui, no gerador, e não num arquivo à parte, porque cada número
   citado tem de sair do mesmo lugar que a tela usa — se o pipeline mudar e o
   texto ficar, o texto vira mentira antiga. */
function pintarSobre() {
  const alvo = document.getElementById("sobre");
  const nUF = D.ufs.length;
  const nMun = Object.values(D.estados).reduce((s,e) => s + e.m.length, 0);
  const c = D.emendasBR ? D.emendasBR.cobertura : null;
  const bi = v => "R$ " + dec(v/1e9, 1) + " bi";

  alvo.innerHTML = `
  <div class="cartaz">
    <h2>O que é isto</h2>
    <p class="cap"><strong>Cadê o Voto?</strong> é um produto da
      <strong>Lastro — Inteligência Política</strong>. Ele mostra onde cada
      candidato tirou voto, município a município, e para onde cada parlamentar
      mandou emenda — e cruza as duas coisas.</p>
    <p class="cap">São ${num(nUF)} unidades da federação, ${num(nMun)} municípios,
      sete pleitos de 1998 a 2022 no voto, e doze exercícios de 2015 a 2026 na
      emenda. Todo dado é público. Nada aqui é estimativa, projeção ou pesquisa
      de intenção: é apuração e execução orçamentária, como os órgãos
      publicaram.</p>
    <div class="nota">
      <strong>O que fazemos não é achar o dado — é fazer o dado não mentir.</strong>
      Os arquivos são abertos e qualquer um baixa. O trabalho está nas armadilhas
      que eles contêm, e é sobre elas que esta página fala. Todo número publicado
      sai de um script que está no repositório; se uma afirmação não é
      reproduzível, ela não entra.
    </div>
  </div>

  <div class="cartaz">
    <h2>De onde vem cada número</h2>
    <div class="rolagem"><table id="t-fontes"></table></div>
    <p class="cap" style="margin-top:10px">O CDN do TSE recusa cliente HTTP
      comum, requisição <span class="num">HEAD</span> e requisição com
      <span class="num">Range</span>. Só passa em GET simples com o conjunto
      completo de cabeçalhos de navegador — descobrir isso foi o primeiro dia
      de trabalho, e está documentado para não ser redescoberto.</p>
  </div>

  <div class="cartaz">
    <h2>Como o voto é contado</h2>
    <p class="cap">Votos <strong>nominais</strong>, de <strong>1º turno</strong>,
      agregados de zona eleitoral para município. Nominal exclui voto de legenda,
      branco e nulo. O 1º turno é onde está a disputa territorial: no segundo
      sobram dois nomes.</p>
    <ul class="lista-fatos">
      <li><strong>A coluna de votos muda ao longo da série.</strong> Em 1998 o
        campo <span class="num">QT_VOTOS_NOMINAIS</span> vem zerado; em 2002 não
        existe a coluna de válidos. A escolha é resolvida por soma, ano a ano,
        nunca por regra fixa.</li>
      <li><strong>"MÉDIA" é eleito.</strong> Quem entra pela média das sobras tem
        situação diferente de quem entra pelo quociente. Tratar só
        <em>"ELEITO"</em> dava 35 a 38 cadeiras numa assembleia de 41.</li>
      <li><strong>1998 tem registro duplicado.</strong> Quatro candidaturas
        aparecem com dois registros cada e votos contados duas vezes. Fica o
        registro deferido.</li>
      <li><strong>O código do candidato se repete entre anos.</strong> O mesmo
        <span class="num">SQ_CANDIDATO</span> pertence a pessoas diferentes em
        pleitos diferentes. A chave é o par (ano, código) — sem isso, um suplente
        de 2010 vazava para 2014.</li>
      <li><strong>Pessoa é pareada sem acento.</strong> A grafia do mesmo nome
        varia dentro do próprio arquivo do TSE. Corrigir isso levou a
        reincidência medida de 61% para 70,7%.</li>
    </ul>
  </div>

  <div class="cartaz">
    <h2>O pareamento com o IBGE, e os 23 milhões de votos</h2>
    <p class="cap">O TSE nomeia municípios; o IBGE também, e diferente. Quando o
      nome não casa, a linha é descartada — e o mapa fica com aparência de certo,
      porque o município apenas some do total sem que nada avise.</p>
    <p class="cap">Havia <strong>153 nomes órfãos e 23.063.701 votos</strong>
      fora do mapa. E o estrago não era num ano: <strong>era na linha do
      tempo</strong>. O TSE mudou a grafia ao longo da série — "MOJI GUAÇU"
      virou "MOGI GUAÇU" — então os pleitos antigos perdiam e os recentes não.</p>
    <div class="rolagem"><table id="t-perda"></table></div>
    <p class="cap" style="margin-top:10px">Uma série de concentração lida assim
      mostraria Pernambuco espalhando o voto ao longo de 24 anos por puro
      artefato de pareamento.</p>
    <div class="nota">
      <strong>Como os pares foram estabelecidos.</strong> Casar por semelhança de
      texto é perigoso: um par errado não perde voto, põe voto no município
      errado. O crivo veio do dado, não do texto — <em>duas grafias do mesmo
      lugar nunca dividem o mesmo pleito</em>. Isso reprovou propostas
      plausíveis e identificou o alvo certo de uma delas. Hoje são 163 correções
      manuais e restam <strong>47.535 votos</strong> sem par, em três municípios,
      todos só em 1998.
    </div>
  </div>

  <div class="cartaz">
    <h2>Como a emenda é contada</h2>
    <p class="cap">O valor é sempre o que <strong>saiu do caixa</strong> — pago
      no exercício mais restos a pagar efetivamente pagos. Nunca o empenhado, que
      é compromisso e não gasto: no país são
      ${c ? bi(308.6e9) : "R$ 308,6 bi"} empenhados contra
      ${c ? bi(259.5e9) : "R$ 259,5 bi"} pagos.</p>
    <ul class="lista-fatos">
      <li><strong>Só 10,5% do dinheiro chega a um município.</strong> Das emendas
        individuais, 76% do valor está declarado como <em>MÚLTIPLO</em> —
        espalhado por cidades que o arquivo não nomeia. Por UF a cobertura é
        97,1%, e é por isso que a leitura completa é estadual, não municipal.</li>
      <li><strong>Existe um atalho falso, e ele fica fechado.</strong> Há um
        arquivo por favorecido com município em 100% do dinheiro. Nele,
        <strong>Brasília concentra 36,4%</strong> das emendas individuais do
        país — porque é o endereço do Fundo Nacional de Saúde e dos
        intermediários. Seria um mapa completo e falso. O município aqui vem
        sempre da localidade de aplicação.</li>
      <li><strong>"Emenda Pix" é a Transferência Especial.</strong> Cai direto na
        conta do município, sem convênio, sem finalidade definida no orçamento e
        sem acompanhamento federal. São R$ 32,2 bi — 23% das individuais — e têm
        filtro próprio porque são o dinheiro sobre o qual se sabe menos.</li>
      <li><strong>O mapa abre acumulado.</strong> Num ano só, um estado mostra
        poucos municípios e o mapa sugere ausência de dinheiro onde há ausência
        de rastreabilidade. Somando 2015 a 2026, 69% dos municípios do país
        receberam alguma emenda rastreável.</li>
    </ul>
  </div>

  <div class="cartaz">
    <h2>Os índices, e quando eles não se comparam</h2>
    <p class="cap">Os mesmos índices valem para todo candidato, cargo e estado —
      é isso que permite comparar. Mas dois deles têm limite, e ignorá-lo produz
      leitura errada.</p>
    <div class="rolagem"><table id="t-indices"></table></div>
    <div class="nota" style="margin-top:12px">
      <strong>Municípios efetivos não se comparam entre estados.</strong> Roraima
      tem 15 municípios e Minas tem 853; um estado com 15 não pode ter 16
      efetivos. Por isso a <em>fração do estado</em> anda junto — é ela que é
      comparável. E <strong>semelhança de cosseno não se compara entre
      escalas</strong>: sobre 15 municípios ela é mecanicamente maior que sobre
      853. Serve para ordenar dentro de um estado e pleito, não entre estados.
    </div>
  </div>

  <div class="cartaz">
    <h2>O que não fazemos</h2>
    <ul class="lista-fatos">
      <li><strong>Não preenchemos lacuna com zero.</strong> Município sem dado
        aparece como sem dado. Zero e "não sei" são coisas diferentes, e
        confundi-las é como um mapa mente.</li>
      <li><strong>Não afrouxamos teste para ele passar.</strong> Quando um
        denominador não fechou com o painel de referência, a saída foi separar o
        que é verificável do que não é e publicar a divergência — não calibrar a
        tolerância até o verde aparecer.</li>
      <li><strong>Não chutamos pareamento.</strong> Um município goiano segue sem
        par porque "pode ser" outro não é evidência. Par errado põe dinheiro no
        lugar errado, que é pior que dinheiro sem lugar.</li>
      <li><strong>Não escondemos o denominador.</strong> Toda tela que mostra uma
        fatia diz de quanto ela é fatia.</li>
    </ul>
  </div>

  <div class="cartaz">
    <h2>Onde o juízo é nosso, e não do dado</h2>
    <p class="cap">Três camadas não saem de arquivo nenhum. São classificação
      editorial, discutível por natureza, e ficam em arquivos separados
      justamente para poderem ser contestadas sem tocar no código:</p>
    <ul class="lista-fatos">
      <li><strong>Linhagem partidária</strong> — 58 siglas reduzidas a 31
        linhagens. PFL vira DEM vira União Brasil. Sem isso a série de 24 anos se
        desfaz; com isso, some a informação de que houve fusão. As duas visões
        existem.</li>
      <li><strong>Espectro ideológico</strong> — 32 partidos em cinco faixas. É o
        que separa "aliado" de "adversário" na análise de rivais. Trocar o
        arquivo troca a leitura.</li>
      <li><strong>Os cortes da tipologia</strong> — concentração e domínio viram
        quatro perfis a partir de limiares que escolhemos, não que o TSE
        publicou.</li>
    </ul>
  </div>

  <div class="cartaz">
    <h2>Fale com a gente</h2>
    <p class="cap">Achou um número errado? É o tipo de mensagem que mais nos
      interessa. Todo número desta página sai de um script identificado, e uma
      correção que se confirme entra na próxima publicação com o motivo
      registrado.</p>
    <p class="cap"><strong>Lastro — Inteligência Política.</strong></p>
  </div>`;

  tabela(document.getElementById("t-fontes"),
    ["O quê","Fonte","Arquivo"],
    [["Voto, 1998–2022","Tribunal Superior Eleitoral, dados abertos",
      "votacao_candidato_munzona"],
     ["Emenda federal, 2015–2026","Portal da Transparência",
      "Emendas Parlamentares (arquivo único)"],
     ["Emenda estadual (piloto)","Dados abertos do estado",
      "Assembleia Legislativa, via SERINT em Goiás"],
     ["Malha municipal e estadual","IBGE","API de malhas"],
     ["População e área","IBGE","Censo 2022, agregado 4714"]]);

  tabela(document.getElementById("t-perda"),
    ["Pleito","Perda nacional","Pior estado"],
    [["1998","1,98%","Pernambuco, 8,9%"],
     ["2002","1,66%","Pernambuco, 10,0%"],
     ["2006","1,12%","Rondônia, 9,5%"],
     ["2010","0,44%","Rondônia, 9,4%"],
     ["2014","0,13%","Rondônia, 3,1%"],
     ["2018","0,14%","Rondônia, 2,9%"],
     ["2022","0,12%","Rondônia, 2,9%"]]);

  tabela(document.getElementById("t-indices"),
    ["Índice","O que mede","Cuidado"],
    [["Municípios efetivos","Equivale a concentrar tudo nesse tanto de municípios iguais (1/HHI)","Limitado pelo tamanho do estado"],
     ["Fração do estado","Municípios efetivos sobre o total do estado","É o número comparável entre UFs"],
     ["Domínio médio","Fatia do candidato onde ele tem voto","—"],
     ["Contiguidade","Voto no reduto e nos municípios que fazem fronteira","Vem da malha completa, não da simplificada"],
     ["Gini municipal","0 = espalhado por igual, 1 = tudo num lugar","—"],
     ["Semelhança (cosseno)","Quanto dois mapas têm o mesmo formato","Não se compara entre estados de portes diferentes"]]);
}

/* ---------- piloto: consumindo a API da ALEGO ----------
   A aba API cataloga quem publica. Esta seção mostra o que sai quando se
   consome de fato — e serve de prova de que o catálogo não é teórico. */
function secaoPiloto() {
  const v = (D.estados.GO || {}).vb;
  if (!v) return "";
  const t = v.total;
  const pctG = t.apresentado > 0 ? t.glosa / t.apresentado * 100 : 0;
  const mil = reais;
  const teto = v.deputados.filter(d => d.ms >= 60);
  const medias = teto.map(d => d.m).sort((a,b)=>a-b);
  const mediana = medias.length ? medias[Math.floor(medias.length/2)] : 0;
  const faixa = medias.length ? [medias[0], medias[medias.length-1]] : [0,0];

  return `
  <div class="cartaz">
    <h2>Piloto: a API da ALEGO, consumida</h2>
    <p class="cap">Catalogar quem publica é metade do trabalho. Esta seção
      consome de fato um dos dezesseis assuntos da API de Goiás — a
      <strong>verba indenizatória</strong>, o reembolso de despesa de gabinete
      de cada deputado, mês a mês, de ${v.periodo[0]} a ${v.periodo[1]}.</p>
    <div class="indices">
      ${ind("Apresentado", mil(t.apresentado), "o que os gabinetes pediram")}
      ${ind("Indenizado", mil(t.indenizado), "o que a Casa pagou")}
      ${ind("Glosado", pct(pctG, 2), mil(t.glosa) + " recusados")}
      ${ind("Deputados", num(t.nDeputados), `${t.nCasados} casam com eleito à ALEGO`)}
    </div>
    <div class="nota" style="margin-top:14px">
      <strong>Verba indenizatória não é salário nem emenda.</strong> É custeio de
      gabinete, pago pela própria Assembleia. Somar com emenda seria misturar o
      orçamento do Executivo com reembolso da Casa — naturezas diferentes, contas
      separadas.
    </div>
  </div>

  <div class="cartaz">
    <h2>Dois achados que saem de uma subtração</h2>
    <p class="cap">Nenhum dos dois é publicado como indicador em lugar nenhum.
      Os dois saem de comparar duas colunas que a API já entrega.</p>
    <ul class="lista-fatos">
      <li><strong>Quase nada é recusado: ${pct(pctG, 2)} do apresentado.</strong>
        De ${mil(t.apresentado)} pedidos, ${mil(t.glosa)} foram glosados. A
        diferença entre <em>apresentado</em> e <em>indenizado</em> mede decisão
        administrativa, e a decisão é praticamente sempre aprovar.</li>
      <li><strong>Todo mundo usa o teto.</strong> Entre os ${num(teto.length)}
        deputados com cinco anos ou mais de série, a média mensal fica entre
        ${mil(faixa[0])} e ${mil(faixa[1])}, com mediana de
        <span class="num">${mil(mediana)}</span>. Não há quem gaste pouco: a
        verba é usada como piso, não como limite.</li>
      <li><strong>E isso muda o que a pergunta "quem gasta mais" significa.</strong>
        Se todos batem no teto, ordenar por valor total ordena por tempo de
        mandato, não por comportamento. O que distingue é a glosa — e ela é
        rara o bastante para que os poucos casos mereçam olhar.</li>
    </ul>
  </div>

  <div class="cartaz">
    <h2>Por deputado</h2>
    <p class="cap">Ordenado pelo total indenizado no período. O ponto marca quem
      casa com um eleito à ALEGO nos pleitos que temos.</p>
    <div class="rolagem"><table id="t-verbas"></table></div>
    <p class="cap" style="margin-top:10px">Cobertura: 91 dos 96 meses entre
      ${v.periodo[0]} e ${v.periodo[1]} responderam. A primeira varredura trouxe
      só 37 — as requisições que falhavam eram lidas como ausência de dado, e
      dois anos inteiros apareciam vazios. Com três tentativas por mês, o dado
      apareceu.</p>
  </div>`;
}

function tabelaPiloto() {
  const v = (D.estados.GO || {}).vb;
  const el = document.getElementById("t-verbas");
  if (!v || !el) return;
  tabela(el, ["Deputado(a)","Indenizado","Média mensal","Glosado","Meses"],
    v.deputados.slice(0, 20).map(d => [
      esc(d.n) + (d.el ? ' <span style="color:var(--accent)">●</span>' : ""),
      reais(d.t), reais(d.m), pct(d.pg, 2), d.ms]));
}

/* ---------- API: o que as assembleias publicam ----------
   Levantamento próprio. Não existe catálogo público de quais assembleias
   legislativas estaduais oferecem dado aberto, e a resposta importa para este
   projeto: foi procurando emenda estadual que a pergunta apareceu. */
function pintarApi() {
  const alvo = document.getElementById("api");
  const A = D.assembleias;
  if (!A) { alvo.innerHTML = `<p class="indice exp">Levantamento não publicado.</p>`; return; }
  const linhas = Object.entries(A).map(([uf, r]) => ({uf, ...r}));
  const comPortal = linhas.filter(r => r.n > 0);
  const confirmadas = linhas.filter(r => r.conf);
  const sem = linhas.filter(r => !r.n);

  alvo.innerHTML = `
  <div class="cartaz">
    <h2>Quais assembleias publicam dado aberto</h2>
    <p class="cap">Sondamos as 27 casas legislativas estaduais em agosto de
      2026, tentando os caminhos onde portais legislativos brasileiros
      costumam guardar dado aberto. Não existe catálogo público disso — este
      levantamento é nosso, e a pergunta apareceu procurando emenda estadual.</p>
    <div class="indices">
      ${ind("Casas sondadas", num(linhas.length), "as 26 assembleias e a Câmara Legislativa do DF")}
      ${ind("Com portal respondendo", num(comPortal.length), `de ${linhas.length}`)}
      ${ind("API confirmada à mão", num(confirmadas.length), "abertas uma a uma")}
      ${ind("Nada nos caminhos testados", num(sem.length), "o que não é prova de ausência")}
    </div>
    <div class="nota" style="margin-top:14px">
      <strong>Responder não é publicar, e publicar não é publicar o que importa.</strong>
      A sonda mede a existência da porta, não o que há atrás dela. Goiás tem API
      documentada com dezesseis assuntos e <em>nenhum</em> é emenda parlamentar —
      só se descobre abrindo. Da mesma forma, "nada nos caminhos testados" quer
      dizer que não achamos, não que não exista.
    </div>
  </div>

  <div class="cartaz">
    <h2>Casa por casa</h2>
    <p class="cap">Endereço onde o dado apareceu, quando apareceu. As linhas com
      observação foram abertas manualmente.</p>
    <div class="rolagem"><table id="t-casas"></table></div>
  </div>

  <div class="cartaz">
    <h2>O que elas publicam — e o que nenhuma publica</h2>
    <p class="cap">Abrindo as que respondem, o padrão é nítido e vale mais que a
      contagem.</p>
    <ul class="lista-fatos">
      <li><strong>A assembleia publica a si mesma.</strong> Os assuntos que
        aparecem são folha de pagamento, diárias, verbas indenizatórias,
        licitações, contratos, convênios e a execução do próprio orçamento da
        Casa. É a assembleia como empregadora e compradora.</li>
      <li><strong>Nenhuma publica emenda parlamentar.</strong> Em Goiás, os
        dezesseis assuntos da API não incluem emenda; os endereços plausíveis
        (<span class="num">emendas</span>,
        <span class="num">emendas-parlamentares</span>,
        <span class="num">indicacoes</span>) devolvem 404. Em Minas, a vitrine do
        portal não menciona emenda.</li>
      <li><strong>E isso é coerência institucional, não omissão.</strong> A
        emenda é indicação de deputado sobre o orçamento do <em>Executivo</em>, e
        quem a executa são as secretarias. O dado nasce do outro lado — por isso
        o Emendômetro estadual sai de portais do governo do estado, não das
        assembleias.</li>
      <li><strong>O legislativo é mais opaco que o executivo nesse recorte.</strong>
        Dos portais do Executivo, cinco tinham conjunto de emenda em formato
        tabular. Das assembleias, nenhuma.</li>
    </ul>
  </div>

  ${secaoPiloto()}

  <div class="cartaz">
    <h2>O que dá para fazer com isso</h2>
    <p class="cap">O levantamento não entrega emenda, mas entrega outra coisa —
      e vale dizer o que, para não parecer que foi trabalho perdido.</p>
    <ul class="lista-fatos">
      <li><strong>Custo de gasto legislativo comparado.</strong> Folha, diárias e
        verba indenizatória por deputado são publicados por várias casas no mesmo
        formato conceitual. Dá para comparar quanto custa um deputado estadual
        entre estados — que ninguém compila. <em>O piloto acima já fez isso para
        Goiás; falta repetir onde houver API.</em></li>
      <li><strong>Um mapa de transparência com método.</strong> Dezenove de 27
        respondem alguma coisa; quatro têm API confirmada. Esse número é aferível
        e repetível, ao contrário dos selos de transparência que circulam sem
        critério publicado.</li>
      <li><strong>A confirmação de onde procurar.</strong> Quem for atrás de
        emenda estadual em qualquer estado sabe agora que a assembleia não é o
        caminho, e economiza o dia que gastamos descobrindo.</li>
    </ul>
    <div class="nota" style="margin-top:12px">
      <strong>Feito em 2026-08-23.</strong> Portal muda de endereço e de conteúdo;
      um levantamento assim envelhece. O script que o produziu está no
      repositório e pode ser rodado de novo — é a data que dá validade ao número,
      não a nossa palavra.
    </div>
  </div>`;

  tabelaPiloto();
  tabela(document.getElementById("t-casas"),
    ["UF","Casa","Situação","Onde","Observação"],
    linhas.sort((a,b) => (b.conf - a.conf) || (b.n - a.n) || a.uf.localeCompare(b.uf))
      .map(r => [r.uf, esc(r.sigla),
        r.conf ? '<span style="color:var(--accent)">●</span> API confirmada'
               : r.n ? "portal responde" : "nada nos caminhos testados",
        r.url ? `<span class="num">${esc(r.url.replace(/^https?:\/\//,"").slice(0,44))}</span>` : "—",
        esc(r.obs || "")]));
}

/* ---------- navegação ---------- */
function irPara(v) { vista = v; render(); }

const VISTAS = ["nacional","estado","padroes","cruzamentos","emendas","api","sobre"];
const SUB = {
  nacional: "Distribuição espacial do voto para deputado estadual em cada unidade da federação, de 1998 a 2022, município a município.",
  estado: "Onde cada deputado estadual eleito tirou voto, município a município, de 1998 a 2022.",
  padroes: "O que muda na geografia do voto ao longo de sete pleitos, e que tipo de deputado o estado elege.",
  cruzamentos: "Como os cinco cargos se relacionam no mesmo território, e o que anda junto entre eles.",
  emendas: "Para onde cada parlamentar mandou emenda individual, de 2015 a 2026 — e quanto disso dá para rastrear até o município.",
  api: "Quais das 27 assembleias legislativas estaduais publicam dado aberto — levantamento próprio, porque não existe catálogo.",
  sobre: "De onde vem cada número, como ele é contado, e as armadilhas do dado público que este trabalho existe para desarmar.",
};

function render() {
  for (const v of VISTAS)
    document.getElementById("v-"+v).classList.toggle("oculto", v !== vista);
  for (const b of document.querySelectorAll("#abas button"))
    b.setAttribute("aria-selected", String(b.dataset.v === vista));

  /* O título só nomeia o estado quando o que está na tela é de um estado. */
  const semEstado = vista === "nacional" || vista === "sobre" || vista === "api";
  document.getElementById("titulo").textContent = semEstado
    ? "Cadê o Voto?" : `Cadê o Voto ${PREP[uf]||"em"} ${nomeUF.get(uf)||uf}?`;
  document.title = document.getElementById("titulo").textContent;
  document.getElementById("sub").textContent = SUB[vista];
  document.getElementById("atual").textContent =
    `${nomeUF.get(uf)||uf} · ${num(D.estados[uf].m.length)} municípios`;
  const g = document.getElementById("gaveta");
  g.classList.toggle("oculto", semEstado);
  if (semEstado) g.open = false;
  for (const b of document.querySelectorAll("#estados button"))
    b.setAttribute("aria-pressed", String(b.dataset.uf === uf));

  gravarHash();
  ({nacional: pintarNacional, estado: pintarEstado, padroes: pintarPadroes,
    cruzamentos: pintarCruzamentos, emendas: pintarEmendas,
    api: pintarApi, sobre: pintarSobre}[vista])();
  montarSumario(vista);
  observarSecoes(vista);
  esconderDica();
}

document.getElementById("abas").addEventListener("click", e => {
  const b = e.target.closest("button[data-v]");
  if (b) irPara(b.dataset.v);
});

document.getElementById("estados").innerHTML = D.ufs
  .filter(u => Object.keys(D.estados[u.s].a).length)
  .map(u => `<button data-uf="${u.s}"><span>${esc(u.n)}</span>` +
    `<span class="sg">${u.s}</span></button>`).join("");
document.getElementById("estados").addEventListener("click", e => {
  const b = e.target.closest("button[data-uf]");
  if (!b) return;
  trocarUF(b.dataset.uf);
  document.getElementById("gaveta").open = false;
});

document.getElementById("anos").innerHTML = D.anos
  .map(a => `<button data-a="${a}">${a}</button>`).join("");
document.getElementById("anos").addEventListener("click", e => {
  const b = e.target.closest("button[data-a]");
  if (!b) return;
  ano = +b.dataset.a; sel = 0;
  for (const x of document.querySelectorAll("#anos button"))
    x.setAttribute("aria-pressed", String(+x.dataset.a === ano));
  render();
});

lerHash();
for (const x of document.querySelectorAll("#anos button"))
  x.setAttribute("aria-pressed", String(+x.dataset.a === ano));
render();
</script>
"""


def main():
    css = (APP / "src" / "estilos" / "tokens.css").read_text(encoding="utf-8")
    dados = montar_dados()
    html = PAGINA
    for marca, valor in (
        ("@CSS@", css),
        ("@LOGO@", logo_do_componente()),
        ("@FONTES@", FONTES),
        ("@DADOS@", json.dumps(dados, separators=(",", ":"), ensure_ascii=False)),
    ):
        html = html.replace(marca, valor)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(html, encoding="utf-8")
    mb = SAIDA.stat().st_size / 1024 / 1024
    com_dado = sum(1 for u in dados["estados"].values() if u["a"])
    print(f"{SAIDA.name}: {mb:.1f} MB")
    print(f"  {com_dado} estados com deputado estadual, {len(dados['anos'])} pleitos")
    print(f"  {sum(len(u['m']) for u in dados['estados'].values()):,} municípios")
    if mb > TETO_MB:
        raise SystemExit(f"passou do teto de {TETO_MB} MB do artefato")


if __name__ == "__main__":
    main()
