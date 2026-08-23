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
                       "p": ler("padroes.json"), "c": ler("cruzamentos.json")}
    return {
        "anos": indice["anos"],
        "ufs": indice["ufs"],
        "agregado": indice["agregado"],
        # a malha do Brasil vira anéis também: uma projeção só serve as duas telas
        "malhaBR": [{"cod": f["cod"], "g": aneis(f["geom"])}
                    for f in indice["malhaUF"]],
        "estados": estados,
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

  <details class="gaveta" id="gaveta">
    <summary><span class="seta">&#9656;</span> Qual seu estado?
      <span class="atual" id="atual"></span></summary>
    <div class="estados" id="estados"></div>
  </details>

  <div class="abas" role="tablist" id="abas">
    <button role="tab" data-v="nacional" aria-selected="true">Nacional</button>
    <button role="tab" data-v="estado" aria-selected="false">Estado</button>
    <button role="tab" data-v="padroes" aria-selected="false">Padrões</button>
    <button role="tab" data-v="cruzamentos" aria-selected="false">Cruzamentos</button>
  </div>
</div></div>

<main class="wrap">
  <div id="v-nacional">
    <div class="painel" style="grid-template-columns:1fr">
      <div class="conteudo">
        <div class="cartaz">
          <h2>Concentração do voto por estado</h2>
          <p class="cap">Cada estado colorido pela <strong>fração dos seus
            municípios</strong> que a votação mediana dos eleitos efetivamente
            ocupa. <span style="color:var(--s1)">&#9632;</span> vermelho = voto
            concentrado em poucos municípios;
            <span style="color:var(--s5)">&#9632;</span> verde = espalhado pelo
            estado. <strong>Clique num estado para abrir a tela dele.</strong></p>
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
      </aside>
      <div class="conteudo" id="detalhe"></div>
    </div>
  </div>

  <div id="v-padroes" class="oculto"><div class="conteudo" id="padroes"
       style="padding:20px 0 40px"></div></div>
  <div id="v-cruzamentos" class="oculto"><div class="conteudo" id="cruzamentos"
       style="padding:20px 0 40px"></div></div>
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
  return {L, H: Math.max(120, Math.round((y1-y0)*e)),
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
  }, i => { const s = SIG_BR[i]; if (m.has(s)) { uf = s; sel = 0; irPara("estado"); } });

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
  if (b) { uf = b.dataset.uf; sel = 0; irPara("estado"); }
});

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
    "</svg>";

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
  sel = +b.dataset.i; gravarHash(); pintarEstado();
});
document.getElementById("busca").addEventListener("input", e => {
  filtro = e.target.value; sel = 0; pintarEstado();
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
        +  `<text x="${ml-6}" y="${py(v)+3}" text-anchor="end" font-size="10" fill="var(--ink-3)" font-family="IBM Plex Mono, monospace">${v.toFixed(casas)}</text>`;
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

/* ---------- navegação ---------- */
function irPara(v) { vista = v; render(); }

const VISTAS = ["nacional","estado","padroes","cruzamentos"];
const SUB = {
  nacional: "Distribuição espacial do voto para deputado estadual em cada unidade da federação, de 1998 a 2022, município a município.",
  estado: "Onde cada deputado estadual eleito tirou voto, município a município, de 1998 a 2022.",
  padroes: "O que muda na geografia do voto ao longo de sete pleitos, e que tipo de deputado o estado elege.",
  cruzamentos: "Como os cinco cargos se relacionam no mesmo território, e o que anda junto entre eles.",
};

function render() {
  for (const v of VISTAS)
    document.getElementById("v-"+v).classList.toggle("oculto", v !== vista);
  for (const b of document.querySelectorAll("#abas button"))
    b.setAttribute("aria-selected", String(b.dataset.v === vista));

  /* O título só nomeia o estado quando o que está na tela é de um estado. */
  document.getElementById("titulo").textContent = vista === "nacional"
    ? "Cadê o Voto?" : `Cadê o Voto ${PREP[uf]||"em"} ${nomeUF.get(uf)||uf}?`;
  document.title = document.getElementById("titulo").textContent;
  document.getElementById("sub").textContent = SUB[vista];
  document.getElementById("atual").textContent =
    `${nomeUF.get(uf)||uf} · ${num(D.estados[uf].m.length)} municípios`;
  for (const b of document.querySelectorAll("#estados button"))
    b.setAttribute("aria-pressed", String(b.dataset.uf === uf));

  gravarHash();
  ({nacional: pintarNacional, estado: pintarEstado,
    padroes: pintarPadroes, cruzamentos: pintarCruzamentos}[vista])();
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
  uf = b.dataset.uf; sel = 0; filtro = ""; document.getElementById("busca").value = "";
  document.getElementById("gaveta").open = false;
  irPara("estado");
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
