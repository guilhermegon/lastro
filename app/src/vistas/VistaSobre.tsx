import { numero } from "../lib/formato";

/** Tabela simples de texto. As desta aba são fixas: descrevem método e fonte,
 *  não dado apurado, então viverem no código é onde elas devem estar. */
function Tabela({ cab, linhas }: { cab: string[]; linhas: string[][] }) {
  return (
    <div className="rolagem">
      <table>
        <thead>
          <tr>{cab.map((h, i) => (
            <th key={h} className={i === 0 ? undefined : "n"}>{h}</th>
          ))}</tr>
        </thead>
        <tbody>
          {linhas.map((l) => (
            <tr key={l[0]}>
              {l.map((v, i) => (
                <td key={i} className={i === 0 ? undefined : "n"}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const FONTES = [
  ["Voto, 1998–2022", "Tribunal Superior Eleitoral, dados abertos",
   "votacao_candidato_munzona"],
  ["Voto por seção e local, 2024", "Tribunal Superior Eleitoral, dados abertos",
   "votacao_secao e eleitorado_local_votacao"],
  ["Emenda federal, 2015–2026", "Portal da Transparência",
   "Emendas Parlamentares (arquivo único)"],
  ["Emenda estadual (piloto)", "Dados abertos estaduais",
   "Assembleia Legislativa, via SERINT em Goiás"],
  ["Malha municipal e estadual", "Instituto Brasileiro de Geografia e Estatística",
   "API de malhas"],
  ["População e área", "Instituto Brasileiro de Geografia e Estatística",
   "Censo 2022, agregado 4714"],
];

const PERDA = [
  ["1998", "1,98%", "Pernambuco, 8,9%"],
  ["2002", "1,66%", "Pernambuco, 10,0%"],
  ["2006", "1,12%", "Rondônia, 9,5%"],
  ["2010", "0,44%", "Rondônia, 9,4%"],
  ["2014", "0,13%", "Rondônia, 3,1%"],
  ["2018", "0,14%", "Rondônia, 2,9%"],
  ["2022", "0,12%", "Rondônia, 2,9%"],
];

const INDICES = [
  ["Municípios efetivos",
   "Número de municípios de igual peso que produziria a mesma concentração (1/HHI)",
   "Limitado pela quantidade de municípios da unidade"],
  ["Fração do estado",
   "Municípios efetivos sobre o total de municípios da unidade",
   "Indicador comparável entre unidades da federação"],
  ["Domínio médio",
   "Participação do candidato no total apurado nos municípios em que obteve voto",
   "—"],
  ["Contiguidade",
   "Votos no município principal e nos limítrofes a ele",
   "Calculada sobre a malha completa, não sobre a simplificada"],
  ["Gini municipal",
   "0 indica distribuição uniforme; 1, concentração integral",
   "—"],
  ["Semelhança (cosseno)",
   "Grau de coincidência entre dois vetores municipais de votação",
   "Não comparável entre unidades de portes distintos"],
];

const ESTADO = [
  ["Voto, todos os cargos", "27 unidades, 1998–2022", "integral"],
  ["Emenda federal", "território nacional, 2015–2026",
   "97,1% do valor com unidade da federação; 10,5% com município"],
  ["Emenda estadual", "2 das 27 unidades", "Goiás e Espírito Santo"],
  ["Emenda de assembleia", "1 das 27 (Distrito Federal)",
   "sem autoria e sem município: não atribuível"],
  ["Gasto administrativo do Legislativo", "19 das 27 mantêm portal",
   "4 com interface programática confirmada"],
  ["Vereador", "246 municípios de Goiás e 25 demais capitais, 2000–2024",
   "mapa por local de votação apenas em 2024"],
  ["Zonas eleitorais", "Goiás, 2024",
   "75 das 92 com limite territorial exato"],
];

export function VistaSobre({ nUF, nMun }: { nUF: number; nMun: number }) {
  return (
    <>
      <div className="cartaz">
        <h2>Objeto e escopo</h2>
        <p className="cap">
          <strong>Cadê o Voto?</strong> é um produto da{" "}
          <strong>Lastro — Inteligência Política</strong>. Apresenta a
          distribuição municipal do voto para os cargos eletivos e a execução
          das emendas parlamentares individuais, bem como o cruzamento entre
          ambas.
        </p>
        <p className="cap">
          A cobertura compreende {numero(nUF)} unidades da federação e{" "}
          {numero(nMun)} municípios, sete pleitos entre 1998 e 2022 no caso do
          voto e doze exercícios entre 2015 e 2026 no caso da emenda. Todas as
          fontes são públicas. Não há estimativa, projeção ou pesquisa de
          intenção de voto: os dados correspondem a apuração eleitoral e a
          execução orçamentária, nos termos em que os órgãos competentes as
          divulgaram.
        </p>
        <div className="nota">
          <strong>Princípio metodológico.</strong> Os arquivos de origem são
          abertos e de acesso irrestrito. O trabalho desta publicação consiste
          em identificar e tratar as inconsistências que eles contêm, e é sobre
          esse tratamento que esta página presta contas. Todo número divulgado
          é produzido por rotina versionada no repositório do projeto;
          afirmações não reproduzíveis por script não são publicadas.
        </div>
      </div>

      <div className="cartaz">
        <h2>Fontes primárias</h2>
        <Tabela cab={["Objeto", "Órgão", "Conjunto de dados"]} linhas={FONTES} />
        <p className="cap" style={{ marginTop: 10 }}>
          O servidor de distribuição do Tribunal Superior Eleitoral recusa
          clientes HTTP genéricos, requisições do tipo{" "}
          <span className="num">HEAD</span> e requisições com cabeçalho{" "}
          <span className="num">Range</span>. O acesso exige requisição GET
          simples acompanhada do conjunto completo de cabeçalhos de navegador.
          A restrição está documentada no repositório.
        </p>
      </div>

      <div className="cartaz">
        <h2>Critério de apuração do voto</h2>
        <p className="cap">
          Consideram-se os votos <strong>nominais</strong> de{" "}
          <strong>primeiro turno</strong>, agregados da zona eleitoral para o
          município. O voto nominal exclui voto de legenda, branco e nulo.
          Adota-se o primeiro turno por ser nele que se manifesta a disputa
          territorial; no segundo remanescem duas candidaturas.
        </p>
        <ul className="lista-fatos">
          <li><strong>A coluna de votos não é constante ao longo da
            série.</strong> Em 1998 o campo{" "}
            <span className="num">QT_VOTOS_NOMINAIS</span> encontra-se zerado;
            em 2002 não há coluna de votos válidos. A seleção da coluna é
            resolvida por verificação de soma, exercício a exercício, e não por
            regra fixa.</li>
          <li><strong>A situação "MÉDIA" corresponde a candidato eleito.</strong>{" "}
            O eleito pela média das sobras recebe classificação distinta do
            eleito pelo quociente partidário. A consideração exclusiva do valor{" "}
            <em>"ELEITO"</em> resultava em 35 a 38 cadeiras em assembleia de 41.</li>
          <li><strong>O exercício de 1998 contém registros duplicados.</strong>{" "}
            Quatro candidaturas apresentam dois registros cada, com contagem
            duplicada de votos. Preserva-se o registro deferido.</li>
          <li><strong>O identificador de candidatura se repete entre
            exercícios.</strong> O mesmo{" "}
            <span className="num">SQ_CANDIDATO</span> corresponde a pessoas
            distintas em pleitos distintos. Adota-se como chave o par
            (exercício, identificador); sem essa composição, registros de 2010
            contaminavam o pleito de 2014.</li>
          <li><strong>O pareamento de pessoas dispensa acentuação.</strong> A
            grafia de um mesmo nome varia dentro do próprio arquivo de origem. A
            normalização elevou a reincidência medida de 61% para 70,7%.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>Pareamento entre as bases do TSE e do IBGE</h2>
        <p className="cap">
          As duas instituições nomeiam os municípios de forma divergente. Quando
          o nome não encontra correspondência, o registro é descartado — e o
          mapa resultante conserva aparência de integridade, uma vez que o
          município apenas deixa de constar do total, sem qualquer sinalização.
        </p>
        <p className="cap">
          Foram identificados <strong>153 nomes sem correspondência e
          23.063.701 votos</strong> excluídos do mapa. O efeito não se
          concentrava em um exercício: <strong>distribuía-se ao longo da
          série</strong>. A grafia adotada pelo TSE variou no período — "MOJI
          GUAÇU" passou a "MOGI GUAÇU" —, de modo que os pleitos mais antigos
          registravam perda e os recentes, não.
        </p>
        <Tabela cab={["Pleito", "Perda nacional", "Unidade mais afetada"]}
                linhas={PERDA} />
        <p className="cap" style={{ marginTop: 10 }}>
          Uma série de concentração construída sobre essa base indicaria
          dispersão progressiva do voto em Pernambuco ao longo de 24 anos, por
          efeito exclusivo de falha de pareamento.
        </p>
        <div className="nota">
          <strong>Critério adotado no estabelecimento das
          correspondências.</strong> O pareamento por semelhança textual é
          inadequado ao caso: a correspondência incorreta não suprime votos,
          atribui-os a município diverso. O critério empregado é factual —{" "}
          <em>duas grafias do mesmo município não coexistem no mesmo
          pleito</em>. Sua aplicação rejeitou correspondências textualmente
          plausíveis e identificou o município correto em uma delas. Vigoram 163
          correções manuais; permanecem sem correspondência{" "}
          <strong>47.535 votos</strong>, distribuídos em três municípios, todos
          restritos ao exercício de 1998.
        </div>
      </div>

      <div className="cartaz">
        <h2>Critério de apuração das emendas</h2>
        <p className="cap">
          Considera-se o valor efetivamente <strong>desembolsado</strong> — pago
          no exercício, acrescido dos restos a pagar quitados. Não se considera
          o valor empenhado, que constitui compromisso e não despesa realizada:
          no âmbito nacional, R$ 308,6 bi empenhados correspondem a R$ 259,5 bi
          pagos.
        </p>
        <ul className="lista-fatos">
          <li><strong>O escopo restringe-se à emenda individual.</strong> As
            emendas de bancada, de comissão e de relator somam R$ 119,5 bi dos
            R$ 259,5 bi pagos no país, correspondendo a 46% do montante, que
            permanece fora desta publicação por delimitação de escopo. Desse
            total, R$ 4,7 bi dispõem de município identificado e ainda assim não
            são incorporados.</li>
          <li><strong>Apenas 10,5% do montante é atribuível a município.</strong>{" "}
            Nas emendas individuais, 75,5% do valor consta como{" "}
            <em>MÚLTIPLO</em>, isto é, distribuído por municípios que o arquivo
            não discrimina. Por unidade da federação a cobertura atinge 97,1%,
            razão pela qual a leitura íntegra é estadual e não municipal. Ambos
            os percentuais são verificados por{" "}
            <span className="num">48_audita_emendas.py</span>, que reconcilia o
            publicado com o arquivo de origem ao centavo.</li>
          <li><strong>Há atalho metodológico disponível, deliberadamente não
            adotado.</strong> Existe arquivo por favorecido com município
            informado em 100% do montante. Nele,{" "}
            <strong>Brasília concentra 36,4%</strong> das emendas individuais do
            país, por sediar o Fundo Nacional de Saúde e entidades
            intermediárias. O resultado seria um mapa íntegro e incorreto. O
            município adotado é sempre o da localidade de aplicação.</li>
          <li><strong>A denominada "emenda Pix" corresponde à Transferência
            Especial.</strong> Repassada diretamente à conta do município, sem
            convênio, sem finalidade definida em orçamento e sem
            acompanhamento federal. Totaliza R$ 32,2 bi, ou 23% das
            individuais, e dispõe de filtro próprio por constituir a modalidade
            sobre a qual há menor informação disponível.</li>
          <li><strong>A emenda individual é das duas casas legislativas, e as
            cotas não são iguais.</strong> Verificam-se <strong>594 autores por
            exercício</strong>, número que corresponde exatamente às 513 cadeiras
            da Câmara dos Deputados somadas às 81 do Senado Federal. A mediana
            paga por senador na série é de R$ 148,2 mi, contra R$ 79,6 mi por
            deputado — proporção de 1,86. A ordenação por valor sem distinção de
            casa reflete, portanto, regra orçamentária, e não comportamento
            parlamentar. A casa de cada autor é apresentada na listagem, com
            filtro próprio.</li>
          <li><strong>A identificação da casa é derivada do resultado
            eleitoral, e sua cobertura é declarada.</strong> O arquivo de origem
            não informa o mandato do autor. O pareamento é feito contra os
            eleitos para deputado federal e para senador de 1998 a 2022,
            alcançando <strong>1.266 dos 1.492 autores</strong> da série — 91,4%
            do valor. Os 226 restantes correspondem a suplentes que assumiram,
            mandatos anteriores a 1998 e casos de homonímia em que o critério
            recusou desempatar: pai e filho com o mesmo nome, entre eles.</li>
          <li><strong>A apresentação padrão é acumulada.</strong> Em exercício
            isolado, a maioria dos municípios não apresenta registro, e o mapa
            sugere ausência de recurso onde há ausência de rastreabilidade. No
            acumulado de 2015 a 2026, 69% dos municípios do país receberam
            emenda rastreável.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>Índices e limites de comparabilidade</h2>
        <p className="cap">
          Os índices são calculados de modo uniforme para todo candidato, cargo
          e unidade da federação, o que assegura a comparabilidade. Dois deles,
          contudo, apresentam limitação cuja desconsideração produz leitura
          incorreta.
        </p>
        <Tabela cab={["Índice", "Definição", "Restrição"]} linhas={INDICES} />
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>O índice de municípios efetivos não é comparável entre
          unidades da federação.</strong> Roraima possui 15 municípios e Minas
          Gerais, 853; uma unidade com 15 não pode apresentar 16 municípios
          efetivos. Por essa razão a <em>fração do estado</em> é apresentada em
          conjunto, sendo esta a medida comparável. Do mesmo modo, a{" "}
          <strong>semelhança de cosseno não é comparável entre escalas</strong>:
          calculada sobre 15 municípios, resulta mecanicamente superior à
          calculada sobre 853. Presta-se à ordenação interna a uma unidade e a
          um pleito, não à comparação entre unidades.
        </div>
      </div>

      <div className="cartaz">
        <h2>Disponibilidade de dados públicos no Brasil</h2>
        <p className="cap">
          O quadro a seguir não constitui apreciação: resulta de três
          levantamentos realizados por este projeto, reproduzíveis pelas rotinas
          do repositório. A disponibilidade é desigual, e a desigualdade
          apresenta padrão identificável.
        </p>
        <Tabela cab={["Objeto", "Abrangência", "Cobertura"]} linhas={ESTADO} />
        <ul className="lista-fatos" style={{ marginTop: 14 }}>
          <li><strong>A esfera federal apresenta cobertura integral; a
            estadual, excepcional.</strong> A emenda federal está disponível
            para todo o território, em arquivo único, com atualização contínua.
            A emenda estadual está disponível em <strong>duas das 27
            unidades</strong> — Goiás e Espírito Santo. Pernambuco e Bahia
            publicam conjuntos cuja denominação não corresponde ao conteúdo,
            circunstância verificável apenas mediante inspeção do arquivo.</li>
          <li><strong>O Poder Legislativo apresenta menor transparência que o
            Executivo, por decorrência de sua competência.</strong> Das 27
            assembleias, <strong>uma</strong> publica conjunto relativo a
            emendas — a do Distrito Federal —, e este não informa autoria nem
            município, não permitindo estabelecer destinação por parlamentar.
            Não se trata de omissão: a emenda é indicação sobre o orçamento do
            Executivo, cuja execução compete às secretarias. As Casas publicam
            informações sobre si próprias — folha de pagamento, diárias, verba
            de gabinete e contratos.</li>
          <li><strong>A publicação não equivale a disponibilidade
            utilizável.</strong> O portal de Pernambuco documenta esquema com
            autoria e município que <em>nenhum arquivo publicado
            utiliza</em>. A Bahia divulga o parlamentar e não o município. A
            Assembleia de Goiás publica diárias contendo registro de R$ 2,7
            milhões referente a 1,5 diária. Nenhuma dessas circunstâncias é
            perceptível a quem consulte a descrição em lugar do arquivo.</li>
          <li><strong>O formato varia entre exercícios.</strong> Em Goiás, sete
            exercícios de emenda estadual apresentam sete esquemas distintos,
            com alteração do separador para tabulação em 2025 e três mudanças na
            denominação da coluna de autoria. A leitura por posição ou por nome
            fixo de coluna não se sustenta no exercício seguinte.</li>
        </ul>
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>Justificativa da inclusão nesta página.</strong> Quem consulta
          um número aqui divulgado tem direito a saber que ele constitui
          exceção, e não regra, e que a maior parte do que seria pertinente
          medir não é publicada em formato que permita a medição.
        </div>
      </div>

      <div className="cartaz">
        <h2>Restrições metodológicas</h2>
        <ul className="lista-fatos">
          <li><strong>Não se preenchem lacunas com valor zero.</strong> O
            município sem dado é apresentado como sem dado. Ausência de valor e
            valor nulo são categorias distintas, e sua confusão constitui
            distorção de leitura.</li>
          <li><strong>Não se flexibilizam tolerâncias de teste.</strong> Quando
            um denominador divergiu do painel de referência, procedeu-se à
            separação entre o verificável e o não verificável, com divulgação da
            divergência, e não ao ajuste da tolerância.</li>
          <li><strong>Não se estabelece pareamento por inferência.</strong> Um
            município goiano permanece sem correspondência porque a
            plausibilidade não constitui evidência. A correspondência incorreta
            atribui recurso a município diverso, resultado mais gravoso que a
            ausência de atribuição.</li>
          <li><strong>Não se omite o denominador.</strong> Toda tela que
            apresenta participação relativa informa o total de referência.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>Camadas de classificação editorial</h2>
        <p className="cap">
          Três camadas não decorrem de arquivo de origem. Constituem
          classificação editorial, discutível por natureza, e são mantidas em
          arquivos apartados justamente para que possam ser contestadas sem
          alteração de código:
        </p>
        <ul className="lista-fatos">
          <li><strong>Linhagem partidária</strong> — 58 siglas reduzidas a 31
            linhagens. PFL corresponde a DEM, que corresponde a União Brasil. Sem
            essa consolidação a série de 24 anos não se sustenta; com ela,
            suprime-se a informação da fusão. Ambas as leituras estão
            disponíveis.</li>
          <li><strong>Espectro ideológico</strong> — 32 partidos distribuídos em
            cinco faixas. É o critério que distingue aliado de adversário na
            análise de rivalidade territorial. A substituição do arquivo altera a
            leitura.</li>
          <li><strong>Limiares da tipologia</strong> — concentração e domínio
            resultam em quatro perfis a partir de limiares definidos por este
            projeto, e não divulgados pelo Tribunal Superior Eleitoral.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>Contato e retificações</h2>
        <p className="cap">
          Comunicações que apontem incorreção em qualquer número aqui divulgado
          são de especial interesse. Todo valor desta publicação é produzido por
          rotina identificada; verificada a procedência da observação, a
          correção é incorporada na publicação seguinte, com registro do motivo.
        </p>
        <p className="cap"><strong>Lastro — Inteligência Política.</strong></p>
      </div>
    </>
  );
}
