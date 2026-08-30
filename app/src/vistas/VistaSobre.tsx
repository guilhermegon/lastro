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
  ["Emenda federal, 2015–2026", "Portal da Transparência",
   "Emendas Parlamentares (arquivo único)"],
  ["Emenda estadual (piloto)", "Dados abertos do estado",
   "Assembleia Legislativa, via SERINT em Goiás"],
  ["Malha municipal e estadual", "IBGE", "API de malhas"],
  ["População e área", "IBGE", "Censo 2022, agregado 4714"],
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
   "Equivale a concentrar tudo nesse tanto de municípios iguais (1/HHI)",
   "Limitado pelo tamanho do estado"],
  ["Fração do estado", "Municípios efetivos sobre o total do estado",
   "É o número comparável entre UFs"],
  ["Domínio médio", "Fatia do candidato onde ele tem voto", "—"],
  ["Contiguidade",
   "Voto no reduto e nos municípios que fazem fronteira",
   "Vem da malha completa, não da simplificada"],
  ["Gini municipal", "0 = espalhado por igual, 1 = tudo num lugar", "—"],
  ["Semelhança (cosseno)", "Quanto dois mapas têm o mesmo formato",
   "Não se compara entre estados de portes diferentes"],
];

const ESTADO = [
  ["Voto, todos os cargos", "27 unidades, 1998–2022", "completa"],
  ["Emenda federal", "país inteiro, 2015–2026",
   "97,1% do valor tem UF; 10,5% tem município"],
  ["Emenda estadual", "2 de 27 estados", "Goiás e Espírito Santo"],
  ["Emenda de assembleia", "1 das 27 (DF)",
   "sem autor e sem município: não é atribuível"],
  ["Gasto administrativo do Legislativo", "19 de 27 têm portal",
   "4 com API confirmada"],
  ["Vereador", "26 capitais, 2000–2024",
   "sem mapa: a cidade é um município só"],
];

