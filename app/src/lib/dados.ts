import type { DadosUF, Indice, Sigla } from "../tipos";

const BASE = `${import.meta.env.BASE_URL}dados`;

async function baixar<T>(caminho: string): Promise<T> {
  const r = await fetch(caminho);
  if (!r.ok) throw new Error(`${caminho}: ${r.status} ${r.statusText}`);
  return (await r.json()) as T;
}

export const carregarIndice = (): Promise<Indice> =>
  baixar<Indice>(`${BASE}/indice.json`);

/**
 * Cache por UF. O usuário troca de estado várias vezes numa sessão e não faz
 * sentido rebaixar Minas — 2,3 MB — a cada volta. Guarda a promessa, não o
 * resultado, para que dois pedidos simultâneos do mesmo estado virem um só.
 */
const cache = new Map<Sigla, Promise<DadosUF>>();

export function carregarUF(uf: Sigla): Promise<DadosUF> {
  let p = cache.get(uf);
  if (!p) {
    p = baixar<DadosUF>(`${BASE}/uf/${uf}.json`).catch((e) => {
      cache.delete(uf); // falha não fica em cache: a próxima tentativa refaz
      throw e;
    });
    cache.set(uf, p);
  }
  return p;
}
