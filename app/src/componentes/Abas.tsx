import { CARGOS, nomeCargo, type Cargo, type Sigla } from "../tipos";

export type Vista = "home" | "nacional" | Cargo | "vereador"
  | "emendas" | "api" | "sobre";

/** Ordem decrescente de escopo — o país, depois presidente até vereador — e as duas
 *  abas de análise. Esta barra é o SEGUNDO nível: são as seções de dentro de
 *  Cadê o Voto?, não os produtos — trocar de produto é a fileira de cima.
 *  Padrões e Cruzamentos saíram daqui: viraram o Radar. API e Sobre também
 *  saíram: são da casa, não de Cadê o Voto?, e vivem no canto direito do
 *  cabeçalho. Estavam aparecendo nos dois lugares. A barra rola na horizontal
 *  no celular:
 *  sem isso, as últimas abas ficam fora da tela e sem como chegar nelas. */
export function Abas({ atual, aoTrocar, cargosDisponiveis, temVereador, cidade,
                       uf }: {
  atual: Vista;
  aoTrocar: (v: Vista) => void;
  cargosDisponiveis: Cargo[];
  temVereador: boolean;
  cidade: string | undefined;
  /** so para o rotulo: no DF a aba do proporcional estadual chama Distrital */
  uf: Sigla | undefined;
}) {
  const itens: { id: Vista; rotulo: string; ativo: boolean }[] = [
    { id: "nacional" as Vista, rotulo: "Nacional", ativo: true },
    ...CARGOS.map((c) => ({
      id: c as Vista, rotulo: nomeCargo(c, uf), ativo: cargosDisponiveis.includes(c),
    })),
    { id: "vereador" as Vista,
      rotulo: cidade ? `Vereador · ${cidade}` : "Vereador",
      ativo: temVereador },
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
