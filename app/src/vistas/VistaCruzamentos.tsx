import type { Cargo, Cruzamentos } from "../tipos";
import { CARGOS, NOME_CARGO } from "../tipos";
import { Linha } from "../componentes/Linha";
import { decimal, numero, percentual } from "../lib/formato";
import { token } from "../lib/escalas";

const COR: Record<Cargo, string> = {
  presidente: "--s5", governador: "--s3", senador: "--s4",
  federal: "--s2", estadual: "--s1",
};

export function VistaCruzamentos({ c, ano, nMun, uf }: {
  c: Cruzamentos; ano: number; nMun: number; uf: string;
}) {
  const anos = [...new Set(c.escala.map((e) => e.ano))].sort();
  const arrastoAno = c.arrasto
    .filter((a) => a.ano === ano)
    .sort((a, b) => b.r - a.r);
  const duplasAno = c.duplas.filter((d) => d.ano === ano).slice(0, 15);

  return (
    <div className="conteudo" style={{ padding: "20px 0 40px" }}>
      <div className="cartaz">
        <h2>Cada cargo se disputa numa escala diferente</h2>
        <p className="cap">
          Municípios efetivos, mediana por pleito. Nos cargos majoritários usa-se o
          mais votado no estado, não o vencedor da eleição — para presidente os dois
          raramente coincidem, e é a geografia local que interessa aqui.
        </p>
        <Linha eixoX={anos} casas={1} series={CARGOS.map((cg) => ({
          rotulo: NOME_CARGO[cg], cor: COR[cg],
          pontos: anos.map((a) =>
            c.escala.find((e) => e.cargo === cg && e.ano === a)?.ef ?? null),
        }))} />
        <div className="legenda">
          {CARGOS.map((cg) => (
            <span className="item" key={cg}>
              <span className="swatch" style={{ background: token(COR[cg]) }} />
              {NOME_CARGO[cg]}
            </span>
          ))}
        </div>
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>O teto é o número de municípios do estado.</strong> {uf} tem{" "}
          {numero(nMun)}, e nenhum cargo pode passar disso. Em estados pequenos os
          cinco cargos se aproximam por limitação aritmética, não porque a disputa
          seja parecida — por isso a coluna de fração, abaixo, é a comparável.
        </div>
        <div className="rolagem" style={{ marginTop: 12 }}>
          <table>
            <thead>
              <tr><th>Cargo</th><th>Municípios efetivos</th>
                <th>Fração do estado</th><th>Maior município</th></tr>
            </thead>
            <tbody>
              {CARGOS.map((cg) => {
                const e = c.escala.find((x) => x.cargo === cg && x.ano === ano);
                if (!e) return null;
                return (
                  <tr key={cg}>
                    <td>{NOME_CARGO[cg]}</td>
                    <td className="n">{decimal(e.ef, 1)}</td>
                    <td className="n">{percentual(e.fr, 1)}</td>
                    <td className="n">{percentual(e.t1, 1)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="cartaz">
        <h2>O partido anda junto entre os cargos?</h2>
        <p className="cap">
          Correlação, entre os municípios do estado, da fatia do partido no deputado
          estadual e no federal em {ano}. Perto de 1, o partido tem a mesma geografia
          nos dois cargos — máquina coordenada. Perto de 0, as duas disputas correm
          soltas: candidatos independentes dividindo só a legenda.
        </p>
        {arrastoAno.length === 0 ? (
          <p className="indice exp">
            Nenhum partido com presença em pelo menos metade dos municípios nos dois
            cargos neste pleito.
          </p>
        ) : (
          <div className="rolagem">
            <table>
              <thead>
                <tr><th>Partido</th><th>Correlação</th><th>Municípios</th></tr>
              </thead>
              <tbody>
                {arrastoAno.slice(0, 14).map((a) => (
                  <tr key={a.partido}>
                    <td>{a.partido}</td>
                    <td className="n">{decimal(a.r, 3)}</td>
                    <td className="n">{a.nm}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="cap" style={{ marginTop: 10 }}>
          Só entram partidos presentes em metade dos municípios ou mais, nos dois
          cargos. Sem esse corte, uma legenda com voto em poucas cidades correlaciona
          alto por acaso e aparece no topo sem dizer nada sobre território.
        </p>
      </div>

      <div className="cartaz">
        <h2>Duplas estadual e federal com o mesmo mapa</h2>
        <p className="cap">
          Para cada deputado estadual, o federal cujo mapa municipal mais se parece
          com o dele em {ano}.
        </p>
        <div className="rolagem">
          <table>
            <thead>
              <tr><th>Estadual</th><th>Federal</th><th>Mesmo partido</th>
                <th>Afinidade</th></tr>
            </thead>
            <tbody>
              {duplasAno.map((d, i) => (
                <tr key={i}>
                  <td>{d.e} <span style={{ color: "var(--ink-3)" }}>{d.ep}</span></td>
                  <td>{d.f} <span style={{ color: "var(--ink-3)" }}>{d.fp}</span></td>
                  <td>{d.mp ? "sim" : "não"}</td>
                  <td className="n">{decimal(d.af, 4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>Isto não prova campanha casada.</strong> Dois candidatos concentrados
          na mesma cidade têm mapas quase idênticos por geometria, sem combinação
          nenhuma — por isso as afinidades chegam perto de 1. A tabela mostra
          coincidência territorial; a intenção o dado não revela. O número informativo
          é o de baixo.
        </div>
        {c.mesmoPartido.length > 0 && (
          <>
            <p className="cap" style={{ marginTop: 14 }}>
              Entre as duplas mais parecidas, quantas dividem a mesma legenda:
            </p>
            <Linha eixoX={c.mesmoPartido.map((m) => m.ano)} casas={0} altura={150}
                   series={[{ rotulo: "Mesmo partido, %", cor: "--accent",
                              pontos: c.mesmoPartido.map((m) => m.pct) }]} />
          </>
        )}
      </div>
    </div>
  );
}
