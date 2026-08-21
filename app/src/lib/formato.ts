/** Formatação em pt-BR, num lugar só: número solto na tela é erro de produto. */

export const numero = (n: number): string => n.toLocaleString("pt-BR");

export const decimal = (n: number, casas = 2): string =>
  n.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

export const percentual = (n: number, casas = 2): string => `${decimal(n, casas)}%`;

/** Plural sem gambiarra de "(s)". */
export const plural = (n: number, singular: string, plural_: string): string =>
  `${numero(n)} ${n === 1 ? singular : plural_}`;
