import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  AlegoAdmin, AlegoVerbas, AlmgVerbas, Assembleias, BaseUF, Cargo, CldfAdmin,
  CldfVerbas, DadosCargo, Demografia, Emendas, EmendasBR, Esfera, Indice,
  CidadeServida, Rivais, Sigla, Urnas, Vereador,
} from "./tipos";

/** O pacote da aba API, buscado de uma vez porque a aba é nacional. */
interface ApiCasas {
  assembleias: Assembleias | null;
  alegoVerbas: AlegoVerbas | null;
  alegoAdmin: AlegoAdmin | null;
  cldfVerbas: CldfVerbas | null;
  cldfAdmin: CldfAdmin | null;
  almgVerbas: AlmgVerbas | null;
}
import { CARGOS } from "./tipos";
import {
  carregarAnosCargo, carregarBase, carregarCargoAno,
  carregarAlegoAdmin, carregarAlegoVerbas, carregarAlmgVerbas,
  carregarAssembleias, carregarCldfAdmin, carregarCldfVerbas,
  carregarDemografia, carregarEmendas, carregarEmendasBR,
  carregarEmendasEstadual, carregarIndice,
  carregarCidade, carregarCidades, carregarRivaisAno,
  carregarUrnasCidade, prebuscar,
} from "./lib/dados";
import { numero } from "./lib/formato";
import { noEstado } from "./lib/uf";
import { Logo } from "./componentes/Logo";
import { SeletorEstado } from "./componentes/SeletorEstado";
import { SeletorCidade } from "./componentes/SeletorCidade";
import { Abas, type Vista } from "./componentes/Abas";
import { Dica, type EstadoDica } from "./componentes/Dica";
import { VistaCargo } from "./vistas/VistaCargo";
import { VistaEmendas } from "./vistas/VistaEmendas";
import { VistaSobre } from "./vistas/VistaSobre";
import { VistaApi } from "./vistas/VistaApi";
import { VistaHome } from "./vistas/VistaHome";
import { TrocaProduto } from "./componentes/TrocaProduto";
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
interface Selecao {
  uf: Sigla; ano: number; vista: Vista; cand: number;
  /** cidade aberta na aba de vereador — a chave de `cidades.json`. Vazio
   *  significa "a capital desta UF", que e' o que a aba servia antes de haver
   *  cobertura municipal. */
  cid: string;
}

function ehVista(v: string): v is Vista {
  return v === "home" || v === "nacional" || v === "vereador"
    || v === "emendas" || v === "sobre" || v === "api"
    || (CARGOS as string[]).includes(v);
}

function lerURL(): Selecao {
  const p = new URLSearchParams(location.search);
  const v = p.get("v") ?? "home";
  return {
    uf: (p.get("uf") ?? "GO").toUpperCase(),
    // `Number("abc")` e' NaN, e NaN escapa de qualquer `includes` mais
    // adiante sem nunca ser igual a nada. Vira 2022 aqui, na porta.
    ano: Number.isFinite(Number(p.get("ano"))) ? Number(p.get("ano")) : 2022,
    vista: ehVista(v) ? v : "home",
    cand: Number(p.get("c") ?? 0),
    cid: p.get("cid") ?? "",
  };
}

function gravarURL(s: Selecao) {
  const p = new URLSearchParams({
    uf: s.uf, ano: String(s.ano), v: s.vista, c: String(s.cand),
  });
  if (s.cid) p.set("cid", s.cid);
  history.replaceState(null, "", `?${p}`);
}

