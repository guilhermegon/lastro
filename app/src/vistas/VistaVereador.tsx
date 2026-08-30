import { useEffect, useMemo, useState } from "react";
import { MapaUrnas } from "../componentes/MapaUrnas";
import type { EstadoDica } from "../componentes/Dica";
import { Legenda } from "../componentes/Legenda";
import { quantis } from "../lib/escalas";
import { MapaZonas } from "../componentes/MapaZonas";
import type { BaseUF, Urnas, Vereador, Zonas } from "../tipos";
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
                                base, zonas, aoInspecionar }: {
  v: Vereador;
  selecionado: number;
  aoSelecionar: (i: number) => void;
  /** voto por local de votação; existe só onde foi gerado */
  urnas: Urnas | null;
  /** malha do estado, para o mapa das zonas */
  base: BaseUF | null;
  /** zonas eleitorais da UF; ausente onde ainda não foram mapeadas */
  zonas: Zonas | null;
  aoInspecionar: (d: EstadoDica | null) => void;
}) {
  const anos = useMemo(
    () => Object.keys(v.anos).map(Number).sort((a, b) => a - b), [v.anos]);
  const [ano, setAno] = useState(() => anos[anos.length - 1] ?? 2024);
  /** zona em foco no mapa de urnas; `null` é "todas" */
  const [zona, setZona] = useState<number | null>(null);
  const [filtro, setFiltro] = useState("");
  const bloco = v.anos[String(ano)];

  /** As zonas presentes no mapa, com quantos locais cada uma tem.
   *
   *  Só aparece onde há mais de uma: em 242 dos 246 municípios de Goiás a
   *  cidade inteira é uma zona só, e oferecer o filtro ali seria oferecer uma
   *  divisão que não existe. */
  const zonasNoMapa = useMemo(() => {
    if (!urnas) return [] as [number, number][];
    const c = new Map<number, number>();
    urnas.locais.forEach((l) => c.set(l.z, (c.get(l.z) ?? 0) + 1));
    return [...c.entries()].sort((a, b) => a[0] - b[0]);
  }, [urnas]);

  /** Índice do município aberto na malha do estado, e os que dividem a zona
   *  com ele. O pareamento é por código IBGE — `zonas.cods` guarda a mesma
   *  ordem de `base.json` — e nunca por nome: grafia varia, índice não. */
  const noEstado = useMemo(() => {
    if (!zonas || !base || !v.cod) return null;
    const i = zonas.cods.indexOf(v.cod);
    if (i < 0) return null;
    const zs = zonas.porMun[i] ?? [];
    const irmaos = new Set<number>();
    zonas.zonas.forEach((z) => {
      if (zs.includes(z.z)) z.mi.forEach((j) => { if (j !== i) irmaos.add(j); });
    });
    return {
      i, zs,
      irmaos: [...irmaos].map((j) => base.municipios[j]?.n ?? "")
        .filter(Boolean).sort((x, y) => x.localeCompare(y, "pt-BR")),
    };
  }, [zonas, base, v.cod]);

  // Trocar de cidade ou de pleito zera a zona: a 34 de uma cidade não é a 34
  // de outra, e um filtro que sobrevive à troca esconderia a cidade nova atrás
  // de uma seleção feita para a antiga.
  useEffect(() => { setZona(null); }, [urnas]);

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
        {bloco.semTotalizacao && (
          /* Sem isto a tela mostraria "Cadeiras 0" e uma camara vazia, e o
             leitor concluiria que ninguem se elegeu em Aguas Lindas. O que
             houve foi outra coisa: o TSE nao publicou quem se elegeu. Zero e
             ausencia tem a mesma aparencia num numero, e sao opostos. */
          <div className="nota">
            <strong>O TSE não publicou o resultado totalizado deste pleito
            aqui.</strong>{" "}
            Os votos existem e estão nesta tela: vieram do arquivo de votação
            por seção, que o TSE divulga por inteiro. O que não existe é a
            marcação de quem foi eleito — em{" "}
            <code>votacao_candidato_munzona</code> {v.cidade} não aparece com o
            cargo de vereador, e em <code>consulta_cand</code> todos os
            candidatos daqui estão com a situação <code>#NULO</code>. Por isso
            a lista está ordenada por voto, e não por mandato, e cadeiras,
            quociente e último eleito não aparecem: seriam zeros lidos como
            resultado. São 23 municípios do país nessa situação em 2024, oito
            deles em Goiás.
          </div>
        )}
        {/* A segunda metade desta nota dizia "não há mapa", e passou a ser
            falsa no dia em que o mapa de urnas nasceu — ficava escrita logo
            acima dele. O que continua verdade é mais específico: não há
            *coroplético*, porque uma cidade é um município só e o coroplético
            precisa de vários. O mapa que existe é de outro tipo. */}
        <div className="nota">
          <strong>Outro ciclo, outra geografia.</strong> A eleição municipal é
          de 2000, 2004, … 2024 — não há um único ano em comum com os pleitos
          gerais, então esta aba nunca cruza com as outras. E a cidade é um
          município só: não há coroplético aqui, porque pintar área exige várias
          áreas.{" "}
          {urnas && urnas.ano === ano
            ? <>O mapa desta tela é de outro tipo — <em>ponto</em>, um por local
                de votação, dentro do contorno do município. A zona eleitoral, que
                seria a divisão interna natural, o TSE publica sem malha
                desenhada; o local de votação ele publica com coordenada.</>
            : <>A única divisão interna que o TSE publica é a zona eleitoral, e
                ela não tem malha desenhada — há número e não há mapa.</>}
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
                {zonasNoMapa.length > 1 && (
                  <div className="seg-rot" style={{ margin: "2px 0 12px" }}>
                    <span className="et">Zona eleitoral</span>
                    <div className="seg" role="group" aria-label="Zona eleitoral">
                      <button aria-pressed={zona === null}
                              onClick={() => setZona(null)}>todas</button>
                      {zonasNoMapa.map(([z, n]) => (
                        <button key={z} aria-pressed={zona === z}
                                title={`${n} local(is) de votação`}
                                onClick={() => setZona(zona === z ? null : z)}>
                          {z}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <MapaUrnas
                  realce={zona == null ? undefined
                    : (i) => urnas.locais[i]?.z === zona}
                  contorno={urnas.geo}
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
                {zonasNoMapa.length > 1 && (
                  <div className="nota" style={{ marginTop: 12 }}>
                    <strong>A zona eleitoral entra por seleção, e não por
                    cor.</strong> São {zonasNoMapa.length} zonas aqui, e elas não
                    são bairros: se interpenetram no mapa — em Goiânia, 19 dos 36
                    pares de zonas têm áreas sobrepostas. {zonasNoMapa.length} cores
                    embaralhadas no mesmo espaço não se leem; uma zona de cada vez
                    mostra exatamente onde ela está e o quanto se mistura com as
                    vizinhas. Os demais locais ficam apagados em vez de sumir,
                    para a cidade continuar à vista por trás.
                  </div>
                )}
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

            {noEstado && base && zonas && (
              <div className="cartaz">
                <h2>A zona de {v.cidade} no estado</h2>
                <p className="cap">
                  {noEstado.zs.length === 1
                    ? <>A <strong>zona {noEstado.zs[0]}</strong>{" "}
                        {noEstado.irmaos.length
                          ? <>cobre {v.cidade} e mais{" "}
                              {numero(noEstado.irmaos.length)} município(s).</>
                          : <>cobre só {v.cidade}.</>}</>
                    : <>{v.cidade} sozinha contém{" "}
                        <strong>{noEstado.zs.length} zonas</strong>{" "}
                        ({noEstado.zs.join(", ")}) — por isso ela sai hachurada,
                        e não pintada: a divisão existe dentro da cidade, e não
                        há fronteira publicada para desenhá-la.</>}{" "}
                  A cor não identifica a zona: ela só impede que duas vizinhas
                  se confundam. São {zonas.nCores} cores para{" "}
                  {numero(zonas.zonas.length)} zonas.
                </p>
                <MapaZonas geo={base.geo} municipios={base.municipios}
                           zonas={zonas} idx={noEstado.i}
                           aoInspecionar={aoInspecionar} />
                {noEstado.irmaos.length > 0 && (
                  <p className="cap" style={{ marginTop: 10 }}>
                    <strong>Divide a zona com:</strong>{" "}
                    {noEstado.irmaos.join(" · ")}.
                  </p>
                )}
                <div className="nota" style={{ marginTop: 12 }}>
                  <strong>A zona não cabe dentro do município — ela contém
                  municípios.</strong> Em Goiás, 68 das 92 zonas cobrem mais de
                  um, e 242 dos 246 municípios pertencem a uma zona só. É o que
                  torna este mapa possível sem inventar fronteira: onde todos os
                  municípios de uma zona são exclusivos dela, o limite da zona
                  <em> é</em> a soma de limites municipais que o IBGE publicou.
                  São 75 das 92 assim.
                  <br /><br />
                  As outras 17 encostam em Goiânia, Anápolis, Aparecida ou Rio
                  Verde — as quatro cidades que sozinhas contêm várias zonas — e
                  por isso não fecham fronteira: basta um pedaço da zona cair
                  dentro de um município dividido para o limite dela deixar de
                  existir no mapa. São <strong>12 municípios hachurados</strong>:
                  os 4 divididos e mais 8 inteiros que dividem zona com eles.
                  Ali a separação é por seção eleitoral, e seção não tem área —
                  são 3.040 delas em 354 endereços só em Goiânia. Quem quiser ver
                  zona nessas cidades usa o mapa de urnas acima, onde cada local
                  de votação traz a sua.
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
              /* Cadeiras, "por cadeira", último eleito e a razão para ele são
                 medidas do CORTE DE MANDATO. Sem totalização não há corte, e
                 imprimir zero ali seria oferecer um resultado no lugar de uma
                 ausência. */
              ...(bloco.semTotalizacao ? [
                { rotulo: "Candidatos", valor: numero(bloco.pleito.nCand),
                  explicacao: "nenhum eleito publicado" },
                { rotulo: "Mais votado", valor: numero(bloco.pleito.maior),
                  explicacao: "maior votação apurada" },
              ] : [
                { rotulo: "Cadeiras", valor: numero(bloco.pleito.cadeiras),
                  explicacao: "eleitos na câmara" },
                { rotulo: "Candidatos", valor: numero(bloco.pleito.nCand),
                  explicacao: `${decimal(bloco.pleito.nCand / Math.max(bloco.pleito.cadeiras, 1), 1)} por cadeira` },
                { rotulo: "Último eleito", valor: numero(bloco.pleito.ultimo),
                  explicacao: "menor votação que entrou" },
                { rotulo: "Mais votado", valor: numero(bloco.pleito.maior),
                  explicacao: `${decimal(bloco.pleito.maior / Math.max(bloco.pleito.ultimo, 1), 1)}× o último` },
              ]),
              ...(bloco.semTotalizacao ? [] : [
                { rotulo: "Reincidência", valor: percentual(bloco.pleito.rePct, 1),
                  explicacao: "eleitos que já haviam concorrido antes" },
              ]),
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
