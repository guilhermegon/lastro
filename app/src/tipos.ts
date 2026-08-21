/** Formas do dado servido em /dados. Espelham o que 18_dados_web.py grava —
 *  mudou lá, muda aqui, e o compilador aponta quem quebrou. */

export type Sigla = string;

export interface ResumoUF {
  /** sigla, ex. "GO" */ s: Sigla;
  /** nome por extenso */ n: string;
  /** quantidade de municípios */ nm: number;
}

export interface AgregadoUF {
  uf: Sigla;
  ano: number;
  /** cadeiras na assembleia */ cad: number;
  /** candidatos no pleito */ cand: number;
  /** total de votos nominais */ tot: number;
  /** municípios do estado */ nmun: number;
  /** quociente eleitoral aproximado */ qe: number;
  /** votos do último eleito */ ult: number;
  /** municípios efetivos, mediana dos eleitos */ ef: number;
  /** fatia do maior município, mediana */ t1: number;
  /** gini municipal, mediana */ gi: number;
}

export interface FeicaoUF {
  cod: string;
  geom: { type: "Polygon" | "MultiPolygon"; coordinates: number[][][] | number[][][][] };
}

export interface Indice {
  anos: number[];
  ufs: ResumoUF[];
  agregado: AgregadoUF[];
  malhaUF: FeicaoUF[];
}

export interface Municipio {
  /** nome */ n: string;
  /** código IBGE */ c: string;
}

export interface Candidato {
  /** nome de urna */ n: string;
  /** sigla do partido à época */ p: string;
  /** sigla após resolver fusões */ pn: string;
  /** total de votos nominais */ t: number;
  /** municípios com voto */ nm: number;
  /** fatia do maior município, % */ t1: number;
  /** fatia dos cinco maiores, % */ t5: number;
  /** municípios efetivos */ ef: number;
  /** gini municipal */ gi: number;
  /** índice do município reduto, -1 se desconhecido */ r: number;
  /** índices de município com voto */ mi: number[];
  /** votos, na mesma ordem de mi */ mv: number[];
}

/** Um município é uma lista de polígonos; cada polígono, uma lista de pontos. */
export type GeometriaMunicipio = [number, number][][];

export interface DadosUF {
  uf: Sigla;
  nome: string;
  municipios: Municipio[];
  geo: (GeometriaMunicipio | null)[];
  eleitos: Record<string, Candidato[]>;
  totais: Record<string, number[]>;
}
