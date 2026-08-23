/**
 * Preposição de cada unidade da federação.
 *
 * Não dá para derivar do nome: "em Goiás" e "no Pará" terminam igual, "na
 * Bahia" e "no Paraná" são ambos femininos na aparência e não no artigo. É
 * tabela, e tabela por sigla — o nome vem do IBGE e pode mudar de grafia.
 *
 * Mato Grosso e Mato Grosso do Sul vão sem artigo, que é o uso oficial e o da
 * imprensa ("em Mato Grosso"), embora "no Mato Grosso" circule na fala.
 */
const PREPOSICAO: Record<string, string> = {
  AC: "no", AL: "em", AP: "no", AM: "no", BA: "na", CE: "no", DF: "no",
  ES: "no", GO: "em", MA: "no", MT: "em", MS: "em", MG: "em", PA: "no",
  PB: "na", PR: "no", PE: "em", PI: "no", RJ: "no", RN: "no", RS: "no",
  RO: "em", RR: "em", SC: "em", SE: "em", SP: "em", TO: "no",
};

/** "Goiás" → "em Goiás"; "Rio de Janeiro" → "no Rio de Janeiro". */
export function noEstado(sigla: string, nome: string): string {
  return `${PREPOSICAO[sigla] ?? "em"} ${nome}`;
}

/**
 * Código IBGE → sigla. A malha do Brasil vem chaveada por código numérico e
 * todo o resto do projeto trabalha por sigla; é aqui que os dois se encontram.
 */
const POR_CODIGO: Record<string, string> = {
  "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
  "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
  "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
  "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
  "51": "MT", "52": "GO", "53": "DF",
};

export const siglaDoCodigo = (cod: string): string => POR_CODIGO[cod] ?? cod;
