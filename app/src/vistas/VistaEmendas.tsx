import { useEffect, useMemo, useState } from "react";
import type {
  BaseUF, BlocoEmenda, Demografia, Emendas, EmendasBR, Esfera, FichaEmenda,
  Sigla,
} from "../tipos";
import { NOME_GRUPO, type GrupoEmenda } from "../tipos";
import { decimal, numero, percentual } from "../lib/formato";
import { quantis } from "../lib/escalas";
import { fundeMandato, LEGISLATURAS } from "../lib/mandato";
import { PaisEntreMandatos } from "./PaisEntreMandatos";
import { Mapa } from "../componentes/Mapa";
import { Legenda } from "../componentes/Legenda";
import { Indices } from "../componentes/Indices";
import { Cartoes } from "../componentes/Cartoes";
import type { EstadoDica } from "../componentes/Dica";

/** R$ com magnitude, porque emenda vai de mil a bilhão na mesma tabela e
 *  alinhar centavos ao lado de bilhões não se lê. */
function reais(v: number): string {
  const a = Math.abs(v);
  if (a >= 1e9) return `R$ ${decimal(v / 1e9, 2)} bi`;
  if (a >= 1e6) return `R$ ${decimal(v / 1e6, 2)} mi`;
  if (a >= 1e3) return `R$ ${decimal(v / 1e3, 0)} mil`;
  return `R$ ${decimal(v, 2)}`;
}

/** Reais cheios, para quando a magnitude importa menos que o valor exato. */
const reaisCheio = (v: number): string =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL",
                              maximumFractionDigits: 0 });

type Medida = "total" | "hab" | "area";

const ROTULO_MEDIDA: Record<Medida, string> = {
  total: "Total pago",
  hab: "Por habitante",
  area: "Por km²",
};

interface Props {
  e: Emendas;
  esfera: Esfera;
  esferasDisponiveis: Esfera[];
  aoTrocarEsfera: (e: Esfera) => void;
  base: BaseUF;
  demo: Demografia | null;
  /** o agregado nacional, para a comparacao entre mandatos */
  br: EmendasBR | null;
  uf: Sigla;
  aoInspecionar: (d: EstadoDica | null) => void;
}

