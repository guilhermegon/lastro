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
