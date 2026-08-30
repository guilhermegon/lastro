import type {
  BaseUF, BlocoAno, BlocoRivais, Cargo, CargoComRival, Cruzamentos, Demografia,
  AlegoAdmin, AlegoVerbas, AlmgVerbas, Assembleias, CldfAdmin, CldfVerbas,
  Cidades, Emendas, EmendasBR, Indice, Padroes, Sigla, Urnas, Vereador, Zonas,
} from "../tipos";

const BASE = `${import.meta.env.BASE_URL}dados`;

async function baixar<T>(caminho: string): Promise<T> {
  const r = await fetch(caminho);
  if (!r.ok) throw new Error(`${caminho}: ${r.status} ${r.statusText}`);
  return (await r.json()) as T;
}

/**
 * Cache por recurso. O usuário troca de estado e de cargo várias vezes numa
 * sessão e não faz sentido rebaixar São Paulo — 2,7 MB só no estadual — a cada
 * volta. Guarda a promessa, não o resultado: dois pedidos simultâneos do mesmo
 * recurso viram uma requisição só, e a falha não fica presa no cache.
 */
const cache = new Map<string, Promise<unknown>>();

function comCache<T>(chave: string, caminho: string): Promise<T> {
  let p = cache.get(chave) as Promise<T> | undefined;
  if (!p) {
    p = baixar<T>(caminho).catch((e) => {
      cache.delete(chave);
      throw e;
    });
    cache.set(chave, p);
  }
  return p;
}

export const carregarIndice = (): Promise<Indice> =>
  comCache<Indice>("indice", `${BASE}/indice.json`);

export const carregarBase = (uf: Sigla): Promise<BaseUF> =>
  comCache<BaseUF>(`base:${uf}`, `${BASE}/${uf}/base.json`);

/**
 * Um arquivo por pleito, não um por cargo — ver 22_publicar_web.py.
 *
 * A tela mostra um ano de cada vez, e o arquivo trazia os sete. Em São Paulo,
 * o pior caso do país, a aba do estadual baixava 2,7 MB para desenhar um ano;
 * agora são 481 KB. Não é compressão: o gzip do servidor já corta 79% e
 * espremer mais renderia 4%. É deixar de mandar seis anos que ninguém pediu.
 */
export const carregarCargoAno = (
  uf: Sigla, cargo: Cargo, ano: number,
): Promise<BlocoAno> =>
  comCache<BlocoAno>(`${uf}:${cargo}:${ano}`,
                     `${BASE}/${uf}/${cargo}/${ano}.json`);

export const carregarRivaisAno = (
  uf: Sigla, cargo: CargoComRival, ano: number,
): Promise<BlocoRivais> =>
  comCache<BlocoRivais>(`rivais:${uf}:${cargo}:${ano}`,
                        `${BASE}/${uf}/rivais_${cargo}/${ano}.json`);

/**
 * Os anos que ESTE cargo tem NESTA UF.
 *
 * Vive ao lado dos arquivos e não no índice porque uma UF pode não ter disputado
 * um cargo num pleito — sem esta lista, descobrir isso custaria um 404 por ano,
 * e 404 é indistinguível de rede caída.
 */
export const carregarAnosCargo = (uf: Sigla, cargo: string): Promise<number[]> =>
  comCache<number[]>(`anos:${uf}:${cargo}`, `${BASE}/${uf}/${cargo}/anos.json`);

/**
 * Puxa os demais pleitos em segundo plano, um de cada vez.
 *
 * Sequencial de propósito: o ponto é a tela aberta ficar pronta primeiro. Sete
 * requisições paralelas competiriam com o que o usuário está esperando ver, que
 * é exatamente o problema que a divisão por ano veio resolver.
 *
 * `comCache` guarda a promessa, então o que for pré-buscado aqui é entregue na
 * hora quando o usuário troca de ano, e um clique durante a pré-busca não
 * dispara segunda requisição.
 */
export async function prebuscar(
  uf: Sigla, cargo: Cargo, anos: number[], jaTem: number,
  rival: boolean, vivo: () => boolean,
  aoChegar: (ano: number, bloco: BlocoAno, riv: BlocoRivais | null) => void,
): Promise<void> {
  for (const ano of anos) {
    if (ano === jaTem) continue;
    if (!vivo()) return;
    try {
      const bloco = await carregarCargoAno(uf, cargo, ano);
      let riv: BlocoRivais | null = null;
      if (rival) {
        riv = await carregarRivaisAno(uf, cargo as CargoComRival, ano)
                .catch(() => null);
      }
      if (vivo()) aoChegar(ano, bloco, riv);
    } catch {
      // um pleito que falha não derruba os outros nem a tela: quem trocar para
      // ele pega o erro no caminho normal, com aviso
    }
  }
}

