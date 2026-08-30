/**
 * A capital, apontada e nomeada, em todo mapa de estado.
 *
 * Um coroplético sem referência é uma mancha: o leitor vê onde a cor é forte e
 * não sabe onde isso fica. A capital é o único ponto que praticamente todo
 * brasileiro localiza no próprio estado, e marcá-la converte a mancha em
 * geografia — "o voto está a noroeste de Goiânia" é uma frase que o mapa passa
 * a permitir, e antes não permitia.
 *
 * **A marca tem de sobreviver a qualquer preenchimento embaixo dela.** O mapa
 * pinta o município com a cor da faixa, que vai do vermelho ao verde escuro, ou
 * com a cor da zona. Por isso o ponto é um disco na cor da superfície com um
 * núcleo de tinta, e o rótulo leva contorno da mesma superfície
 * (`paint-order: stroke`): os dois se separam do que estiver atrás, claro ou
 * escuro, sem depender de qual cor caiu ali.
 *
 * **O rótulo vira de lado perto da borda.** Ancorado sempre à direita, ele
 * sairia do quadro nas capitais que ficam no leste do estado — e um nome
 * cortado pela metade é pior que nenhum, porque parece defeito de render.
 */
export function MarcaCapital({ p, nome, largura }: {
  /** centroide já projetado do município da capital */
  p: [number, number];
  nome: string;
  /** largura do viewBox, para decidir de que lado o rótulo cabe */
  largura: number;
}) {
  const [x, y] = p;
  const aEsquerda = x > largura * 0.72;
  return (
    <g className="capital-marca" aria-hidden="true">
      <circle cx={x} cy={y} r="5.4" />
      <circle cx={x} cy={y} r="2.6" className="nucleo" />
      <text x={aEsquerda ? x - 9 : x + 9} y={y + 3.6}
            textAnchor={aEsquerda ? "end" : "start"}>
        {nome}
      </text>
    </g>
  );
}
