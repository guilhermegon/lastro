import { token } from "../lib/escalas";

export interface Barra { rotulo: string; valor: number; destaque?: boolean }

/** Barras verticais simples. Não vale uma biblioteca: são 20 linhas e o
 *  controle sobre rótulo e cor é total. */
export function Barras({ itens, formatar, altura = 150 }: {
  itens: Barra[];
  formatar?: (v: number) => string;
  altura?: number;
}) {
  const L = 460, mb = 26, mt = 16, ml = 8;
  const max = Math.max(...itens.map((d) => d.valor), 1);
  const larg = (L - ml * 2) / Math.max(itens.length, 1);
  return (
    <svg viewBox={`0 0 ${L} ${altura}`} role="img" aria-label="gráfico de barras">
      {itens.map((d, i) => {
        const h = Math.max(2, (altura - mb - mt) * (d.valor / max));
        const x = ml + i * larg + larg * 0.18;
        const w = larg * 0.64;
        const y = altura - mb - h;
        return (
          <g key={d.rotulo}>
            <rect x={x} y={y} width={w} height={h} rx={4}
                  fill={token(d.destaque ? "--accent" : "--s4")} />
            {d.valor > 0 && (
              <text x={x + w / 2} y={y - 5} textAnchor="middle" fontSize={11}
                    fill={token("--ink-2")} fontFamily="IBM Plex Mono, monospace">
                {formatar ? formatar(d.valor) : d.valor}
              </text>
            )}
            <text x={x + w / 2} y={altura - mb + 13} textAnchor="middle" fontSize={11}
                  fill={token("--ink-3")} fontFamily="IBM Plex Mono, monospace">
              {d.rotulo}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
