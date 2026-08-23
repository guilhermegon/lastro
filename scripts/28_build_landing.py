"""Monta `dist/cade_o_voto.html`: a tela nacional, sozinha e autocontida.

Por que existe, ja que o app React ja tem essa tela: o app serve 80 MB de dados
por requisicao sob demanda, e isso precisa de hospedagem. A tela nacional, nao -
ela consome so o `indice.json`, 96 KB, e por isso cabe inteira num arquivo unico
que se abre em qualquer lugar e se manda por link.

O que fica de fora e' o detalhe por estado: eleito, mapa municipal, rivais,
vereador. Isso e' o app.

A folha de estilo e a marca vem dos mesmos arquivos que o app usa, para que as
duas telas nao divirjam com o tempo.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

APP = cfg.ROOT / "app"
SAIDA = cfg.ROOT / "dist" / "cade_o_voto.html"
FONTES = ("https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700"
          "&family=IBM+Plex+Mono:wght@400;500"
          "&family=IBM+Plex+Sans:wght@400;500;600&display=swap")

PAGINA = """<title>Cadê o Voto?</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="@FONTES@">
<style>
@CSS@
.wrap { max-width: 1180px; margin: 0 auto; padding: 0 20px; }
.topo-in { display: flex; justify-content: space-between; align-items: flex-start;
  gap: 20px; flex-wrap: wrap; padding: 22px 0 16px; }
.marca p { color: var(--ink-2); font-size: var(--step--1); margin: 6px 0 0;
  max-width: 46ch; }
.ligacao { background: none; border: 0; padding: 0; font: inherit;
  color: var(--accent); text-align: left; }
.tabelas { display: grid; gap: 18px; }
svg .mun { stroke: var(--surface); stroke-width: .6; }
footer { color: var(--ink-3); font-size: var(--step--1); padding: 26px 0 40px; }
footer p { margin: 0 0 8px; }
</style>

<div class="topo"><div class="wrap"><div class="topo-in">
  <div class="marca">
    @LOGO@
    <h1>Cadê o Voto?</h1>
    <p>Distribuição espacial do voto para deputado estadual em cada unidade da
       federação, de 1998 a 2022, município a município.</p>
  </div>
  <div class="seg" role="group" aria-label="Pleito" id="anos"></div>
</div></div></div>

<main class="wrap">
  <div class="cartaz">
    <h2>Concentração do voto por estado</h2>
    <p class="cap">Cada estado colorido pela <strong>fração dos seus
      municípios</strong> que a votação mediana dos eleitos efetivamente ocupa.
      <span style="color:var(--s1)">&#9632;</span> vermelho = voto concentrado em
      poucos municípios; <span style="color:var(--s5)">&#9632;</span> verde =
      espalhado pelo estado.</p>
    <div id="mapa"></div>
    <div class="legenda" id="legenda"></div>
    <div class="rolagem" style="margin-top:16px"><table id="tconc"></table></div>
    <div class="nota" style="margin-top:14px">
      <strong>Municípios efetivos não se comparam entre estados sem cuidado.</strong>
      Roraima tem 15 municípios e Minas tem 853 — um estado com 15 não pode ter 16
      municípios efetivos. O índice está limitado pelo tamanho do estado. Por isso
      a tabela traz também a <em>fração</em> do estado efetivamente usada, que é
      comparável, e o mapa colore por ela.
    </div>
    <p class="cap">O Distrito Federal fica sem cor: elege deputado distrital, não
      estadual. São 26 unidades.</p>
  </div>

  <div class="cartaz">
    <h2>O preço da cadeira em cada estado</h2>
    <p class="cap">Total de votos nominais dividido pelas cadeiras, e a votação do
      último eleito — o corte real de entrada na assembleia. Ordenado pelo corte.</p>
    <div class="rolagem"><table id="tpreco"></table></div>
  </div>
</main>