export default function App() {
  const [indice, setIndice] = useState<Indice | null>(null);
  const [base, setBase] = useState<BaseUF | null>(null);
  const [cargo, setCargo] = useState<DadosCargo | null>(null);
  const [rivais, setRivais] = useState<Rivais | null>(null);
  const [ver, setVer] = useState<Vereador | null>(null);
  // Mapa de urna: existe só onde foi gerado, e a ausência não é erro.
  const [urnas, setUrnas] = useState<Urnas | null>(null);
  // As duas esferas vivem em arquivos separados e nem toda UF tem a estadual:
  // guardar as duas evita rebaixar ao alternar, e `null` distingue "não
  // carregado" de "não existe aqui".
  const [emFed, setEmFed] = useState<Emendas | null>(null);
  const [emEst, setEmEst] = useState<Emendas | null | false>(null);
  const [esfera, setEsfera] = useState<Esfera>("federal");
  const [demo, setDemo] = useState<Demografia | null>(null);
  // Nacional: nao muda com a UF, entao carrega uma vez e fica.
  const [emBR, setEmBR] = useState<EmendasBR | null>(null);
  // A aba API é nacional: carregada uma vez, não por UF.
  const [api, setApi] = useState<ApiCasas | null>(null);
  // As cidades servidas: uma vez por sessao, e so' quando a aba de vereador
  // e' aberta — 34 KB que nao servem a mais nenhuma tela.
  const [cidades, setCidades] = useState<CidadeServida[] | null>(null);
  const [sel, setSel] = useState<Selecao>(lerURL);
  const [gaveta, setGaveta] = useState(false);
  const [dica, setDica] = useState<EstadoDica | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    carregarIndice().then(setIndice).catch((e) => setErro(String(e)));
  }, []);

  useEffect(() => {
    if (sel.vista !== "vereador" || cidades) return;
    carregarCidades().then((c) => setCidades(c.cidades)).catch(() => setCidades([]));
  }, [sel.vista, cidades]);

  // Os mapas por ano acumulam, então precisam zerar quando muda o que eles
  // indexam. Sem isto o pleito de 2022 de São Paulo apareceria sob Minas.
  useEffect(() => {
    setCargo(null);
    setRivais(null);
    setVer(null);
    setUrnas(null);
  }, [sel.uf, sel.vista, sel.cid]);

  useEffect(() => {
    setEmFed(null);
    setEmEst(null);
    setDemo(null);
    setEsfera("federal");
  }, [sel.uf]);

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
    if (v === "home") {           // só marca e texto
      setCarregando(false);
      return () => { vivo = false; };
    }
    if (v === "api") {
      if (api) { setCarregando(false); return () => { vivo = false; }; }
      // Cada arquivo falha por si: uma casa fora do ar não apaga as outras.
      const nulo = () => null;
      Promise.all([
        carregarAssembleias().catch(nulo),
        carregarAlegoVerbas().catch(nulo),
        carregarAlegoAdmin().catch(nulo),
        carregarCldfVerbas().catch(nulo),
        carregarCldfAdmin().catch(nulo),
        carregarAlmgVerbas().catch(nulo),
      ]).then(([as, av, aa, cv, ca, mv]) => {
        if (!vivo) return;
        setApi({ assembleias: as, alegoVerbas: av, alegoAdmin: aa,
                 cldfVerbas: cv, cldfAdmin: ca, almgVerbas: mv });
        setErro(null);
      }).finally(() => { if (vivo) setCarregando(false); });
      return () => { vivo = false; };
    }
    if (v === "sobre") {          // texto e método; nada a buscar
      setCarregando(false);
      return () => { vivo = false; };
    }
    if (v === "emendas") {
      // Demografia é para as leituras por habitante e por km². Falha nela não
      // derruba a tela: some a opção, não o mapa.
      carregarDemografia(sel.uf).then((d) => { if (vivo) setDemo(d); })
        .catch(() => { /* sem per capita */ });
      if (!emBR) {
        carregarEmendasBR().then((d) => { if (vivo) setEmBR(d); })
          .catch(() => { /* sem comparacao nacional */ });
      }
      // A estadual só existe onde o governo do estado publica com autor e
      // município. `false` registra "procurei e não há", que é diferente de
      // "ainda não busquei".
      carregarEmendasEstadual(sel.uf)
        .then((d) => { if (vivo) setEmEst(d); })
        .catch(() => { if (vivo) setEmEst(false); });
      carregarEmendas(sel.uf)
        .then((d) => { if (vivo) { setEmFed(d); setErro(null); } })
        .catch((e) => { if (vivo) setErro(String(e)); })
        .finally(() => { if (vivo) setCarregando(false); });
      return () => { vivo = false; };
    }
    if (v === "vereador") {
      // A cidade manda, e a UF só entra quando nenhuma foi escolhida — aí é a
      // capital, que é o que esta aba servia antes de haver cobertura
      // municipal. Um link antigo, sem `cid`, continua abrindo o que abria.
      //
      // Cada cidade traz o CAMINHO do próprio arquivo, então a capital de São
      // Paulo e um município de Goiás entram pela mesma linha de código: a
      // diferença mora no índice, não aqui.
      if (!cidades) return () => { vivo = false; };
      const c = cidades.find((x) => x.k === sel.cid)
        ?? cidades.find((x) => x.uf === sel.uf && x.cap)
        ?? cidades.find((x) => x.uf === sel.uf && x.src === "vereador.json")
        ?? cidades.find((x) => x.uf === sel.uf);
      if (!c) {
        setErro(`Sem dado de vereador em ${sel.uf}.`);
        return () => { vivo = false; };
      }
      // O mapa de urna existe só onde foi gerado. Zerar antes de pedir impede
      // que o mapa da cidade anterior fique na tela sob o nome da nova.
      setUrnas(null);
      if (c.urna) {
        carregarUrnasCidade(c.uf, c.urna).then((u) => { if (vivo) setUrnas(u); })
          .catch(() => { if (vivo) setUrnas(null); });
      }
      carregarCidade(c.uf, c.src)
        .then((d) => { if (vivo) { setVer(d); setErro(null); } })
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
  }, [sel.uf, sel.vista, sel.ano, sel.cid, cidades]);

  // O ano da URL contra a lista de pleitos que existe de verdade.
  //
  // A aba de vereador tem escala propria — 2000, 2004, ... 2024 — e nenhum ano
  // em comum com os pleitos gerais. Ela guarda o ano dela em estado local, e
  // por isso nunca sujou `sel.ano`; quem suja e' um LINK. Compartilhar
  // `?v=vereador&ano=2024` e depois clicar em Presidente pedia
  // `presidente/2024.json`, que nao existe.
  //
  // Encaixa no pleito imediatamente anterior em vez de pular para o ultimo:
  // quem abriu um link de 2024 quer o mais recente, e o mais recente que os
  // cargos gerais tem e' 2022 — nao 1998.
  useEffect(() => {
    if (!indice || indice.anos.includes(sel.ano)) return;
    const encaixe = [...indice.anos].reverse().find((a) => a <= sel.ano)
      ?? indice.anos[indice.anos.length - 1];
    if (encaixe != null) setSel((s) => ({ ...s, ano: encaixe }));
  }, [indice, sel.ano]);

  useEffect(() => gravarURL(sel), [sel]);

  useEffect(() => {
    if (!indice) return;
    const r = indice.ufs.find((u) => u.s === sel.uf);
    // Na home quem fala é a casa; nas telas de produto, o produto.
    document.title =
      sel.vista === "home" ? "Lastro — Inteligência Política"
      : sel.vista === "emendas" ? "Emendômetro"
      : r && sel.vista !== "nacional" ? `Cadê o Voto ${noEstado(r.s, r.n)}?`
      : "Cadê o Voto?";
  }, [indice, sel.uf, sel.vista]);

  const trocarUF = useCallback((uf: Sigla) => {
    // `cid` sai junto. Sem isso dá para estar em São Paulo com Itumbiara
    // aberta: a resolução procura por `cid` ANTES de procurar por UF, então a
    // cidade antiga vence o estado novo.
    setSel((s) => ({ ...s, uf, cid: "", cand: 0 }));
    setGaveta(false);
  }, []);

  // Entrar na aba de vereador começa pela capital, sempre.
  //
  // Antes a aba reabria a última cidade escolhida, o que soa prestativo e não
  // é: a capital é o único ponto de partida que existe em toda UF, e voltar
  // à aba num município qualquer do interior deixa o leitor sem referência de
  // onde está. Quem limpa é o CLIQUE — um link com `cid` continua abrindo a
  // cidade do link, que é o que faz o endereço valer a pena compartilhar.
  const trocarVista = useCallback((v: Vista) => {
    setSel((s) => ({ ...s, vista: v, cand: 0,
                     cid: v === "vereador" ? "" : s.cid }));
  }, []);

  // A MESMA resolução do efeito que carrega a cidade, e de propósito: o rótulo
  // da aba e o subtítulo têm de nomear a cidade que está na tela. Enquanto
  // usavam `resumo.capital`, a aba dizia "Goiânia" com Caçu aberto.
  const cidadeAtual = useMemo(() => {
    if (!cidades) return undefined;
    return (cidades.find((x) => x.k === sel.cid)
      ?? cidades.find((x) => x.uf === sel.uf && x.cap)
      ?? cidades.find((x) => x.uf === sel.uf && x.src === "vereador.json")
      ?? cidades.find((x) => x.uf === sel.uf))?.n;
  }, [cidades, sel.cid, sel.uf]);

  // Hooks antes de qualquer `return` antecipado: abaixo do `if (erro)` o
  // React renderizaria menos hooks num render que no outro (erro #310).
  // Sem índice não há o que desenhar em volta: aí a tela de erro é a tela
  // inteira, e é a única vez em que isso é correto. Quando o índice existe e o
  // que falhou foi UMA vista, o erro passou a morar dentro do conteúdo — ver
  // `<main>`. Antes ele era um return antecipado e levava junto o cabeçalho, a
  // fileira de produtos e a barra de abas: o leitor ficava numa tela de erro
  // sem um único botão para sair dela.
  if (erro && !indice) {
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
  // O Emendômetro tem seus próprios anos (2015 em diante, todo ano — não só
  // ano de eleição), então também não usa a faixa de pleito.
  const usaAno = sel.vista !== "vereador"
    && sel.vista !== "emendas" && sel.vista !== "sobre"
    && sel.vista !== "api" && sel.vista !== "home";
  // A esfera escolhida, se ela existir aqui; senão a que existir.
  const emAtual: Emendas | null =
    (esfera === "estadual" ? (emEst || null) : emFed) ?? emFed ?? null;
  const nacional = sel.vista === "nacional";
  const naCasa = sel.vista === "home" || sel.vista === "api"
    || sel.vista === "sobre";
  // As seções de "Cadê o Voto?": tudo que não é casa nem outro produto.
  const ehCadeOVoto = !naCasa && sel.vista !== "emendas";
  // O cabeçalho dizia "Cadê o Voto em Goiás?" com o Emendômetro aberto: o
  // título ignorava o produto e olhava só o estado. Agora cada produto fala
  // por si, e a casa fala quando nenhum produto está aberto.
  const titulo =
    sel.vista === "emendas"
      ? (resumo ? `Emendômetro ${noEstado(resumo.s, resumo.n)}` : "Emendômetro")
    : sel.vista === "api" ? "O que as assembleias publicam"
    : sel.vista === "sobre" ? "Como este dado é feito"
    : resumo && !nacional ? `Cadê o Voto ${noEstado(resumo.s, resumo.n)}?`
    : "Cadê o Voto?";

  return (
    <>
      <div className="topo">
        <div className="wrap">
          {/* Primeiro nível: a casa à esquerda, sempre clicável, e os produtos
              lado a lado. Trocar de produto é um clique de qualquer lugar. */}
          <div className="cabeca">
            <Logo aoClicar={() => setSel((x) => ({ ...x, vista: "home", cand: 0 }))} />
            <TrocaProduto
              atual={sel.vista}
              aoTrocar={trocarVista} />
            <div className="meta">
              {([["api", "API"], ["sobre", "Sobre"]] as [Vista, string][]).map(
                ([id, r]) => (
                  <button key={id} type="button"
                          aria-current={sel.vista === id ? "true" : undefined}
                          onClick={() => setSel((x) => ({ ...x, vista: id, cand: 0 }))}>
                    {r}
                  </button>
                ))}
            </div>
          </div>

          <div className="topo-in">
            <div className="marca">
              <h1>{titulo}</h1>
              <p>
                {naCasa
                  ? sel.vista === "api"
                    ? "As 27 assembleias estaduais, o que cada uma publica sobre"
                      + " si mesma, e três casas cujo dado dá para consumir."
                    : sel.vista === "sobre"
                    ? "De onde vem cada número, como ele é contado, e o que"
                      + " decidimos não fazer."
                    : ""
                  : sel.vista === "emendas"
                  ? "Para onde cada parlamentar mandou dinheiro, município a"
                    + " município, com a transferência especial separada."
                  : nacional
                  ? "Distribuição espacial do voto para deputado estadual em cada"
                    + " unidade da federação, de 1998 a 2022, município a município."
                  : sel.vista === "vereador"
                  ? (cidadeAtual
                      ? `Vereadores de ${cidadeAtual}, por zona eleitoral e por `
                        + "local de votação, de 2000 a 2024."
                      : "Vereadores, por zona eleitoral, de 2000 a 2024.")
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
              <div className="seg-rot">
                <span className="et">Pleito geral</span>
              <div className="seg" data-pleito="geral" role="group"
                   aria-label="Pleito geral">
                {anosComDado.map((a) => (
                  <button key={a} aria-pressed={a === sel.ano}
                          onClick={() => setSel((s) => ({ ...s, ano: a, cand: 0 }))}>
                    {a}
                  </button>
                ))}
              </div>
              </div>
            )}
          </div>

          {/* Nas telas da casa — home, API e Sobre — não há estado escolhido
              nem seção de produto: a home é a vitrine, a API é nacional e o
              Sobre é método. Mostrar "Qual seu estado?" ali pede uma escolha
              que não muda nada, e mostrar as abas de cargo convida a entrar
              numa seção de um produto que ainda não foi aberto — que é
              justamente o achatamento que a fileira de produtos desfez. */}
          {/* No vereador a unidade e' a cidade, nao a UF: perguntar o estado
              faria o leitor traduzir a pergunta que ele tem na que a tela
              aceita. Mesma navegacao, uma traducao a menos. A gaveta de cidade
              nao fica aqui — desceu para depois das abas, ver abaixo. */}
          {!naCasa && sel.vista !== "vereador" && (
            <SeletorEstado ufs={indice.ufs} atual={sel.uf} aberto={gaveta}
                           aoAbrir={setGaveta} aoEscolher={trocarUF} />
          )}

          {/* A barra de seções é de "Cadê o Voto?" — Nacional, os cargos e o
              vereador. O Emendômetro tem os controles dele dentro da própria
              tela (esfera, ano, medida, Pix), e mostrar as abas de cargo ali
              ofereceria seções de outro produto. */}
          {ehCadeOVoto && (
            /* `ver` liga a aba, `capital` só nomeia: sem arquivo de vereador
               ela fica desligada e SEM cidade, porque "Vereador · Brasília"
               apagado sugeriria dado faltando — Brasília não tem câmara
               municipal, a CLDF acumula o papel. */
            <Abas atual={sel.vista} cargosDisponiveis={resumo?.cargos ?? CARGOS}
                  temVereador={resumo?.ver === true}
                  cidade={resumo?.ver ? (cidadeAtual ?? resumo.capital) : undefined}
                  uf={sel.uf}
                  aoTrocar={trocarVista} />
          )}

          {/* Depois das abas, e não antes: o estado governa a tela inteira, a
              cidade governa UMA aba. Controle que vale para tudo vem antes da
              barra; controle de uma seção vem depois dela, encostado no que
              ele muda. Acima, "Qual sua cidade?" se lia como se valesse para
              Presidente e Estadual também. */}
          {sel.vista === "vereador" && (
            <SeletorCidade
              cidades={cidades} atual={sel.cid} uf={sel.uf} aberto={gaveta}
              aoAbrir={setGaveta}
              aoEscolher={(c) => setSel((x) => ({ ...x, uf: c.uf, cid: c.k,
                                                  cand: 0 }))} />
          )}
        </div>
      </div>

      <main className="wrap">
        {erro && (
          <div className="nota" style={{ marginTop: 14 }}>
            <strong>Esta seção não carregou.</strong> {erro}
            <br /><br />
            As abas acima continuam funcionando — o que falhou foi o dado desta
            tela, não o site.
          </div>
        )}

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

        {/* O gate testa o objeto que de fato vai para a vista, não "alguma das
            duas chegou". As duas esferas resolvem em ordem imprevisível: com a
            estadual chegando primeiro, a condição antiga passava e a federal ia
            nula, e a tela quebrava em `e.anos`. */}
        {sel.vista === "emendas" && base && emAtual && (
          <VistaEmendas
            e={emAtual}
            esfera={esfera}
            esferasDisponiveis={emEst
              ? (["federal", "estadual"] as Esfera[])
              : (["federal"] as Esfera[])}
            aoTrocarEsfera={setEsfera}
            base={base}
            demo={demo}
            br={emBR}
            uf={sel.uf}
            aoInspecionar={setDica}
          />
        )}

        {sel.vista === "home" && (
          <VistaHome
            aoEntrar={trocarVista}
            nUF={indice.ufs.length}
            nMun={indice.ufs.reduce((t, u) => t + (u.nm ?? 0), 0)} />
        )}

        {sel.vista === "api" && api && <VistaApi {...api} />}

        {sel.vista === "sobre" && (
          <VistaSobre
            nUF={indice.ufs.length}
            nMun={indice.ufs.reduce((s, u) => s + (u.nm ?? 0), 0)} />
        )}

        {sel.vista === "vereador" && ver && (
          <VistaVereador v={ver} selecionado={sel.cand}
                         aoSelecionar={(i) => setSel((s) => ({ ...s, cand: i }))}
                         urnas={urnas} aoInspecionar={setDica} />
        )}

        {sel.vista !== "vereador" && sel.vista !== "home"
          && sel.vista !== "emendas" && sel.vista !== "api" && sel.vista !== "sobre" && base && cargo?.[String(sel.ano)] && (
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
          O Distrito Federal elege deputado <em>distrital</em>, não estadual. Os 24
          distritais são o equivalente funcional dos estaduais — a Câmara Legislativa
          acumula as competências de assembleia e de câmara municipal — e por isso
          entram no painel equiparados, o que fecha as 27 unidades. A aba se chama
          Distrital lá, e o DF é um município só: a geografia do voto não existe
          nele, e a tela diz isso.
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
