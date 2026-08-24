"""Emendas estaduais no mesmo formato do Emendometro federal.

Le `emendas_go_estadual.csv` (piloto do `34_`) e grava
`web/{UF}/emendas_estadual.json` com a MESMA forma de `emendas.json`, para que a
tela troque de esfera sem trocar de codigo de desenho.

**Por que fusao e nao aba nova** (aplicado sob a pre-autorizacao do DaRulez):
uma aba que existe so' em Goias ficaria vazia em 26 estados. Um seletor de
esfera que simplesmente nao aparece onde nao ha dado e' mais honesto e mais
util — e a pergunta que interessa e' comparativa: o deputado estadual manda
dinheiro para o mesmo tipo de lugar que o federal?

**Duas diferencas em relacao ao federal, e as duas importam na leitura:**

1. **Nao ha "emenda Pix" aqui.** Transferencia Especial e' instrumento do
   orcamento da Uniao. O arquivo estadual traz `tipo`, mas com outra
   classificacao; o campo `totalPix` sai zerado de proposito, e a tela esconde
   o filtro na esfera estadual em vez de mostrar um filtro que sempre da zero.

2. **A cobertura municipal e' MUITO maior**: 65,8% do valor contra 10,5% no
   federal. Nao e' o estado sendo mais transparente por virtude — e' que a
   emenda estadual e' menor e quase sempre nomeia um municipio, enquanto a
   federal frequentemente vai para "MULTIPLO" ou para o estado inteiro.
"""
import json
import re
import sys
import unicodedata
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

WEB = cfg.PROCESSED / "web"
# Um ingestor por estado, de proposito: a sondagem mostrou que nao existe
# formato comum entre portais estaduais, e um leitor generico so' esconderia
# isso. Cada UF entra aqui depois de ter seu proprio 3x_ conferido.
FONTES = {"GO": cfg.PROCESSED / "emendas_go_estadual.csv",
          "ES": cfg.PROCESSED / "emendas_es_estadual.csv"}
TOP_AUTORES = 80


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def chave_pessoa(t):
    return re.sub(r"^(DEP\.?|DEPUTAD[OA])\s+", "", sem_acento(t)).strip()


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def eleitos_estaduais(uf):
    """Quem foi eleito à assembleia, por chave de pessoa -> pleitos."""
    f = WEB / uf / "estadual.json"
    if not f.exists():
        return {}
    d = json.loads(f.read_text(encoding="utf-8"))
    por = {}
    for ano, b in d.items():
        for ficha in b["fichas"]:
            if not ficha.get("el"):
                continue
            for k in {chave_pessoa(ficha["n"]),
                      chave_pessoa(ficha.get("completo", ""))}:
                if k:
                    por.setdefault(k, set()).add(int(ano))
    return por


def main():
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    feito = []
    for uf, fonte in FONTES.items():
        if not fonte.exists():
            print(f"  {uf}: sem fonte ({fonte.name}) — rode 34_ antes")
            continue
        d = pd.read_csv(fonte, dtype={"cod_ibge": str}, low_memory=False)
        d = d[d["cod_ibge"].notna() & d["valor"].notna() & (d["valor"] > 0)]
        d["ano"] = pd.to_numeric(d["ano"], errors="coerce")
        d = d[d["ano"].notna()]

        g = dim[dim["uf"] == uf].sort_values("cod_ibge")
        pos = {c: i for i, c in enumerate(g["cod_ibge"])}
        n = len(pos)
        d = d[d["cod_ibge"].isin(pos)]
        if d.empty:
            print(f"  {uf}: nenhuma linha pareada com a malha")
            continue
        el = eleitos_estaduais(uf)

        blocos = {}
        for ano, ga in d.groupby("ano"):
            tot = np.zeros(n)
            for c, v in ga.groupby("cod_ibge")["valor"].sum().items():
                tot[pos[c]] = v

            fichas = []
            for autor, gg in ga.groupby("autor_norm"):
                por_mun = gg.groupby("cod_ibge")["valor"].sum()
                por_mun = por_mun[por_mun > 0]
                if por_mun.empty:
                    continue
                v = por_mun.to_numpy(dtype=float)
                p = v / v.sum()
                anos_el = el.get(autor, set())
                fichas.append({
                    "n": str(gg["autor"].iloc[0]),
                    "t": round(float(v.sum()), 2),
                    "pix": 0.0, "pxi": [], "pxv": [],
                    "emp": round(float(gg["valor"].sum()), 2),
                    "ne": int(gg["emenda"].nunique()) if "emenda" in gg else len(gg),
                    "nm": int(len(v)),
                    "mi": [pos[c] for c in por_mun.index],
                    "mv": [round(float(x), 2) for x in v],
                    "t1": round(float(p.max() * 100), 2),
                    "ef": round(float(1 / (p ** 2).sum()), 2),
                    "gi": round(gini(v), 4),
                    "el": bool(anos_el),
                    "ufEl": uf if anos_el else "",
                    "amb": False,
                    "fn": (gg.groupby("funcao")["valor"].sum().idxmax()
                           if gg["funcao"].notna().any() else ""),
                })
            fichas.sort(key=lambda x: -x["t"])
            blocos[str(int(ano))] = {
                "totalMun": [round(float(x), 2) for x in tot],
                # zerado de proposito: Transferencia Especial e' instrumento
                # federal e nao existe no orcamento estadual
                "totalPix": [0.0] * n,
                "fichas": fichas[:TOP_AUTORES],
                "partidos": [],
                "pleito": {
                    "pago": round(float(ga["valor"].sum()), 2),
                    "emp": round(float(ga["valor"].sum()), 2),
                    "nAutores": int(ga["autor_norm"].nunique()),
                    "nEmendas": int(ga["emenda"].nunique()) if "emenda" in ga else len(ga),
                    "nMun": int(ga["cod_ibge"].nunique()),
                    "pix": 0.0, "nPix": 0,
                    "cortados": max(0, len(fichas) - TOP_AUTORES),
                },
            }

        todo = pd.read_csv(fonte, low_memory=False)
        todo = todo[todo["valor"].notna() & (todo["valor"] > 0)]
        obj = {"anos": blocos, "esfera": "estadual",
               "cobertura": {"pago": round(float(todo["valor"].sum()), 2),
                             "pagoMun": round(float(d["valor"].sum()), 2),
                             "pix": 0.0, "pixMun": 0.0}}
        f = WEB / uf / "emendas_estadual.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
        casados = sum(1 for b in blocos.values() for x in b["fichas"] if x["el"])
        total_f = sum(len(b["fichas"]) for b in blocos.values())
        feito.append(uf)
        print(f"  {uf}: {len(blocos)} exercícios, {f.stat().st_size/1024:.0f} KB")
        print(f"     R$ {d['valor'].sum()/1e6:.0f} mi em {d['cod_ibge'].nunique()} "
              f"municípios | fichas casadas com eleito: {casados}/{total_f}")

    print(f"\nemendas_estadual.json em {len(feito)} UF(s): {', '.join(feito) or '—'}")
    if feito:
        print("O seletor de esfera só aparece nessas; nas outras o Emendômetro "
              "segue só federal.")


if __name__ == "__main__":
    main()
