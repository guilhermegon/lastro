import { useMemo, useState } from "react";
import type { AgregadoUF, BaseUF, Cargo, DadosCargo } from "../tipos";
import { MAJORITARIOS, NOME_CARGO } from "../tipos";
import { quantis } from "../lib/escalas";
import { decimal, numero, percentual } from "../lib/formato";
import { Cartoes } from "../componentes/Cartoes";
import { Indices } from "../componentes/Indices";
import { Legenda } from "../componentes/Legenda";
import { ListaCandidatos } from "../componentes/ListaCandidatos";
import { Mapa } from "../componentes/Mapa";
import type { EstadoDica } from "../componentes/Dica";

interface Props {
  cargo: Cargo;
  base: BaseUF;
  dados: DadosCargo;
  ano: number;
  agregado: AgregadoUF | undefined;
  selecionado: number;
  aoSelecionar: (i: number) => void;
  aoInspecionar: (d: EstadoDica | null) => void;
}

export function VistaCargo({
  cargo, base, dados, ano, agregado, selecionado, aoSelecionar, aoInspecionar,
}: Props) {
  const [filtro, setFiltro] = useState("");
  const bloco = dados[String(ano)];
  const municipios = base.municipios;

  const lista = useMemo(() => {
    const todos = bloco?.fichas ?? [];
    const f = filtro.trim().toLowerCase();
    return f ? todos.filter((c) => c.n.toLowerCase().includes(f)) : todos;
  }, [bloco, filtro]);

  const atual = lista[selecionado] ?? lista[0];

  const { votos, influencia } = useMemo(() => {
    const v = new Array<number>(municipios.length).fill(0);
    if (atual) atual.mi.forEach((idx, k) => { v[idx] = atual.mv[k] as number; });
    const tot = bloco?.totalMun ?? [];
    return {
      votos: v,
      influencia: v.map((x, i) => {
        const t = tot[i] ?? 0;
        return x > 0 && t > 0 ? (x / t) * 100 : 0;
      }),
    };
  }, [atual, municipios.length, bloco]);

  const cortesVotos = useMemo(() => quantis(votos), [votos]);
  const cortesInfl = useMemo(() => quantis(influencia), [influencia]);

  if (!bloco) {
    return (
      <p className="indice exp">
        Sem dado de {NOME_CARGO[cargo].toLowerCase()} neste pleito.
      </p>
    );
  }

  const majoritario = MAJORITARIOS.has(cargo);
  const venceuUF = atual && bloco.vencedorUF === atual.sq;

  return (
    <div className="painel">
      <aside className="rail">
        <ListaCandidatos
          titulo={majoritario
            ? `Candidato(a) · ${NOME_CARGO[cargo]}`
            : `Eleito(a) · ${NOME_CARGO[cargo]}`}
          candidatos={lista}
          selecionado={selecionado}
          filtro={filtro}
          aoFiltrar={(v) => { setFiltro(v); aoSelecionar(0); }}
          aoSelecionar={aoSelecionar}
        />
      </aside>

      <div className="conteudo">
        {majoritario && (
          <div className="nota">
            <strong>Cargo majoritário, mapa de primeiro turno.</strong> A lista traz
            todos os candidatos, não só quem venceu — com um nome a tela não serviria
            para nada. O mapa e os índices usam sempre o 1º turno, que é onde está a
            disputa territorial: no segundo sobram dois.
          </div>
        )}

        {atual && (
          <>
            <Cartoes itens={[
              { rotulo: "Candidato(a)", valor: atual.n, texto: true,
                sub: atual.completo !== atual.n ? atual.completo : undefined },
              { rotulo: "Partido", valor: atual.p, texto: true,
                sub: atual.pn !== atual.p ? `hoje ${atual.pn}` : undefined },
              { rotulo: "Situação", texto: true,
                valor: atual.el ? "Eleito" : venceuUF ? "Venceu no estado" : "Não eleito",
                sub: venceuUF && !atual.el ? "mais votado na UF" : undefined },
              { rotulo: "Municípios com voto", valor: numero(atual.nm),
                sub: `de ${numero(municipios.length)}` },
              { rotulo: "Votos nominais", valor: numero(atual.t) },
              { rotulo: "Do estado",
                valor: agregado?.tot ? percentual((atual.t / bloco.pleito.totalUF) * 100) : "—",
                sub: `${numero(bloco.pleito.totalUF)} no total` },
            ]} />

            <div className="mapas">
              <div className="cartaz">
                <h2>Votação</h2>
                <p className="cap">Votos nominais recebidos em cada município.</p>
                <Mapa geo={base.geo} valores={votos} cortes={cortesVotos}
                      rotulo="Votos nominais" aoInspecionar={aoInspecionar}
                      descrever={(i, v) => (
                        <>
                          <strong>{municipios[i]?.n}</strong>
                          Votos: <span className="num">
                            {v > 0 ? numero(v) : "sem voto"}</span>
                        </>
                      )} />
                <Legenda cortes={cortesVotos} />
              </div>

              <div className="cartaz">
                <h2>Influência</h2>
                <p className="cap">
                  Quanto representa do total de votos nominais apurados no município.
                </p>
                <Mapa geo={base.geo} valores={influencia} cortes={cortesInfl}
                      rotulo="Influência" aoInspecionar={aoInspecionar}
                      descrever={(i, v) => (
                        <>
                          <strong>{municipios[i]?.n}</strong>
                          Influência: <span className="num">
                            {v > 0 ? percentual(v) : "sem voto"}</span>
                        </>
                      )} />
                <Legenda cortes={cortesInfl} sufixo="%" />
              </div>
            </div>

            <div className="cartaz">
              <h2>Perfil territorial</h2>
              <p className="cap">Os mesmos índices em todos os cargos e estados.</p>
              <Indices itens={[
                { rotulo: "Municípios efetivos", valor: decimal(atual.ef, 1),
                  explicacao: `de ${numero(municipios.length)} — equivale a concentrar tudo nesse tanto de municípios iguais` },
                { rotulo: "Fração do estado",
                  valor: percentual((atual.ef / Math.max(municipios.length, 1)) * 100, 1),
                  explicacao: "é o número comparável entre estados de portes diferentes" },
                { rotulo: "Maior município", valor: percentual(atual.t1, 1),
                  explicacao: atual.r >= 0 ? municipios[atual.r]?.n ?? "" : "" },
                { rotulo: "Cinco maiores", valor: percentual(atual.t5, 1),
                  explicacao: "do total do candidato" },
                { rotulo: "Domínio médio", valor: percentual(atual.dom, 1),
                  explicacao: "fatia dele nos municípios onde tem voto" },
                { rotulo: "Municípios dominados", valor: numero(atual.dom25),
                  explicacao: "onde tem 25% ou mais do total apurado" },
                { rotulo: "Contiguidade", valor: percentual(atual.contig, 1),
                  explicacao: "votos no reduto e nos municípios que fazem fronteira com ele" },
                { rotulo: "Gini municipal", valor: decimal(atual.gi, 3),
                  explicacao: "0 = espalhado por igual, 1 = tudo num lugar" },
              ]} />
              <p className="cap" style={{ marginTop: 12 }}>
                Perfil: <strong>{atual.tipo}</strong>
              </p>
            </div>

            <div className="duas">
              <div className="cartaz">
                <h2>Concentração</h2>
                <p className="cap">Os 20 municípios que mais renderam votos.</p>
                <div className="rolagem">
                  <TabelaConcentracao atual={atual} municipios={municipios}
                                      totalMun={bloco.totalMun} />
                </div>
              </div>

              <div className="cartaz">
                <h2>Partidos</h2>
                <p className="cap">
                  Partidos com três candidaturas ou mais. A semelhança mede quanto os
                  candidatos do mesmo partido disputam o mesmo território — não se
                  compara entre estados de portes diferentes.
                </p>
                <div className="rolagem">
                  <table>
                    <thead>
                      <tr><th>Partido</th><th>Cand.</th><th>Eleitos</th>
                        <th>Votos</th><th>Puxador</th><th>Semelhança</th></tr>
                    </thead>
                    <tbody>
                      {bloco.partidos.slice(0, 12).map((p) => (
                        <tr key={p.nome}>
                          <td>{p.nome}</td>
                          <td className="n">{p.nc}</td>
                          <td className="n">{p.ne}</td>
                          <td className="n">{numero(p.votos)}</td>
                          <td className="n">{percentual(p.puxador, 1)}</td>
                          <td className="n">{p.sim == null ? "—" : decimal(p.sim, 3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function TabelaConcentracao({ atual, municipios, totalMun }: {
  atual: { mi: number[]; mv: number[]; t: number };
  municipios: { n: string }[];
  totalMun: number[];
}) {
  const linhas = atual.mi
    .map((idx, k) => {
      const v = atual.mv[k] as number;
      const t = totalMun[idx] ?? 0;
      return {
        nome: municipios[idx]?.n ?? "—", v,
        pd: (v / atual.t) * 100,
        pm: t > 0 ? (v / t) * 100 : 0,
      };
    })
    .sort((a, b) => b.v - a.v)
    .slice(0, 20);

  return (
    <table>
      <thead>
        <tr><th>Município</th><th>Votos</th><th>% do candidato</th>
          <th>% do município</th></tr>
      </thead>
      <tbody>
        {linhas.map((r) => (
          <tr key={r.nome}>
            <td>{r.nome}</td>
            <td className="n">{numero(r.v)}</td>
            <td className="n">{percentual(r.pd)}</td>
            <td className="n">{percentual(r.pm)}</td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr><td>Total</td><td className="n">{numero(atual.t)}</td>
          <td className="n">100,00%</td><td /></tr>
      </tfoot>
    </table>
  );
}
