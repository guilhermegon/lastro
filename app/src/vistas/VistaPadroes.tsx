import type { Padroes } from "../tipos";
import { Linha } from "../componentes/Linha";
import { decimal, numero, percentual } from "../lib/formato";
import { RAMPA, token } from "../lib/escalas";

const CORES_TIPO: Record<string, string> = {
  "Concentrado-Dominante": "--s1",
  "Disperso-Dominante": "--s3",
  "Concentrado-Compartilhado": "--s4",
  "Disperso-Difuso": "--s5",
};

export function VistaPadroes({ p, nMun, uf }: {
  p: Padroes; nMun: number; uf: string;
}) {
  const anos = p.serie.map((s) => s.ano);

  return (
    <div className="conteudo" style={{ padding: "20px 0 40px" }}>
      <div className="cartaz">
        <h2>Como as bases mudaram, {anos[0]} a {anos[anos.length - 1]}</h2>
        <p className="cap">
          Medianas entre os eleitos de cada pleito, não médias: a distribuição é
          assimétrica e a média seria puxada pelos casos extremos.
        </p>
        <Linha eixoX={anos} casas={1} series={[
          { rotulo: "Municípios efetivos", cor: "--accent",
            pontos: p.serie.map((s) => s.ef) },
        ]} />
        <p className="cap" style={{ marginTop: 10 }}>
          Municípios efetivos — quanto menor, mais a votação depende de poucas cidades.
          Em {uf} o teto é {numero(nMun)}.
        </p>
        <Linha eixoX={anos} casas={1} series={[
          { rotulo: "Maior município (%)", cor: "--s1",
            pontos: p.serie.map((s) => s.t1) },
          { rotulo: "Domínio médio (%)", cor: "--s5",
            pontos: p.serie.map((s) => s.dom) },
        ]} />
        <div className="legenda">
          <span className="item">
            <span className="swatch" style={{ background: token("--s1") }} />
            Maior município, % do total do eleito
          </span>
          <span className="item">
            <span className="swatch" style={{ background: token("--s5") }} />
            Domínio médio, % que ele detém onde atua
          </span>
        </div>
      </div>

      <div className="cartaz">
        <h2>Que tipo de deputado o estado elege</h2>
        <p className="cap">
          Cruzamento de concentração (10 ou menos municípios efetivos) com domínio
          (10% ou mais em média). Os cortes são escolha analítica, não do TSE.
        </p>
        <div className="rolagem">
          <table>
            <thead>
              <tr><th>Pleito</th>
                {Object.keys(CORES_TIPO).map((t) => <th key={t}>{t}</th>)}
              </tr>
            </thead>
            <tbody>
              {p.tipologia.map((linha) => (
                <tr key={linha.ano}>
                  <td className="n">{linha.ano}</td>
                  {Object.keys(CORES_TIPO).map((t) => {
                    const n = linha.tipos[t] ?? 0;
                    return (
                      <td key={t} className="n">
                        {n}
                        <span style={{ color: "var(--ink-3)", fontSize: ".7rem" }}>
                          {" "}({percentual((n / linha.n) * 100, 0)})
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="cartaz">
        <h2>A janela de captura municipal</h2>
        <p className="cap">
          Fatia do maior candidato no total de votos nominais do município, por porte
          do eleitorado. Valores medianos; cor mais escura significa mais capturado.
        </p>
        <div className="rolagem">
          <table>
            <thead>
              <tr><th>Pleito</th>
                {p.captura.faixas.map((f) => <th key={f}>{f}</th>)}
              </tr>
            </thead>
            <tbody>
              {p.captura.anos.map((a) => {
                const vals = a.t1.filter((v): v is number => v != null);
                const lo = Math.min(...vals, 0), hi = Math.max(...vals, 1);
                const passo = (v: number) =>
                  Math.min(4, Math.max(0, Math.floor(((v - lo) / ((hi - lo) || 1)) * 5)));
                return (
                  <tr key={a.ano}>
                    <td className="n">{a.ano}</td>
                    {a.t1.map((v, i) => (
                      <td key={i} className="n" style={v == null ? undefined : {
                        background: token(RAMPA[passo(v)] as string),
                        color: token((RAMPA[passo(v)] as string).replace("--s", "--tinta-s")),
                      }}>
                        {v == null ? "—" : decimal(v, 1)}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr><td>Municípios</td>
                {(p.captura.anos[p.captura.anos.length - 1]?.n ?? []).map((n, i) => (
                  <td key={i} className="n">{n}</td>
                ))}
              </tr>
            </tfoot>
          </table>
        </div>
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>Existe um tamanho ótimo de captura.</strong> Município pequeno demais
          não sustenta candidato próprio e acaba repartido entre os vizinhos; grande
          demais, ninguém domina. O pico costuma ficar numa faixa intermediária — em
          estados com poucos municípios o padrão some, porque não há faixas suficientes.
        </div>
      </div>

      <div className="cartaz">
        <h2>O preço da cadeira</h2>
        <p className="cap">
          Quociente eleitoral aproximado — total de nominais dividido pelas cadeiras —
          e a votação do último eleito, que é o corte real de entrada.
        </p>
        <div className="rolagem">
          <table>
            <thead>
              <tr><th>Pleito</th><th>Cadeiras</th><th>Nominais</th><th>Quociente</th>
                <th>Último eleito</th><th>Candidatos</th><th>Por cadeira</th></tr>
            </thead>
            <tbody>
              {p.custo.map((c) => (
                <tr key={c.ano}>
                  <td className="n">{c.ano}</td>
                  <td className="n">{c.cad}</td>
                  <td className="n">{numero(c.tot)}</td>
                  <td className="n">{numero(Math.round(c.qe))}</td>
                  <td className="n">{numero(c.ult)}</td>
                  <td className="n">{c.cand}</td>
                  <td className="n">{decimal(c.cand / Math.max(c.cad, 1), 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
