import { useEffect, useMemo, useState } from "react";
import type { Cruzamentos, Indice, Padroes, Sigla } from "@app/tipos";
import { decimal, numero, percentual } from "@app/lib/formato";
import { LogoRadar } from "@app/componentes/LogoProduto";
import { SeletorEstado } from "@app/componentes/SeletorEstado";
import { Indices } from "@app/componentes/Indices";
import { Linha } from "@app/componentes/Linha";
import { Tabela } from "@app/componentes/Tabela";
import { VistaPadroes } from "@app/vistas/VistaPadroes";
import { VistaCruzamentos } from "@app/vistas/VistaCruzamentos";
import { leitura, projetar } from "./projecao";

const BASE = `${import.meta.env.BASE_URL}dados`;

const cache = new Map<string, Promise<unknown>>();
function baixar<T>(chave: string, caminho: string): Promise<T> {
  let p = cache.get(chave) as Promise<T> | undefined;
  if (!p) {
    p = fetch(caminho).then((r) => {
      if (!r.ok) throw new Error(`${caminho}: ${r.status}`);
      return r.json() as Promise<T>;
    }).catch((e) => { cache.delete(chave); throw e; });
    cache.set(chave, p);
  }
  return p;
}

type Aba = "projecao" | "padroes" | "cruzamentos";

export function AppRadar() {
  const [indice, setIndice] = useState<Indice | null>(null);
  const [uf, setUF] = useState<Sigla>("GO");
  const [gaveta, setGaveta] = useState(false);
  const [aba, setAba] = useState<Aba>("projecao");
  const [pad, setPad] = useState<Padroes | null>(null);
  const [cruz, setCruz] = useState<Cruzamentos | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    baixar<Indice>("indice", `${BASE}/indice.json`)
      .then(setIndice).catch((e) => setErro(String(e)));
  }, []);

  useEffect(() => {
    let vivo = true;
    setPad(null); setCruz(null);
    Promise.all([
      baixar<Padroes>(`p:${uf}`, `${BASE}/${uf}/padroes.json`),
      baixar<Cruzamentos>(`c:${uf}`, `${BASE}/${uf}/cruzamentos.json`),
    ]).then(([p, c]) => {
      if (!vivo) return;
      setPad(p); setCruz(c); setErro(null);
    }).catch((e) => { if (vivo) setErro(String(e)); });
    return () => { vivo = false; };
  }, [uf]);

  const resumo = indice?.ufs.find((u) => u.s === uf);
  const nMun = resumo?.nm ?? 0;
  const anos = pad?.serie.map((s) => s.ano) ?? [];
  const proximo = anos.length ? (anos[anos.length - 1] as number) + 4 : null;

  if (erro && !indice) {
    return (
      <main className="wrap" style={{ padding: "3rem 0" }}>
        <LogoRadar />
        <p className="cap">Não consegui ler os dados: {erro}</p>
        <p className="cap">
          O Radar se serve de <code>radar/public/dados</code>. Rode{" "}
          <code>scripts/22_publicar_web.py</code> e depois{" "}
          <code>scripts/47_publica_radar.py</code>.
        </p>
      </main>
    );
  }
  if (!indice) {
    return <main className="wrap" style={{ padding: "3rem 0" }}><p>Carregando…</p></main>;
  }

  return (
    <>
      <div className="topo">
        <div className="wrap">
          <div className="topo-in">
            <div className="marca">
              <LogoRadar />
              <h1>{resumo?.n ?? uf}</h1>
              <p>
                O que os padrões de {anos[0]} a {anos[anos.length - 1]} dizem
                sobre {proximo}. Projeção declarada, com a qualidade do ajuste à
                vista — não oráculo.
              </p>
            </div>
          </div>
          <div className="abas" role="tablist">
            {([["projecao", "Projeção"], ["padroes", "Padrões"],
               ["cruzamentos", "Cruzamentos"]] as [Aba, string][]).map(([id, r]) => (
              <button key={id} role="tab" aria-selected={id === aba}
                      onClick={() => setAba(id)}>{r}</button>
            ))}
          </div>
          <SeletorEstado ufs={indice.ufs} atual={uf} aberto={gaveta}
                         aoAbrir={setGaveta} aoEscolher={(s) => { setUF(s); setGaveta(false); }} />
        </div>
      </div>

      <main className="wrap">
        {erro && <p className="cap">Erro: {erro}</p>}

        {aba === "projecao" && pad && cruz && (
          <Projecao pad={pad} cruz={cruz} proximo={proximo} />
        )}
        {aba === "padroes" && pad && (
          <VistaPadroes p={pad} nMun={nMun} uf={resumo?.n ?? uf} />
        )}
        {aba === "cruzamentos" && cruz && (
          <VistaCruzamentos c={cruz} ano={anos[anos.length - 1] as number}
                            nMun={nMun} uf={resumo?.n ?? uf} />
        )}
      </main>

      <footer className="wrap">
        <p>
          <strong>Radar</strong> — Lastro. Uso interno e de cliente. Os números
          desta tela saem dos mesmos scripts que sustentam o site aberto; o que
          muda é a leitura para a frente.
        </p>
      </footer>
    </>
  );
}

/* ---------------- a seção que é o produto ---------------- */

