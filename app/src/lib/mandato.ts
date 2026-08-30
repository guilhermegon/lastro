import type { BlocoEmenda, FichaEmenda } from "../tipos";

/**
 * Agrupa a emenda por mandato, não por ano.
 *
 * O ano é unidade contábil; o mandato é a unidade política. A pergunta "quanto
 * este parlamentar mandou para o território dele" é de mandato, e a visão anual
 * a esconde atrás da volatilidade de execução — em Goiás, 2019 pagou R$ 2,57 bi
 * e 2020 pagou R$ 1,02 bi, e nada disso é mudança de comportamento.
 *
 * **O agrupamento é honesto porque o campo é o certo.** O `ano` do arquivo é o
 * *Ano da Emenda* — o exercício em que ela foi autorizada —, não o ano em que o
 * dinheiro saiu. Se fosse o ano de pagamento, um resto a pagar quitado em 2019
 * cairia na legislatura errada. Como é o ano da emenda, cada uma fica na
 * legislatura que a autorizou, tenha o dinheiro saído quando tiver saído.
 *
 * **Uma hipótese que medimos e caiu.** Supus que mandato antigo apareceria
 * inflado, por ter tido mais tempo de pagar restos. É o contrário: resto a pagar
 * não pago acaba *cancelado*, não pago. A razão pago/empenhado é 81,9% em 2015 e
 * 96,3% em 2023. O único ano de fato imaturo é o corrente — 69,4% em 2026 —, e é
 * por isso que só a legislatura em curso leva aviso.
 */

export interface Legislatura {
  id: string;
  rotulo: string;
  /** ano da eleição que a formou — é por aqui que ela cruza com o voto */
  eleicao: number;
  anos: number[];
}

/** As legislaturas que a série de emenda alcança. A emenda federal começa em
 *  2015, que é o primeiro ano da 55ª — a janela do dado bate com o mandato por
 *  coincidência feliz, e não há legislatura partida ao meio. */
export const LEGISLATURAS: Legislatura[] = [
  { id: "55", rotulo: "55ª · 2015–2018", eleicao: 2014,
    anos: [2015, 2016, 2017, 2018] },
  { id: "56", rotulo: "56ª · 2019–2022", eleicao: 2018,
    anos: [2019, 2020, 2021, 2022] },
  { id: "57", rotulo: "57ª · 2023–2026", eleicao: 2022,
    anos: [2023, 2024, 2025, 2026] },
];

export const legislaturaDoAno = (ano: number): Legislatura | undefined =>
  LEGISLATURAS.find((l) => l.anos.includes(ano));

/**
 * Funde os anos de uma legislatura num bloco só.
 *
 * Os índices de concentração são RECALCULADOS do vetor somado, nunca a média
 * dos anuais: a média de quatro frações não é a fração do total, e usá-la daria
 * um número que parece certo e não é. `t1` sobre quatro anos somados responde
 * "que fatia do que este autor mandou no mandato foi para o maior município" —
 * que é a pergunta. A média de quatro `t1` anuais não responde pergunta nenhuma.
 */
export function fundeMandato(
  anos: Record<string, BlocoEmenda>,
  leg: Legislatura,
  nMunicipios: number,
): BlocoEmenda | null {
  const blocos = leg.anos
    .map((a) => anos[String(a)])
    .filter((b): b is BlocoEmenda => !!b);
  if (!blocos.length) return null;

  const totalMun = new Array<number>(nMunicipios).fill(0);
  const totalPix = new Array<number>(nMunicipios).fill(0);
  for (const b of blocos) {
    b.totalMun.forEach((v, i) => { if (i < nMunicipios) totalMun[i]! += v || 0; });
    b.totalPix.forEach((v, i) => { if (i < nMunicipios) totalPix[i]! += v || 0; });
  }

  // Autor é a chave. O mesmo nome em anos diferentes é a mesma pessoa dentro de
  // uma legislatura — entre legislaturas não seria, mas aqui não cruzamos.
  const porAutor = new Map<string, {
    f: FichaEmenda; mun: Map<number, number>; pxMun: Map<number, number>;
  }>();
  for (const b of blocos) {
    for (const f of b.fichas) {
      let e = porAutor.get(f.n);
      if (!e) {
        e = { f: { ...f, t: 0, pix: 0, emp: 0, ne: 0, nm: 0, mi: [], mv: [],
                   pxi: [], pxv: [] },
              mun: new Map(), pxMun: new Map() };
        porAutor.set(f.n, e);
      }
      e.f.t += f.t; e.f.pix += f.pix; e.f.emp += f.emp; e.f.ne += f.ne;
      f.mi.forEach((idx, k) => e!.mun.set(idx, (e!.mun.get(idx) ?? 0) + (f.mv[k] ?? 0)));
      (f.pxi ?? []).forEach((idx, k) =>
        e!.pxMun.set(idx, (e!.pxMun.get(idx) ?? 0) + (f.pxv?.[k] ?? 0)));
    }
  }

  const fichas: FichaEmenda[] = [];
  for (const { f, mun, pxMun } of porAutor.values()) {
    const pares = [...mun.entries()].sort((a, b) => a[0] - b[0]);
    f.mi = pares.map((p) => p[0]);
    f.mv = pares.map((p) => p[1]);
    const px = [...pxMun.entries()].sort((a, b) => a[0] - b[0]);
    f.pxi = px.map((p) => p[0]);
    f.pxv = px.map((p) => p[1]);
    f.nm = f.mi.length;
    // recalculados do vetor somado — ver docstring
    const maior = f.mv.length ? Math.max(...f.mv) : 0;
    f.t1 = f.t > 0 ? (maior / f.t) * 100 : 0;
    const soma2 = f.mv.reduce((s, v) => s + (f.t > 0 ? (v / f.t) ** 2 : 0), 0);
    f.ef = soma2 > 0 ? 1 / soma2 : 0;
    fichas.push(f);
  }
  fichas.sort((a, b) => b.t - a.t);

  const p = blocos.reduce((acc, b) => ({
    pago: acc.pago + b.pleito.pago,
    emp: acc.emp + b.pleito.emp,
    nEmendas: acc.nEmendas + b.pleito.nEmendas,
    pix: acc.pix + b.pleito.pix,
    nPix: acc.nPix + b.pleito.nPix,
    cortados: acc.cortados + b.pleito.cortados,
    nAutores: 0, nMun: 0,
  }), { pago: 0, emp: 0, nEmendas: 0, pix: 0, nPix: 0, cortados: 0,
        nAutores: 0, nMun: 0 });
  // autores e municípios são DISTINTOS no mandato, nunca a soma dos anuais:
  // quem manda emenda nos quatro anos seria contado quatro vezes
  p.nAutores = porAutor.size;
  p.nMun = totalMun.filter((v) => v > 0).length;

  return { totalMun, totalPix, fichas, pleito: p };
}
