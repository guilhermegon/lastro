import { useCallback, useEffect, useMemo, useState } from "react";
import type { Candidato, DadosUF, Indice, Sigla } from "./tipos";
import { carregarIndice, carregarUF } from "./lib/dados";
import { quantis } from "./lib/escalas";
import { numero, decimal, percentual } from "./lib/formato";
import { Logo } from "./componentes/Logo";
import { SeletorEstado } from "./componentes/SeletorEstado";
import { Cartoes } from "./componentes/Cartoes";
import { Indices } from "./componentes/Indices";
import { Legenda } from "./componentes/Legenda";
import { ListaCandidatos } from "./componentes/ListaCandidatos";
import { Mapa } from "./componentes/Mapa";
import { Dica, type EstadoDica } from "./componentes/Dica";

/**
 * O estado da tela mora na URL.
 *
 * Não é preciosismo: num produto de inteligência política a ação mais comum é
 * mandar a tela para outra pessoa. Com o estado na URL, copiar o endereço
 * compartilha exatamente o que está sendo visto, o botão voltar funciona, e
 * recarregar não perde nada — tudo isso de graça, sem biblioteca de rota.
 */
interface Selecao {
  uf: Sigla;
  ano: number;
  cand: number;
}

function lerURL(): Selecao {
  const p = new URLSearchParams(location.search);
  return {
    uf: (p.get("uf") ?? "GO").toUpperCase(),
    ano: Number(p.get("ano") ?? 2022),
    cand: Number(p.get("c") ?? 0),
  };
}

function gravarURL(s: Selecao) {
  const p = new URLSearchParams({ uf: s.uf, ano: String(s.ano), c: String(s.cand) });
  history.replaceState(null, "", `?${p}`);
}

