/**
 * Projeção por tendência linear, com a qualidade do ajuste à vista.
 *
 * O Radar existe para dizer o que vem. A tentação é entregar o número projetado
 * sozinho, porque é ele que o cliente quer ouvir — e é exatamente aí que um
 * produto de previsão passa a mentir. Sete pleitos são sete pontos: uma reta
 * sobre sete pontos é uma leitura, não um oráculo.
 *
 * Por isso toda projeção daqui sai acompanhada de:
 *
 *   - `r2`, a fração da variação que a reta explica. Abaixo de 0,5 a série não
 *     tem tendência que se sustente, e a tela diz isso em palavras;
 *   - `erroTipico`, o desvio médio dos pontos em relação à reta, na unidade do
 *     próprio indicador — é o que dá tamanho ao "mais ou menos";
 *   - `pontos`, os valores observados, para o leitor conferir a reta contra o
 *     que de fato aconteceu.
 *
 * Nada aqui é modelo causal. É extrapolação declarada, e o nome do campo diz.
 */

export interface Projecao {
  /** valor projetado para o próximo ponto do eixo */
  valor: number;
  /** inclinação por período — o quanto anda a cada pleito */
  porPleito: number;
  /** 0 a 1: quanto da variação a reta explica */
  r2: number;
  /** desvio típico dos observados em relação à reta, na unidade do indicador */
  erroTipico: number;
  /** quantos pontos sustentam a reta */
  n: number;
  /** a reta tem sustentação suficiente para ser lida como tendência? */
  confiavel: boolean;
}

/**
 * Mínimos quadrados sobre (i, y). O eixo é a ordem do pleito, não o ano: os
 * pleitos são equidistantes de quatro em quatro anos, e usar o ano daria a
 * mesma reta com números piores de ler.
 */
export function projetar(valores: (number | null | undefined)[]): Projecao | null {
  const pts: { x: number; y: number }[] = [];
  valores.forEach((v, i) => {
    if (typeof v === "number" && Number.isFinite(v)) pts.push({ x: i, y: v });
  });
  // Três pontos é o mínimo para uma reta dizer algo além de ligar dois pontos.
  if (pts.length < 3) return null;

  const n = pts.length;
  const mx = pts.reduce((s, p) => s + p.x, 0) / n;
  const my = pts.reduce((s, p) => s + p.y, 0) / n;
  const sxy = pts.reduce((s, p) => s + (p.x - mx) * (p.y - my), 0);
  const sxx = pts.reduce((s, p) => s + (p.x - mx) ** 2, 0);
  if (sxx === 0) return null;

  const a = sxy / sxx;
  const b = my - a * mx;
  const prever = (x: number) => a * x + b;

  const ssRes = pts.reduce((s, p) => s + (p.y - prever(p.x)) ** 2, 0);
  const ssTot = pts.reduce((s, p) => s + (p.y - my) ** 2, 0);
  const r2 = ssTot === 0 ? 0 : 1 - ssRes / ssTot;
  const erroTipico = Math.sqrt(ssRes / Math.max(n - 2, 1));

  const proximo = (valores.length);
  return {
    valor: prever(proximo),
    porPleito: a,
    r2,
    erroTipico,
    n,
    // 0,5 não é lei da natureza: é o corte que escolhemos, e a tela declara.
    // Abaixo disso a reta explica menos da metade do que a série faz.
    confiavel: r2 >= 0.5 && n >= 4,
  };
}

/** Frase honesta para a projeção, incluindo quando ela não se sustenta. */
export function leitura(p: Projecao | null, unidade: string): string {
  if (!p) return "Série curta demais para projetar: são menos de três pleitos.";
  if (!p.confiavel) {
    return `A reta explica ${Math.round(p.r2 * 100)}% da variação — pouco. `
      + `Esta série não tem tendência que se sustente, e o número projetado `
      + `abaixo vale como referência, não como previsão.`;
  }
  const dir = p.porPleito >= 0 ? "sobe" : "desce";
  return `A série ${dir} cerca de ${Math.abs(p.porPleito).toFixed(2)} ${unidade} `
    + `por pleito, e a reta explica ${Math.round(p.r2 * 100)}% da variação. `
    + `O desvio típico dos pleitos observados em relação à reta é `
    + `${p.erroTipico.toFixed(2)} ${unidade} — é esse o tamanho do "mais ou menos".`;
}
