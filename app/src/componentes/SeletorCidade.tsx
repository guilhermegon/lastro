import type { ResumoUF, Sigla } from "../tipos";

interface Props {
  /** as UFs do índice; a cidade com dado é a capital de cada uma */
  ufs: ResumoUF[];
  atual: Sigla;
  aberto: boolean;
  aoAbrir: (v: boolean) => void;
  aoEscolher: (uf: Sigla) => void;
}

/**
 * Gaveta "Qual sua cidade?" — o par do seletor de estado, para o vereador.
 *
 * **Por que existe uma gaveta só para isto.** O vereador é a única tela cuja
 * unidade é a cidade, não a UF. Fazer o leitor escolher um estado para chegar à
 * capital dele é pedir que ele traduza a pergunta que tem ("como foi em
 * Goiânia?") na pergunta que a tela aceita ("qual estado?"). Escolher a cidade
 * direto é a mesma navegação com uma tradução a menos.
 *
 * **A lista diz o que tem, e o que não tem.** Hoje há dado das 26 capitais e do
 * Distrito Federal — não dos 5.570 municípios. Uma gaveta de cidades que
 * mostrasse só 27 sem dizer por quê pareceria um recorte arbitrário; a nota no
 * rodapé diz que é cobertura, não escolha editorial, e o que falta para ampliá-la.
 */
export function SeletorCidade({ ufs, atual, aberto, aoAbrir, aoEscolher }: Props) {
  const comCidade = ufs.filter((u) => u.capital);
  const escolhida = comCidade.find((u) => u.s === atual);
  // ordena pelo nome da CIDADE, que é o que o leitor procura, não pelo do estado
  const lista = [...comCidade].sort((a, b) =>
    (a.capital ?? "").localeCompare(b.capital ?? "", "pt-BR"));

  return (
    <details className="gaveta" open={aberto}
             onToggle={(e) => aoAbrir(e.currentTarget.open)}>
      <summary>
        <span className="seta" aria-hidden="true">▸</span>
        Qual sua cidade?
        {escolhida && (
          <span className="atual">
            {escolhida.capital} · {escolhida.s}
          </span>
        )}
      </summary>
      <div className="estados">
        {lista.map((u) => (
          <button key={u.s} aria-pressed={u.s === atual}
                  onClick={() => aoEscolher(u.s)}>
            <span>{u.capital}</span>
            <span className="sg">{u.s}</span>
          </button>
        ))}
      </div>
      <p className="gaveta-nota">
        São as {lista.length} capitais. O vereador é apurado por município, e há
        5.561 deles com eleição em 2024 — a cobertura aqui é das capitais porque
        é o recorte que cabe no que servimos hoje, não um julgamento sobre o
        resto. Ampliar é trabalho de ingestão, não de decisão.
      </p>
    </details>
  );
}
