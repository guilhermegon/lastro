import { RAMPA, SEM_VOTO, token } from "../lib/escalas";
import { numero, percentual } from "../lib/formato";

export function Legenda({ cortes, sufixo }: { cortes: number[]; sufixo?: "%" }) {
  const rotular = (v: number) => (sufixo === "%" ? percentual(v, 1) : numero(Math.round(v)));
  return (
    <div className="legenda">
      <span className="item">
        <span className="swatch" style={{ background: token(SEM_VOTO) }} />
        Nenhum voto
      </span>
      {cortes.map((corte, i) => (
        <span className="item" key={i}>
          <span className="swatch" style={{ background: token(RAMPA[i] as string) }} />
          {i === 0
            ? `até ${rotular(corte)}`
            : `${rotular(cortes[i - 1] as number)} a ${rotular(corte)}`}
        </span>
      ))}
    </div>
  );
}
