import type { GeometriaMunicipio } from "../tipos";

export interface Projecao {
  /** um caminho SVG por município, "" quando não há geometria */
  caminhos: string[];
  largura: number;
  altura: number;
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
  if (!Number.isFinite(minX)) return { caminhos: geo.map(() => ""), largura: larguraAlvo, altura: 100 };

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

  return { caminhos, largura: larguraAlvo, altura };
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
