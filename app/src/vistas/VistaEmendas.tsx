import { useEffect, useMemo, useState } from "react";
import type {
  BaseUF, BlocoEmenda, Demografia, Emendas, Esfera, FichaEmenda,
} from "../tipos";
import { decimal, numero, percentual } from "../lib/formato";
import { quantis } from "../lib/escalas";
import { fundeMandato, LEGISLATURAS } from "../lib/mandato";
import { Mapa } from "../componentes/Mapa";
import { Legenda } from "../componentes/Legenda";
import { Indices } from "../componentes/Indices";
import { Cartoes } from "../componentes/Cartoes";
import { LogoEmendometro } from "../componentes/LogoProduto";
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
  aoInspecionar: (d: EstadoDica | null) => void;
}

export function VistaEmendas({
  e, esfera, esferasDisponiveis, aoTrocarEsfera, base, demo, aoInspecionar,
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

  const fichas = bloco?.fichas ?? [];
  const atual: FichaEmenda | undefined = fichas[autor] ?? fichas[0];
  const p = bloco?.pleito;

  const cob = e.cobertura;
  const pctComMunicipio = cob.pago > 0 ? (cob.pagoMun / cob.pago) * 100 : 0;

  const sufixo = medida === "hab" ? " por habitante"
    : medida === "area" ? " por km²" : "";

  return (
    <>
      {/* A marca do produto abre a aba. A Lastro fica no topo da página, como
          casa; aqui quem fala é o produto. */}
      <LogoEmendometro />

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

          {fichas.length > 0 && atual && (
            <div className="duas">
              <div className="cartaz">
                <h2>Quem mandou</h2>
                <p className="cap">
                  Autores por valor pago em {periodo}. São só emendas
                  <strong> individuais</strong>: bancada, comissão e relator não
                  entram, e o cartaz abaixo diz quanto isso deixa de fora.
                </p>
                <div className="rolagem">
                  <table>
                    <thead>
                      <tr>
                        <th>Autor</th>
                        <th className="n">Pago</th>
                        <th className="n">Municípios</th>
                        <th className="n">No maior</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fichas.slice(0, 20).map((f, i) => (
                        <tr key={f.n + i}
                            aria-selected={i === autor}
                            onClick={() => setAutor(i)}
                            style={{ cursor: "pointer" }}>
                          <td>{f.n}{f.amb ? " (coletiva)" : ""}</td>
                          <td className="n">{reais(f.t)}</td>
                          <td className="n">{numero(f.nm)}</td>
                          <td className="n">{percentual(f.t1, 1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="cartaz">
                <h2>{atual.n}</h2>
                <p className="cap">
                  {atual.amb
                    ? "Autoria ambígua: há mais de um eleito com este nome de urna, "
                      + "em UFs diferentes, e o arquivo não distingue."
                    : atual.el
                    ? `Eleito por ${atual.ufEl}.`
                    : "Autor sem mandato eleito nesta série."}
                  {atual.fn ? ` Função dominante: ${atual.fn}.` : ""}
                </p>
                <Indices itens={[
                  { rotulo: "Pago", valor: reais(atual.t),
                    explicacao: `${numero(atual.ne)} emendas` },
                  { rotulo: "Municípios", valor: numero(atual.nm),
                    explicacao: porMandato ? "alcançados no mandato"
                                           : "alcançados no ano" },
                  { rotulo: "No maior", valor: percentual(atual.t1, 1),
                    explicacao: "fatia do município que mais recebeu" },
                  { rotulo: "Municípios efetivos", valor: decimal(atual.ef, 1),
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
