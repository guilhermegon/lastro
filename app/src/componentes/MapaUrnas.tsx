import { useMemo, type ReactNode } from "react";
import { corDaFaixa, quantis, SEM_VOTO, token } from "../lib/escalas";
import type { EstadoDica } from "./Dica";

export interface LocalUrna {
  n: string; b: string; z: number;
  lat: number | null; lon: number | null;
  e: number;
}

/** Anéis externos do município, em [lon, lat] — ver `55_contorno_municipio.py`. */
export type Contorno = number[][][];

type Ponto = readonly [number, number];

/** Abaixo desta fração da largura do quadro, os círculos se sobrepõem.
 *
 *  Não é percentil, é pixel: o raio chega a 13 px, então dois locais precisam
 *  de ~30 px entre si para se distinguirem. Com a mediana de 4 locais por
 *  cidade, isso pede ~90 px de mancha num quadro de 560 — 16%. Arredondado
 *  para 22% com folga, porque quatro pontos raramente se distribuem em linha. */
const APERTADO = 0.22;

function caixa(pts: Ponto[]) {
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  return {
    minX: Math.min(...xs), maxX: Math.max(...xs),
    minY: Math.min(...ys), maxY: Math.max(...ys),
  };
}

/**
 * Equirretangular com correção de latitude, enquadrada numa caixa dada.
 *
 * O `kx` é o cosseno da latitude média: sem ele um município de Goiás sai
 * ~4% mais largo do que é, e a mancha de urnas junto com ele.
 */
function enquadrar(
  c: { minX: number; maxX: number; minY: number; maxY: number },
  largura: number, altMax: number, pad: number,
) {
  const kx = Math.cos(((c.minY + c.maxY) / 2) * (Math.PI / 180));
  const dx = (c.maxX - c.minX) * kx || 1e-6;
  const dy = (c.maxY - c.minY) || 1e-6;
  let L = largura;
  let escala = (L - pad * 2) / dx;
  let alt = Math.round(dy * escala) + pad * 2;
  // Cabe reduzindo a LARGURA, nunca esticando: esticar para caber distorceria
  // a geografia, que é justamente o que o mapa afirma.
  if (alt > altMax) {
    escala *= (altMax - pad * 2) / (alt - pad * 2);
    alt = altMax;
    L = Math.round(dx * escala) + pad * 2;
  }
  alt = Math.max(120, alt);
  return {
    L, alt,
    em: (p: Ponto): Ponto =>
      [pad + (p[0] - c.minX) * kx * escala, pad + (c.maxY - p[1]) * escala],
  };
}

