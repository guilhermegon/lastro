import type {
  AlegoAdmin, AlegoVerbas, Assembleias, AlmgVerbas, CldfAdmin, CldfVerbas,
} from "../tipos";
import { decimal, numero, percentual } from "../lib/formato";
import { Tabela } from "../componentes/Tabela";
import { Indices } from "../componentes/Indices";
import { Linha } from "../componentes/Linha";
import { Legenda as _Legenda } from "../componentes/Legenda";

void _Legenda;

function reais(v: number): string {
  const a = Math.abs(v);
  if (a >= 1e9) return `R$ ${decimal(v / 1e9, 2)} bi`;
  if (a >= 1e6) return `R$ ${decimal(v / 1e6, 2)} mi`;
  if (a >= 1e3) return `R$ ${decimal(v / 1e3, 0)} mil`;
  return `R$ ${decimal(v, 2)}`;
}

interface Props {
  assembleias: Assembleias | null;
  alegoVerbas: AlegoVerbas | null;
  alegoAdmin: AlegoAdmin | null;
  cldfVerbas: CldfVerbas | null;
  cldfAdmin: CldfAdmin | null;
  almgVerbas: AlmgVerbas | null;
}

/**
 * O que as assembleias publicam sobre si mesmas.
 *
 * Esta aba é nacional: não muda com o estado escolhido. Os três pilotos são
 * Goiás, DF e Minas porque são as casas cujo dado dá para consumir — e a
 * comparação entre elas é o achado, porque cada uma publica um pedaço diferente
 * do mesmo objeto.
 */
