/** Rampa sequencial de vermelho (baixo) a verde (alto), em tokens de tema. */
export const RAMPA = ["--s1", "--s2", "--s3", "--s4", "--s5"] as const;
export const SEM_VOTO = "--sem-voto";

export const token = (t: string): string => `var(${t})`;

/**
 * Cortes por quantis sobre os valores maiores que zero.
 *
 * Faixas fixas não servem para comparar estados de portes muito diferentes: o
 * mesmo corte de 5.000 votos separa bem em São Paulo e deixa Roraima inteira
 * numa classe só. Quantis adaptam ao caso.
 */
export function quantis(valores: number[], n = 5): number[] {
  const v = valores.filter((x) => x > 0).sort((a, b) => a - b);
  if (v.length === 0) return Array.from({ length: n }, (_, i) => i + 1);
  return Array.from({ length: n }, (_, i) => {
    const pos = Math.min(v.length - 1, Math.ceil((v.length * (i + 1)) / n) - 1);
    return v[pos] as number;
  });
}

/** Índice da faixa, ou -1 quando não há voto. */
export function faixaDe(valor: number, cortes: number[]): number {
  if (!(valor > 0)) return -1;
  for (let i = 0; i < cortes.length; i++) if (valor <= (cortes[i] as number)) return i;
  return cortes.length - 1;
}

export function corDaFaixa(valor: number, cortes: number[]): string {
  const i = faixaDe(valor, cortes);
  return token(i < 0 ? SEM_VOTO : (RAMPA[Math.min(i, RAMPA.length - 1)] as string));
}