export function VistaSobre({ nUF, nMun }: { nUF: number; nMun: number }) {
  return (
    <>
      <div className="cartaz">
        <h2>O que é isto</h2>
        <p className="cap">
          <strong>Cadê o Voto?</strong> é um produto da{" "}
          <strong>Lastro — Inteligência Política</strong>. Ele mostra onde cada
          candidato tirou voto, município a município, e para onde cada
          parlamentar mandou emenda — e cruza as duas coisas.
        </p>
        <p className="cap">
          São {numero(nUF)} unidades da federação, {numero(nMun)} municípios,
          sete pleitos de 1998 a 2022 no voto, e doze exercícios de 2015 a 2026
          na emenda. Todo dado é público. Nada aqui é estimativa, projeção ou
          pesquisa de intenção: é apuração e execução orçamentária, como os
          órgãos publicaram.
        </p>
        <div className="nota">
          <strong>O que fazemos não é achar o dado — é fazer o dado não
          mentir.</strong> Os arquivos são abertos e qualquer um baixa. O
          trabalho está nas armadilhas que eles contêm, e é sobre elas que esta
          página fala. Todo número publicado sai de um script que está no
          repositório; se uma afirmação não é reproduzível, ela não entra.
        </div>
      </div>

      <div className="cartaz">
        <h2>De onde vem cada número</h2>
        <Tabela cab={["O quê", "Fonte", "Arquivo"]} linhas={FONTES} />
        <p className="cap" style={{ marginTop: 10 }}>
          O CDN do TSE recusa cliente HTTP comum, requisição{" "}
          <span className="num">HEAD</span> e requisição com{" "}
          <span className="num">Range</span>. Só passa em GET simples com o
          conjunto completo de cabeçalhos de navegador — descobrir isso foi o
          primeiro dia de trabalho, e está documentado para não ser
          redescoberto.
        </p>
      </div>

      <div className="cartaz">
        <h2>Como o voto é contado</h2>
        <p className="cap">
          Votos <strong>nominais</strong>, de <strong>1º turno</strong>,
          agregados de zona eleitoral para município. Nominal exclui voto de
          legenda, branco e nulo. O 1º turno é onde está a disputa territorial:
          no segundo sobram dois nomes.
        </p>
        <ul className="lista-fatos">
          <li><strong>A coluna de votos muda ao longo da série.</strong> Em 1998
            o campo <span className="num">QT_VOTOS_NOMINAIS</span> vem zerado; em
            2002 não existe a coluna de válidos. A escolha é resolvida por soma,
            ano a ano, nunca por regra fixa.</li>
          <li><strong>"MÉDIA" é eleito.</strong> Quem entra pela média das sobras
            tem situação diferente de quem entra pelo quociente. Tratar só{" "}
            <em>"ELEITO"</em> dava 35 a 38 cadeiras numa assembleia de 41.</li>
          <li><strong>1998 tem registro duplicado.</strong> Quatro candidaturas
            aparecem com dois registros cada e votos contados duas vezes. Fica o
            registro deferido.</li>
          <li><strong>O código do candidato se repete entre anos.</strong> O
            mesmo <span className="num">SQ_CANDIDATO</span> pertence a pessoas
            diferentes em pleitos diferentes. A chave é o par (ano, código) — sem
            isso, um suplente de 2010 vazava para 2014.</li>
          <li><strong>Pessoa é pareada sem acento.</strong> A grafia do mesmo
            nome varia dentro do próprio arquivo do TSE. Corrigir isso levou a
            reincidência medida de 61% para 70,7%.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>O pareamento com o IBGE, e os 23 milhões de votos</h2>
        <p className="cap">
          O TSE nomeia municípios; o IBGE também, e diferente. Quando o nome não
          casa, a linha é descartada — e o mapa fica com aparência de certo,
          porque o município apenas some do total sem que nada avise.
        </p>
        <p className="cap">
          Havia <strong>153 nomes órfãos e 23.063.701 votos</strong> fora do
          mapa. E o estrago não era num ano: <strong>era na linha do
          tempo</strong>. O TSE mudou a grafia ao longo da série — "MOJI GUAÇU"
          virou "MOGI GUAÇU" — então os pleitos antigos perdiam e os recentes
          não.
        </p>
        <Tabela cab={["Pleito", "Perda nacional", "Pior estado"]} linhas={PERDA} />
        <p className="cap" style={{ marginTop: 10 }}>
          Uma série de concentração lida assim mostraria Pernambuco espalhando o
          voto ao longo de 24 anos por puro artefato de pareamento.
        </p>
        <div className="nota">
          <strong>Como os pares foram estabelecidos.</strong> Casar por
          semelhança de texto é perigoso: um par errado não perde voto, põe voto
          no município errado. O crivo veio do dado, não do texto —{" "}
          <em>duas grafias do mesmo lugar nunca dividem o mesmo pleito</em>. Isso
          reprovou propostas plausíveis e identificou o alvo certo de uma delas.
          Hoje são 163 correções manuais e restam{" "}
          <strong>47.535 votos</strong> sem par, em três municípios, todos só em
          1998.
        </div>
      </div>

      <div className="cartaz">
        <h2>Como a emenda é contada</h2>
        <p className="cap">
          O valor é sempre o que <strong>saiu do caixa</strong> — pago no
          exercício mais restos a pagar efetivamente pagos. Nunca o empenhado,
          que é compromisso e não gasto: no país são R$ 308,6 bi empenhados
          contra R$ 259,5 bi pagos.
        </p>
        <ul className="lista-fatos">
          <li><strong>O Emendômetro cobre emenda individual, e só ela.</strong>{" "}
            Bancada, comissão e relator somam R$ 119,5 bi dos R$ 259,5 bi pagos
            no país — 46% do dinheiro de emenda fica fora por escolha de escopo.
            Destes, R$ 4,7 bi têm município identificado e ainda assim não
            entram.</li>
          <li><strong>Só 10,5% do dinheiro chega a um município.</strong> Das
            emendas individuais, 75,5% do valor está declarado como{" "}
            <em>MÚLTIPLO</em> — espalhado por cidades que o arquivo não nomeia.
            Por UF a cobertura é 97,1%, e é por isso que a leitura completa é
            estadual, não municipal. Os dois números são conferidos por
            <span className="num"> 48_audita_emendas.py</span>, que reconcilia o
            publicado com o arquivo de origem ao centavo.</li>
          <li><strong>Existe um atalho falso, e ele fica fechado.</strong> Há um
            arquivo por favorecido com município em 100% do dinheiro. Nele,{" "}
            <strong>Brasília concentra 36,4%</strong> das emendas individuais do
            país — porque é o endereço do Fundo Nacional de Saúde e dos
            intermediários. Seria um mapa completo e falso. O município aqui vem
            sempre da localidade de aplicação.</li>
          <li><strong>"Emenda Pix" é a Transferência Especial.</strong> Cai
            direto na conta do município, sem convênio, sem finalidade definida
            no orçamento e sem acompanhamento federal. São R$ 32,2 bi — 23% das
            individuais — e têm filtro próprio porque são o dinheiro sobre o qual
            se sabe menos.</li>
          <li><strong>O mapa abre acumulado.</strong> Num ano só, um estado
            mostra poucos municípios e o mapa sugere ausência de dinheiro onde há
            ausência de rastreabilidade. Somando 2015 a 2026, 69% dos municípios
            do país receberam alguma emenda rastreável.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>Os índices, e quando eles não se comparam</h2>
        <p className="cap">
          Os mesmos índices valem para todo candidato, cargo e estado — é isso
          que permite comparar. Mas dois deles têm limite, e ignorá-lo produz
          leitura errada.
        </p>
        <Tabela cab={["Índice", "O que mede", "Cuidado"]} linhas={INDICES} />
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>Municípios efetivos não se comparam entre estados.</strong>{" "}
          Roraima tem 15 municípios e Minas tem 853; um estado com 15 não pode
          ter 16 efetivos. Por isso a <em>fração do estado</em> anda junto — é
          ela que é comparável. E <strong>semelhança de cosseno não se compara
          entre escalas</strong>: sobre 15 municípios ela é mecanicamente maior
          que sobre 853. Serve para ordenar dentro de um estado e pleito, não
          entre estados.
        </div>
      </div>

      <div className="cartaz">
        <h2>O estado do dado no Brasil, medido</h2>
        <p className="cap">
          Não é impressão: são três levantamentos que fizemos e que podem ser
          repetidos pelos scripts do repositório. O retrato é desigual, e a
          desigualdade tem forma.
        </p>
        <Tabela cab={["O quê", "Onde existe", "Cobertura"]} linhas={ESTADO} />
        <ul className="lista-fatos" style={{ marginTop: 14 }}>
          <li><strong>O federal é completo; o estadual é exceção.</strong> A
            emenda federal existe para o país inteiro, num arquivo só, atualizado
            o ano todo. A emenda estadual existe em <strong>dois estados de
            27</strong> — Goiás e Espírito Santo. Pernambuco e Bahia publicam
            conjuntos com nome certo e conteúdo insuficiente, e só se descobre
            abrindo.</li>
          <li><strong>O Legislativo é mais opaco que o Executivo, e por
            desenho.</strong> Das 27 assembleias, <strong>uma</strong> publica um
            conjunto de emenda — a do DF — e ele não traz autor nem município,
            então não diz quem mandou dinheiro para onde. Não é omissão: a emenda
            é indicação sobre o orçamento do Executivo, e quem executa são as
            secretarias. As Casas publicam a si mesmas — folha, diária, verba de
            gabinete, contrato.</li>
          <li><strong>Publicar não é publicar utilizável.</strong> O portal de
            Pernambuco documenta um esquema com autor e município que{" "}
            <em>nenhum arquivo publicado usa</em>. A Bahia publica o deputado e
            não o município. A ALEGO publica diárias com um registro de R$ 2,7
            milhões para 1,5 diária. Cada um desses casos passaria despercebido
            por quem lesse a descrição em vez do arquivo.</li>
          <li><strong>E o formato muda embaixo do pé.</strong> Em Goiás, sete
            exercícios de emenda estadual têm sete esquemas diferentes, com o
            separador virando tabulação em 2025 e a coluna de autor mudando de
            nome três vezes. Ler por posição ou por nome fixo quebra no próximo
            arquivo.</li>
        </ul>
        <div className="nota" style={{ marginTop: 12 }}>
          <strong>Por que isto está aqui e não num relatório à parte.</strong>{" "}
          Quem lê um número desta página tem direito de saber que ele é a
          exceção, não a regra — e que a maior parte do que seria interessante
          medir simplesmente não é publicada em formato que permita medir.
        </div>
      </div>

      <div className="cartaz">
        <h2>O que não fazemos</h2>
        <ul className="lista-fatos">
          <li><strong>Não preenchemos lacuna com zero.</strong> Município sem
            dado aparece como sem dado. Zero e "não sei" são coisas diferentes, e
            confundi-las é como um mapa mente.</li>
          <li><strong>Não afrouxamos teste para ele passar.</strong> Quando um
            denominador não fechou com o painel de referência, a saída foi
            separar o que é verificável do que não é e publicar a divergência —
            não calibrar a tolerância até o verde aparecer.</li>
          <li><strong>Não chutamos pareamento.</strong> Um município goiano segue
            sem par porque "pode ser" outro não é evidência. Par errado põe
            dinheiro no lugar errado, que é pior que dinheiro sem lugar.</li>
          <li><strong>Não escondemos o denominador.</strong> Toda tela que mostra
            uma fatia diz de quanto ela é fatia.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>Onde o juízo é nosso, e não do dado</h2>
        <p className="cap">
          Três camadas não saem de arquivo nenhum. São classificação editorial,
          discutível por natureza, e ficam em arquivos separados justamente para
          poderem ser contestadas sem tocar no código:
        </p>
        <ul className="lista-fatos">
          <li><strong>Linhagem partidária</strong> — 58 siglas reduzidas a 31
            linhagens. PFL vira DEM vira União Brasil. Sem isso a série de 24
            anos se desfaz; com isso, some a informação de que houve fusão. As
            duas visões existem.</li>
          <li><strong>Espectro ideológico</strong> — 32 partidos em cinco faixas.
            É o que separa "aliado" de "adversário" na análise de rivais. Trocar
            o arquivo troca a leitura.</li>
          <li><strong>Os cortes da tipologia</strong> — concentração e domínio
            viram quatro perfis a partir de limiares que escolhemos, não que o
            TSE publicou.</li>
        </ul>
      </div>

      <div className="cartaz">
        <h2>Fale com a gente</h2>
        <p className="cap">
          Achou um número errado? É o tipo de mensagem que mais nos interessa.
          Todo número desta página sai de um script identificado, e uma correção
          que se confirme entra na próxima publicação com o motivo registrado.
        </p>
        <p className="cap"><strong>Lastro — Inteligência Política.</strong></p>
      </div>
    </>
  );
}
