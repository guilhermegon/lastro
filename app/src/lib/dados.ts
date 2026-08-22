import type {
  BaseUF, Cargo, CargoComRival, Cruzamentos, DadosCargo, Indice, Padroes,
  Rivais, Sigla, Vereador,
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

export const carregarCargo = (uf: Sigla, cargo: Cargo): Promise<DadosCargo> =>
  comCache<DadosCargo>(`${uf}:${cargo}`, `${BASE}/${uf}/${cargo}.json`);

export const carregarPadroes = (uf: Sigla): Promise<Padroes> =>
  comCache<Padroes>(`padroes:${uf}`, `${BASE}/${uf}/padroes.json`);

export const carregarCruzamentos = (uf: Sigla): Promise<Cruzamentos> =>
  comCache<Cruzamentos>(`cruz:${uf}`, `${BASE}/${uf}/cruzamentos.json`);

export const carregarRivais = (uf: Sigla, cargo: CargoComRival): Promise<Rivais> =>
  comCache<Rivais>(`rivais:${uf}:${cargo}`, `${BASE}/${uf}/rivais_${cargo}.json`);

export const carregarVereador = (uf: Sigla): Promise<Vereador> =>
  comCache<Vereador>(`ver:${uf}`, `${BASE}/${uf}/vereador.json`);
