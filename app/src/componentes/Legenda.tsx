import { RAMPA, SEM_VOTO, token } from "../lib/escalas";
import { numero, percentual } from "../lib/formato";

/** `semDado` existe porque a mesma legenda serve voto e dinheiro: "Nenhum voto"
 *  num mapa de emenda descreve a coisa errada.
 *
 *  `forma="anel"` existe porque a legenda tem de mostrar a MARCA. No mapa de
 *  urnas o local sem voto é um anel vazio, não uma área preenchida — e
 *  enquanto o quadradinho vinha cheio, a legenda ensinava a procurar no mapa
 *  uma coisa que não está lá. */
export function Legenda({ cortes, sufixo, semDado = "Nenhum voto",
                          forma = "area" }: {
  cortes: number[]; sufixo?: "%"; semDado?: string;
  forma?: "area" | "anel";
}) {
  const rotular = (v: number) => (sufixo === "%" ? percentual(v, 1) : numero(Math.round(v)));
  return (
    <div className="legenda">
      <span className="item">
        {forma === "anel"
          ? <span className="swatch anel" />
          : <span className="swatch" style={{ background: token(SEM_VOTO) }} />}
        {semDado}
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
