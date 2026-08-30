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

/** O DF nao elege deputado estadual: elege **distrital**, para a Camara
 *  Legislativa, que acumula as competencias de assembleia e de camara municipal.
 *  O dado entra no painel sob a chave `estadual` — e' o que torna as 27 unidades
 *  comparaveis entre si — mas o rotulo tem de dizer o nome do cargo que existe.
 *  Chave para comparar, rotulo para nao mentir. */
export function nomeCargo(c: Cargo, uf?: Sigla): string {
  return c === "estadual" && uf === "DF" ? "Distrital" : NOME_CARGO[c];
}

export interface ResumoUF {
  s: Sigla;
  n: string;
  /** municípios do estado */ nm: number;
  cargos: Cargo[];
  /** capital do estado — a marca no mapa. Existe também no DF, que tem
   *  capital e não tem câmara municipal: não confundir com `ver`. */
  capital?: string;
  /** há arquivo de vereador para esta UF — é isto que liga a aba */
  ver?: boolean;
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

/** Um rival territorial: quem disputa o mesmo chão, não quem teve votação de
 *  tamanho parecido. `pr` é assimétrico — um gigante pressiona um pequeno
 *  muito mais do que o contrário; `af` é o cosseno, e é simétrico. */
export interface Rival {
  n: string;
  p: string;
  /** banda ideológica */ b: string;
  el: boolean;
  t: number;
  /** afinidade: quanto os dois mapas têm o mesmo formato */ af: number;
  /** pressão, % do voto do eleito em chão onde o rival é forte */ pr: number;
  /** índices, em `BaseUF.municipios`, do chão onde os dois mais se encostam */
  mun: number[];
}

/**
 * Aferição do achado "o rival nº 1 costuma ser aliado".
 *
 * `observado` sozinho não vale nada: se a maioria das candidaturas já está na
 * mesma faixa ideológica, aliado venceria por acaso — é o que `esperado` mede.
 * O número que sobrevive sozinho é `pareado`: para o MESMO eleito, quanto o
 * aliado mais pressionante pressiona a mais que o adversário mais pressionante.
 */
export interface Afericao {
  n: number;
  esperado: number | null;
  observado: number | null;
  pareado: number | null;
  nPar: number;
  aliadoMais: number;
}

export interface BlocoRivais {
  fichas: Record<string, { b: string; al?: Rival[]; ad?: Rival[] }>;
  afericao: Afericao;
}

/** Um arquivo por UF e por cargo, indexado por ano — quem abre o estadual de
 *  São Paulo não deve pagar pelo federal. Só os proporcionais têm: nos
 *  majoritários a disputa não se dá dentro de uma lista, e "rival" seria o
 *  próprio adversário da eleição, que a tela do cargo já mostra inteiro. */
export type CargoComRival = "estadual" | "federal";
export type Rivais = Record<string, BlocoRivais>;

/* ---------- Emendômetro ----------
   A emenda tem a mesma forma do voto — `mi`/`mv` por município — de propósito:
   é o que permite ao mapa e às tabelas serem os mesmos componentes. O que muda
   é o que o número significa, e isso a tela diz em palavras. */

export interface FichaEmenda {
  n: string;
  /** pago no ano, em reais */
  t: number;
  /** parte do pago que é Transferência Especial, a "emenda Pix" */
  pix: number;
  /** municípios e valores só do Pix */
  pxi: number[];
  pxv: number[];
  emp: number;
  /** nº de emendas e de municípios alcançados */
  ne: number;
  nm: number;
  mi: number[];
  mv: number[];
  /** concentração: fatia do maior município, municípios efetivos, Gini */
  t1: number;
  ef: number;
  gi: number;
  /** o autor foi eleito, e por qual UF */
  el: boolean;
  ufEl: string;
  /** emenda de bancada/comissão, sem autor individual */
  amb: boolean;
  /** função orçamentária dominante */
  fn: string;
}

export interface BlocoEmenda {
  totalMun: number[];
  totalPix: number[];
  fichas: FichaEmenda[];
  pleito: {
    pago: number; emp: number; nAutores: number; nEmendas: number;
    nMun: number; pix: number; nPix: number; cortados: number;
  };
  partidos?: { nome: string; v: number; n: number }[];
}

export interface Emendas {
  anos: Record<string, BlocoEmenda>;
  /** o denominador honesto: quanto do total tem município identificado */
  cobertura: { pago: number; pagoMun: number; pix: number; pixMun: number };
  esfera?: string;
}

export interface EmendasBR {
  anos: number[];
  uf: { uf: string; ano: number; pago: number; pix: number; emp: number;
        n: number; aut: number; pagoMun: number; nMun: number }[];
  cobertura: { pago: number; pagoMun: number; pix: number; pixMun: number };
}

/** População e área por município, na ordem de `base.municipios`.
 *  `null` onde o IBGE não tem o município — nunca zero, que seria um valor. */
export interface Demografia {
  pop: (number | null)[];
  area: (number | null)[];
}

export type Esfera = "federal" | "estadual";

/* ---------- aba API: o que as assembleias publicam sobre si mesmas ----------
   Estes tipos descrevem seis arquivos de origens diferentes — duas APIs REST e
   um CKAN — e por isso não têm forma comum. Tentar unificá-los esconderia
   justamente o achado: cada casa publica um pedaço diferente do mesmo objeto. */

export interface CasaLegislativa {
  sigla: string;
  /** conjuntos de dados encontrados no portal */
  n: number;
  url: string;
  /** API confirmada: devolve JSON consumível */
  conf: boolean;
  obs: string;
  assuntos: number | null;
}
export type Assembleias = Record<string, CasaLegislativa>;

export interface AlegoVerbas {
  fonte: string;
  periodo: [number, number];
  total: { apresentado: number; indenizado: number; glosa: number;
           nDeputados: number; nCasados: number };
  serie: { ano: number; indenizado: number; glosa: number;
           deputados: number; meses: number }[];
  deputados: { n: string; t: number; g: number; pg: number; m: number;
               ms: number; el: boolean }[];
}

export interface AlegoAdmin {
  fonte: string;
  anos: [number, number];
  orcamento: { ano: number; autorizado: number; pessoal: number;
               custeio: number; investimento: number }[];
  diarias?: { n: number; nParlamentar: number; nServidor: number;
              unitMediana: number; suspeitas: number; valorSuspeitas: number;
              valorTotalBruto: number; pctSuspeitas: number };
  terceirizados?: { registros: number; pessoas: number; empresas: number;
                    porEmpresa: { n: string; q: number }[] };
  contratos?: { n: number; fornecedores: number };
}

export interface CldfVerbas {
  fonte: string;
  periodo: [number, number];
  grao: string;
  total: { valor: number; notas: number; nDeputados: number;
           semCategoria: number; pctSemCategoria: number };
  /** deputados com verba publicada em cada ano — a razão de não comparar */
  cobertura: { ano: number; deputados: number }[];
  comparavel: boolean;
  serie: { ano: number; valor: number; notas: number; deputados: number }[];
  categorias: { n: string; v: number; q: number }[];
  deputados: { n: string; t: number; m: number; q: number; a: number }[];
}

export interface CldfAdmin {
  fonte: string;
  despesas?: { ate: string; anosCompletos: number[];
               serie: { ano: number; pago: number; empenhado: number;
                        meses: number }[] };
  duodecimo?: { ano: number; recebido: number; previsto: number;
                meses: number }[];
  terceirizados?: { registros: number; pessoas: number; empresas: number;
                    meses: number; porEmpresa: { n: string; q: number }[] };
  folha?: { mes: string; linhas: number; semDetalhe: number; pessoas: number;
            bruto: number; deputados: number; brutoDeputados: number;
            temLotacao: boolean; emGabinete: number; brutoGabinete: number;
            pctGabinete: number;
            porTipo: { n: string; q: number; v: number }[] };
  folhaSerie?: { mes: string; pessoas: number; bruto: number }[];
  folhaFalhas?: string[];
}

export interface AlmgVerbas {
  fonte: string;
  janela: [string, string];
  total: { notas: number; deputados: number; mesesDeputado: number;
           pedido: number; pago: number; glosa: number; pctGlosa: number;
           comGlosa: number };
  serie: { ano: number; pago: number; deputados: number;
           porDeputado: number; meses: number }[];
  categorias: { n: string; v: number; q: number }[];
  fornecedores: { distintos: number; compartilhados: number;
                  top: { n: string; dep: number; v: number }[] };
  deputados: { medianaMensal: number; minMensal: number; maxMensal: number;
               top: { n: string; p: string; v: number; m: number }[] };
}

/* ---------- voto por urna, na capital ----------
   O grao mais fino do projeto: um local de votacao. `lat`/`lon` sao `null`
   quando o TSE nao publica a coordenada — nunca 0 e nunca -1, que e' a
   sentinela dele e poria a escola no Atlantico. */

export interface LocalVotacao {
  n: string;
  b: string;
  /** zona eleitoral: a chave do local e' (zona, local), nunca o local sozinho */
  z: number;
  lat: number | null;
  lon: number | null;
  /** eleitores aptos no local */
  e: number;
}

export interface FichaUrna {
  sq: string;
  n: string;
  t: number;
  /** indices de local, e os votos correspondentes — esparso */
  li: number[];
  lv: number[];
}

export interface Urnas {
  cidade: string;
  uf: string;
  ano: number;
  eleitores: number;
  secoes: number;
  /** locais sem coordenada: ficam fora do mapa e dentro da contagem */
  semCoordenada: number;
  /** destes, os que nem constam do cadastro de locais */
  semCadastro: number;
  locais: LocalVotacao[];
  totalLocal: number[];
  fichas: FichaUrna[];
}

export interface FichaVereador {
  sq: string;
  n: string;
  completo: string;
  p: string;
  pn: string;
  el: boolean;
  t: number;
  /** índices na lista `zonas` do ano */ zi: number[];
  zv: number[];
  nz: number;
  /** zonas efetivas — só vale dentro de um ano */ ef: number;
  t1: number;
  gi: number;
  /** número da zona de maior votação */ reduto: number;
  /** já havia concorrido antes */ re: boolean;
  /** cosseno com o pleito anterior; null quando as zonas foram redesenhadas */
  sim: number | null;
}

export interface Vereador {
  cidade: string;
  anos: Record<string, {
    pleito: {
      nCand: number; cadeiras: number; total: number; ultimo: number;
      maior: number; qe: number; nz: number; rePct: number;
    };
    zonas: number[];
    fichas: FichaVereador[];
    partidos: Partido[];
  }>;
}
