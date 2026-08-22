import { CARGOS, NOME_CARGO, type Cargo } from "../tipos";

export type Vista = Cargo | "padroes" | "cruzamentos";

/** Ordem decrescente de escopo — presidente até estadual — e depois as duas
 *  abas de análise, que não são cargo. A barra rola na horizontal no celular:
 *  sem isso, as últimas abas ficam fora da tela e sem como chegar nelas. */
export function Abas({ atual, aoTrocar, cargosDisponiveis }: {
  atual: Vista;
  aoTrocar: (v: Vista) => void;
  cargosDisponiveis: Cargo[];
}) {
  const itens: { id: Vista; rotulo: string; ativo: boolean }[] = [
    ...CARGOS.map((c) => ({
      id: c as Vista, rotulo: NOME_CARGO[c], ativo: cargosDisponiveis.includes(c),
    })),
    { id: "padroes", rotulo: "Padrões", ativo: true },
    { id: "cruzamentos", rotulo: "Cruzamentos", ativo: true },
  ];
  return (
    <div className="abas" role="tablist">
      {itens.map((i) => (
        <button
          key={i.id}
          role="tab"
          aria-selected={i.id === atual}
          disabled={!i.ativo}
          style={{ opacity: i.ativo ? undefined : 0.35 }}
          onClick={() => i.ativo && aoTrocar(i.id)}
        >
          {i.rotulo}
        </button>
      ))}
    </div>
  );
}