export function VistaEmendas({
  e, esfera, esferasDisponiveis, aoTrocarEsfera, base, demo, br, uf,
  aoInspecionar,
}: Props) {
  const anos = useMemo(
    () => Object.keys(e.anos).map(Number).sort((a, b) => a - b), [e.anos]);

  /* Abre no último ano FECHADO, não no mais recente.
     O ano corrente está em execução e o pagamento tem defasagem: em Goiás, 2026
     aparece com R$ 2,7 mi contra R$ 20,4 mi de 2025 — uma ordem de grandeza a
     menos, e nada disso é queda de emenda. Abrir ali daria ao leitor uma
     primeira impressão falsa antes de ele tocar em qualquer controle. O ano
     corrente continua acessível, com aviso. */
  const anoCorrente = new Date().getFullYear();
  const [ano, setAno] = useState(() => {
    const fechados = anos.filter((a) => a < anoCorrente);
    return fechados[fechados.length - 1] ?? anos[anos.length - 1] ?? 0;
  });
  /* Trocar de esfera troca o conjunto de anos: a federal vai de 2015 a 2026, a
     estadual de Goiás só de 2020 a 2025. Sem isto, quem estivesse em 2026 e
     alternasse para estadual caía num ano que não existe ali, e a tela dizia
     "sem emenda" — o que se lê como ausência de emenda, não como ausência de
     ano. Cai no último fechado do conjunto novo. */
  useEffect(() => {
    if (anos.length && !anos.includes(ano)) {
      const fechados = anos.filter((a) => a < anoCorrente);
      setAno(fechados[fechados.length - 1] ?? (anos[anos.length - 1] as number));
      setAutor(0);
    }
  }, [anos, ano, anoCorrente]);

  /* Ano ou mandato. O ano é unidade contábil e o mandato é a unidade política:
     "quanto este parlamentar mandou para o território dele" é pergunta de
     mandato, e a visão anual a esconde atrás da volatilidade de execução. */
  const [porMandato, setPorMandato] = useState(false);
  const [leg, setLeg] = useState<string>("");

  const legsComDado = useMemo(
    () => LEGISLATURAS.filter((l) => l.anos.some((a) => !!e.anos[String(a)])),
    [e.anos]);

  useEffect(() => {
    if (porMandato && !legsComDado.some((l) => l.id === leg)) {
      setLeg(legsComDado[legsComDado.length - 1]?.id ?? "");
      setAutor(0);
    }
  }, [porMandato, legsComDado, leg]);

  const [medida, setMedida] = useState<Medida>("total");
  const [comPix, setComPix] = useState(true);
  const [autor, setAutor] = useState(0);
  /** filtro por casa do autor. "todas" não é neutro: é a leitura que mistura
   *  duas cotas diferentes, e por isso o aviso fica sempre à vista. */
  const [casa, setCasa] = useState<"todas" | "federal" | "senador">("todas");

  const municipios = base.municipios;

  const legAtual = legsComDado.find((l) => l.id === leg);
  const blocoMandato = useMemo(
    () => (porMandato && legAtual
      ? fundeMandato(e.anos, legAtual, municipios.length) : null),
    [porMandato, legAtual, e.anos, municipios.length]);

  const bloco: BlocoEmenda | undefined =
    porMandato ? (blocoMandato ?? undefined) : e.anos[String(ano)];

  // O rótulo do período, para os textos não dizerem "em 2025" quando a tela
  // mostra um mandato inteiro.
  const periodo = porMandato ? (legAtual?.rotulo ?? "") : String(ano);
  // A legislatura em curso ainda paga: em 2026 só 69,4% do empenhado virou
  // pago, contra 96,3% em 2023. É o único ano de fato imaturo da série.
  const emCurso = porMandato
    ? !!legAtual?.anos.includes(anoCorrente)
    : ano >= anoCorrente;

  /* O mapa mostra o total do município, não o de um autor: emenda se lê por
     território, e a pergunta "quanto chegou aqui" é a que interessa primeiro.
     `sem Pix` sai por subtração do próprio arquivo — assim os três números não
     têm como discordar entre si. */
  const valores = useMemo(() => {
    const t = bloco?.totalMun ?? [];
    const p = bloco?.totalPix ?? [];
    const bruto = municipios.map((_, i) =>
      (t[i] ?? 0) - (comPix ? 0 : (p[i] ?? 0)));
    if (medida === "total") return bruto;
    const div = medida === "hab" ? demo?.pop : demo?.area;
    // sem denominador o município fica FORA da escala, não em zero: zero diria
    // "não chegou dinheiro", e o que houve foi não sabermos por quanto dividir
    return bruto.map((v, i) => {
      const d = div?.[i];
      return d && d > 0 ? v / d : Number.NaN;
    });
  }, [bloco, municipios, medida, comPix, demo]);

  const cortes = useMemo(
    () => quantis(valores.filter((v) => Number.isFinite(v) && v > 0)),
    [valores]);

  const semDenominador = useMemo(
    () => (medida === "total" ? 0
      : valores.reduce((n, v) => n + (Number.isFinite(v) ? 0 : 1), 0)),
    [valores, medida]);

  const todasFichas = bloco?.fichas ?? [];
  // "ambas" entra no filtro de senador: quem teve mandato nas duas casas ao
  // longo da série recebeu cota de senador em parte dela, e escondê-lo do
  // recorte do Senado tiraria justamente os maiores.
  // O filtro de casa só governa a esfera federal: no estadual `casa` não existe
  // nas fichas, e filtrar por ela esvaziaria a lista inteira.
  const fichas = esfera !== "federal" || casa === "todas" ? todasFichas
    : todasFichas.filter((f) => casa === "senador"
        ? f.casa === "senador" || f.casa === "ambas"
        : f.casa === "federal");
  const atual: FichaEmenda | undefined = fichas[autor] ?? fichas[0];
  const p = bloco?.pleito;

  const cob = e.cobertura;
  const pctComMunicipio = cob.pago > 0 ? (cob.pagoMun / cob.pago) * 100 : 0;

  const sufixo = medida === "hab" ? " por habitante"
    : medida === "area" ? " por km²" : "";

  return (
    <>
      <div className="controles">
        {esferasDisponiveis.length > 1 && (
          <div className="seg" role="group" aria-label="Esfera">
            {esferasDisponiveis.map((x) => (
              <button key={x} aria-pressed={x === esfera}
                      onClick={() => aoTrocarEsfera(x)}>
                {x === "federal" ? "Federal" : "Estadual"}
              </button>
            ))}
          </div>
        )}
        <div className="seg" role="group" aria-label="Agrupamento">
          <button aria-pressed={!porMandato}
                  onClick={() => { setPorMandato(false); setAutor(0); }}>
            Por ano
          </button>
          <button aria-pressed={porMandato}
                  onClick={() => { setPorMandato(true); setAutor(0); }}>
            Por mandato
          </button>
        </div>
        {porMandato ? (
          <div className="seg" role="group" aria-label="Legislatura">
            {legsComDado.map((l) => (
              <button key={l.id} aria-pressed={l.id === leg}
                      onClick={() => { setLeg(l.id); setAutor(0); }}>
                {l.rotulo}
              </button>
            ))}
          </div>
        ) : (
          <div className="seg" role="group" aria-label="Ano da emenda">
            {anos.map((a) => (
              <button key={a} aria-pressed={a === ano}
                      onClick={() => { setAno(a); setAutor(0); }}>
                {a}
              </button>
            ))}
          </div>
        )}
        <div className="seg" role="group" aria-label="Medida">
          {(["total", "hab", "area"] as Medida[]).map((m) => (
            <button key={m} aria-pressed={m === medida}
                    onClick={() => setMedida(m)}>
              {ROTULO_MEDIDA[m]}
            </button>
          ))}
        </div>
        <div className="seg" role="group" aria-label="Transferência especial">
          <button aria-pressed={comPix} onClick={() => setComPix(true)}>
            Com Pix
          </button>
          <button aria-pressed={!comPix} onClick={() => setComPix(false)}>
            Sem Pix
          </button>
        </div>
      </div>

      {!bloco ? (
        <p className="cap">Sem emenda registrada em {periodo}.</p>
      ) : (
        <>
          {emCurso && (
            <div className="nota">
              <strong>{periodo} ainda está em execução.</strong> Em {anoCorrente}
              , 69,4% do empenhado virou pago, contra 96,3% em 2023 — o valor
              aqui é o que já saiu, não o que o período terá.
              {porMandato
                ? " Comparar este mandato com os anteriores subestima o atual."
                : " Comparar com um ano completo mediria o calendário, não a"
                  + " emenda."}
            </div>
          )}

          <Cartoes itens={[
            { rotulo: "Pago em " + periodo, valor: reais(p?.pago ?? 0),
              sub: `${numero(p?.nEmendas ?? 0)} emendas` },
            { rotulo: "Autores", valor: numero(p?.nAutores ?? 0),
              sub: porMandato ? "distintos no mandato" : "com emenda paga no ano" },
            { rotulo: "Municípios alcançados", valor: numero(p?.nMun ?? 0),
              sub: `de ${numero(municipios.length)}` },
            { rotulo: "Transferência especial", valor: reais(p?.pix ?? 0),
              sub: `${percentual(p?.pago ? (p.pix / p.pago) * 100 : 0, 1)} do pago` },
          ]} />

          <div className="cartaz">
            <h2>Onde o dinheiro chegou{sufixo}</h2>
            <p className="cap">
              {ROTULO_MEDIDA[medida]} por município em {periodo},
              {comPix ? " incluindo" : " excluindo"} a transferência especial —
              a chamada emenda Pix, que vai direto ao caixa da prefeitura sem
              projeto vinculado.
            </p>
            <Mapa
              geo={base.geo}
              valores={valores}
              cortes={cortes}
              rotulo={ROTULO_MEDIDA[medida]}
              aoInspecionar={aoInspecionar}
              descrever={(i, v) => (
                <>
                  <strong>{municipios[i]?.n}</strong>
                  <br />
                  {Number.isFinite(v)
                    ? medida === "total"
                      ? reaisCheio(v)
                      : `${reaisCheio(v)}${sufixo}`
                    : "sem denominador no Censo"}
                </>
              )}
            />
            <Legenda cortes={cortes} semDado="Nenhuma emenda" />
            {semDenominador > 0 && (
              <p className="cap">
                {numero(semDenominador)}{" "}
                {semDenominador === 1 ? "município fica" : "municípios ficam"} fora
                da escala por não {semDenominador === 1 ? "ter" : "terem"}{" "}
                {medida === "hab" ? "população" : "área"} no Censo de 2022. Ficam
                fora, não em zero: zero diria que não chegou dinheiro, e o que
                houve foi não sabermos por quanto dividir.
              </p>
            )}
          </div>

          <div className="nota">
            <strong>O que fica de fora, e é muito.</strong> O Emendômetro cobre
            <strong> emenda individual</strong> — a de um parlamentar. Emenda de
            bancada, de comissão e de relator não entra: são
            <span className="num"> R$ 119,5 bi</span> de
            <span className="num"> R$ 259,5 bi</span> pagos no país, ou 46% de
            todo o dinheiro de emenda. Delas,{" "}
            <span className="num">R$ 4,7 bi</span> até têm município identificado e ainda assim ficam fora — é escolha
            de escopo, não limitação da fonte, e reabri-la é decisão de produto.
          </div>

          <div className="nota">
            <strong>O denominador honesto.</strong> Do total pago nesta esfera,{" "}
            <span className="num">{percentual(pctComMunicipio, 1)}</span> tem
            município identificado no arquivo de origem —{" "}
            {reais(cob.pagoMun)} de {reais(cob.pago)}. O mapa fala desse pedaço.
            O resto sai com localidade <span className="num">MÚLTIPLO</span> ou
            em branco, e não há como distribuí-lo por território sem inventar.
          </div>

          {/* So na esfera federal: o agregado nacional e de emenda federal, e
              po-lo sob a estadual compararia coisas de origens diferentes. */}
          {br && esfera === "federal" && (
            <PaisEntreMandatos br={br} uf={uf} anoCorrente={anoCorrente} />
          )}

          {fichas.length > 0 && atual && (
            <div className="duas">
              <div className="cartaz">
                <h2>Quem mandou</h2>
                <p className="cap">
                  Autores por valor pago em {periodo}. São só emendas
                  <strong> individuais</strong>: bancada, comissão e relator não
                  entram, e o cartaz abaixo diz quanto isso deixa de fora.
                </p>

                {/* Só na esfera federal. A emenda estadual é de uma casa só —
                    a assembleia —, e oferecer "Câmara ou Senado" ali seria
                    oferecer uma divisão que não existe naquele dado. */}
                {esfera === "federal" && (
                <div className="seg-rot" style={{ margin: "2px 0 10px" }}>
                  <span className="et">Casa do autor</span>
                  <div className="seg" role="group" aria-label="Casa do autor">
                    {([["todas", "as duas"], ["federal", "Câmara"],
                       ["senador", "Senado"]] as const).map(([id, r]) => (
                      <button key={id} aria-pressed={casa === id}
                              onClick={() => { setCasa(id); setAutor(0); }}>
                        {r}
                      </button>
                    ))}
                  </div>
                </div>
                )}

                {esfera === "federal" && casa === "todas" && (
                  <div className="nota" style={{ marginBottom: 12 }}>
                    <strong>Senador e deputado não têm a mesma cota, e esta lista
                    mistura as duas.</strong> A emenda individual é das duas casas
                    — são <span className="num">594</span> autores por exercício,
                    que é exatamente 513 deputados mais 81 senadores — e a mediana
                    paga por senador na série é de{" "}
                    <span className="num">R$ 148,2 mi</span> contra{" "}
                    <span className="num">R$ 79,6 mi</span> por deputado:{" "}
                    <strong>1,86 vez</strong>. Ordenar por valor sem separar as
                    casas põe o Senado no topo por regra de orçamento, e não por
                    comportamento político. Os botões acima separam.
                  </div>
                )}
                <div className="rolagem">
                  <table>
                    <thead>
                      <tr>
                        <th>Autor</th>
                        <th className="n">Pago</th>
                        <th className="n">Municípios</th>
                        <th className="n">No maior</th>
                        <th className="n">Sem destino</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fichas.slice(0, 20).map((f, i) => (
                        <tr key={f.n + i}
                            aria-selected={i === autor}
                            onClick={() => setAutor(i)}
                            style={{ cursor: "pointer" }}>
                          <td>{f.n}{f.amb ? " (coletiva)" : ""}
                            {/* A etiqueta marca o que FOGE do padrão. Na esfera
                                federal o padrão é a Câmara, e Senado ou as duas
                                casas ganham marca. Na estadual a assembleia é
                                casa única e `casa` nem existe — ali a única
                                marca possível é a ausência de par com eleito.
                                Enquanto o teste era `!f.casa`, toda ficha
                                estadual saía "sem par", inclusive as 237 de 248
                                que casam. */}
                            {f.pt && <span className="pt-tag">{f.pt}</span>}
                            {f.gr && f.gr !== "individual" &&
                              <span className="casa-tag">
                                {NOME_GRUPO[f.gr as GrupoEmenda] ?? f.gr}
                              </span>}
                            {f.casa === "senador" && <span className="casa-tag">Senado</span>}
                            {f.casa === "ambas" && <span className="casa-tag">as duas</span>}
                            {!f.el && f.gr === "individual" &&
                              <span className="casa-tag vazio">sem par</span>}
                          </td>
                          <td className="n">{reais(f.t)}</td>
                          <td className="n">{numero(f.nm)}</td>
                          <td className="n">
                            {f.t1 == null ? "—" : percentual(f.t1, 1)}
                          </td>
                          <td className="n">
                            {f.sm ? reais(f.sm) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="cartaz">
                <h2>{atual.n}{atual.pt ? ` (${atual.pt})` : ""}</h2>
                <p className="cap">
                  {atual.amb
                    ? "Autoria ambígua: há mais de um eleito com este nome de urna, "
                      + "em UFs diferentes, e o arquivo não distingue."
                    : atual.gr && atual.gr !== "individual"
                    ? `Emenda de ${(NOME_GRUPO[atual.gr as GrupoEmenda] ?? atual.gr)
                        .toLowerCase()}: o autor é uma instituição, não uma `
                      + "pessoa, e por isso não tem partido."
                    : atual.el
                    ? `Eleito por ${atual.ufEl}${
                        atual.casa === "senador" ? ", para o Senado"
                        : atual.casa === "ambas" ? ", para as duas casas"
                        : atual.casa === "federal" ? ", para a Câmara" : ""}${
                        atual.ptn && atual.ptn !== atual.pt
                          ? `, pelo ${atual.pt} (hoje ${atual.ptn})` 
                          : atual.pt ? `, pelo ${atual.pt}` : ""}.`
                    : "O nome deste autor não casou com nenhum eleito de 1998 a "
                      + "2022 — pode ser suplente que assumiu, mandato anterior a "
                      + "1998, ou homônimo que o critério recusou desempatar."}
                  {atual.fn ? ` Função dominante: ${atual.fn}.` : ""}
                </p>
                <Indices itens={[
                  { rotulo: "Pago", valor: reais(atual.t),
                    explicacao: `${numero(atual.ne)} emendas` },
                  { rotulo: "Municípios", valor: numero(atual.nm),
                    explicacao: porMandato ? "alcançados no mandato"
                                           : "alcançados no ano" },
                  { rotulo: "Sem destino declarado",
                    valor: atual.sm ? reais(atual.sm) : "—",
                    explicacao: atual.sm
                      ? `${percentual((atual.sm / atual.t) * 100, 0)} do que ele pagou`
                      : "todo o valor tem município no arquivo" },
                  { rotulo: "No maior",
                    valor: atual.t1 == null ? "—" : percentual(atual.t1, 1),
                    explicacao: "fatia do município que mais recebeu" },
                  { rotulo: "Municípios efetivos",
                    valor: atual.ef == null ? "—" : decimal(atual.ef, 1),
                    explicacao: "inverso da concentração" },
                ]} />
                {atual.pix > 0 && (
                  <p className="cap">
                    <strong>{reais(atual.pix)}</strong> saíram como transferência
                    especial — {percentual((atual.pix / atual.t) * 100, 1)} do que
                    este autor pagou {porMandato ? "no mandato" : "no ano"}.
                  </p>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
}
