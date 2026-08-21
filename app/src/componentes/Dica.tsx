import { useEffect, useState, type ReactNode } from "react";

export interface EstadoDica {
  conteudo: ReactNode;
  x: number;
  y: number;
}

/**
 * Balão de inspeção. Fica fora do fluxo e some ao toque fora — em tela sem
 * hover, o toque é o único gesto disponível, e sem uma saída explícita o balão
 * ficaria preso.
 */
export function Dica({ dica, aoFechar }: { dica: EstadoDica | null; aoFechar: () => void }) {
  const [caixa, setCaixa] = useState({ largura: 0, altura: 0 });

  useEffect(() => {
    if (!dica) return;
    const fechar = () => aoFechar();
    window.addEventListener("scroll", fechar, true);
    return () => window.removeEventListener("scroll", fechar, true);
  }, [dica, aoFechar]);

  if (!dica) return null;

  const movel = window.matchMedia("(max-width: 760px)").matches;
  let x = dica.x + 14;
  let y = dica.y + 14;
  if (movel) {
    // acima do dedo: embaixo, a própria mão cobre a informação
    x = Math.max(12, Math.min(dica.x - caixa.largura / 2, window.innerWidth - caixa.largura - 12));
    y = dica.y - caixa.altura - 18;
    if (y < 12) y = dica.y + 24;
  } else {
    if (x + caixa.largura > window.innerWidth - 8) x = dica.x - caixa.largura - 14;
    if (y + caixa.altura > window.innerHeight - 8) y = dica.y - caixa.altura - 14;
  }

  return (
    <div
      className="dica"
      role="status"
      aria-live="polite"
      style={{ opacity: 1, left: x, top: y }}
      ref={(n) => {
        if (!n) return;
        const r = n.getBoundingClientRect();
        if (Math.abs(r.width - caixa.largura) > 1 || Math.abs(r.height - caixa.altura) > 1) {
          setCaixa({ largura: r.width, altura: r.height });
        }
      }}
    >
      {dica.conteudo}
    </div>
  );
}
