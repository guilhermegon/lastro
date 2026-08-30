/**
 * Marcas dos produtos da Lastro.
 *
 * A casa é a Lastro; "Cadê o Voto?" e "Emendômetro" são produtos dela. Para
 * lerem como família e não como peças soltas, os três compartilham a mesma
 * construção — e só ela:
 *
 *   1. uma régua vertical à esquerda e uma linha de base embaixo, sempre nas
 *      mesmas coordenadas (x=12 e y=52). É o lastro no sentido do nome — o
 *      respaldo, como o ouro que lastreia uma moeda: nada flutua solto, tudo se
 *      apoia nessa quina. É o que o olho reconhece antes de ler a palavra;
 *   2. só retângulos de canto arredondado, nada de arco ou curva;
 *   3. hierarquia por opacidade (.42 / .66 / 1), nunca por segunda cor;
 *   4. `fill: var(--accent)`, então as três acompanham o tema sozinhas.
 *
 * Os produtos não assinam "um produto Lastro": a moldura já diz isso, e repetir
 * em texto o que o desenho afirma enfraquece os dois.
 *
 * O que muda é o que vive dentro da moldura, e cada um diz o que o produto faz:
 * a Lastro empilha barras crescentes (a base que sustenta); "Cadê o Voto?"
 * espalha células por um território com uma acesa (onde o voto está); o
 * Emendômetro é um medidor segmentado com marcador (quanto foi, e até onde).
 */

/** "Cadê o Voto?" — território com uma célula acesa.
 *
 *  As células são o município, que é a unidade de tudo neste produto. Uma está
 *  cheia e as outras em meio-tom: a pergunta do nome é "onde", e a resposta é
 *  um lugar entre muitos — não um total. */
export function LogoCadeOVoto() {
  const cel = [
    [21, 12, 0.28], [31, 12, 0.42], [41, 12, 0.28],
    [21, 22, 0.42], [31, 22, 1.00], [41, 22, 0.55],
    [21, 32, 0.28], [31, 32, 0.55], [41, 32, 0.34],
  ] as const;
  return (
    <span className="lastro produto"
          role="img" aria-label="Cadê o Voto? — um produto da Lastro">
      <svg viewBox="0 0 260 68" aria-hidden="true" focusable="false">
        <g className="lastro-mark">
          {/* a quina da casa: régua e base, nas mesmas coordenadas das três */}
          <rect x="12" y="12" width="4" height="44" rx="1" />
          <rect x="12" y="52" width="52" height="4" rx="1.5" />
          {cel.map(([x, y, o]) => (
            <rect key={`${x}-${y}`} x={x} y={y} width="8" height="8" rx="2"
                  opacity={o} />
          ))}
          {/* o traço que aponta a célula acesa até a base — "chegou aqui" */}
          <rect x="33" y="32" width="4" height="14" rx="1.5" opacity=".66" />
        </g>
        <text className="lastro-nome produto-nome" x="72" y="42">
          Cadê o Voto?
        </text>
      </svg>
    </span>
  );
}

/** "Emendômetro" — medidor segmentado com marcador.
 *
 *  O nome promete um medidor, então o desenho é um. Os segmentos crescem da
 *  esquerda para a direita e o marcador cai num deles: emenda se lê como
 *  quantidade que chegou a algum ponto de uma escala, não como total solto. */
export function LogoEmendometro() {
  const seg = [
    [21, 0.30], [30, 0.44], [39, 0.58], [48, 0.78],
  ] as const;
  return (
    <span className="lastro produto"
          role="img" aria-label="Emendômetro — um produto da Lastro">
      <svg viewBox="0 0 260 68" aria-hidden="true" focusable="false">
        <g className="lastro-mark">
          <rect x="12" y="12" width="4" height="44" rx="1" />
          <rect x="12" y="52" width="52" height="4" rx="1.5" />
          {/* a escala: segmentos de altura crescente */}
          {seg.map(([x, o], i) => (
            <rect key={x} x={x} y={38 - i * 6} width="6" height={i * 6 + 8}
                  rx="2" opacity={o} />
          ))}
          {/* o marcador: onde a medida parou */}
          <rect x="28" y="14" width="10" height="4" rx="1.5" />
          <rect x="31.5" y="14" width="3" height="20" rx="1.5" />
        </g>
        <text className="lastro-nome produto-nome" x="72" y="42">
          Emendômetro
        </text>
      </svg>
    </span>
  );
}

/** "Radar" — o visor.
 *
 *  Duas versoes anteriores erraram, e por motivos diferentes. A primeira eram
 *  barras crescentes com a ultima em contorno: o Emendometro TAMBEM e' barras
 *  crescentes, e a 158 px os dois liam quase igual. A segunda trocou as barras
 *  por quartos de moldura — distinguia, mas nao dizia "radar": dizia "alcance",
 *  que e' abstrato demais para uma marca ler de relance.
 *
 *  Esta e' o visor: tres arcos de alcance, a linha de varredura e o eco sobre
 *  ela. E' a imagem que qualquer pessoa reconhece sem legenda.
 *
 *  **E e' o unico da familia com curva.** As outras tres sao so' retangulo, e
 *  quebrar isso foi decisao, nao descuido: um visor de radar sem arco nao e' um
 *  visor de radar, e o Radar e' justamente o produto que se separa dos outros —
 *  fechado, premium, outra natureza. A quebra fica onde ela significa algo.
 *
 *  O que NAO se quebra e' o parentesco: os arcos partem da mesma quina em que
 *  tudo se apoia, x=12 com y=52, e a marca ocupa a mesma caixa das outras tres.
 *  O radar varre a partir do lastro. */
export function LogoRadar() {
  // raio, opacidade — o alcance cresce e ganha peso
  const arco = [[12, 0.34], [24, 0.5], [36, 0.68]] as const;
  return (
    <span className="lastro produto" role="img" aria-label="Radar">
      <svg viewBox="0 0 260 68" aria-hidden="true" focusable="false">
        <g className="lastro-mark" fill="none">
          <rect x="12" y="12" width="4" height="44" rx="1"
                fill="currentColor" />
          <rect x="12" y="52" width="52" height="4" rx="1.5"
                fill="currentColor" />
          {/* quartos de circulo centrados na quina (16, 52) */}
          {arco.map(([r, o]) => (
            <path key={r} d={`M${16 + r} 52 A${r} ${r} 0 0 0 16 ${52 - r}`}
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                  opacity={o} />
          ))}
          {/* a varredura, e o eco sobre ela: o unico elemento solido */}
          <line x1="16" y1="52" x2="43" y2="20"
                stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
          <circle cx="35.5" cy="29.5" r="4" fill="currentColor" />
        </g>
        <text className="lastro-nome produto-nome" x="72" y="42">Radar</text>
      </svg>
    </span>
  );
}
