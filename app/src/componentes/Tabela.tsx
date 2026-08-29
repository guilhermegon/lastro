import type { ReactNode } from "react";

/**
 * Tabela de leitura, com rolagem horizontal própria.
 *
 * A rolagem fica no contêiner da tabela e não no corpo da página: tabela larga
 * que empurra o `body` faz a página inteira deslizar de lado no celular, e aí
 * o leitor perde a coluna de referência ao rolar.
 */
export function Tabela({ cab, linhas, rodape, aoClicar, selecionada }: {
  cab: string[];
  linhas: ReactNode[][];
  rodape?: ReactNode[];
  aoClicar?: (i: number) => void;
  selecionada?: number;
}) {
  return (
    <div className="rolagem">
      <table>
        <thead>
          <tr>
            {cab.map((h, i) => (
              <th key={h + i} className={i === 0 ? undefined : "n"}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, li) => (
            <tr key={li}
                aria-selected={aoClicar ? li === selecionada : undefined}
                onClick={aoClicar ? () => aoClicar(li) : undefined}
                style={aoClicar ? { cursor: "pointer" } : undefined}>
              {l.map((v, i) => (
                <td key={i} className={i === 0 ? undefined : "n"}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
        {rodape ? (
          <tfoot>
            <tr>
              {rodape.map((v, i) => (
                <td key={i} className={i === 0 ? undefined : "n"}>{v}</td>
              ))}
            </tr>
          </tfoot>
        ) : null}
      </table>
    </div>
  );
}
