import { numero } from "../lib/formato";

/** Só nome e total: serve tanto para as fichas de cargo quanto para as de
 *  vereador, que não têm geografia municipal. */
interface Item { n: string; t: number }

interface Props {
  candidatos: Item[];
  selecionado: number;
  filtro: string;
  aoFiltrar: (v: string) => void;
  aoSelecionar: (i: number) => void;
  titulo: string;
}

export function ListaCandidatos({
  candidatos, selecionado, filtro, aoFiltrar, aoSelecionar, titulo,
}: Props) {
  return (
    <div className="rail-bloco rail-primario">
      <p className="rail-titulo">{titulo}</p>
      <input
        className="busca"
        type="search"
        placeholder="Buscar pelo nome"
        aria-label="Buscar candidato"
        value={filtro}
        onChange={(e) => aoFiltrar(e.target.value)}
      />
      <div className="lista">
        {candidatos.length === 0 ? (
          <p className="indice exp">Ninguém com esse nome neste pleito.</p>
        ) : (
          candidatos.map((c, i) => (
            <button
              key={`${c.n}-${i}`}
              aria-pressed={i === selecionado}
              onClick={() => aoSelecionar(i)}
            >
              <span>{c.n}</span>
              <span className="lv">{numero(c.t)}</span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
