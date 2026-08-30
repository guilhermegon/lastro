import { useMemo } from "react";
import type { Indice, Sigla } from "../tipos";
import { feicoesParaGeo } from "../lib/projecao";
import { quantis } from "../lib/escalas";
import { siglaDoCodigo } from "../lib/uf";
import { decimal, numero, percentual } from "../lib/formato";
import { Mapa } from "../componentes/Mapa";
import { Legenda } from "../componentes/Legenda";
import type { EstadoDica } from "../componentes/Dica";

/**
 * A tela de entrada: o país inteiro antes de qualquer estado.
 *
 * Tudo aqui sai de `indice.json`, os mesmos 96 KB que já são baixados para
 * desenhar a primeira tela — o comparativo nacional não custa uma requisição
 * a mais. E ele é montado a partir dos arquivos por UF já validados, e não de
 * um cálculo paralelo, para que não exista a possibilidade de discordar da
 * tela do estado.
 */
export function VistaNacional({ indice, ano, aoEscolher, aoInspecionar }: {
  indice: Indice;
  ano: number;
  aoEscolher: (uf: Sigla) => void;
  aoInspecionar: (d: EstadoDica | null) => void;
}) {
  const geo = useMemo(
    () => feicoesParaGeo(indice.malhaUF.map((f) => f.geom)), [indice.malhaUF]);

  const porUF = useMemo(() => {
    const nome = new Map(indice.ufs.map((u) => [u.s, u.n]));
    const m = new Map<string, {
      uf: string; nome: string; nmun: number; cad: number; tot: number;
      cand: number; qe: number; ult: number; ef: number | null;
      t1: number | null; fr: number | null;
    }>();
    for (const a of indice.agregado) {
      if (a.ano !== ano) continue;
      m.set(a.uf, {
        uf: a.uf, nome: nome.get(a.uf) ?? a.uf, nmun: a.nmun, cad: a.cad,
        tot: a.tot, cand: a.cand, qe: a.qe, ult: a.ult,
        ef: a.ef, t1: a.t1, fr: a.fr,
      });
    }
    return m;
  }, [indice, ano]);

  // as feições vêm por código do IBGE; os dados, por sigla
  const siglas = useMemo(
    () => indice.malhaUF.map((f) => siglaDoCodigo(f.cod)), [indice.malhaUF]);
  const valores = useMemo(
    () => siglas.map((s) => porUF.get(s)?.fr ?? 0), [siglas, porUF]);
  const cortes = useMemo(() => quantis(valores), [valores]);

  const linhas = useMemo(() => [...porUF.values()], [porUF]);
  const porFracao = useMemo(
    // sem fração não há posição no ranking: vai para o fim, e a célula
    // mostra travessão — o último lugar aqui não é um resultado, é uma ausência
    () => [...linhas].sort((a, b) => (b.fr ?? -1) - (a.fr ?? -1)), [linhas]);
  const porPreco = useMemo(
    () => [...linhas].sort((a, b) => b.ult - a.ult), [linhas]);

  if (linhas.length === 0) {
    return <p className="indice exp">Sem dado de deputado estadual em {ano}.</p>;
  }

  return (
    <div className="conteudo" style={{ paddingTop: 14 }}>
      <div className="cartaz">
        <h2>Concentração do voto por estado</h2>
        <p className="cap">
          Cada estado colorido pela <strong>fração dos seus municípios</strong>{" "}
          que a votação mediana dos eleitos efetivamente ocupa, em {ano}.{" "}
          <span className="swatch" style={{ display: "inline-block",
                verticalAlign: -2, background: "var(--s1)" }} /> vermelho = voto
          concentrado em poucos municípios;{" "}
          <span className="swatch" style={{ display: "inline-block",
                verticalAlign: -2, background: "var(--s5)" }} /> verde =
          espalhado pelo estado. Clique num estado para abrir a tela dele.
        </p>

        <div className="mapas" style={{ gridTemplateColumns: "1fr" }}>
          <div>
            <Mapa
              geo={geo}
              valores={valores}
              cortes={cortes}
              rotulo="Fração do estado ocupada pelo voto"
              aoInspecionar={aoInspecionar}
              aoClicar={(i) => {
                const s = siglas[i];
                if (s && porUF.has(s)) aoEscolher(s);
              }}
              descrever={(i, v) => {
                const s = siglas[i];
                const d = s ? porUF.get(s) : undefined;
                return (
                  <>
                    <strong>{d?.nome ?? s}</strong>
                    {!d ? (
                      "sem dado neste pleito"
                    ) : d.fr == null ? (
                      <>
                        Um município só: não há fração de estado a medir.
                        <br />
                        {d.cad} cadeiras, {numero(d.tot)} votos nominais
                      </>
                    ) : (
                      <>
                        Fração do estado:{" "}
                        <span className="num">{percentual(v, 1)}</span>
                        <br />
                        {decimal(d.ef ?? 0, 1)} municípios efetivos de{" "}
                        {numero(d.nmun)}
                      </>
                    )}
                  </>
                );
              }}
            />
            <Legenda cortes={cortes} sufixo="%" />
          </div>
        </div>

        <div className="rolagem" style={{ marginTop: 16 }}>
          <table>
            <thead>
              <tr>
                <th>Estado</th><th>Munic.</th><th>Cadeiras</th>
                <th>Mun. efetivos</th><th>Fração do estado</th>
                <th>Maior município</th>
              </tr>
            </thead>
            <tbody>
              {porFracao.map((d) => (
                <tr key={d.uf}>
                  <td>
                    <button className="ligacao" onClick={() => aoEscolher(d.uf)}>
                      {d.nome}
                    </button>
                  </td>
                  <td className="n">{numero(d.nmun)}</td>
                  <td className="n">{d.cad}</td>
                  <td className="n">{d.ef == null ? "—" : decimal(d.ef, 1)}</td>
                  <td className="n">{d.fr == null ? "—" : percentual(d.fr, 1)}</td>
                  <td className="n">{d.t1 == null ? "—" : percentual(d.t1, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="nota" style={{ marginTop: 14 }}>
          <strong>Municípios efetivos não se comparam entre estados sem
          cuidado.</strong> Roraima tem 15 municípios e Minas tem 853 — um estado
          com 15 não pode ter 16 municípios efetivos. O índice está limitado pelo
          tamanho do estado. Por isso a tabela traz também a <em>fração</em> do
          estado efetivamente usada, que é comparável, e o mapa colore por ela.
        </div>

        <p className="cap">
          O Distrito Federal fica sem cor, e com travessão nas três últimas
          colunas. Ele está no painel — os 24 distritais entram equiparados a
          estaduais — mas é um município só: fração do estado, municípios
          efetivos e maior município não têm o que medir ali. As colunas de
          cadeiras, quociente e preço da cadeira valem, e o DF aparece nelas.
        </p>
      </div>

      <div className="cartaz">
        <h2>O preço da cadeira em cada estado</h2>
        <p className="cap">
          Total de votos nominais dividido pelas cadeiras, e a votação do último
          eleito — o corte real de entrada na assembleia. Ordenado pelo corte.
        </p>
        <div className="rolagem">
          <table>
            <thead>
              <tr>
                <th>Estado</th><th>Nominais</th><th>Cadeiras</th>
                <th>Quociente</th><th>Último eleito</th><th>Candidatos</th>
                <th>Por cadeira</th>
              </tr>
            </thead>
            <tbody>
              {porPreco.map((d) => (
                <tr key={d.uf}>
                  <td>
                    <button className="ligacao" onClick={() => aoEscolher(d.uf)}>
                      {d.nome}
                    </button>
                  </td>
                  <td className="n">{numero(d.tot)}</td>
                  <td className="n">{d.cad}</td>
                  <td className="n">{numero(Math.round(d.qe))}</td>
                  <td className="n">{numero(d.ult)}</td>
                  <td className="n">{numero(d.cand)}</td>
                  <td className="n">{decimal(d.cand / Math.max(d.cad, 1), 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
