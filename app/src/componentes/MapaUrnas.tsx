import { useMemo, type ReactNode } from "react";
import { corDaFaixa, quantis, SEM_VOTO, token } from "../lib/escalas";
import type { EstadoDica } from "./Dica";

export interface LocalUrna {
  n: string; b: string; z: number;
  lat: number | null; lon: number | null;
  e: number;
}

/**
 * Mapa de pontos: um local de votação, uma urna.
 *
 * É o grão mais fino do projeto. No coroplético a unidade é o município e a
 * cor preenche uma área; aqui a unidade é a escola, e a área não existe — um
 * local de votação é um endereço, não um território. Por isso ponto, e não
 * polígono: fingir área onde há endereço inventaria uma fronteira que ninguém
 * desenhou.
 *
 * **A área do círculo é proporcional ao voto, então o raio vai na raiz.** Raio
 * proporcional ao voto faria um local com o dobro dos votos parecer ter quatro
 * vezes mais — o olho lê área, não raio, e é assim que um gráfico de bolha
 * mente sem errar um número.
 *
 * **Todo local aparece, inclusive os de voto zero.** Eles ficam como anel vazio.
 * Sem isso o mapa mostraria só onde o candidato foi votado e o leitor não teria
 * como distinguir "não foi votado aqui" de "não há urna aqui" — que é a mesma
 * confusão entre zero e ausência que o resto do projeto recusa.
 */
export function MapaUrnas({ locais, valores, rotulo, descrever, aoInspecionar }: {
  locais: LocalUrna[];
  valores: number[];
  rotulo: string;
  descrever: (i: number, valor: number) => ReactNode;
  aoInspecionar: (d: EstadoDica | null) => void;
}) {
  const proj = useMemo(() => {
    const pts = locais.map((l) =>
      (l.lat != null && l.lon != null ? [l.lon, l.lat] as const : null));
    const vis = pts.filter(Boolean) as (readonly [number, number])[];
    if (!vis.length) return null;
    const xs = vis.map((p) => p[0]), ys = vis.map((p) => p[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    // mesma equirretangular do coroplético: cos da latitude média, senão a
    // cidade sai esticada na horizontal
    const kx = Math.cos(((minY + maxY) / 2) * (Math.PI / 180));
    // A caixa da cidade pode ser bem mais alta que larga — Goiania tem 0,36 de
    // latitude para 0,24 de longitude corrigida, e ao largo total isso daria 822
    // px de altura. Cabe na tela reduzindo a LARGURA e mantendo a proporcao:
    // esticar para caber distorceria a geografia, que e' o que o mapa afirma.
    const ALT_MAX = 620;
    let L = 560;
    const pad = 22;
    let escala = (L - pad * 2) / ((maxX - minX) * kx || 1);
    let alt = Math.round((maxY - minY) * escala) + pad * 2;
    if (alt > ALT_MAX) {
      escala *= (ALT_MAX - pad * 2) / (alt - pad * 2);
      alt = ALT_MAX;
      L = Math.round((maxX - minX) * kx * escala) + pad * 2;
    }
    alt = Math.max(200, alt);
    return {
      L, alt,
      pos: pts.map((p) => p
        ? [pad + (p[0] - minX) * kx * escala, pad + (maxY - p[1]) * escala] as const
        : null),
    };
  }, [locais]);

  const cortes = useMemo(
    () => quantis(valores.filter((v) => v > 0)), [valores]);
  const maior = useMemo(
    () => Math.max(1, ...valores.filter((v) => Number.isFinite(v))), [valores]);

  if (!proj) return <p className="indice exp">Sem coordenada para desenhar.</p>;

  // área ∝ voto ⇒ raio ∝ √voto — ver docstring
  const raio = (v: number) => (v > 0 ? 2.2 + 11 * Math.sqrt(v / maior) : 2.4);

  return (
    <svg viewBox={`0 0 ${proj.L} ${proj.alt}`} role="img"
         aria-label={`${rotulo} por local de votação`}
         style={{ width: "100%", maxWidth: proj.L, height: "auto",
                 display: "block", margin: "0 auto" }}>
      {locais.map((_l, i) => {
        const p = proj.pos[i];
        if (!p) return null;
        const v = valores[i] ?? 0;
        const r = raio(v);
        const comum = {
          onMouseEnter: (e: React.MouseEvent) =>
            aoInspecionar({ x: e.clientX, y: e.clientY, conteudo: descrever(i, v) }),
          onMouseLeave: () => aoInspecionar(null),
          onTouchStart: (e: React.TouchEvent) => {
            const t = e.touches[0];
            if (t) aoInspecionar({ x: t.clientX, y: t.clientY, conteudo: descrever(i, v) });
          },
          style: { cursor: "pointer" as const },
        };
        // sem voto: anel vazio, para "não foi votado aqui" não virar "não há
        // urna aqui" — ver docstring
        if (v <= 0) {
          return (
            <circle key={i} cx={p[0]} cy={p[1]} r={r} fill="none"
                    stroke={token(SEM_VOTO)} strokeWidth="1.2" {...comum} />
          );
        }
        return (
          <circle key={i} cx={p[0]} cy={p[1]} r={r}
                  fill={corDaFaixa(v, cortes)}
                  stroke="var(--surface)" strokeWidth="1.1"
                  fillOpacity="0.86" {...comum} />
        );
      })}
    </svg>
  );
}