<footer class="wrap">
  <p><strong>Lastro — Inteligência Política.</strong> Fonte: Tribunal Superior
     Eleitoral, dados abertos, arquivo
     <span class="num">votacao_candidato_munzona</span>, 1º turno. Malha
     municipal e estadual: IBGE.</p>
  <p>Esta página é o comparativo nacional. O detalhe de cada estado — eleito por
     eleito, mapa municipal, rivais territoriais, câmara da capital — está no
     aplicativo, que carrega os dados sob demanda.</p>
  <p>O pareamento entre os nomes de município do TSE e a malha do IBGE tem 159
     correções manuais; 47.535 votos de 1998, em três municípios, seguem sem par
     e estão fora destes números.</p>
</footer>

<script>
const D = @DADOS@;
const RAMPA = ["--s1","--s2","--s3","--s4","--s5"];
const COD = {"11":"RO","12":"AC","13":"AM","14":"RR","15":"PA","16":"AP",
 "17":"TO","21":"MA","22":"PI","23":"CE","24":"RN","25":"PB","26":"PE",
 "27":"AL","28":"SE","29":"BA","31":"MG","32":"ES","33":"RJ","35":"SP",
 "41":"PR","42":"SC","43":"RS","50":"MS","51":"MT","52":"GO","53":"DF"};
const nome = new Map(D.ufs.map(u => [u.s, u.n]));
const num = v => v.toLocaleString("pt-BR");
const dec = (v,n) => v.toLocaleString("pt-BR",{minimumFractionDigits:n,maximumFractionDigits:n});
const pct = (v,n=2) => dec(v,n) + "%";

/* Equirretangular com correcao de longitude por cos(latitude media). Sem o
   cosseno, os estados do Norte ficam esticados na horizontal. */
function projetar(feicoes, L=760) {
  const aneis = feicoes.map(f => {
    const ps = f.geom.type === "Polygon" ? [f.geom.coordinates] : f.geom.coordinates;
    return ps.map(p => p[0]);
  });
  let x0=1/0,x1=-1/0,y0=1/0,y1=-1/0;
  for (const f of aneis) for (const a of f) for (const [x,y] of a) {
    if(x<x0)x0=x; if(x>x1)x1=x; if(y<y0)y0=y; if(y>y1)y1=y; }
  const k = Math.cos((y0+y1)/2*Math.PI/180), e = L/((x1-x0)*k||1);
  const H = Math.round((y1-y0)*e);
  return {H, L, d: aneis.map(f => f.map(a => "M"+a.map(([x,y]) =>
    ((x-x0)*k*e).toFixed(1)+","+((y1-y)*e).toFixed(1)).join("L")+"Z").join(" "))};
}
const PROJ = projetar(D.malhaUF);

/* Quantis, e nao faixas fixas: com faixas iguais quase todo estado cai na
   classe de baixo e o mapa vira monocromatico. */
function quantis(v, n=5) {
  const s = v.filter(x=>x>0).sort((a,b)=>a-b);
  if (!s.length) return [1,2,3,4,5];
  return Array.from({length:n}, (_,i) =>
    s[Math.min(s.length-1, Math.ceil(s.length*(i+1)/n)-1)]);
}
const faixa = (v,c) => { if(!(v>0)) return -1;
  for(let i=0;i<c.length;i++) if(v<=c[i]) return i; return c.length-1; };

let ano = D.anos[D.anos.length-1];