export const carregarPadroes = (uf: Sigla): Promise<Padroes> =>
  comCache<Padroes>(`padroes:${uf}`, `${BASE}/${uf}/padroes.json`);

export const carregarCruzamentos = (uf: Sigla): Promise<Cruzamentos> =>
  comCache<Cruzamentos>(`cruz:${uf}`, `${BASE}/${uf}/cruzamentos.json`);

export const carregarVereador = (uf: Sigla): Promise<Vereador> =>
  comCache<Vereador>(`ver:${uf}`, `${BASE}/${uf}/vereador.json`);

/* ---------- Emendômetro ----------
   A emenda federal existe para as 27 unidades; a estadual só onde o governo do
   estado publica em formato tabular com autor e município — hoje Goiás e
   Espírito Santo. Por isso `carregarEmendasEstadual` pode 404, e quem chama
   trata isso como "esta esfera não existe aqui", não como erro. */

export const carregarEmendas = (uf: Sigla): Promise<Emendas> =>
  comCache<Emendas>(`emendas:${uf}`, `${BASE}/${uf}/emendas.json`);

export const carregarEmendasEstadual = (uf: Sigla): Promise<Emendas> =>
  comCache<Emendas>(`emendasE:${uf}`, `${BASE}/${uf}/emendas_estadual.json`);

export const carregarEmendasBR = (): Promise<EmendasBR> =>
  comCache<EmendasBR>("emendasBR", `${BASE}/emendas_br.json`);

/** População e área, para as leituras por habitante e por km². */
export const carregarDemografia = (uf: Sigla): Promise<Demografia> =>
  comCache<Demografia>(`demo:${uf}`, `${BASE}/${uf}/demografia.json`);

/* ---------- aba API ----------
   Seis arquivos de três casas. A aba é nacional: não muda com o estado
   escolhido, porque o achado é a comparação entre as casas cujo dado dá para
   consumir — e são estas três. */

export const carregarAssembleias = (): Promise<Assembleias> =>
  comCache<Assembleias>("assembleias", `${BASE}/assembleias.json`);

export const carregarAlegoVerbas = (): Promise<AlegoVerbas> =>
  comCache<AlegoVerbas>("alegoV", `${BASE}/GO/alego_verbas.json`);

export const carregarAlegoAdmin = (): Promise<AlegoAdmin> =>
  comCache<AlegoAdmin>("alegoA", `${BASE}/GO/alego_admin.json`);

export const carregarCldfVerbas = (): Promise<CldfVerbas> =>
  comCache<CldfVerbas>("cldfV", `${BASE}/DF/cldf_verbas.json`);

export const carregarCldfAdmin = (): Promise<CldfAdmin> =>
  comCache<CldfAdmin>("cldfA", `${BASE}/DF/cldf_admin.json`);

export const carregarAlmgVerbas = (): Promise<AlmgVerbas> =>
  comCache<AlmgVerbas>("almgV", `${BASE}/MG/almg_verbas.json`);

/** As cidades servidas, com o caminho de cada arquivo. 34 KB para 271 cidades.
 *
 *  Vem antes de escolher o estado de proposito: sem isso o leitor teria de
 *  adivinhar em qual UF esta a cidade dele para descobrir se ela esta na lista.
 */
export const carregarCidades = (): Promise<Cidades> =>
  comCache<Cidades>("cidades", `${BASE}/cidades.json`);

/** As zonas eleitorais de uma UF. Existe onde o `56_` rodou — hoje Goiás —,
 *  então quem chama trata a ausência como "ainda não mapeamos as zonas aqui". */
export const carregarZonas = (uf: Sigla): Promise<Zonas> =>
  comCache<Zonas>(`zonas:${uf}`, `${BASE}/${uf}/zonas.json`);

/** Vereador de uma cidade, pelo caminho que o indice deu. */
export const carregarCidade = (uf: Sigla, src: string): Promise<Vereador> =>
  comCache<Vereador>(`cid:${uf}:${src}`, `${BASE}/${uf}/${src}`);

/** Mapa de urnas de uma cidade, pelo caminho que o indice deu. */
export const carregarUrnasCidade = (uf: Sigla, src: string): Promise<Urnas> =>
  comCache<Urnas>(`urn:${uf}:${src}`, `${BASE}/${uf}/${src}`);
