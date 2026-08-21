import type { ReactNode } from "react";

export interface Cartao {
  rotulo: string;
  valor: ReactNode;
  sub?: string;
  /** valor é texto, não número: muda a fonte */
  texto?: boolean;
}

export function Cartoes({ itens }: { itens: Cartao[] }) {
  return (
    <div className="cartoes">
      {itens.map((c) => (
        <div className="cartao" key={c.rotulo}>
          <div className="rot">{c.rotulo}</div>
          <div className={`val${c.texto ? " txt" : ""}`}>{c.valor}</div>
          {c.sub ? <div className="sub">{c.sub}</div> : null}
        </div>
      ))}
    </div>
  );
}