export function VistaApi({
  assembleias, alegoVerbas, alegoAdmin, cldfVerbas, cldfAdmin, almgVerbas,
}: Props) {
  const casas = assembleias
    ? Object.entries(assembleias).sort((a, b) => a[0].localeCompare(b[0]))
    : [];
  const comPortal = casas.filter(([, v]) => v.url).length;
  const comApi = casas.filter(([, v]) => v.conf).length;

  return (
    <>
      <div className="cartaz">
        <h2>Quais assembleias publicam dado aberto</h2>
        <p className="cap">
          Fomos às 27 casas legislativas estaduais procurar dado aberto sobre
          elas mesmas. O levantamento roda por script e pode ser repetido.
        </p>
        <Indices itens={[
          { rotulo: "Casas com portal", valor: `${comPortal} de 27`,
            explicacao: "responderam com página de dados abertos" },
          { rotulo: "API confirmada", valor: String(comApi),
            explicacao: "devolvem JSON consumível" },
          { rotulo: "Publicam emenda", valor: "1",
            explicacao: "e sem autor nem município" },
        ]} />
      </div>

      {casas.length > 0 && (
        <div className="cartaz">
          <h2>Casa por casa</h2>
          <Tabela
            cab={["UF", "Casa", "Conjuntos", "API", "Observação"]}
            linhas={casas.map(([uf, v]) => [
              uf, v.sigla, v.n ? numero(v.n) : "—",
              v.conf ? "sim" : v.url ? "não" : "—",
              v.obs || (v.url ? "" : "sem portal encontrado"),
            ])} />
        </div>
      )}

      <div className="cartaz">
        <h2>O que elas publicam — e o que quase nenhuma publica</h2>
        <p className="cap">
          Abrindo as que respondem, o padrão é nítido e vale mais que a contagem.
        </p>
        <ul className="lista-fatos">
          <li><strong>A assembleia publica a si mesma.</strong> Os assuntos que
            aparecem são folha de pagamento, diárias, verbas indenizatórias,
            licitações, contratos, convênios e a execução do próprio orçamento
            da Casa. É a assembleia como empregadora e compradora.</li>
          <li><strong>Uma publica emenda — e mesmo assim não dá para usar.</strong>{" "}
            A Câmara Legislativa do DF tem um conjunto chamado, literalmente,{" "}
            <span className="num">emendas-parlamentares</span>: cinco CSV, de
            2021 a 2025. Abrindo, são dezoito colunas de execução orçamentária
            (<span className="num">VL_EMENDA</span>,{" "}
            <span className="num">VL_EMPENHADO</span>,{" "}
            <span className="num">NOME_UO</span>) e{" "}
            <strong>nenhuma coluna de autor, nenhuma de município</strong>. É
            emenda como linha de orçamento, não como ato de um parlamentar sobre
            um território.</li>
          <li><strong>Nas demais, o endereço nem existe.</strong> Em Goiás, os
            três endereços plausíveis devolvem 404 — o servidor responde dizendo
            que não há, que é diferente de não responder. Em Minas, os 108
            endpoints da API vão de proposição a contrato e não incluem
            emenda.</li>
          <li><strong>E isso é coerência institucional, não omissão.</strong> A
            emenda é indicação de deputado sobre o orçamento do{" "}
            <em>Executivo</em>, e quem a executa são as secretarias. O dado nasce
            do outro lado — por isso o Emendômetro estadual sai de portais do
            governo do estado, não das assembleias.</li>
        </ul>
      </div>

      {/* ---------------- Goiás ---------------- */}
      {alegoAdmin?.orcamento?.length ? (
        <SecaoOrcamentoGO a={alegoAdmin} />
      ) : null}

      {alegoVerbas ? <SecaoVerbaGO v={alegoVerbas} /> : null}

      {/* ---------------- DF ---------------- */}
      {cldfAdmin?.folha ? <SecaoFolhaDF a={cldfAdmin} /> : null}
      {cldfVerbas ? <SecaoVerbaDF v={cldfVerbas} /> : null}

      {/* ---------------- Minas ---------------- */}
      {almgVerbas ? <SecaoMG v={almgVerbas} /> : null}

      {alegoVerbas && cldfVerbas && almgVerbas ? (
        <div className="cartaz">
          <h2>As três casas, lado a lado</h2>
          <p className="cap">
            A mesma verba indenizatória, publicada em três grãos diferentes. A
            comparação é o achado: cada casa responde o que a outra não responde.
          </p>
          <Tabela
            cab={["", "Goiás (ALEGO)", "DF (CLDF)", "Minas (ALMG)"]}
            linhas={[
              ["grão", "mês, por deputado", "comprovante",
               "deputado × mês × categoria"],
              ["glosa", "sim", "não: só o pago", "sim"],
              ["categoria", "não", "sim, 68,3% do valor sem", "sim"],
              ["fornecedor", "não", "sim", "sim, com CNPJ"],
              ["autor da nota", "sim", "não", "sim"],
              ["período", "8 anos", "12 anos", "2019 em diante, por mandato"],
            ]} />
          <div className="nota" style={{ marginTop: 12 }}>
            <strong>Os totais não se somam.</strong> Os períodos não coincidem, o
            grão não coincide, e Goiás publica o pedido enquanto o DF publica só
            o pago. Um total "das três casas" sairia redondo e não significaria
            nada.
          </div>
        </div>
      ) : null}
    </>
  );
}

/* ---------------- seções por casa ---------------- */

