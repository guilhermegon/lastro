import type { Afericao, Rival } from "../tipos";
import { decimal, percentual } from "../lib/formato";
import { token } from "../lib/escalas";

/**
 * Quem disputa o mesmo chão que este eleito — não quem teve votação de tamanho
 * parecido. As duas colunas vêm da distância ideológica entre os partidos, que
 * é juízo externo (`data/overrides/partidos_espectro.csv`), não dado eleitoral.
 */
export function Rivais({ aliados, adversarios, afericao, ano, municipios }: {
  aliados: Rival[] | undefined;
  adversarios: Rival[] | undefined;
  afericao: Afericao | undefined;
  ano: number;
  municipios: { n: string }[];
}) {
  const teto = Math.max(
    ...[...(aliados ?? []), ...(adversarios ?? [])].map((r) => r.pr), 1);

  // Sem municípios não há geografia a medir. No Distrito Federal, que é um
  // município só, o cosseno entre dois candidatos quaisquer dá exatamente
  // 1,000: o painel pareceria certo e estaria ordenando por tamanho de
  // votação, não por território disputado.
  if (municipios.length < 3) {
    return (
      <div className="cartaz">
        <h2>Rivais territoriais</h2>
        <p className="cap">
          Não se mede aqui. Rivalidade territorial compara como dois candidatos
          se distribuem pelos municípios, e esta unidade tem{" "}
          {municipios.length === 1 ? "um município só"
            : `apenas ${municipios.length} municípios`}. Sem chão para dividir,
          qualquer par sairia com afinidade máxima e a lista estaria ordenando
          tamanho de votação, não território.
        </p>
      </div>
    );
  }

  if (!aliados?.length && !adversarios?.length) {
    return (
      <div className="cartaz">
        <h2>Rivais territoriais</h2>
        <p className="cap">
          Sem rival apurável neste pleito — a medida exige pelo menos mil votos
          do outro lado, abaixo disso o mapa municipal é ruído e não geografia.
        </p>
      </div>
    );
  }

  return (
    <div className="cartaz">
      <h2>Rivais territoriais</h2>
      <p className="cap">
        Quem disputa o mesmo chão. <strong>Pressão</strong> é a fatia do voto
        deste eleito que está em municípios onde o rival também é forte — não é
        simétrica, um gigante pressiona um pequeno muito mais que o contrário.{" "}
        <strong>Afinidade</strong> é o quanto os dois mapas têm o mesmo formato.
      </p>

      <div className="duas">
        <Coluna titulo="Aliados" sub="mesma faixa ideológica ou vizinha"
                itens={aliados} teto={teto} cor="--s4" municipios={municipios} />
        <Coluna titulo="Adversários" sub="duas faixas de distância ou mais"
                itens={adversarios} teto={teto} cor="--s2" municipios={municipios} />
      </div>

      {afericao && <Afere a={afericao} ano={ano} />}
    </div>
  );
}

function Coluna({ titulo, sub, itens, teto, cor, municipios }: {
  titulo: string; sub: string; itens: Rival[] | undefined;
  teto: number; cor: string; municipios: { n: string }[];
}) {
  return (
    <div>
      <h3 style={{ font: "inherit", fontWeight: 600, margin: "0 0 2px" }}>
        {titulo}
      </h3>
      <p className="cap" style={{ marginTop: 0 }}>{sub}</p>
      {!itens?.length ? (
        <p className="cap">Nenhum neste pleito.</p>
      ) : (
        <ul className="rivais">
          {itens.map((r, i) => (
            <li key={`${r.n}-${i}`}>
              <div className="rival-topo">
                <span className="rival-nome">
                  {r.n}
                  {r.el && <span className="rival-el" title="eleito"> ●</span>}
                </span>
                <span className="num">{percentual(r.pr, 1)}</span>
              </div>
              <div className="rival-barra" aria-hidden="true">
                <span style={{ width: `${(r.pr / teto) * 100}%`,
                               background: token(cor) }} />
              </div>
              <div className="cap">
                {r.p} · afinidade <span className="num">{decimal(r.af, 3)}</span>
                {r.mun.length > 0 && (
                  <> · disputam{" "}
                    {r.mun.map((m) => municipios[m]?.n ?? "—").join(", ")}</>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * O controle que impede ler demais no resultado. Em Goiás o rival nº 1 sai
 * aliado na maioria dos casos, e isso parece achado até se perguntar quantas
 * candidaturas já estão na mesma faixa: se dois terços estão, aliado venceria
 * por acaso. O número que sobrevive sozinho é o pareado.
 */
function Afere({ a, ano }: { a: Afericao; ano: number }) {
  if (a.observado == null || a.esperado == null) return null;
  const excesso = a.observado - a.esperado;
  return (
    <div className="nota" style={{ marginTop: 14 }}>
      <strong>O rival nº 1 ser aliado é achado ou composição?</strong> Em {ano},
      o rival mais pressionante foi um aliado para{" "}
      <span className="num">{percentual(a.observado, 1)}</span> dos eleitos — mas{" "}
      <span className="num">{percentual(a.esperado, 1)}</span> das candidaturas
      já estavam na mesma faixa ideológica, então boa parte disso sai por acaso
      ({excesso >= 0 ? "+" : ""}{decimal(excesso, 1)} pp de excesso).
      {a.pareado != null && a.nPar > 0 && (
        <>
          {" "}O teste que controla isso é pareado, dentro do mesmo eleito: o
          aliado pressiona{" "}
          <span className="num">
            {a.pareado >= 0 ? "+" : ""}{decimal(a.pareado, 2)} pp
          </span>{" "}
          a mais que o adversário na mediana, e pressiona mais em{" "}
          <span className="num">{a.aliadoMais}</span> de{" "}
          <span className="num">{a.nPar}</span> eleitos.
        </>
      )}
    </div>
  );
}
