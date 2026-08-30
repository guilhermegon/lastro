import { useMemo } from "react";
import type { EmendasBR, Sigla } from "../tipos";
import { decimal, numero, percentual } from "../lib/formato";
import { LEGISLATURAS } from "../lib/mandato";
import { Tabela } from "../componentes/Tabela";

const reais = (v: number): string => {
  const a = Math.abs(v);
  if (a >= 1e9) return `R$ ${decimal(v / 1e9, 2)} bi`;
  if (a >= 1e6) return `R$ ${decimal(v / 1e6, 2)} mi`;
  return `R$ ${decimal(v / 1e3, 0)} mil`;
};

interface Linha {
  id: string; rotulo: string;
  pago: number; pix: number; emendas: number; comMun: number;
  emCurso: boolean;
}

/**
 * O país entre mandatos — o contexto em que o estado aberto se lê.
 *
 * **Esta seção usa outro denominador que o mapa acima, e isso precisa estar
 * dito.** O mapa é escopo município: só os 10,5% do dinheiro cujo arquivo nomeia
 * a cidade. Aqui o escopo é UF, que cobre 97,1% — é o recorte em que dá para
 * falar de volume nacional sem que a resposta seja sobre rastreabilidade em vez
 * de sobre dinheiro. Dois denominadores na mesma tela sem aviso seria o tipo de
 * coisa que faz um leitor somar o que não se soma.
 */
export function PaisEntreMandatos({ br, uf, anoCorrente }: {
  br: EmendasBR; uf: Sigla; anoCorrente: number;
}) {
  const linhas = useMemo<Linha[]>(() => LEGISLATURAS.map((l) => {
    const r = br.uf.filter((x) => l.anos.includes(x.ano));
    const pago = r.reduce((s, x) => s + x.pago, 0);
    return {
      id: l.id, rotulo: l.rotulo, pago,
      pix: r.reduce((s, x) => s + x.pix, 0),
      emendas: r.reduce((s, x) => s + x.n, 0),
      comMun: r.reduce((s, x) => s + x.pagoMun, 0),
      emCurso: l.anos.includes(anoCorrente),
    };
  }).filter((x) => x.pago > 0), [br, anoCorrente]);

  const noEstado = useMemo(() => LEGISLATURAS.map((l) => {
    const r = br.uf.filter((x) => l.anos.includes(x.ano) && x.uf === uf);
    return { id: l.id, pago: r.reduce((s, x) => s + x.pago, 0) };
  }), [br, uf]);

  if (linhas.length < 2) return null;
  const p = linhas[0]!, u = linhas[linhas.length - 1]!;
  const meio = linhas[1];

  const media = (x: Linha) => (x.emendas ? x.pago / x.emendas : 0);
  const rastro = (x: Linha) => (x.pago ? (x.comMun / x.pago) * 100 : 0);

  return (
    <div className="cartaz">
      <h2>O país entre mandatos</h2>
      <p className="cap">
        A mesma emenda individual, somada por legislatura, no país inteiro. É o
        contexto em que o estado acima se lê — e mostra três coisas que a visão
        ano a ano espalha.
      </p>

      <Tabela
        cab={["Legislatura", "Pago", "Emenda Pix", "Emendas", "Valor médio",
              "Com município"]}
        linhas={linhas.map((x) => [
          x.rotulo + (x.emCurso ? " *" : ""),
          reais(x.pago),
          percentual(x.pago ? (x.pix / x.pago) * 100 : 0, 1),
          numero(x.emendas),
          reais(media(x)),
          percentual(rastro(x), 1),
        ])}
        rodape={["* legislatura em curso: o valor ainda cresce", "", "", "", "", ""]} />

      <ul className="lista-fatos" style={{ marginTop: 14 }}>
        <li>
          <strong>O dinheiro cresceu e as emendas diminuíram.</strong> De{" "}
          {reais(p.pago)} na {p.rotulo.split(" ·")[0]} para {reais(u.pago)} na{" "}
          {u.rotulo.split(" ·")[0]} — e com <em>menos</em> emendas
          {meio && u.emendas < meio.emendas
            ? ` que na ${meio.rotulo.split(" ·")[0]}` : ""}. O valor médio de
          cada uma saiu de {reais(media(p))} para {reais(media(u))}. São emendas
          maiores, não mais emendas.
        </li>
        <li>
          <strong>A emenda Pix nasceu e virou um terço do total.</strong> Era{" "}
          {percentual(p.pago ? (p.pix / p.pago) * 100 : 0, 1)} na{" "}
          {p.rotulo.split(" ·")[0]} — a Transferência Especial não existia antes
          de 2019 — e hoje é {percentual(u.pago ? (u.pix / u.pago) * 100 : 0, 1)}.
          É o dinheiro que cai direto no caixa do município, sem convênio e sem
          finalidade definida no orçamento.
        </li>
        <li>
          <strong>Mais dinheiro, menos rastro.</strong> A fatia com município
          identificado caiu de {percentual(rastro(p), 1)} para{" "}
          {percentual(rastro(u), 1)}. Não é efeito do ano corrente: em 2025,
          exercício fechado, foram 5,1% — contra 34,5% em 2015. O volume
          multiplicou e a capacidade de saber para onde ele foi encolheu.
        </li>
      </ul>

      <div className="nota" style={{ marginTop: 12 }}>
        <strong>Esta tabela usa outro denominador que o mapa acima.</strong> O
        mapa é escopo município — os 10,5% do dinheiro cujo arquivo nomeia a
        cidade. Aqui o escopo é UF, que cobre 97,1%, porque é nele que dá para
        falar de volume nacional sem que a resposta acabe sendo sobre
        rastreabilidade em vez de sobre dinheiro. Os dois números não se somam e
        não se comparam entre si.
      </div>

      {noEstado.some((x) => x.pago > 0) && (
        <p className="cap" style={{ marginTop: 12 }}>
          Em {uf}, as mesmas legislaturas somam{" "}
          {noEstado.filter((x) => x.pago > 0)
            .map((x) => `${reais(x.pago)} (${x.id}ª)`).join(", ")} —{" "}
          <strong>ainda no escopo UF</strong>. Os cartões no topo desta tela são
          maiores ou menores porque falam do escopo município, que é outro
          recorte do mesmo dinheiro.
        </p>
      )}
    </div>
  );
}