function SecaoOrcamentoGO({ a }: { a: AlegoAdmin }) {
  const orc = a.orcamento.filter((x) => x.autorizado > 0);
  if (!orc.length) return null;
  const p = orc[0]!, u = orc[orc.length - 1]!;
  const cresc = (u.autorizado / p.autorizado - 1) * 100;
  const di = a.diarias;
  const te = a.terceirizados;
  return (
    <>
      <div className="cartaz">
        <h2>Quanto custa a Assembleia de Goiás</h2>
        <p className="cap">
          O orçamento autorizado da ALEGO, ano a ano. Só o da Casa: o arquivo
          traz também o FEMAL, um fundo à parte, e somar os dois responderia
          outra pergunta.
        </p>
        <Linha
          eixoX={orc.map((x) => x.ano)}
          casas={0}
          series={[
            { rotulo: "Autorizado", cor: "--accent",
              pontos: orc.map((x) => x.autorizado / 1e6) },
            { rotulo: "Pessoal", cor: "--s2",
              pontos: orc.map((x) => x.pessoal / 1e6) },
          ]} />
        <Indices itens={[
          { rotulo: String(p.ano), valor: reais(p.autorizado), explicacao: "autorizado" },
          { rotulo: String(u.ano), valor: reais(u.autorizado), explicacao: "autorizado" },
          { rotulo: "Crescimento",
            valor: `${cresc >= 0 ? "+" : ""}${decimal(cresc, 0)}%`,
            explicacao: `em ${u.ano - p.ano} anos, nominal` },
          { rotulo: "Fatia de pessoal",
            valor: percentual((u.pessoal / u.autorizado) * 100, 0),
            explicacao: `era ${percentual((p.pessoal / p.autorizado) * 100, 0)} em ${p.ano}` },
        ]} />
        <p className="cap" style={{ marginTop: 10 }}>
          <strong>O orçamento cresceu {decimal(cresc, 0)}%, mas a folha não
          acompanhou.</strong> A fatia de pessoal caiu, e o que cresceu foi
          custeio e investimento. Está em reais correntes, sem deflacionar.
        </p>
      </div>

      {di ? (
        <div className="cartaz">
          <h2>Diárias, e por que não somamos o total</h2>
          <p className="cap">
            São {numero(di.n)} registros de diária, {numero(di.nParlamentar)} de
            parlamentar e {numero(di.nServidor)} de servidor. O valor típico é{" "}
            <span className="num">{reais(di.unitMediana)}</span> por diária.
          </p>
          <div className="nota">
            <strong>O campo de valor não pode ser somado, e isso é achado sobre
            a fonte.</strong> A maior "diária" do conjunto é de{" "}
            <span className="num">R$ 2.676.075,25</span> para 1,5 diárias de um
            assessor. Há {numero(di.suspeitas)} registros com valor por diária
            acima de R$ 5 mil, e eles concentram {reais(di.valorSuspeitas)} de{" "}
            {reais(di.valorTotalBruto)} —{" "}
            <span className="num">{percentual(di.pctSuspeitas, 0)} da soma vem
            de menos de 1% dos registros</span>, e esses registros não são
            diárias. Por isso publicamos o valor típico e a contagem, nunca o
            somatório.
          </div>
        </div>
      ) : null}

      {te?.pessoas ? (
        <div className="cartaz">
          <h2>O quadro terceirizado de Goiás</h2>
          <p className="cap">
            {numero(te.pessoas)} pessoas distintas em {numero(te.empresas)}{" "}
            empresas. O arquivo vem por pessoa-mês: contar linhas contaria{" "}
            {numero(te.registros)} e mediria permanência, não tamanho de quadro.
          </p>
          <Tabela
            cab={["Empresa", "Pessoas", "% do quadro"]}
            linhas={(te.porEmpresa ?? []).map((e) => [
              e.n, numero(e.q),
              percentual(te.pessoas ? (e.q / te.pessoas) * 100 : 0, 1),
            ])} />
        </div>
      ) : null}
    </>
  );
}

function SecaoVerbaGO({ v }: { v: AlegoVerbas }) {
  const t = v.total;
  return (
    <div className="cartaz">
      <h2>Piloto: a API da ALEGO, consumida</h2>
      <p className="cap">
        Verba indenizatória de gabinete, {v.periodo[0]} a {v.periodo[1]}, mês a
        mês por deputado. Goiás é a única das três que publica o que foi{" "}
        <em>apresentado</em> ao lado do que foi <em>indenizado</em> — e é essa
        diferença que revela a glosa.
      </p>
      <Indices itens={[
        { rotulo: "Apresentado", valor: reais(t.apresentado),
          explicacao: "o que os gabinetes pediram" },
        { rotulo: "Indenizado", valor: reais(t.indenizado),
          explicacao: "o que a Casa pagou" },
        { rotulo: "Glosado",
          valor: percentual(t.apresentado ? (t.glosa / t.apresentado) * 100 : 0, 2),
          explicacao: `${reais(t.glosa)} recusados` },
        { rotulo: "Deputados", valor: `${numero(t.nCasados)} de ${numero(t.nDeputados)}`,
          explicacao: "casam com eleito na base do TSE" },
      ]} />
      <Linha
        eixoX={v.serie.map((x) => x.ano)}
        casas={1}
        series={[{ rotulo: "Indenizado", cor: "--accent",
                   pontos: v.serie.map((x) => x.indenizado / 1e6) }]} />
      <p className="cap" style={{ marginTop: 10 }}>
        Em milhões de reais correntes. O número de deputados com verba lançada
        muda de ano para ano, o que move o total sem que ninguém tenha gasto
        diferente — por isso a leitura por deputado é mediana mensal, não total.
      </p>
    </div>
  );
}

