import type { GeometriaMunicipio } from "../tipos";

export interface Projecao {
  /** um caminho SVG por município, "" quando não há geometria */
  caminhos: string[];
  /** centroide projetado de cada município, para ancorar marca e rótulo */
  pontos: ([number, number] | null)[];
  largura: number;
  altura: number;
}

/**
 * Centroide de área do anel, e não a média dos vértices.
 *
 * A média simples puxa o ponto para onde o desenho tem mais vértices — o lado
 * recortado do município —, e a marca da capital sairia deslocada justamente
 * nos municípios de fronteira irregular. A fórmula de área não tem esse viés.
 * Quando a área degenera (anel com menos de três pontos, ou colinear), cai na
 * média, que aí é o que existe.
 */
function centroide(anel: readonly (readonly [number, number])[]): [number, number] {
  let a2 = 0, cx = 0, cy = 0;
  for (let i = 0, j = anel.length - 1; i < anel.length; j = i++) {
    const p0 = anel[j] as readonly [number, number];
    const p1 = anel[i] as readonly [number, number];
    const f = p0[0] * p1[1] - p1[0] * p0[1];
    a2 += f;
    cx += (p0[0] + p1[0]) * f;
    cy += (p0[1] + p1[1]) * f;
  }
  if (Math.abs(a2) < 1e-12) {
    const n = Math.max(anel.length, 1);
    return [anel.reduce((s, p) => s + p[0], 0) / n,
            anel.reduce((s, p) => s + p[1], 0) / n];
  }
  const a3 = a2 * 3;
  return [cx / a3, cy / a3];
}

/** Num MultiPolygon manda a maior ilha: a marca vai no corpo do município, não
 *  numa ilha solta que por acaso veio primeiro na lista. */
function maiorAnel(municipio: readonly (readonly (readonly [number, number])[])[]) {
  let melhor: readonly (readonly [number, number])[] = municipio[0] ?? [];
  let area = -1;
  for (const anel of municipio) {
    let a2 = 0;
    for (let i = 0, j = anel.length - 1; i < anel.length; j = i++) {
      const p0 = anel[j] as readonly [number, number];
      const p1 = anel[i] as readonly [number, number];
      a2 += p0[0] * p1[1] - p1[0] * p0[1];
    }
    const abs = Math.abs(a2);
    if (abs > area) { area = abs; melhor = anel; }
  }
  return melhor;
}

/**
 * Projeta lat/long em coordenadas de tela.
 *
 * Equirretangular com correção de longitude por cos(latitude média). Não é uma
 * projeção cartográfica séria — para um estado, na escala em que isso é
 * desenhado, a distorção é invisível, e ela tem a vantagem de não depender de
 * biblioteca nenhuma. O cosseno importa: sem ele, os estados do Norte ficam
 * esticados na horizontal.
 */
export function projetar(
  geo: (GeometriaMunicipio | null)[],
  larguraAlvo = 560,
): Projecao {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const municipio of geo) {
    if (!municipio) continue;
    for (const anel of municipio) {
      for (const [x, y] of anel) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  if (!Number.isFinite(minX)) {
    return { caminhos: geo.map(() => ""), pontos: geo.map(() => null),
             largura: larguraAlvo, altura: 100 };
  }

  const kx = Math.cos(((minY + maxY) / 2) * (Math.PI / 180));
  const escala = larguraAlvo / ((maxX - minX) * kx || 1);
  const altura = Math.max(120, Math.round((maxY - minY) * escala));

  const caminhos = geo.map((municipio) => {
    if (!municipio) return "";
    return municipio
      .map(
        (anel) =>
          "M" +
          anel
            .map(([x, y]) =>
              `${((x - minX) * kx * escala).toFixed(1)},${((maxY - y) * escala).toFixed(1)}`,
            )
            .join("L") +
          "Z",
      )
      .join(" ");
  });

  const pontos = geo.map((municipio) => {
    if (!municipio || !municipio.length) return null;
    const [x, y] = centroide(maiorAnel(municipio));
    return [(x - minX) * kx * escala, (maxY - y) * escala] as [number, number];
  });

  return { caminhos, pontos, largura: larguraAlvo, altura };
}

/**
 * A malha do Brasil vem em GeoJSON e o resto do projeto trabalha com anéis de
 * pontos. Só o anel externo de cada polígono entra: buracos não existem numa
 * malha de UFs, e num MultiPolygon cada ilha vira o seu próprio anel.
 */
export function feicoesParaGeo(
  feicoes: { coordinates: number[][][] | number[][][][]; type: string }[],
): GeometriaMunicipio[] {
  return feicoes.map((g) => {
    const polys = (g.type === "Polygon" ? [g.coordinates] : g.coordinates) as number[][][][];
    return polys.map((p) => p[0] as [number, number][]) as GeometriaMunicipio;
  });
}

/** Mesma projeção para a malha do Brasil. */
export function projetarFeicoes(
  feicoes: { coordinates: number[][][] | number[][][][]; type: string }[],
  larguraAlvo = 520,
): Projecao {
  return projetar(feicoesParaGeo(feicoes), larguraAlvo);
}