function caminho(anel: number[][], em: (p: Ponto) => Ponto) {
  return anel.map((v, i) => {
    const [x, y] = em([v[0] as number, v[1] as number]);
    return `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join("") + "Z";
}

/**
 * Mapa de pontos: um local de votação, uma urna — dentro do município.
 *
 * É o grão mais fino do projeto. No coroplético a unidade é o município e a
 * cor preenche uma área; aqui a unidade é a escola, e a área não existe — um
 * local de votação é um endereço, não um território. Por isso ponto, e não
 * polígono: fingir área onde há endereço inventaria uma fronteira que ninguém
 * desenhou.
 *
 * **O contorno mudou o que este mapa afirma.** Sem ele o quadro se ajustava à
 * própria nuvem de pontos, e então "as urnas estão todas num canto" e "as
 * urnas estão espalhadas" tinham exatamente a mesma aparência — o
 * enquadramento apagava a diferença. Com o município desenhado, a distribuição
 * vira afirmação: numa cidade rural os pontos se juntam na sede e o resto do
 * território fica vazio, que é o fato.
 *
 * **E o fato é o caso comum.** Medido nos 246 municípios de Goiás: a mediana é
 * de 4 locais de votação, e em 109 deles a mancha ocupa menos de 15% da
 * largura do município. Enquadrar no município deixaria esses 109 com os
 * pontos empilhados num borrão — por isso a *lupa*: quando a mancha é apertada
 * demais para o olho separar, entra um segundo quadro, ampliado. O mapa
 * principal continua sendo o município, que é o que foi pedido; a lupa só
 * resolve a legibilidade que a verdade geográfica custou.
 *
 * **A área do círculo é proporcional ao voto, então o raio vai na raiz.** Raio
 * proporcional ao voto faria um local com o dobro dos votos parecer ter quatro
 * vezes mais — o olho lê área, não raio, e é assim que um gráfico de bolha
 * mente sem errar um número.
 *
 * **Todo local aparece, inclusive os de voto zero.** Eles ficam como anel
 * vazio. Sem isso o mapa mostraria só onde o candidato foi votado e o leitor
 * não teria como distinguir "não foi votado aqui" de "não há urna aqui" — que
 * é a mesma confusão entre zero e ausência que o resto do projeto recusa.
 */
export function MapaUrnas({ locais, valores, rotulo, descrever, aoInspecionar,
                            contorno }: {
  locais: LocalUrna[];
  valores: number[];
  rotulo: string;
  descrever: (i: number, valor: number) => ReactNode;
  aoInspecionar: (d: EstadoDica | null) => void;
  /** ausente nos arquivos de capital anteriores ao `55_` — o mapa continua
   *  funcionando sem ele, enquadrado na nuvem, como era antes */
  contorno?: Contorno;
}) {
  const dados = useMemo(() => {
    const pts: (Ponto | null)[] = locais.map((l) =>
      (l.lat != null && l.lon != null ? [l.lon, l.lat] as Ponto : null));
    const vis = pts.filter(Boolean) as Ponto[];
    if (!vis.length) return null;

    const cp = caixa(vis);
    const aneis = contorno?.length ? contorno : null;

    // A caixa do quadro principal é a do município unida à dos pontos: os
    // poucos locais que caem 60 a 90 m fora da fronteira continuam visíveis
    // em vez de sumirem na borda. Ver `55_contorno_municipio.py`.
    let cm = cp;
    if (aneis) {
      const todos = aneis.flat().map((v) => [v[0], v[1]] as Ponto);
      const cg = caixa(todos);
      cm = {
        minX: Math.min(cg.minX, cp.minX), maxX: Math.max(cg.maxX, cp.maxX),
        minY: Math.min(cg.minY, cp.minY), maxY: Math.max(cg.maxY, cp.maxY),
      };
    }

    const principal = enquadrar(cm, 560, 620, 22);
    const larg = (cm.maxX - cm.minX) || 1e-9;
    const altu = (cm.maxY - cm.minY) || 1e-9;
    const mancha = Math.max((cp.maxX - cp.minX) / larg, (cp.maxY - cp.minY) / altu);

    // Lupa só quando há mais de um ponto para separar: com um local só, o
    // ponto único no meio do município já é a informação inteira.
    const lupa = aneis && vis.length > 1 && mancha < APERTADO
      ? enquadrar(cp, 250, 250, 16)
      : null;

    // O retangulo que amarra os dois quadros. Sem ele a lupa e' um segundo
    // desenho solto, e o leitor tem de acreditar na legenda para saber que os
    // dois falam da mesma mancha.
    //
    // A marca ENVOLVE os circulos, nao a caixa das coordenadas: a mancha aqui
    // e' sub-pixel e o raio chega a 13 px, entao um retangulo do tamanho da
    // caixa real ficaria inteiro debaixo dos pontos — desenhado e invisivel.
    // Dai o piso de 40 px e a folga de 24.
    let marca = null;
    if (lupa) {
      const [x1, y1] = principal.em([cp.minX, cp.maxY]);
      const [x2, y2] = principal.em([cp.maxX, cp.minY]);
      const L = Math.max(40, x2 - x1 + 24), A = Math.max(40, y2 - y1 + 24);
      marca = { x: (x1 + x2) / 2 - L / 2, y: (y1 + y2) / 2 - A / 2, L, A };
    }

    return { pts, principal, lupa, aneis, mancha, marca };
  }, [locais, contorno]);

  const cortes = useMemo(
    () => quantis(valores.filter((v) => v > 0)), [valores]);
  const maior = useMemo(
    () => Math.max(1, ...valores.filter((v) => Number.isFinite(v))), [valores]);

  if (!dados) return <p className="indice exp">Sem coordenada para desenhar.</p>;

  // área ∝ voto ⇒ raio ∝ √voto — ver docstring
  const raio = (v: number, k = 1) =>
    (v > 0 ? 2.2 + 11 * Math.sqrt(v / maior) : 2.4) * k;

  const circulos = (em: (p: Ponto) => Ponto, k: number) =>
    locais.map((_l, i) => {
      const p = dados.pts[i];
      if (!p) return null;
      const [cx, cy] = em(p);
      const v = valores[i] ?? 0;
      const r = raio(v, k);
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
          <circle key={i} cx={cx} cy={cy} r={r} fill="none"
                  stroke={token(SEM_VOTO)} strokeWidth="1.2" {...comum} />
        );
      }
      return (
        <circle key={i} cx={cx} cy={cy} r={r}
                fill={corDaFaixa(v, cortes)}
                stroke="var(--surface)" strokeWidth="1.1"
                fillOpacity="0.86" {...comum} />
      );
    });

  const municipio = (em: (p: Ponto) => Ponto) => dados.aneis?.map((a, i) => (
    <path key={i} d={caminho(a, em)}
          fill="var(--surface-2)" stroke="var(--line-strong)"
          strokeWidth="1.1" strokeLinejoin="round" />
  ));

  return (
    <div className="urnas-quadros">
      <svg viewBox={`0 0 ${dados.principal.L} ${dados.principal.alt}`} role="img"
           aria-label={`${rotulo} por local de votação, no município`}
           style={{ width: "100%", maxWidth: dados.principal.L, height: "auto",
                   display: "block", margin: "0 auto" }}>
        {municipio(dados.principal.em)}
        {dados.marca && (
          <rect x={dados.marca.x} y={dados.marca.y}
                width={dados.marca.L} height={dados.marca.A}
                rx="3" fill="none" stroke="var(--ink-3)"
                strokeWidth="1.1" strokeDasharray="3 2" />
        )}
        {circulos(dados.principal.em, 1)}
      </svg>

      {dados.lupa && (
        <figure className="urnas-lupa">
          <svg viewBox={`0 0 ${dados.lupa.L} ${dados.lupa.alt}`} role="img"
               aria-label={`${rotulo}, aproximação dos locais de votação`}
               style={{ width: "100%", maxWidth: dados.lupa.L, height: "auto",
                       display: "block" }}>
            {circulos(dados.lupa.em, 0.72)}
          </svg>
          <figcaption>
            De perto — o tracejado no mapa ao lado. A mancha de urnas ocupa{" "}
            <span className="num">{(dados.mancha * 100).toFixed(0)}%</span>{" "}
            da largura do município — apertada demais para o olho separar no
            mapa ao lado.
          </figcaption>
        </figure>
      )}
    </div>
  );
}
