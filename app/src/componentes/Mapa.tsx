import { useMemo, type ReactNode } from "react";
import type { GeometriaMunicipio } from "../tipos";
import { projetar } from "../lib/projecao";
import { corDaFaixa } from "../lib/escalas";
import type { EstadoDica } from "./Dica";

interface Props {
  geo: (GeometriaMunicipio | null)[];
  valores: number[];
  cortes: number[];
  rotulo: string;
  /** conteúdo do balão para o município i */
  descrever: (i: number, valor: number) => ReactNode;
  aoInspecionar: (d: EstadoDica | null) => void;
  /** quando existe, cada feição vira alvo de clique — é assim que o mapa
   *  nacional serve de porta de entrada para o estado */
  aoClicar?: (i: number) => void;
}

/**
 * Coroplético. O mesmo componente serve município e UF: quem chama decide a
 * geometria e a escala.
 *
 * Os eventos cobrem mouse e toque. Em tela de toque não existe hover, e sem
 * `touchStart` o mapa vira desenho mudo no celular — dá para ver a mancha e não
 * dá para saber o que ela é.
 */
export function Mapa({ geo, valores, cortes, rotulo, descrever, aoInspecionar,
                       aoClicar }: Props) {
  const { caminhos, largura, altura } = useMemo(() => projetar(geo), [geo]);

  return (
    <svg viewBox={`0 0 ${largura} ${altura}`} role="img" aria-label={`Mapa: ${rotulo}`}>
      {caminhos.map((d, i) => {
        if (!d) return null;
        const v = valores[i] ?? 0;
        const mostrar = (x: number, y: number) =>
          aoInspecionar({ conteudo: descrever(i, v), x, y });
        return (
          <path
            key={i}
            d={d}
            className="mun"
            fill={corDaFaixa(v, cortes)}
            onMouseMove={(e) => mostrar(e.clientX, e.clientY)}
            onMouseLeave={() => aoInspecionar(null)}
            onTouchStart={(e) => {
              const t = e.touches[0];
              if (t) mostrar(t.clientX, t.clientY);
            }}
            onClick={aoClicar ? () => aoClicar(i) : undefined}
            style={aoClicar ? { cursor: "pointer" } : undefined}
          />
        );
      })}
    </svg>
  );
}
