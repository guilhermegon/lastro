import { useCallback, useEffect, useState } from "react";
import type {
  BaseUF, Cargo, Cruzamentos, DadosCargo, Indice, Padroes, Rivais, Sigla,
  Vereador,
} from "./tipos";
import { CARGOS } from "./tipos";
import {
  carregarAnosCargo, carregarBase, carregarCargoAno, carregarCruzamentos,
  carregarIndice, carregarPadroes, carregarRivaisAno, carregarVereador,
  prebuscar,
} from "./lib/dados";
import { numero } from "./lib/formato";
import { noEstado } from "./lib/uf";
import { Logo } from "./componentes/Logo";
import { SeletorEstado } from "./componentes/SeletorEstado";
import { Abas, type Vista } from "./componentes/Abas";
import { Dica, type EstadoDica } from "./componentes/Dica";
import { VistaCargo } from "./vistas/VistaCargo";
import { VistaPadroes } from "./vistas/VistaPadroes";
import { VistaCruzamentos } from "./vistas/VistaCruzamentos";
import { VistaVereador } from "./vistas/VistaVereador";
import { VistaNacional } from "./vistas/VistaNacional";

/**
 * O estado da tela mora na URL: `?uf=GO&ano=2022&v=estadual&c=0`.
 *
 * Num produto de inteligência política a ação mais frequente é mandar a tela
 * para outra pessoa. Com o estado na URL, copiar o endereço compartilha
 * exatamente o que está sendo visto, o botão voltar funciona e recarregar não
 * perde nada — sem biblioteca de rota.
 */
interface Selecao { uf: Sigla; ano: number; vista: Vista; cand: number }

function ehVista(v: string): v is Vista {
  return v === "nacional" || v === "padroes" || v === "cruzamentos"
    || v === "vereador" || (CARGOS as string[]).includes(v);
}

function lerURL(): Selecao {
  const p = new URLSearchParams(location.search);
  const v = p.get("v") ?? "nacional";
  return {
    uf: (p.get("uf") ?? "GO").toUpperCase(),
    ano: Number(p.get("ano") ?? 2022),
    vista: ehVista(v) ? v : "nacional",
    cand: Number(p.get("c") ?? 0),
  };
}

function gravarURL(s: Selecao) {
  const p = new URLSearchParams({
    uf: s.uf, ano: String(s.ano), v: s.vista, c: String(s.cand),
  });
  history.replaceState(null, "", `?${p}`);
}

