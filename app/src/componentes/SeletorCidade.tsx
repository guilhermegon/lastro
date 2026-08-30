import { useMemo, useState } from "react";
import type { CidadeServida, Sigla } from "../tipos";

interface Props {
  /** as cidades servidas; `null` enquanto o índice não chegou */
  cidades: CidadeServida[] | null;
  /** chave da cidade aberta; vazio significa "a capital da UF atual" */
  atual: string;
  uf: Sigla;
  aberto: boolean;
  aoAbrir: (v: boolean) => void;
  aoEscolher: (c: CidadeServida) => void;
}

/** Chave de busca: sem acento e sem caixa, porque ninguém digita "Anicuns"
 *  com a cedilha certa quando está procurando depressa. */
const chave = (t: string) =>
  t.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

/**
 * Gaveta "Qual sua cidade?" — o par do seletor de estado, para o vereador.
 *
 * **Por que existe uma gaveta só para isto.** O vereador é a única tela cuja
 * unidade é a cidade, não a UF. Fazer o leitor escolher um estado para chegar
 * à cidade dele é pedir que ele traduza a pergunta que tem ("como foi em
 * Anápolis?") na pergunta que a tela aceita ("qual estado?"). Escolher a
 * cidade direto é a mesma navegação com uma tradução a menos.
 *
 * **A busca aparece porque a lista cresceu, e a lista cresceu de propósito.**
 * Enquanto eram 27 capitais, rolar era mais rápido que digitar. Com Goiás
 * inteiro são 271 cidades, e o número vai subir a cada estado ingerido — a
 * busca é o que faz a cobertura maior não virar navegação pior.
 *
 * **A lista diz o que tem e o que não tem.** Uma lista que mistura 246
 * municípios de um estado com as capitais dos outros 26 pareceria arbitrária
 * sem explicação. A nota do rodapé diz que Goiás é o piloto da cobertura
 * municipal e que os demais estados ainda estão na capital — é cobertura, não
 * julgamento sobre o resto.
 */
export function SeletorCidade({ cidades, atual, uf, aberto, aoAbrir,
                                aoEscolher }: Props) {
  const [busca, setBusca] = useState("");

  const lista = cidades ?? [];
  // sem cidade escolhida, a aba está na capital da UF atual — que é o que ela
  // servia antes de existir cobertura municipal
  const escolhida = lista.find((c) => c.k === atual)
    ?? lista.find((c) => c.uf === uf && c.src === "vereador.json");

  const vistas = useMemo(() => {
    const q = chave(busca.trim());
    if (!q) return lista;
    return lista.filter((c) => chave(c.n).includes(q)
      || c.uf.toLowerCase() === q);
  }, [lista, busca]);

  const nUF = useMemo(
    () => new Set(lista.filter((c) => c.cod).map((c) => c.uf)).size, [lista]);

  return (
    <details className="gaveta" open={aberto}
             onToggle={(e) => aoAbrir(e.currentTarget.open)}>
      <summary>
        <span className="seta" aria-hidden="true">▸</span>
        Qual sua cidade?
        {escolhida && (
          <span className="atual">{escolhida.n} · {escolhida.uf}</span>
        )}
      </summary>

      {cidades === null ? (
        <p className="gaveta-nota">Carregando as cidades…</p>
      ) : (
        <>
          <div className="gaveta-busca">
            <input className="busca" type="search" value={busca}
                   placeholder={`Buscar entre ${lista.length} cidades…`}
                   aria-label="Buscar cidade"
                   onChange={(e) => setBusca(e.target.value)} />
          </div>

          {vistas.length === 0 ? (
            <p className="gaveta-nota">
              Nenhuma cidade com esse nome na cobertura atual. Hoje há as 26
              capitais, o Distrito Federal e todos os municípios de{" "}
              {nUF === 1 ? "Goiás" : `${nUF} estados`}.
            </p>
          ) : (
            <div className="estados rolagem">
              {vistas.map((c) => (
                <button key={c.k} aria-pressed={c.k === escolhida?.k}
                        onClick={() => { aoEscolher(c); setBusca(""); }}>
                  <span>{c.n}</span>
                  <span className="sg">{c.uf}</span>
                </button>
              ))}
            </div>
          )}

          <p className="gaveta-nota">
            {busca.trim()
              ? <>{vistas.length} de {lista.length} cidades. </>
              : <>São {lista.length} cidades. </>}
            Goiás é o piloto da cobertura municipal e entra inteiro, com os 246
            municípios; nos demais estados a aba ainda serve a capital.
            Ampliar é trabalho de ingestão, não de decisão.
          </p>
        </>
      )}
    </details>
  );
}
