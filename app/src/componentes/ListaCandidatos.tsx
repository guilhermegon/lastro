import type { Candidato } from "../tipos";
import { numero } from "../lib/formato";

interface Props {
  candidatos: Candidato[];
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
          <p className="indice exp">Nenhum eleito com esse nome neste pleito.</p>
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
