import { Logo } from "../componentes/Logo";
import {
  LogoCadeOVoto, LogoEmendometro, LogoRadar,
} from "../componentes/LogoProduto";
import type { Vista } from "../componentes/Abas";

/**
 * A entrada da casa.
 *
 * Lastro no topo, os produtos abaixo. A ordem não é decorativa: quem chega
 * precisa saber de quem é a página antes de saber o que ela oferece, e é isso
 * que separa uma casa com produtos de um site com abas.
 *
 * O Radar aparece sem destino. Ele existe, tem marca e tem descrição, e não tem
 * link porque não está publicado — publicar antes da autenticação faria dele um
 * produto fechado que responde 200. Um card que diz "sob acesso" é honesto; um
 * card que leva a lugar nenhum, não.
 */

interface Produto {
  id: string;
  marca: React.ReactNode;
  o: string;
  faz: string;
  numeros: string;
  destino: Vista | null;
  nota?: string;
}

export function VistaHome({ aoEntrar, nMun, nUF }: {
  aoEntrar: (v: Vista) => void;
  nMun: number;
  nUF: number;
}) {
  const produtos: Produto[] = [
    {
      id: "cadeovoto",
      marca: <LogoCadeOVoto />,
      o: "Onde cada candidato tirou voto",
      faz: "Município a município, em todos os cargos, de 1998 a 2022. Quem "
         + "domina qual território, quem espalha, e quem depende de uma cidade só.",
      numeros: `${nUF} unidades da federação · ${nMun.toLocaleString("pt-BR")} municípios · 7 pleitos`,
      destino: "nacional",
    },
    {
      id: "emendometro",
      marca: <LogoEmendometro />,
      o: "Para onde cada parlamentar mandou dinheiro",
      faz: "Emenda paga por município, federal e estadual, com a transferência "
         + "especial separada — e a cobertura declarada em toda tela.",
      numeros: "2015 a 2026 · 27 unidades · esfera estadual em Goiás e Espírito Santo",
      destino: "emendas",
    },
    {
      id: "radar",
      marca: <LogoRadar />,
      o: "O que os padrões dizem sobre o próximo pleito",
      faz: "Recebe o que os outros produtos apuram e lê para a frente: "
         + "estabilidade de base, concentração, margem de corte. Toda projeção "
         + "sai com a qualidade do ajuste à vista.",
      numeros: "Projeção declarada, nunca prognóstico",
      destino: null,
      nota: "Sob acesso",
    },
  ];

  return (
    <>
      <div className="casa">
        {/* `h1` da página. A entrada é da casa, então o título de primeiro nível
            é o nome dela — e não o de um produto que ainda não foi aberto. O
            texto acessível vem do `aria-label` da marca. */}
        <h1 className="casa-h1"><Logo /></h1>
        <p className="casa-tese">
          Geografia do voto e do dinheiro público no Brasil, a partir de dado
          aberto. Nada aqui é estimativa, projeção de intenção ou pesquisa: é
          apuração e execução orçamentária, como os órgãos publicaram — e todo
          número sai de um script que está no repositório.
        </p>
      </div>

      <div className="vitrine">
        {produtos.map((p) => {
          const Corpo = (
            <>
              <div className="vitrine-marca">{p.marca}</div>
              <h2>{p.o}</h2>
              <p className="cap">{p.faz}</p>
              <p className="vitrine-num">{p.numeros}</p>
              {p.nota ? <span className="vitrine-selo">{p.nota}</span> : null}
            </>
          );
          return p.destino ? (
            <button key={p.id} type="button" className="cartaz vitrine-card"
                    onClick={() => aoEntrar(p.destino as Vista)}>
              {Corpo}
            </button>
          ) : (
            <div key={p.id} className="cartaz vitrine-card vitrine-fechado">
              {Corpo}
            </div>
          );
        })}
      </div>
    </>
  );
}
