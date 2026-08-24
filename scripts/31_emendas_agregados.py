"""Agrega as emendas no formato que o front ja consome.

Sai em dois niveis, e a divisao nao e' de conveniencia — e' de honestidade sobre
a cobertura do dado (ver `30_emendas_ingest.py` e o TKT-0005):

  web/emendas_br.json    por UF e por ano. Cobre 97,1% do dinheiro individual,
                         porque ate' as linhas MULTIPLO trazem UF. E' o nivel
                         em que o Emendometro esta completo, e por isso a aba
                         abre por aqui.

  web/{UF}/emendas.json  por municipio e por autor. Cobre 10,5% do dinheiro:
                         so' entra a emenda cuja localidade de aplicacao nomeia
                         um municipio. O arquivo carrega o proprio denominador
                         (`cobertura`) para que a tela possa dizer de quanto
                         esta falando, em vez de insinuar que e' tudo.

**Os indices de municipio sao os mesmos de `base.json`** — ordenacao por
`cod_ibge` dentro da UF, igual a `19_nacional_completo.py`. E' isso que permite
desenhar emenda e voto no mesmo mapa sem uma tabela de conversao no meio.

**O valor e' sempre o que saiu do caixa** (pago + restos a pagar pagos), nunca o
empenhado. O empenhado tambem vai no arquivo, mas como coluna separada: a
diferenca entre os dois e' informacao, nao ruido — sao R$ 308,6 bi contra
R$ 259,5 bi no pais.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

WEB = cfg.PROCESSED / "web"
FONTE = cfg.PROCESSED / "emendas.csv"
CASAMENTO = cfg.PROCESSED / "emendas_autor_deputado.csv"
TOP_AUTORES = 80          # por UF e por ano; o resto entra so' no agregado

# "Emenda Pix" e' como se chama a Transferencia Especial: o dinheiro cai direto
# na conta do municipio, sem convenio, sem finalidade definida no orcamento e
# sem que o governo federal acompanhe a aplicacao. Separar isso do resto nao e'
# detalhe de classificacao - e' a diferenca entre dinheiro com destino declarado
# e dinheiro sem.
PIX = "Transferências Especiais"


def eh_pix(tipo):
    return PIX.lower() in str(tipo).lower()


def indices_uf():
    """Mesma ordenacao que base.json usa, para os indices baterem."""
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    idx, nomes = {}, {}
    for uf, g in dim.groupby("uf"):
        g = g.sort_values("cod_ibge")
        idx[uf] = {c: i for i, c in enumerate(g["cod_ibge"])}
        nomes[uf] = list(g["nome"])
    return idx, nomes


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def main():
    if not FONTE.exists():
        raise SystemExit("rode 30_emendas_ingest.py antes")
    d = pd.read_csv(FONTE, dtype={"cod_ibge": str, "cod_emenda": str},
                    low_memory=False)
    d = d[d["individual"].astype(str).str.lower().isin(("true", "1"))]
    d["ano"] = pd.to_numeric(d["ano"], errors="coerce").astype("Int64")
    d = d[d["ano"].notna()]

    cas = pd.read_csv(CASAMENTO)
    eleito = dict(zip(cas["autor_norm"], cas["eleito"]))
    uf_el = dict(zip(cas["autor_norm"], cas["uf_eleito"].fillna("")))
    ambiguo = dict(zip(cas["autor_norm"], cas["ambiguo"]))

    idx, nomes = indices_uf()
    anos = sorted(int(a) for a in d["ano"].dropna().unique())

    # ---------- nacional, por UF e ano ----------
    poruf = []
    for (uf, ano), g in d[d["uf"].notna()].groupby(["uf", "ano"]):
        com = g[g["cod_ibge"].notna()]
        gp = g[g["tipo"].map(eh_pix)]
        poruf.append({
            "uf": uf, "ano": int(ano),
            "pago": round(float(g["pago"].sum()), 2),
            "pix": round(float(gp["pago"].sum()), 2),
            "emp": round(float(g["empenhado"].sum()), 2),
            "n": int(g["cod_emenda"].nunique()),
            "aut": int(g["autor_norm"].nunique()),
            # o denominador viaja junto com o numero
            "pagoMun": round(float(com["pago"].sum()), 2),
            "nMun": int(com["cod_ibge"].nunique()),
        })
    nacional = {
        "anos": anos,
        "uf": sorted(poruf, key=lambda r: (r["uf"], r["ano"])),
        "cobertura": {
            "pago": round(float(d["pago"].sum()), 2),
            "pix": round(float(d.loc[d["tipo"].map(eh_pix), "pago"].sum()), 2),
            "pagoUF": round(float(d.loc[d["uf"].notna(), "pago"].sum()), 2),
            "pagoMun": round(float(d.loc[d["cod_ibge"].notna(), "pago"].sum()), 2),
            "nAutores": int(d["autor_norm"].nunique()),
            "nCasados": int(sum(1 for a in d["autor_norm"].unique()
                                if eleito.get(a))),
        },
    }
    WEB.mkdir(parents=True, exist_ok=True)
    f = WEB / "emendas_br.json"
    f.write_text(json.dumps(nacional, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")
    print(f"emendas_br.json: {f.stat().st_size/1024:.0f} KB, "
          f"{len(poruf)} pares UF/ano")

    # ---------- por UF: municipio e autor ----------
    com_mun = d[d["cod_ibge"].notna() & d["uf"].notna()]
    total = 0
    for uf, g in com_mun.groupby("uf"):
        if uf not in idx:
            continue
        n = len(nomes[uf])
        pos = idx[uf]
        g = g[g["cod_ibge"].isin(pos)]
        if g.empty:
            continue
        blocos = {}
        for ano, ga in g.groupby("ano"):
            tot_mun = np.zeros(n)
            for c, v in ga.groupby("cod_ibge")["pago"].sum().items():
                tot_mun[pos[c]] = v

            # o mesmo vetor municipal, so' com o que e' Pix
            tot_pix = np.zeros(n)
            gp = ga[ga["tipo"].map(eh_pix)]
            for c, v in gp.groupby("cod_ibge")["pago"].sum().items():
                tot_pix[pos[c]] = v

            fichas = []
            for autor, gg in ga.groupby("autor_norm"):
                por_mun = gg.groupby("cod_ibge")["pago"].sum()
                por_mun = por_mun[por_mun > 0]
                if por_mun.empty:
                    continue
                v = por_mun.to_numpy(dtype=float)
                p = v / v.sum()
                pix = gg[gg["tipo"].map(eh_pix)]
                por_pix = pix.groupby("cod_ibge")["pago"].sum()
                por_pix = por_pix[por_pix > 0]
                fichas.append({
                    "n": str(gg["autor"].iloc[0]),
                    "t": round(float(v.sum()), 2),
                    "pix": round(float(pix["pago"].sum()), 2),
                    "pxi": [pos[c] for c in por_pix.index],
                    "pxv": [round(float(x), 2) for x in por_pix.to_numpy()],
                    "emp": round(float(gg["empenhado"].sum()), 2),
                    "ne": int(gg["cod_emenda"].nunique()),
                    "nm": int(len(v)),
                    "mi": [pos[c] for c in por_mun.index],
                    "mv": [round(float(x), 2) for x in v],
                    "t1": round(float(p.max() * 100), 2),
                    # municipios efetivos: mesmo indice do voto, 1/HHI
                    "ef": round(float(1 / (p ** 2).sum()), 2),
                    "gi": round(gini(v), 4),
                    "el": bool(eleito.get(autor, False)),
                    "ufEl": uf_el.get(autor, ""),
                    "amb": bool(ambiguo.get(autor, False)),
                    "fn": gg.groupby("funcao")["pago"].sum().idxmax()
                          if gg["funcao"].notna().any() else "",
                })
            fichas.sort(key=lambda x: -x["t"])
            todas = ga["pago"].sum()
            blocos[str(int(ano))] = {
                "totalMun": [round(float(x), 2) for x in tot_mun],
                "totalPix": [round(float(x), 2) for x in tot_pix],
                "fichas": fichas[:TOP_AUTORES],
                "pleito": {
                    "pago": round(float(todas), 2),
                    "emp": round(float(ga["empenhado"].sum()), 2),
                    "nAutores": int(ga["autor_norm"].nunique()),
                    "nEmendas": int(ga["cod_emenda"].nunique()),
                    "nMun": int(ga["cod_ibge"].nunique()),
                    "pix": round(float(gp["pago"].sum()), 2),
                    "nPix": int(gp["cod_emenda"].nunique()),
                    "cortados": max(0, len(fichas) - TOP_AUTORES),
                },
            }
        # o denominador da UF inteira, para a tela poder declarar a cobertura
        tudo_uf = d[d["uf"] == uf]
        pix_uf = tudo_uf[tudo_uf["tipo"].map(eh_pix)]
        obj = {"anos": blocos, "cobertura": {
            "pago": round(float(tudo_uf["pago"].sum()), 2),
            "pagoMun": round(float(g["pago"].sum()), 2),
            "pix": round(float(pix_uf["pago"].sum()), 2),
            "pixMun": round(float(g[g["tipo"].map(eh_pix)]["pago"].sum()), 2)}}
        p = WEB / uf / "emendas.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
        total += p.stat().st_size
    print(f"emendas.json por UF: {total/1024/1024:.1f} MB no total")

    c = nacional["cobertura"]
    bi = lambda v: f"R$ {v/1e9:.1f} bi"
    print(f"\ncobertura declarada nos arquivos:")
    print(f"  pago total   {bi(c['pago'])}")
    print(f"  com UF       {bi(c['pagoUF'])}  ({c['pagoUF']/c['pago']*100:.1f}%)")
    print(f"  com município{bi(c['pagoMun']):>12}  ({c['pagoMun']/c['pago']*100:.1f}%)")
    print(f"  autores {c['nAutores']:,}, dos quais {c['nCasados']:,} casam com eleito")


if __name__ == "__main__":
    main()