export default function App() {
  const [indice, setIndice] = useState<Indice | null>(null);
  const [dados, setDados] = useState<DadosUF | null>(null);
  const [sel, setSel] = useState<Selecao>(lerURL);
  const [filtro, setFiltro] = useState("");
  const [gaveta, setGaveta] = useState(false);
  const [dica, setDica] = useState<EstadoDica | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    carregarIndice().then(setIndice).catch((e) => setErro(String(e)));
  }, []);

  useEffect(() => {
    let vivo = true;
    setCarregando(true);
    carregarUF(sel.uf)
      .then((d) => { if (vivo) { setDados(d); setErro(null); } })
      .catch((e) => { if (vivo) setErro(String(e)); })
      .finally(() => { if (vivo) setCarregando(false); });
    return () => { vivo = false; };
  }, [sel.uf]);

  useEffect(() => gravarURL(sel), [sel]);

  const trocarUF = useCallback((uf: Sigla) => {
    setSel((s) => ({ ...s, uf, cand: 0 }));
    setFiltro("");
    setGaveta(false);
  }, []);

  const eleitos = dados?.eleitos[String(sel.ano)] ?? [];
  const visiveis = useMemo(() => {
    const f = filtro.trim().toLowerCase();
    return f ? eleitos.filter((c) => c.n.toLowerCase().includes(f)) : eleitos;
  }, [eleitos, filtro]);

  const atual: Candidato | undefined = visiveis[sel.cand] ?? visiveis[0];
  const municipios = dados?.municipios ?? [];
  const totais = dados?.totais[String(sel.ano)] ?? [];
  const agregado = indice?.agregado.find((a) => a.uf === sel.uf && a.ano === sel.ano);

  const { votos, influencia } = useMemo(() => {
    const v = new Array<number>(municipios.length).fill(0);
    if (atual) atual.mi.forEach((idx, k) => { v[idx] = atual.mv[k] as number; });
    const inf = v.map((x, i) => {
      const t = totais[i] ?? 0;
      return x > 0 && t > 0 ? (x / t) * 100 : 0;
    });
    return { votos: v, influencia: inf };
  }, [atual, municipios.length, totais]);

  const cortesVotos = useMemo(() => quantis(votos), [votos]);
  const cortesInfl = useMemo(() => quantis(influencia), [influencia]);

  if (erro) {
    return (
      <main className="wrap" style={{ padding: "3rem 0" }}>
        <h1>Não foi possível carregar os dados</h1>
        <p style={{ color: "var(--ink-2)" }}>{erro}</p>
        <p className="indice exp">
          Se estiver abrindo o arquivo direto do disco, o navegador bloqueia a leitura
          dos dados por segurança. Sirva a pasta por HTTP — <code>npm run dev</code> ou
          qualquer servidor estático.
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
              <Logo />
              <h1>Cadê o Voto?</h1>
              <p>
                Distribuição espacial do voto para deputado estadual em cada unidade da
                federação, de 1998 a 2022, município a município.
              </p>
            </div>
            <div className="seg" role="group" aria-label="Pleito">
              {indice.anos.map((a) => {
                const tem = !!dados?.eleitos[String(a)]?.length;
                return (
                  <button
                    key={a}
                    aria-pressed={a === sel.ano}
                    disabled={!!dados && !tem}
                    style={{ opacity: !dados || tem ? undefined : 0.35 }}
                    onClick={() => setSel((s) => ({ ...s, ano: a, cand: 0 }))}
                  >
                    {a}
                  </button>
                );
              })}
            </div>
          </div>

          <SeletorEstado
            ufs={indice.ufs}
            atual={sel.uf}
            aberto={gaveta}
            aoAbrir={setGaveta}
            aoEscolher={trocarUF}
          />
        </div>
      </div>

      <main className="wrap">
        <div className="painel">
          <aside className="rail">
            <ListaCandidatos
              titulo={`Deputado(a) estadual · ${sel.uf}`}
              candidatos={visiveis}
              selecionado={sel.cand}
              filtro={filtro}
              aoFiltrar={(v) => { setFiltro(v); setSel((s) => ({ ...s, cand: 0 })); }}
              aoSelecionar={(i) => setSel((s) => ({ ...s, cand: i }))}
            />
          </aside>

          <div className="conteudo">
            {carregando && <p className="indice exp">Carregando {sel.uf}…</p>}

            {atual && (
              <>
                <Cartoes
                  itens={[
                    { rotulo: "Deputado(a)", valor: atual.n, texto: true },
                    {
                      rotulo: "Partido", valor: atual.p, texto: true,
                      sub: atual.pn !== atual.p ? `hoje ${atual.pn}` : undefined,
                    },
                    {
                      rotulo: "Municípios com voto", valor: numero(atual.nm),
                      sub: `de ${numero(municipios.length)}`,
                    },
                    { rotulo: "Votos nominais", valor: numero(atual.t) },
                    {
                      rotulo: "Do estado",
                      valor: agregado ? percentual((atual.t / agregado.tot) * 100) : "—",
                      sub: agregado ? `${numero(agregado.tot)} no total` : undefined,
                    },
                    {
                      rotulo: "Reduto", texto: true,
                      valor: atual.r >= 0 ? (municipios[atual.r]?.n ?? "—") : "—",
                    },
                  ]}
                />

                <div className="mapas">
                  <div className="cartaz">
                    <h2>Votação</h2>
                    <p className="cap">
                      Votos nominais que o deputado recebeu em cada município.
                    </p>
                    <Mapa
                      geo={dados?.geo ?? []}
                      valores={votos}
                      cortes={cortesVotos}
                      rotulo="Votos nominais"
                      aoInspecionar={setDica}
                      descrever={(i, v) => (
                        <>
                          <strong>{municipios[i]?.n}</strong>
                          Votos nominais:{" "}
                          <span className="num">{v > 0 ? numero(v) : "sem voto"}</span>
                        </>
                      )}
                    />
                    <Legenda cortes={cortesVotos} />
                  </div>

                  <div className="cartaz">
                    <h2>Influência</h2>
                    <p className="cap">
                      Quanto ele representa do total de votos nominais apurados no município.
                    </p>
                    <Mapa
                      geo={dados?.geo ?? []}
                      valores={influencia}
                      cortes={cortesInfl}
                      rotulo="Influência"
                      aoInspecionar={setDica}
                      descrever={(i, v) => (
                        <>
                          <strong>{municipios[i]?.n}</strong>
                          Influência:{" "}
                          <span className="num">{v > 0 ? percentual(v) : "sem voto"}</span>
                        </>
                      )}
                    />
                    <Legenda cortes={cortesInfl} sufixo="%" />
                  </div>
                </div>

                <div className="cartaz">
                  <h2>Perfil territorial</h2>
                  <p className="cap">Os mesmos índices aplicados a todas as unidades da federação.</p>
                  <Indices
                    itens={[
                      {
                        rotulo: "Municípios efetivos", valor: decimal(atual.ef, 1),
                        explicacao: `de ${numero(municipios.length)} — equivale a concentrar tudo nesse tanto de municípios iguais`,
                      },
                      {
                        rotulo: "Maior município", valor: percentual(atual.t1, 1),
                        explicacao: "do total do deputado",
                      },
                      {
                        rotulo: "Cinco maiores", valor: percentual(atual.t5, 1),
                        explicacao: "do total do deputado",
                      },
                      {
                        rotulo: "Gini municipal", valor: decimal(atual.gi, 3),
                        explicacao: "0 = espalhado por igual, 1 = tudo num lugar",
                      },
                      {
                        rotulo: "Fração do estado",
                        valor: percentual((atual.ef / Math.max(municipios.length, 1)) * 100, 1),
                        explicacao: "municípios efetivos sobre o total — é o número comparável entre UFs",
                      },
                    ]}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      <footer className="wrap">
        <p>
          <strong>Lastro — Inteligência Política.</strong> Fonte: Tribunal Superior
          Eleitoral, dados abertos, arquivo <span className="num">votacao_candidato_munzona</span>,
          cargo de deputado estadual, 1º turno. Malha municipal: IBGE.
        </p>
        <p>
          O Distrito Federal elege deputado distrital e não estadual, por isso não aparece:
          são 26 unidades.
        </p>
      </footer>

      <Dica dica={dica} aoFechar={() => setDica(null)} />
    </>
  );
}
