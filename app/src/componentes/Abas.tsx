import { CARGOS, NOME_CARGO, type Cargo } from "../tipos";

export type Vista = "nacional" | Cargo | "vereador" | "padroes"
  | "cruzamentos" | "emendas" | "api" | "sobre";

/** Ordem decrescente de escopo — o país, depois presidente até vereador — e as duas
 *  abas de análise. Padrões e Cruzamentos saíram daqui: viraram o Radar, o
 *  produto fechado. A barra rola na horizontal no celular:
 *  sem isso, as últimas abas ficam fora da tela e sem como chegar nelas. */
export function Abas({ atual, aoTrocar, cargosDisponiveis, temVereador, cidade,
                      temEmendas }: {
  atual: Vista;
  aoTrocar: (v: Vista) => void;
  cargosDisponiveis: Cargo[];
  temVereador: boolean;
  cidade: string | undefined;
  temEmendas: boolean;
}) {
  const itens: { id: Vista; rotulo: string; ativo: boolean }[] = [
    { id: "nacional" as Vista, rotulo: "Nacional", ativo: true },
    ...CARGOS.map((c) => ({
      id: c as Vista, rotulo: NOME_CARGO[c], ativo: cargosDisponiveis.includes(c),
    })),
    { id: "vereador" as Vista,
      rotulo: cidade ? `Vereador · ${cidade}` : "Vereador",
      ativo: temVereador },
    { id: "emendas", rotulo: "Emendômetro", ativo: temEmendas },
    { id: "api", rotulo: "API", ativo: true },
    { id: "sobre", rotulo: "Sobre", ativo: true },
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