function SecaoFolhaDF({ a }: { a: CldfAdmin }) {
  const f = a.folha!;
  const tipo = (f.porTipo ?? []).filter((x) => x.n && x.n !== "NAN");
  const conc = tipo.find((x) => x.n === "CONCURSADO");
  const comi = tipo.find((x) => x.n === "COMISSIONADO");
  const inat = tipo.find((x) => x.n === "INATIVO");
  const se = a.folhaSerie ?? [];
  const p = se[0], u = se[se.length - 1];
  return (
    <>
      <div className="cartaz">
        <h2>Quanto custa a Câmara Legislativa do DF</h2>
        <p className="cap">
          O DF não tem API, mas publica o que nenhuma outra publica: a{" "}
          <strong>folha nominal mês a mês</strong>, pessoa por pessoa, com cargo,
          lotação e remuneração — 107 arquivos, de setembro de 2017 a{" "}
          {f.mes.replace("-", "/")}.
        </p>
        <Indices itens={[
          { rotulo: "Pessoas na folha", valor: numero(f.pessoas),
            explicacao: f.mes.replace("-", "/") },
          { rotulo: "Folha do mês", valor: reais(f.bruto),
            explicacao: "bruto, sem descontos" },
          { rotulo: "Deputados", valor: numero(f.deputados),
            explicacao: `${percentual((f.brutoDeputados / f.bruto) * 100, 1)} da folha` },
          { rotulo: "Em gabinete", valor: numero(f.emGabinete),
            explicacao: `${percentual(f.pctGabinete, 1)} da folha` },
        ]} />
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>São {numero(f.linhas)} linhas de pagamento para{" "}
          {numero(f.pessoas)} pessoas.</strong> Uma pessoa aparece em várias
          folhas no mesmo mês. Contar linhas contaria pagamento, não gente — e
          foi assim que a primeira versão deste levantamento relatou 48 deputados
          distritais num Distrito Federal que tem {numero(f.deputados)}.
        </div>
      </div>

      {conc && comi && inat ? (
        <div className="cartaz">
          <h2>Mais comissionado que concursado</h2>
          <Tabela
            cab={["Vínculo", "Pessoas", "Folha do mês", "% da folha", "Por pessoa"]}
            linhas={tipo.map((x) => [
              x.n, numero(x.q), reais(x.v),
              percentual(f.bruto ? (x.v / f.bruto) * 100 : 0, 1),
              reais(x.q ? x.v / x.q : 0),
            ])} />
          <ul className="lista-fatos" style={{ marginTop: 14 }}>
            <li><strong>Há {numero(comi.q)} comissionados para{" "}
              {numero(conc.q)} concursados.</strong> Por cabeça, o cargo de livre
              nomeação é maioria na Casa. Por dinheiro não é: o concursado
              individual custa cerca de{" "}
              {decimal((conc.v / conc.q) / (comi.v / comi.q), 1)}× o
              comissionado individual.</li>
            <li><strong>{numero(inat.q)} inativos custam mais que{" "}
              {numero(comi.q)} comissionados.</strong> {reais(inat.v)} contra{" "}
              {reais(comi.v)} no mesmo mês.</li>
            <li><strong>Os {numero(f.deputados)} deputados são{" "}
              {percentual((f.brutoDeputados / f.bruto) * 100, 1)} da folha.</strong>{" "}
              O custo do Legislativo quase não é o parlamentar: é a estrutura em
              volta dele.</li>
          </ul>
        </div>
      ) : null}

      {se.length > 1 && p && u ? (
        <div className="cartaz">
          <h2>A folha cresce mais rápido que o quadro</h2>
          <p className="cap">
            Julho de cada ano, sempre o mesmo mês — comparar com dezembro
            compararia com o décimo terceiro. Indexado a {p.mes.slice(0, 4)} = 100,
            que é como pôr duas medidas de escalas diferentes num eixo só.
          </p>
          <Linha
            eixoX={se.map((x) => x.mes.slice(0, 4))}
            casas={0}
            series={[
              { rotulo: "Folha", cor: "--accent",
                pontos: se.map((x) => (x.bruto / p.bruto) * 100) },
              { rotulo: "Pessoas", cor: "--s2",
                pontos: se.map((x) => (x.pessoas / p.pessoas) * 100) },
            ]} />
          <Indices itens={[
            { rotulo: "Pessoas",
              valor: `${numero(p.pessoas)} → ${numero(u.pessoas)}`,
              explicacao: `+${decimal((u.pessoas / p.pessoas - 1) * 100, 0)}% em ${se.length - 1} anos` },
            { rotulo: "Folha", valor: `${reais(p.bruto)} → ${reais(u.bruto)}`,
              explicacao: `+${decimal((u.bruto / p.bruto - 1) * 100, 0)}% nominal` },
          ]} />
          <div className="nota" style={{ marginTop: 12 }}>
            <strong>Os dois números não são igualmente sólidos.</strong> O
            crescimento no número de pessoas é contagem: não depende de inflação.
            O da folha está em reais correntes, <em>sem deflacionar</em> — boa
            parte dele é só a moeda valendo menos. O descolamento entre as duas
            séries, esse, sobrevive à correção.
          </div>
          <div className="nota" style={{ marginTop: 12 }}>
            <strong>O bruto é piso, não total.</strong> Só a folha principal
            detalha os créditos; as secundárias trazem as colunas de crédito
            zeradas e apenas o líquido — {reais(f.semDetalhe)} pagos em{" "}
            {f.mes.replace("-", "/")} cujo valor bruto o arquivo não informa.
          </div>
        </div>
      ) : null}
    </>
  );
}

