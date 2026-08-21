export interface Indice {
  rotulo: string;
  valor: string;
  explicacao: string;
}

export function Indices({ itens }: { itens: Indice[] }) {
  return (
    <div className="indices">
      {itens.map((i) => (
        <div className="indice" key={i.rotulo}>
          <div className="rot">{i.rotulo}</div>
          <div className="val">{i.valor}</div>
          <div className="exp">{i.explicacao}</div>
        </div>
      ))}
    </div>
  );
}