function Projecao({ pad, cruz, proximo }: {
  pad: Padroes; cruz: Cruzamentos; proximo: number | null;
}) {
  const anos = pad.serie.map((s) => s.ano);
  const eixo = [...anos, proximo ?? ""];

  const ind = useMemo(() => ([
    { chave: "fr", rotulo: "Fração do estado",
      unidade: "p.p.",
      explica: "Municípios efetivos sobre o total do estado. Sobe = voto mais espalhado.",
      serie: pad.serie.map((s) => s.fr) },
    { chave: "dom", rotulo: "Domínio médio",
      unidade: "p.p.",
      explica: "Fatia média do candidato onde ele tem voto. Sobe = redutos mais fechados.",
      serie: pad.serie.map((s) => s.dom) },
    { chave: "contig", rotulo: "Contiguidade",
      unidade: "p.p.",
      explica: "Voto no reduto e nos municípios que fazem fronteira com ele.",
      serie: pad.serie.map((s) => s.contig) },
  ]), [pad]);

  // A estabilidade da base é o indicador que mais importa para prever: mede
  // quanto o mapa de um pleito repete o do anterior.
  const estab = cruz.base?.map((b) => b.mediana * 100) ?? [];
  const projEstab = projetar(estab);

  return (
    <>
      <div className="cartaz">
        <h2>O mapa do próximo pleito vai parecer com o deste?</h2>
        <p className="cap">
          É a pergunta que decide todas as outras. A estabilidade de base mede
          quanto o mapa de um pleito repete o do anterior — semelhança mediana
          entre os vetores municipais dos mesmos candidatos, pleito a pleito.
        </p>
        {projEstab ? (
          <>
            <Indices itens={[
              { rotulo: `Observado em ${anos[anos.length - 1]}`,
                valor: percentual(estab[estab.length - 1] ?? 0, 1),
                explicacao: "semelhança com o pleito anterior" },
              { rotulo: `Projetado para ${proximo}`,
                valor: percentual(projEstab.valor, 1),
                explicacao: projEstab.confiavel ? "tendência sustentada"
                                                : "tendência fraca — ver abaixo" },
              { rotulo: "Ajuste da reta", valor: percentual(projEstab.r2 * 100, 0),
                explicacao: "da variação, explicada" },
              { rotulo: "Desvio típico", valor: `${decimal(projEstab.erroTipico, 1)} p.p.`,
                explicacao: "o tamanho do mais ou menos" },
            ]} />
            <Linha
              eixoX={eixo}
              casas={0}
              series={[
                { rotulo: "Observado", cor: "--accent",
                  pontos: [...estab, null] },
                { rotulo: "Projetado", cor: "--s3",
                  pontos: [...estab.map(() => null), projEstab.valor] },
              ]} />
            <div className="nota" style={{ marginTop: 12 }}>
              <strong>Como ler.</strong> {leitura(projEstab, "p.p.")}
            </div>
          </>
        ) : (
          <p className="cap">Série curta demais para projetar.</p>
        )}
      </div>

      <div className="cartaz">
        <h2>Para onde cada indicador aponta</h2>
        <p className="cap">
          A mesma reta aplicada aos indicadores de geografia. Onde o ajuste é
          fraco, a coluna diz — e um número projetado com ajuste fraco é
          referência, não previsão.
        </p>
        <Tabela
          cab={["Indicador", `Em ${anos[anos.length - 1]}`, `Projetado ${proximo}`,
                "Por pleito", "Ajuste"]}
          linhas={ind.map((x) => {
            const p = projetar(x.serie);
            const ult = x.serie[x.serie.length - 1] ?? 0;
            return [
              x.rotulo,
              decimal(ult, 2),
              p ? decimal(p.valor, 2) : "—",
              p ? `${p.porPleito >= 0 ? "+" : ""}${decimal(p.porPleito, 2)}` : "—",
              p ? `${percentual(p.r2 * 100, 0)}${p.confiavel ? "" : " (fraco)"}` : "—",
            ];
          })} />
        <ul className="lista-fatos" style={{ marginTop: 14 }}>
          {ind.map((x) => (
            <li key={x.chave}><strong>{x.rotulo}.</strong> {x.explica}</li>
          ))}
        </ul>
      </div>

      <div className="cartaz">
        <h2>A margem de corte</h2>
        <p className="cap">
          Quantos votos separaram o último eleito de ficar de fora, pleito a
          pleito. É o número que diz o quanto uma disputa se decide na margem — e
          quanto uma variação pequena de base muda a composição da bancada.
        </p>
        <Tabela
          cab={["Pleito", "Quociente", "Último eleito", "Do quociente"]}
          linhas={pad.custo.map((c) => [
            String(c.ano), numero(Math.round(c.qe)), numero(c.ult),
            percentual(c.qe ? (c.ult / c.qe) * 100 : 0, 0),
          ])} />
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>O que este número não diz.</strong> A margem é do último
          eleito, não de cada candidato. Ela mede o quanto a última cadeira foi
          barata, não quem vai perdê-la — para isso é preciso a base individual,
          que está nos produtos de vitrine e entra aqui na próxima camada.
        </div>
      </div>

      <div className="nota">
        <strong>O que o Radar é, e o que não é.</strong> Todo número acima é
        extrapolação linear declarada sobre sete pleitos, com o ajuste à vista.
        Não há modelo causal, não há pesquisa de intenção, e não há variável
        externa — nem economia, nem candidatura ainda não registrada, nem
        mudança de regra eleitoral. O que ele entrega é: onde a série vinha indo,
        com que firmeza, e qual o tamanho do erro. Quem trata isso como
        prognóstico está lendo mais do que está escrito.
      </div>
    </>
  );
}