function SecaoVerbaDF({ v }: { v: CldfVerbas }) {
  const t = v.total;
  const classificado = t.valor - t.semCategoria;
  const cob = v.cobertura ?? [];
  const faixa = cob.length
    ? [Math.min(...cob.map((c) => c.deputados)), Math.max(...cob.map((c) => c.deputados))]
    : [0, 0];
  return (
    <>
      <div className="cartaz">
        <h2>Segundo piloto: o DF, e o que a verba compra</h2>
        <p className="cap">
          A CLDF publica a <strong>mesma</strong> verba indenizatória, mas em
          outro grão: <strong>nota a nota</strong>, com fornecedor, CNPJ, data e
          categoria. São {numero(t.notas)} comprovantes de {v.periodo[0]} a{" "}
          {v.periodo[1]}, {reais(t.valor)}.
        </p>
        <Tabela
          cab={["Categoria", "Valor", "% do classificado", "Notas"]}
          linhas={(v.categorias ?? []).slice(0, 10).map((c) => [
            c.n, reais(c.v),
            percentual(classificado > 0 ? (c.v / classificado) * 100 : 0, 1),
            numero(c.q),
          ])} />
        <p className="cap" style={{ marginTop: 10 }}>
          A mesma categoria aparece com mais de uma grafia no próprio arquivo —
          "Locação de Veículos" e "Locação de Veículo" são linhas separadas. Não
          fundimos: juntar por semelhança de texto arriscaria fundir categorias
          distintas, e o leitor consegue somar.
        </p>
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>{percentual(t.pctSemCategoria, 1)} do valor não tem
          categoria.</strong> A tabela acima fala de {reais(classificado)} — o
          que sobra dos {reais(t.valor)} totais. Sem esse denominador ao lado, as
          fatias insinuariam uma cobertura que não existe.
        </div>
      </div>

      <div className="cartaz">
        <h2>O que NÃO dá para comparar entre as casas</h2>
        <p className="cap">
          A tentação é dividir e comparar gasto médio por deputado. O cálculo
          roda e dá um número — e o número seria falso.
        </p>
        <ul className="lista-fatos">
          <li><strong>O DF tem 24 distritais e o arquivo traz de {faixa[0]} a{" "}
            {faixa[1]} por ano.</strong> Isso não é rotatividade — é publicação
            parcial, e uma mediana por deputado sairia de um subconjunto que muda
            de tamanho todo ano.</li>
          <li><strong>Glosa não existe no DF.</strong> O arquivo traz o valor
            pago, não o pedido. A diferença que em Goiás mede decisão
            administrativa aqui não tem como ser calculada.</li>
          <li><strong>Categoria não existe em Goiás.</strong> A série da ALEGO é
            total mensal; não há como saber no que foi gasto.</li>
          <li><strong>Então a comparação fica de fora.</strong> Publicar "o
            deputado do DF gasta um terço do goiano" seria descrever a política
            de publicação de cada casa achando que se está descrevendo
            comportamento.</li>
        </ul>
      </div>
    </>
  );
}

