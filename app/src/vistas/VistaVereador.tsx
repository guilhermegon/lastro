import { useMemo, useState } from "react";
import { MapaUrnas } from "../componentes/MapaUrnas";
import type { EstadoDica } from "../componentes/Dica";
import { Legenda } from "../componentes/Legenda";
import { quantis } from "../lib/escalas";
import type { Urnas, Vereador } from "../tipos";
import { decimal, numero, percentual } from "../lib/formato";
import { token } from "../lib/escalas";
import { Cartoes } from "../componentes/Cartoes";
import { Indices } from "../componentes/Indices";
import { ListaCandidatos } from "../componentes/ListaCandidatos";

/**
 * Câmara municipal da capital. É a única aba sem mapa, e não por falta de
 * trabalho: uma capital é um município só, então o coroplético que sustenta o
 * resto do projeto aqui não existe. A única desagregação territorial que o
 * arquivo do TSE oferece dentro da cidade é a zona eleitoral, e não há malha
 * pública de zona — a geografia entra como distribuição, não como desenho.
 */
export function VistaVereador({ v, selecionado, aoSelecionar, urnas,
                                aoInspecionar }: {
  v: Vereador;
  selecionado: number;
  aoSelecionar: (i: number) => void;
  /** voto por local de votação; existe só onde foi gerado */
  urnas: Urnas | null;
  aoInspecionar: (d: EstadoDica | null) => void;
}) {
  const anos = useMemo(
    () => Object.keys(v.anos).map(Number).sort((a, b) => a - b), [v.anos]);
  const [ano, setAno] = useState(() => anos[anos.length - 1] ?? 2024);
  const [filtro, setFiltro] = useState("");
  const bloco = v.anos[String(ano)];

  const lista = useMemo(() => {
    const todos = bloco?.fichas ?? [];
    const f = filtro.trim().toLowerCase();
    return f ? todos.filter((c) => c.n.toLowerCase().includes(f)) : todos;
  }, [bloco, filtro]);

  const atual = lista[selecionado] ?? lista[0];

  /* O vetor por local do candidato aberto. Sem candidato, mostra o total do
     local — que é o denominador de tudo o mais nesta tela. */
  const porLocal = useMemo(() => {
    const n = urnas?.locais.length ?? 0;
    if (!urnas || !n) return [];
    if (!atual) return urnas.totalLocal.slice(0, n);
    const f = urnas.fichas.find((x) => x.sq === String(atual.sq));
    const out = new Array<number>(n).fill(0);
    f?.li.forEach((idx, k) => { if (idx < n) out[idx] = f.lv[k] ?? 0; });
    return out;
  }, [urnas, atual]);

  const cortesUrna = useMemo(
    () => quantis(porLocal.filter((x) => x > 0)), [porLocal]);

  if (!bloco) return <p className="indice exp">Sem dado neste pleito.</p>;

  const porZona = atual
    ? atual.zi.map((idx, k) => ({
        zona: bloco.zonas[idx] ?? 0, votos: atual.zv[k] as number,
      })).sort((a, b) => b.votos - a.votos)
    : [];
  const maiorZona = Math.max(...porZona.map((z) => z.votos), 1);

  return (
    <div className="painel">
      <aside className="rail">
        <div className="rail-bloco">
          <div className="rail-titulo">Pleito municipal</div>
          <div className="seg-rot" data-pleito="municipal">
            <span className="et">Pleito municipal</span>
            <div className="seg" data-pleito="municipal" role="group"
                 aria-label="Pleito municipal">
            {anos.map((a) => (
              <button key={a} aria-pressed={a === ano}
                      onClick={() => { setAno(a); aoSelecionar(0); }}>
                {a}
              </button>
            ))}
          </div>
        </div>
            </div>
        <ListaCandidatos
          titulo={`Vereador(a) · ${v.cidade}`}
          candidatos={lista}
          selecionado={selecionado}
          filtro={filtro}
          aoFiltrar={(x) => { setFiltro(x); aoSelecionar(0); }}
          aoSelecionar={aoSelecionar}
        />
      </aside>

      <div className="conteudo">
        <div className="nota">
          <strong>Outro ciclo, outra geografia.</strong> A eleição municipal é
          de 2000, 2004, … 2024 — não há um único ano em comum com os pleitos
          gerais, então esta aba nunca cruza com as outras. E como a cidade é um
          município só, não há mapa: a única divisão interna que o TSE publica é
          a zona eleitoral, que não tem malha desenhada.
        </div>

        {atual && (
          <>
            <Cartoes itens={[
              { rotulo: "Vereador(a)", valor: atual.n, texto: true,
                sub: atual.completo !== atual.n ? atual.completo : undefined },
              { rotulo: "Partido", valor: atual.p, texto: true,
                sub: atual.pn !== atual.p ? `hoje ${atual.pn}` : undefined },
              { rotulo: "Situação", valor: atual.el ? "Eleito" : "Não eleito",
                texto: true,
                sub: atual.re ? "já havia concorrido" : "estreia" },
              { rotulo: "Zonas com voto", valor: numero(atual.nz),
                sub: `de ${numero(bloco.zonas.length)}` },
              { rotulo: "Votos nominais", valor: numero(atual.t) },
              { rotulo: "Da cidade",
                valor: percentual((atual.t / Math.max(bloco.pleito.total, 1)) * 100),
                sub: `${numero(bloco.pleito.total)} no total` },
            ]} />

            {/* Ausência do mapa é dita, nunca silenciosa: o seletor de cidade
                convida a trocar, e uma seção que some sem explicação faz o
                leitor achar que quebrou. */}
            {!(urnas && urnas.ano === ano) && (
              <div className="nota">
                <strong>Sem mapa de urna {ano === 2024 ? "nesta cidade" : `em ${ano}`}.</strong>{" "}
                {ano !== 2024
                  ? "O mapa por local de votação existe só para 2024 — é o pleito"
                    + " em que o TSE publica a coordenada de cada urna."
                  : "A coordenada das urnas desta capital ainda não foi ingerida."
                    + " O dado existe no TSE; falta o passo de coleta."}{" "}
                A distribuição por zona eleitoral abaixo continua valendo.
              </div>
            )}

            {urnas && urnas.ano === ano && (
              <div className="cartaz">
                <h2>Onde estão os votos, urna a urna</h2>
                <p className="cap">
                  {atual
                    ? <>Votos de <strong>{atual.n}</strong> em cada um dos{" "}
                        {numero(urnas.locais.length)} locais de votação de{" "}
                        {urnas.cidade}. A área do círculo é proporcional ao
                        voto; o anel vazio é local onde este candidato não teve
                        voto — que é diferente de não haver urna ali.</>
                    : <>Total de votos para vereador em cada local de votação de{" "}
                        {urnas.cidade}.</>}
                </p>
                <MapaUrnas
                  locais={urnas.locais}
                  valores={porLocal}
                  rotulo={atual ? atual.n : "Votos"}
                  aoInspecionar={aoInspecionar}
                  descrever={(i, val) => {
                    const l = urnas.locais[i];
                    const tot = urnas.totalLocal[i] ?? 0;
                    return (
                      <>
                        <strong>{l?.n}</strong>
                        <br />{l?.b} · zona {l?.z}
                        <br />{numero(Math.round(val))} voto(s)
                        {atual && tot > 0
                          ? ` · ${percentual((val / tot) * 100, 1)} do local`
                          : ""}
                        <br />{numero(l?.e ?? 0)} eleitores
                      </>
                    );
                  }} />
                <Legenda cortes={cortesUrna} semDado="Sem voto aqui" />
                <div className="nota" style={{ marginTop: 12 }}>
                  <strong>É o grão mais fino deste projeto, e tem dois
                  limites.</strong> O local de votação é um endereço, não um
                  território: o ponto diz onde a urna estava, não onde o eleitor
                  mora — quem vota numa escola pode morar a quarteirões dela. E a
                  escala do círculo é <em>do candidato aberto</em>, não comum a
                  todos: o maior ponto é sempre o maior local dele. Isso mostra o
                  formato da votação de cada um, e não permite comparar tamanho
                  entre candidatos — para isso, o total está na lista.
                  {urnas.semCoordenada > 0 && (
                    <> {numero(urnas.semCoordenada)} local(is) de{" "}
                      {numero(urnas.locais.length)} ficam fora do mapa por não
                      terem coordenada publicada
                      {urnas.semCadastro > 0
                        ? ` — um deles nem consta do cadastro de locais` : ""}.
                      Continuam somando nos totais: saem do desenho, não da
                      contagem.</>
                  )}
                </div>
              </div>
            )}

            <div className="cartaz">
              <h2>Distribuição por zona eleitoral</h2>
              {bloco.zonas.length < 2 ? (
                <p className="cap">
                  {v.cidade} tem uma zona eleitoral só neste pleito, então não há
                  geografia interna a mostrar: todo o voto do candidato está na
                  mesma unidade. Uma barra de 100% aqui fingiria uma distribuição
                  que o dado não tem.
                </p>
              ) : (
              <>
              <p className="cap">
                Votos em cada zona, da maior para a menor. A zona{" "}
                <span className="num">{atual.reduto}</span> é o reduto.
              </p>
              <ul className="zonas">
                {porZona.map((z) => (
                  <li key={z.zona}>
                    <span className="cap">Zona {z.zona}</span>
                    <span className="zona-barra" aria-hidden="true">
                      <span style={{ width: `${(z.votos / maiorZona) * 100}%`,
                                     background: token("--s4") }} />
                    </span>
                    <span className="num" style={{ textAlign: "right" }}>
                      {numero(z.votos)}
                    </span>
                  </li>
                ))}
              </ul>
              </>
              )}
            </div>

            <div className="cartaz">
              <h2>Perfil na cidade</h2>
              <Indices itens={[
                { rotulo: "Zonas efetivas", valor: decimal(atual.ef, 2),
                  explicacao: `de ${bloco.zonas.length} — só compare dentro deste pleito` },
                { rotulo: "Maior zona", valor: percentual(atual.t1, 1),
                  explicacao: `zona ${atual.reduto}` },
                { rotulo: "Gini entre zonas", valor: decimal(atual.gi, 3),
                  explicacao: "0 = espalhado por igual, 1 = tudo numa zona" },
                { rotulo: "Base do pleito anterior",
                  valor: atual.sim == null ? "—" : decimal(atual.sim, 3),
                  explicacao: atual.sim == null
                    ? "não comparável: as zonas foram redesenhadas ou é estreia"
                    : "cosseno com o próprio mapa de zonas da eleição anterior" },
              ]} />
            </div>
          </>
        )}

        <div className="duas">
          <div className="cartaz">
            <h2>O pleito</h2>
            <Indices itens={[
              { rotulo: "Cadeiras", valor: numero(bloco.pleito.cadeiras),
                explicacao: "eleitos na câmara" },
              { rotulo: "Candidatos", valor: numero(bloco.pleito.nCand),
                explicacao: `${decimal(bloco.pleito.nCand / Math.max(bloco.pleito.cadeiras, 1), 1)} por cadeira` },
              { rotulo: "Último eleito", valor: numero(bloco.pleito.ultimo),
                explicacao: "menor votação que entrou" },
              { rotulo: "Mais votado", valor: numero(bloco.pleito.maior),
                explicacao: `${decimal(bloco.pleito.maior / Math.max(bloco.pleito.ultimo, 1), 1)}× o último` },
              { rotulo: "Reincidência", valor: percentual(bloco.pleito.rePct, 1),
                explicacao: "eleitos que já haviam concorrido antes" },
              { rotulo: "Zonas", valor: numero(bloco.pleito.nz),
                explicacao: "número e traçado mudam entre pleitos" },
            ]} />
          </div>

          <div className="cartaz">
            <h2>Partidos</h2>
            <p className="cap">Com duas candidaturas ou mais.</p>
            <div className="rolagem">
              <table>
                <thead>
                  <tr><th>Partido</th><th>Cand.</th><th>Eleitos</th>
                    <th>Votos</th><th>Puxador</th></tr>
                </thead>
                <tbody>
                  {bloco.partidos.map((p) => (
                    <tr key={p.nome}>
                      <td>{p.nome}</td>
                      <td className="n">{p.nc}</td>
                      <td className="n">{p.ne}</td>
                      <td className="n">{numero(p.votos)}</td>
                      <td className="n">{percentual(p.puxador, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