export default function App() {
  const [indice, setIndice] = useState<Indice | null>(null);
  const [base, setBase] = useState<BaseUF | null>(null);
  const [cargo, setCargo] = useState<DadosCargo | null>(null);
  const [padroes, setPadroes] = useState<Padroes | null>(null);
  const [cruz, setCruz] = useState<Cruzamentos | null>(null);
  const [rivais, setRivais] = useState<Rivais | null>(null);
  const [ver, setVer] = useState<Vereador | null>(null);
  const [sel, setSel] = useState<Selecao>(lerURL);
  const [gaveta, setGaveta] = useState(false);
  const [dica, setDica] = useState<EstadoDica | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    carregarIndice().then(setIndice).catch((e) => setErro(String(e)));
  }, []);

  // Os mapas por ano acumulam, então precisam zerar quando muda o que eles
  // indexam. Sem isto o pleito de 2022 de São Paulo apareceria sob Minas.
  useEffect(() => {
    setCargo(null);
    setRivais(null);
    setVer(null);
  }, [sel.uf, sel.vista]);

  useEffect(() => {
    let vivo = true;
    carregarBase(sel.uf)
      .then((b) => { if (vivo) setBase(b); })
      .catch((e) => { if (vivo) setErro(String(e)); });
    return () => { vivo = false; };
  }, [sel.uf]);

  // Carrega só o recurso da aba aberta E só o pleito aberto. É o motivo de os
  // dados serem fatiados por UF, por cargo e por ano: em São Paulo o estadual
  // inteiro são 2,7 MB, e um pleito são 481 KB.
  //
  // Os demais pleitos vêm depois, em segundo plano, para que a troca de ano
  // continue instantânea — ver `prebuscar` em lib/dados.
  useEffect(() => {
    let vivo = true;
    const v = sel.vista;
    const ano = sel.ano;
    setCarregando(true);
    if (v === "nacional") {           // já está tudo no índice
      setCarregando(false);
      return () => { vivo = false; };
    }
    if (v === "padroes" || v === "cruzamentos" || v === "vereador") {
      const p = v === "padroes"
        ? carregarPadroes(sel.uf).then((d) => { if (vivo) setPadroes(d); })
        : v === "cruzamentos"
        ? carregarCruzamentos(sel.uf).then((d) => { if (vivo) setCruz(d); })
        : carregarVereador(sel.uf).then((d) => { if (vivo) setVer(d); });
      p.then(() => { if (vivo) setErro(null); })
       .catch((e) => { if (vivo) setErro(String(e)); })
       .finally(() => { if (vivo) setCarregando(false); });
      return () => { vivo = false; };
    }

    const proporcional = v === "estadual" || v === "federal";

    // Rivais só nos proporcionais: quem abre a aba de presidente não deve pagar
    // por ele. A falha aqui não derruba a tela — o painel não aparece.
    if (proporcional) {
      carregarRivaisAno(sel.uf, v, ano)
        .then((d) => { if (vivo) setRivais((r) => ({ ...(r ?? {}), [ano]: d })); })
        .catch(() => { /* sem rivais neste pleito */ });
    }

    carregarCargoAno(sel.uf, v, ano)
      .then((d) => {
        if (!vivo) return;
        setCargo((c) => ({ ...(c ?? {}), [String(ano)]: d }));
        setErro(null);
      })
      .catch((e) => { if (vivo) setErro(String(e)); })
      .finally(() => {
        if (!vivo) return;
        setCarregando(false);
        // Só agora: a pré-busca não pode competir com o que a tela espera.
        carregarAnosCargo(sel.uf, v)
          .then((anos) => prebuscar(
            sel.uf, v, anos, ano, proporcional, () => vivo,
            (a, bloco, riv) => {
              setCargo((c) => ({ ...(c ?? {}), [String(a)]: bloco }));
              if (riv) setRivais((r) => ({ ...(r ?? {}), [a]: riv }));
            }))
          .catch(() => { /* sem pré-busca; a troca de ano busca na hora */ });
      });
    return () => { vivo = false; };
  }, [sel.uf, sel.vista, sel.ano]);

  useEffect(() => gravarURL(sel), [sel]);

  useEffect(() => {
    if (!indice) return;
    const r = indice.ufs.find((u) => u.s === sel.uf);
    document.title = r && sel.vista !== "nacional"
      ? `Cadê o Voto ${noEstado(r.s, r.n)}?` : "Cadê o Voto?";
  }, [indice, sel.uf, sel.vista]);

  const trocarUF = useCallback((uf: Sigla) => {
    setSel((s) => ({ ...s, uf, cand: 0 }));
    setGaveta(false);
  }, []);

  if (erro) {
    return (
      <main className="wrap" style={{ padding: "3rem 0" }}>
        <h1>Não foi possível carregar os dados</h1>
        <p style={{ color: "var(--ink-2)" }}>{erro}</p>
        <p className="indice exp">
          Se estiver abrindo o arquivo direto do disco, o navegador bloqueia a leitura
          dos dados por segurança. Sirva a pasta por HTTP — <code>npm run dev</code> ou
          qualquer servidor estático.
        </p>
      </main>
    );
  }

  if (!indice) {
    return <main className="wrap" style={{ padding: "3rem 0" }}><p>Carregando…</p></main>;
  }

  const resumo = indice.ufs.find((u) => u.s === sel.uf);
  const nMun = resumo?.nm ?? base?.municipios.length ?? 0;
  const agregado = indice.agregado.find((a) => a.uf === sel.uf && a.ano === sel.ano);
  const anosComDado = indice.anos;
  // vereador tem seus próprios anos; padrões mostra a série toda de uma vez
  const usaAno = sel.vista !== "vereador" && sel.vista !== "padroes";
  const nacional = sel.vista === "nacional";
  const titulo = resumo && !nacional
    ? `Cadê o Voto ${noEstado(resumo.s, resumo.n)}?` : "Cadê o Voto?";

  return (
    <>
      <div className="topo">
        <div className="wrap">
          <div className="topo-in">
            <div className="marca">
              <Logo />
              <h1>{titulo}</h1>
              <p>
                {nacional
                  ? "Distribuição espacial do voto para deputado estadual em cada"
                    + " unidade da federação, de 1998 a 2022, município a município."
                  : sel.vista === "vereador"
                  ? "Vereadores da capital, por zona eleitoral, de 2000 a 2024."
                  : <>Onde cada candidato tirou voto
                      {nMun > 2 && <>, município a município</>}, em todos os
                      cargos, de 1998 a 2022.</>}
              </p>
            </div>
            {/* Só onde este ano governa a tela.

                Em "vereador" ele não governa: a eleição municipal cai em
                2000, 2004, … 2024, sem um único ano em comum com os pleitos
                gerais, e a vista tem seletor próprio. Os dois juntos mostravam
                duas faixas de ano discordando na mesma tela, e a de cima —
                inerte — parava em 2022, o que se lia como "falta 2024".

                Em "padroes" também não: aquela tela mostra a série inteira de
                uma vez, então escolher um ano não muda nada. */}
            {usaAno && (
              <div className="seg" role="group" aria-label="Pleito">
                {anosComDado.map((a) => (
                  <button key={a} aria-pressed={a === sel.ano}
                          onClick={() => setSel((s) => ({ ...s, ano: a, cand: 0 }))}>
                    {a}
                  </button>
                ))}
              </div>
            )}
          </div>

          <SeletorEstado ufs={indice.ufs} atual={sel.uf} aberto={gaveta}
                         aoAbrir={setGaveta} aoEscolher={trocarUF} />

          <Abas atual={sel.vista} cargosDisponiveis={resumo?.cargos ?? CARGOS}
                temVereador={resumo?.capital != null}
                cidade={resumo?.capital}
                aoTrocar={(v) => setSel((s) => ({ ...s, vista: v, cand: 0 }))} />
        </div>
      </div>

      <main className="wrap">
        {carregando && (
          <p className="indice exp" style={{ padding: "14px 0 0" }}>
            Carregando {sel.uf}…
          </p>
        )}

        {nacional && (
          <VistaNacional indice={indice} ano={sel.ano}
                         aoEscolher={(uf) => setSel((s) => ({
                           ...s, uf, vista: "estadual", cand: 0 }))}
                         aoInspecionar={setDica} />
        )}

        {sel.vista === "padroes" && padroes && (
          <VistaPadroes p={padroes} nMun={nMun} uf={resumo?.n ?? sel.uf} />
        )}

        {sel.vista === "cruzamentos" && cruz && (
          <VistaCruzamentos c={cruz} ano={sel.ano} nMun={nMun}
                            uf={resumo?.n ?? sel.uf} />
        )}

        {sel.vista === "vereador" && ver && (
          <VistaVereador v={ver} selecionado={sel.cand}
                         aoSelecionar={(i) => setSel((s) => ({ ...s, cand: i }))} />
        )}

        {sel.vista !== "padroes" && sel.vista !== "cruzamentos"
          && sel.vista !== "vereador" && base && cargo?.[String(sel.ano)] && (
          <VistaCargo
            cargo={sel.vista as Cargo}
            base={base}
            dados={cargo}
            ano={sel.ano}
            agregado={agregado}
            selecionado={sel.cand}
            aoSelecionar={(i) => setSel((s) => ({ ...s, cand: i }))}
            aoInspecionar={setDica}
            rivais={rivais}
          />
        )}
      </main>

      <footer className="wrap">
        <p>
          <strong>Lastro — Inteligência Política.</strong> Fonte: Tribunal Superior
          Eleitoral, dados abertos, arquivo{" "}
          <span className="num">votacao_candidato_munzona</span>, 1º turno. Malha
          municipal: IBGE. {resumo && `${resumo.n}: ${numero(nMun)} municípios.`}
        </p>
        <p>
          O Distrito Federal elege deputado distrital e não estadual, por isso não
          aparece na lista de estados: são 26 unidades.
        </p>
        <p>
          Municípios efetivos não se comparam entre estados sem cuidado — Roraima tem
          15 municípios e Minas 853, e o índice é limitado pelo porte. Use a fração do
          estado para comparar.
        </p>
      </footer>

      <Dica dica={dica} aoFechar={() => setDica(null)} />
    </>
  );
}