function SecaoMG({ v }: { v: AlmgVerbas }) {
  const t = v.total;
  const se = (v.serie ?? []).filter((x) => x.meses === 12);
  const s0 = se[0], s1 = se[se.length - 1];
  const cTotal = s0 && s1 ? (s1.pago / s0.pago - 1) * 100 : null;
  const cDep = s0 && s1 ? (s1.porDeputado / s0.porDeputado - 1) * 100 : null;
  const fo = v.fornecedores;
  const dp = v.deputados;
  return (
    <>
      <div className="cartaz">
        <h2>Terceiro piloto: Minas, e o grão que junta tudo</h2>
        <p className="cap">
          A ALMG é a única das três que amarra <strong>as três dimensões ao
          mesmo tempo</strong>: quanto foi pedido e quanto foi pago (a glosa, que
          só Goiás dava), em que categoria (que só o DF dava) e para qual
          fornecedor, com CNPJ — tudo ligado ao deputado, o que o DF não liga.
        </p>
        <Indices itens={[
          { rotulo: "Notas", valor: numero(t.notas),
            explicacao: `${v.janela[0].replace("-", "/")} a ${v.janela[1].replace("-", "/")}` },
          { rotulo: "Deputados", valor: numero(t.deputados),
            explicacao: `${numero(t.mesesDeputado)} meses-deputado` },
          { rotulo: "Pago", valor: reais(t.pago),
            explicacao: `de ${reais(t.pedido)} pedidos` },
          { rotulo: "Glosado", valor: percentual(t.pctGlosa, 2),
            explicacao: `${reais(t.glosa)} recusados` },
        ]} />
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>A janela é por mandato, não por data de corte.</strong> O
          arquivo começa em {v.janela[0].replace("-", "/")} — início da
          legislatura 2019–2022 — e a série de cada deputado acompanha o tempo
          dele de mandato. A mediana é de <span className="num">88 meses</span>{" "}
          por deputado. Somar total por deputado mediria tempo de mandato; por
          isso o que se publica por deputado é mediana mensal.
        </div>
      </div>

      {se.length > 1 && s0 && s1 && cTotal != null && cDep != null ? (
        <div className="cartaz">
          <h2>A série que engana, e a mesma série sem enganar</h2>
          <div className="nota">
            <strong>O total por ano não mede gasto: mede quantos dos deputados
            de hoje já estavam lá.</strong> A varredura consulta os{" "}
            {numero(t.deputados)} deputados <em>em exercício</em>, e só{" "}
            {s0.deputados} deles já eram deputados em {s0.ano}. Quando a
            legislatura virou, a cobertura saltou — e o total saltou junto, sem
            que ninguém tivesse gasto diferente.
          </div>
          <Indices itens={[
            { rotulo: "Se olhássemos o total",
              valor: `${cTotal >= 0 ? "+" : ""}${decimal(cTotal, 0)}%`,
              explicacao: "número falso: é cobertura" },
            { rotulo: "Por deputado",
              valor: `${cDep >= 0 ? "+" : ""}${decimal(cDep, 0)}%`,
              explicacao: `de ${s0.ano} a ${s1.ano}, nominal` },
            { rotulo: "A diferença", valor: `${decimal(cTotal - cDep, 0)} pontos`,
              explicacao: "puro artefato" },
          ]} />
          <Linha
            eixoX={se.map((x) => x.ano)}
            casas={0}
            series={[{ rotulo: "Por deputado", cor: "--accent",
                       pontos: se.map((x) => x.porDeputado / 1e3) }]} />
          <Tabela
            cab={["Ano", "Deputados com verba", "Total", "Por deputado"]}
            linhas={(v.serie ?? []).map((x) => [
              `${x.ano}${x.meses < 12 ? " *" : ""}`,
              numero(x.deputados), reais(x.pago), reais(x.porDeputado),
            ])}
            rodape={["* ano incompleto: fora do gráfico e das comparações", "", "", ""]} />
          <p className="cap" style={{ marginTop: 10 }}>
            Mesmo o valor por deputado tem ressalva em {s0.ano}–2022: aqueles{" "}
            {s0.deputados} são os que <strong>continuam</strong> em exercício
            hoje, não os cerca de 77 que havia então. Quem sobrevive a três
            mandatos costuma ter estrutura maior, o que faz de{" "}
            {decimal(cDep, 0)}% um piso, não um teto.
          </p>
        </div>
      ) : null}

      <div className="cartaz">
        <h2>No que a verba mineira é gasta</h2>
        <Tabela
          cab={["Categoria", "Valor", "% do pago", "Notas"]}
          linhas={(v.categorias ?? []).map((c) => [
            c.n, reais(c.v),
            percentual(t.pago ? (c.v / t.pago) * 100 : 0, 1), numero(c.q),
          ])} />
      </div>

      {fo ? (
        <div className="cartaz">
          <h2>A pergunta que só Minas responde</h2>
          <p className="cap">
            Quem vende para quantos gabinetes. O DF não responde por não ter
            autor na nota; Goiás não responde por não ter fornecedor.
          </p>
          <Indices itens={[
            { rotulo: "CNPJ distintos", valor: numero(fo.distintos),
              explicacao: "no período" },
            { rotulo: "Atendem mais de um", valor: numero(fo.compartilhados),
              explicacao: `${percentual((fo.compartilhados / fo.distintos) * 100, 1)} dos fornecedores` },
          ]} />
          <Tabela
            cab={["Fornecedor", "Deputados", "Valor"]}
            linhas={(fo.top ?? []).map((x) => [x.n, numero(x.dep), reais(x.v)])} />
          <div className="nota" style={{ marginTop: 12 }}>
            <strong>Atender vários gabinetes não é irregularidade.</strong> O
            número mede concentração do mercado que vive da verba, e não diz mais
            que isso.
          </div>
        </div>
      ) : null}

      {dp ? (
        <div className="cartaz">
          <h2>Por deputado, e por que é mediana</h2>
          <Indices itens={[
            { rotulo: "Mediana mensal", valor: reais(dp.medianaMensal),
              explicacao: "das medianas de cada deputado" },
            { rotulo: "Menor", valor: reais(dp.minMensal), explicacao: "mediana mensal" },
            { rotulo: "Maior", valor: reais(dp.maxMensal), explicacao: "mediana mensal" },
          ]} />
          <Tabela
            cab={["Deputado", "Partido", "Mediana mensal", "Meses"]}
            linhas={(dp.top ?? []).map((x) => [x.n, x.p, reais(x.v), numero(x.m)])} />
          <div className="nota" style={{ marginTop: 12 }}>
            <strong>Não é total por deputado, e a diferença importa.</strong> A
            janela publicada não tem o mesmo tamanho para todos — quem assumiu
            depois tem menos meses. Somar produziria um ranking que mede tempo de
            mandato dentro da janela, não gasto. A coluna de meses fica à vista
            por isso.
          </div>
        </div>
      ) : null}
    </>
  );
}
