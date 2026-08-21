import type { ResumoUF, Sigla } from "../tipos";
import { numero } from "../lib/formato";

interface Props {
  ufs: ResumoUF[];
  atual: Sigla;
  aberto: boolean;
  aoAbrir: (v: boolean) => void;
  aoEscolher: (uf: Sigla) => void;
}

/** Gaveta "Qual seu estado?". `details` nativo: teclado e leitor de tela já
 *  funcionam sem nada extra. */
export function SeletorEstado({ ufs, atual, aberto, aoAbrir, aoEscolher }: Props) {
  const escolhido = ufs.find((u) => u.s === atual);
  return (
    <details className="gaveta" open={aberto} onToggle={(e) => aoAbrir(e.currentTarget.open)}>
      <summary>
        <span className="seta" aria-hidden="true">▸</span>
        Qual seu estado?
        {escolhido && (
          <span className="atual">
            {escolhido.n} · {numero(escolhido.nm)} municípios
          </span>
        )}
      </summary>
      <div className="estados">
        {ufs.map((u) => (
          <button
            key={u.s}
            aria-pressed={u.s === atual}
            onClick={() => aoEscolher(u.s)}
          >
            <span>{u.n}</span>
            <span className="sg">{u.s}</span>
          </button>
        ))}
      </div>
    </details>
  );
}
