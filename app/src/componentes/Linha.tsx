import { token } from "../lib/escalas";

export interface Serie { rotulo: string; cor: string; pontos: (number | null)[] }

/** Uma ou mais séries no mesmo eixo. Nunca dois eixos: duas medidas de escalas
 *  diferentes viram dois gráficos, não um com dois eixos. */
export function Linha({ eixoX, series, casas = 1, altura = 190 }: {
  eixoX: (string | number)[];
  series: Serie[];
  casas?: number;
  altura?: number;
}) {
  const L = 620, ml = 40, mr = 14, mt = 14, mb = 26;
  const vals = series.flatMap((s) => s.pontos).filter((v): v is number => v != null);
  if (!vals.length) return <p className="indice exp">Sem dado para o período.</p>;
  const hi = Math.max(...vals) * 1.1;
  const px = (i: number) => ml + ((L - ml - mr) * i) / Math.max(eixoX.length - 1, 1);
  const py = (v: number) => mt + (altura - mt - mb) * (1 - v / (hi || 1));

  return (
    <svg viewBox={`0 0 ${L} ${altura}`} role="img" aria-label="série temporal">
      {[0, hi / 2, hi].map((v) => (
        <g key={v}>
          <line x1={ml} x2={L - mr} y1={py(v)} y2={py(v)}
                stroke={token("--line")} strokeWidth={1} />
          <text x={ml - 6} y={py(v) + 3} textAnchor="end" fontSize={11}
                fill={token("--ink-3")} fontFamily="IBM Plex Mono, monospace">
            {v.toFixed(casas)}
          </text>
        </g>
      ))}
      {series.map((s) => {
        const pts = s.pontos
          .map((v, i) => (v == null ? null : [px(i), py(v)] as const))
          .filter((p): p is readonly [number, number] => p != null);
        if (!pts.length) return null;
        return (
          <g key={s.rotulo}>
            <path d={"M" + pts.map((q) => `${q[0].toFixed(1)},${q[1].toFixed(1)}`).join("L")}
                  fill="none" stroke={token(s.cor)} strokeWidth={2.5} strokeLinejoin="round" />
            {pts.map((q, i) => (
              <circle key={i} cx={q[0]} cy={q[1]} r={i === pts.length - 1 ? 5 : 3.5}
                      fill={token(s.cor)} stroke={token("--surface")} strokeWidth={2} />
            ))}
          </g>
        );
      })}
      {eixoX.map((r, i) => (
        <text key={i} x={px(i)} y={altura - 8} textAnchor="middle" fontSize={11}
              fill={token("--ink-3")} fontFamily="IBM Plex Mono, monospace">
          {r}
        </text>
      ))}
    </svg>
  );
}
