import {
  LogoCadeOVoto, LogoEmendometro, LogoRadar,
} from "./LogoProduto";
import type { Vista } from "./Abas";

/**
 * A troca de produto, no topo e sempre visível.
 *
 * Antes havia uma barra só, com Emendômetro enfileirado entre Presidente e
 * Senado — dois níveis achatados num, e o Emendômetro parecendo um cargo. São
 * coisas de ordem diferente: produto é o que o cliente comprou, aba é onde ele
 * está dentro dele. Achatar os dois obriga a ler onze rótulos para trocar de
 * uma coisa que tem três opções.
 *
 * Cada produto entra com a própria marca, não só com o nome: é o que faz a
 * troca ser reconhecida de relance, e é onde as marcas ganham função em vez de
 * enfeite.
 */
export function TrocaProduto({ atual, aoTrocar }: {
  /** a vista aberta — usada só para saber qual produto está ativo */
  atual: Vista;
  aoTrocar: (v: Vista) => void;
}) {
  // Qual produto responde pela vista aberta. Os cargos e o vereador são todos
  // Cadê o Voto?; API e Sobre são da casa e não acendem produto nenhum.
  const produtoDe = (v: Vista): string =>
    v === "emendas" ? "emendometro"
      : v === "home" || v === "api" || v === "sobre" ? "casa"
      : "cadeovoto";
  const ativo = produtoDe(atual);

  const itens = [
    { id: "cadeovoto", marca: <LogoCadeOVoto />, destino: "nacional" as Vista },
    { id: "emendometro", marca: <LogoEmendometro />, destino: "emendas" as Vista },
  ];

  return (
    <div className="produtos" role="group" aria-label="Produto">
      {itens.map((i) => (
        <button key={i.id} type="button"
                className={`produto-bt${ativo === i.id ? " ativo" : ""}`}
                aria-current={ativo === i.id ? "true" : undefined}
                onClick={() => aoTrocar(i.destino)}>
          {i.marca}
        </button>
      ))}
      {/* O Radar aparece porque existe e o cliente precisa saber que existe.
          Não clica porque não está publicado — ver RAS 00 TKT 0008. */}
      <span className="produto-bt fechado" aria-disabled="true">
        <LogoRadar />
        <span className="produto-selo">Sob acesso</span>
      </span>
    </div>
  );
}