function desenhar() {
  const m = new Map();
  for (const a of D.agregado) if (a.ano === ano) m.set(a.uf, a);
  const sig = D.malhaUF.map(f => COD[f.cod] || f.cod);
  const val = sig.map(s => (m.get(s)||{}).fr || 0);
  const c = quantis(val);

  document.getElementById("mapa").innerHTML =
    `<svg viewBox="0 0 ${PROJ.L} ${PROJ.H}" role="img" aria-label="Fração do estado ocupada pelo voto">` +
    PROJ.d.map((d,i) => {
      const f = faixa(val[i], c);
      const t = f<0 ? "--sem-voto" : RAMPA[Math.min(f,4)];
      const s = sig[i], u = m.get(s);
      const tit = u ? `${u2(s)}: ${pct(val[i],1)} do estado, ${dec(u.ef||0,1)} de ${num(u.nmun)} municípios`
                    : `${u2(s)}: elege deputado distrital, não estadual`;
      return `<path d="${d}" class="mun" fill="var(${t})"><title>${tit}</title></path>`;
    }).join("") + "</svg>";

  document.getElementById("legenda").innerHTML =
    `<span class="item"><span class="swatch" style="background:var(--sem-voto)"></span>Sem deputado estadual</span>` +
    c.map((v,i) => `<span class="item"><span class="swatch" style="background:var(${RAMPA[i]})"></span>` +
      (i===0 ? "até "+pct(v,1) : pct(c[i-1],1)+" a "+pct(v,1)) + "</span>").join("");

  const linhas = [...m.values()].map(a => ({...a, nome: nome.get(a.uf)||a.uf}));
  tabela("tconc", ["Estado","Munic.","Cadeiras","Mun. efetivos","Fração do estado","Maior município"],
    linhas.sort((a,b)=>(b.fr||0)-(a.fr||0)).map(d => [d.nome, num(d.nmun), d.cad,
      dec(d.ef||0,1), pct(d.fr||0,1), pct(d.t1||0,1)]));
  tabela("tpreco", ["Estado","Nominais","Cadeiras","Quociente","Último eleito","Candidatos","Por cadeira"],
    linhas.slice().sort((a,b)=>b.ult-a.ult).map(d => [d.nome, num(d.tot), d.cad,
      num(Math.round(d.qe)), num(d.ult), num(d.cand), dec(d.cand/Math.max(d.cad,1),1)]));
}
const u2 = s => nome.get(s) || s;

function tabela(id, cab, linhas) {
  document.getElementById(id).innerHTML =
    "<thead><tr>" + cab.map(h=>`<th>${h}</th>`).join("") + "</tr></thead><tbody>" +
    linhas.map(r => "<tr>" + r.map((v,i) =>
      i===0 ? `<td>${v}</td>` : `<td class="n">${v}</td>`).join("") + "</tr>").join("") +
    "</tbody>";
}

document.getElementById("anos").innerHTML =
  D.anos.map(a => `<button data-a="${a}"${a===ano?' aria-pressed="true"':''}>${a}</button>`).join("");
document.getElementById("anos").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  ano = +b.dataset.a;
  for (const x of document.querySelectorAll("#anos button"))
    x.setAttribute("aria-pressed", String(+x.dataset.a === ano));
  desenhar();
});
desenhar();
</script>
"""


def main():
    css = (APP / "src" / "estilos" / "tokens.css").read_text(encoding="utf-8")
    logo = (cfg.ROOT / "dist" / "logo-lastro-marca.svg").read_text(encoding="utf-8")
    logo = logo.split("?>")[-1].strip()          # sai a declaracao XML
    dados = json.loads((APP / "public" / "dados" / "indice.json")
                       .read_text(encoding="utf-8"))
    # so' o que a tela nacional usa; as fichas por estado ficam no app
    enxuto = {"anos": dados["anos"], "ufs": dados["ufs"],
              "agregado": dados["agregado"], "malhaUF": dados["malhaUF"]}

    # substituicao por marcador, e nao %-formatting: o CSS e o JS estao cheios
    # de "%" literais ("100%", "fração 5,4%") e o formatador tropeca em todos
    html = PAGINA
    for marca, valor in (("@CSS@", css), ("@LOGO@", logo), ("@FONTES@", FONTES),
                         ("@DADOS@", json.dumps(enxuto, separators=(",", ":"),
                                                ensure_ascii=False))):
        html = html.replace(marca, valor)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(html, encoding="utf-8")
    kb = SAIDA.stat().st_size / 1024
    print(f"{SAIDA.name}: {kb:.0f} KB "
          f"({len(enxuto['agregado'])} linhas de agregado, "
          f"{len(enxuto['malhaUF'])} feições)")
    if kb > 16 * 1024:
        raise SystemExit("passou do teto de 16 MB do artefato")


if __name__ == "__main__":
    main()
