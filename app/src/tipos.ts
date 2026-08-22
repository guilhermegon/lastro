/** Formas do dado servido em /dados. Espelham o que 22_publicar_web.py grava —
 *  mudou lá, muda aqui, e o compilador aponta quem quebrou. */

export type Sigla = string;
export type Cargo = "presidente" | "governador" | "senador" | "federal" | "estadual";

export const CARGOS: Cargo[] = [
  "presidente", "governador", "senador", "federal", "estadual",
];

/** Presidente, governador e senador elegem um ou dois: a lista traz todos os
 *  candidatos, não só o vencedor, senão a tela não serviria para nada. */
export const MAJORITARIOS: ReadonlySet<Cargo> = new Set<Cargo>([
  "presidente", "governador", "senador",
]);

export const NOME_CARGO: Record<Cargo, string> = {
  presidente: "Presidente",
  governador: "Governador",
  senador: "Senado",
  federal: "Federal",
  estadual: "Estadual",
};

export interface ResumoUF {
  s: Sigla;
  n: string;
  /** municípios do estado */ nm: number;
  cargos: Cargo[];
}

export interface AgregadoUF {
  uf: Sigla;
  ano: number;
  cad: number;
  cand: number;
  tot: number;
  nmun: number;
  qe: number;
  ult: number;
  /** municípios efetivos, mediana dos eleitos */ ef: number | null;
  /** fatia do maior município, mediana */ t1: number | null;
  /** municípios efetivos sobre o total do estado — comparável entre UFs */
  fr: number | null;
}

export interface FeicaoUF {
  cod: string;
  geom: {
    type: "Polygon" | "MultiPolygon";
    coordinates: number[][][] | number[][][][];
  };
}

export interface Indice {
  anos: number[];
  cargos: Cargo[];
  ufs: ResumoUF[];
  agregado: AgregadoUF[];
  malhaUF: FeicaoUF[];
}

/** Um município é uma lista de polígonos; cada polígono, uma lista de pontos. */
export type GeometriaMunicipio = [number, number][][];

export interface BaseUF {
  uf: Sigla;
  municipios: { n: string }[];
  geo: (GeometriaMunicipio | null)[];
}

export interface Candidato {
  sq: string;
  /** nome de urna */ n: string;
  completo: string;
  chave: string;
  /** sigla à época */ p: string;
  /** sigla após fusões */ pn: string;
  sit: string;
  /** eleito */ el: boolean;
  /** votos nominais */ t: number;
  /** municípios com voto */ nm: number;
  t1: number;
  t5: number;
  /** municípios efetivos */ ef: number;
  gi: number;
  /** domínio médio ponderado, % */ dom: number;
  dommax: number;
  /** municípios com 25% ou mais */ dom25: number;
  /** votos no reduto e vizinhos, % */ contig: number;
  /** índice do município reduto */ r: number;
  tipo: string;
  mi: number[];
  mv: number[];
}

export interface Partido {
  nome: string;
  nc: number;
  ne: number;
  votos: number;
  puxador: number;
  sim: number | null;
}

export interface BlocoAno {
  fichas: Candidato[];
  totalMun: number[];
  /** por município: total apurado, fatia do 1º, candidatos efetivos */
  mm: ({ tot: number; t1: number; ef: number } | null)[];
  vencedorUF: string | null;
  pleito: {
    totalUF: number; nCand: number; cadeiras: number;
    qe: number; ultimo: number; maisVotado: number;
  };
  partidos: Partido[];
  /** agregado por partido sobre TODOS os candidatos, esparso */
  pm?: Record<string, { i: number[]; v: number[] }>;
}

export type DadosCargo = Record<string, BlocoAno>;

export interface Padroes {
  serie: { ano: number; ef: number; t1: number; dom: number; contig: number;
           nm: number; fr: number }[];
  tipologia: { ano: number; tipos: Record<string, number>; n: number }[];
  captura: { faixas: string[];
             anos: { ano: number; t1: (number | null)[]; n: number[] }[] };
  custo: { ano: number; cad: number; cand: number; tot: number;
           qe: number; ult: number }[];
}

export interface Cruzamentos {
  escala: { cargo: Cargo; ano: number; ef: number; t1: number; fr: number }[];
  arrasto: { ano: number; partido: string; nm: number; r: number }[];
  base: { ano: number; mediana: number }[];
  duplas: { ano: number; e: string; ep: string; f: string; fp: string;
            mp: boolean; af: number }[];
  mesmoPartido: { ano: number; pct: number; n: number }[];
}
