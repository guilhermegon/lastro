"""Piloto da API da ALEGO: verba indenizatoria dos deputados de Goias.

Fonte: `transparencia.al.go.leg.br/api/transparencia/verbas_indenizatorias.json`,
com parametros `ano`, `mes` e `todos=true`. E' o "cotao" — reembolso de despesa
de gabinete — de cada um dos 41 deputados, mes a mes, de 2019 a 2026.

**Por que este assunto entre os dezesseis da API.** E' o unico que junta tres
coisas de uma vez: e' por deputado (nao por orgao), e' mensal (serie longa), e
tem um par de valores que revela decisao administrativa —
`valor_apresentado` e `valor_indenizado`. A diferenca e' o que foi **glosado**:
despesa que o deputado pediu e a Casa recusou. Isso nao e' publicado como
indicador em lugar nenhum, e sai de graca desta subtracao.

**O que ele NAO e'.** Verba indenizatoria nao e' salario nem emenda. E' custeio
de gabinete. Somar com emenda seria misturar dinheiro do orcamento do Executivo
com reembolso da propria Casa — coisas de natureza diferente, e a tela diz isso.

O campo `deputado` vem aninhado (`{id, nome}`) e chega como texto com aspas
simples, nao como JSON valido dentro do JSON. E' desembrulhado aqui.
"""
import ast
import json
import re
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

BASE = ("https://transparencia.al.go.leg.br/api/transparencia/"
        "verbas_indenizatorias.json")
ANOS = range(2019, 2027)
SAIDA = cfg.PROCESSED / "alego_verbas.csv"
WEB = cfg.PROCESSED / "web" / "GO"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
FALHAS = []


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def chave_pessoa(t):
    return re.sub(r"^(DEP\.?|DEPUTAD[OA])\s+", "", sem_acento(t)).strip()


def buscar(par):
    """Tres tentativas antes de desistir.

    Sem isso a varredura devolvia zero para 2022 e 2023 inteiros — e eu ja
    tinha testado 2023/02 a mao, com 41 registros. Falha de requisicao lida
    como ausencia de dado e' o pior tipo de erro que este projeto comete: nao
    parece erro, parece resultado.
    """
    ano, mes = par
    url = f"{BASE}?ano={ano}&mes={mes}&todos=true"
    d = None
    for _ in range(3):
        r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "120",
                            "-H", f"User-Agent: {UA}", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            try:
                d = json.loads(r.stdout)
                break
            except json.JSONDecodeError:
                d = None
    if d is None:
        FALHAS.append((ano, mes))
        return []
    itens = d if isinstance(d, list) else next(
        (v for v in d.values() if isinstance(v, list)), [])
    fora = []
    for x in itens:
        dep = x.get("deputado")
        # chega como texto de dict Python, com aspas simples — json.loads nao le
        if isinstance(dep, str):
            try:
                dep = ast.literal_eval(dep)
            except (ValueError, SyntaxError):
                dep = {}
        if not isinstance(dep, dict):
            dep = {}
        fora.append({
            "ano": int(x.get("ano") or ano),
            "mes": int(x.get("mes") or mes),
            "dep_id": dep.get("id"),
            "deputado": str(dep.get("nome") or "").strip(),
            "apresentado": pd.to_numeric(x.get("valor_apresentado"),
                                         errors="coerce"),
            "indenizado": pd.to_numeric(x.get("valor_indenizado"),
                                        errors="coerce"),
        })
    return fora


def main():
    pares = [(a, m) for a in ANOS for m in range(1, 13)]
    print(f"buscando {len(pares)} meses na API da ALEGO...", flush=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        blocos = list(ex.map(buscar, pares))
    linhas = [x for b in blocos for x in b]
    if not linhas:
        raise SystemExit("a API não devolveu nada")

    df = pd.DataFrame(linhas)
    df = df[df["deputado"].str.len() > 2]
    df["apresentado"] = df["apresentado"].fillna(0.0)
    df["indenizado"] = df["indenizado"].fillna(0.0)
    # glosa: o que foi pedido e a Casa recusou. Nunca negativa — quando o
    # indenizado passa o apresentado (acontece em acerto retroativo), e' zero.
    df["glosa"] = (df["apresentado"] - df["indenizado"]).clip(lower=0)
    df["chave"] = df["deputado"].map(chave_pessoa)

    if FALHAS:
        print(f"  {len(FALHAS)} meses falharam em 3 tentativas: "
              + ", ".join(f"{a}/{m:02d}" for a, m in sorted(FALHAS)[:12]))
    meses = df.groupby(["ano", "mes"]).size()
    print(f"{len(df):,} registros | {df['deputado'].nunique()} deputados | "
          f"{len(meses)} meses com dado, de {df['ano'].min()} a {df['ano'].max()}")
    print(f"apresentado R$ {df['apresentado'].sum()/1e6:.1f} mi | "
          f"indenizado R$ {df['indenizado'].sum()/1e6:.1f} mi | "
          f"glosado R$ {df['glosa'].sum()/1e6:.2f} mi "
          f"({df['glosa'].sum()/df['apresentado'].sum()*100:.2f}%)")

    # ---- casamento com quem foi eleito, para ligar ao mapa de voto ----
    f = WEB / "estadual.json"
    eleitos = {}
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        for ano, b in d.items():
            for ficha in b["fichas"]:
                if not ficha.get("el"):
                    continue
                for k in {chave_pessoa(ficha["n"]),
                          chave_pessoa(ficha.get("completo", ""))}:
                    if k:
                        eleitos.setdefault(k, {"anos": set(), "ef": ficha.get("ef"),
                                               "t": ficha.get("t")})
                        eleitos[k]["anos"].add(int(ano))
    df["eleito"] = df["chave"].isin(eleitos)
    casou = df.loc[df["eleito"], "chave"].nunique()
    print(f"casam com eleito à ALEGO: {casou} de {df['chave'].nunique()} "
          f"({casou/df['chave'].nunique()*100:.0f}%)")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, index=False, encoding="utf-8")

    # ---- agregado para a tela ----
    por_dep = (df.groupby(["chave", "deputado"], as_index=False)
               .agg(indenizado=("indenizado", "sum"),
                    apresentado=("apresentado", "sum"),
                    glosa=("glosa", "sum"), meses=("mes", "size")))
    por_dep["pctGlosa"] = (por_dep["glosa"] / por_dep["apresentado"].replace(0, 1) * 100)
    por_dep["media"] = por_dep["indenizado"] / por_dep["meses"].replace(0, 1)
    por_dep["eleito"] = por_dep["chave"].isin(eleitos)
    por_dep = por_dep.sort_values("indenizado", ascending=False)

    serie = (df.groupby("ano", as_index=False)
             .agg(indenizado=("indenizado", "sum"), glosa=("glosa", "sum"),
                  deputados=("chave", "nunique"), meses=("mes", "nunique")))

    obj = {
        "fonte": "API da ALEGO, verbas_indenizatorias",
        "periodo": [int(df["ano"].min()), int(df["ano"].max())],
        "total": {"apresentado": round(float(df["apresentado"].sum()), 2),
                  "indenizado": round(float(df["indenizado"].sum()), 2),
                  "glosa": round(float(df["glosa"].sum()), 2),
                  "nDeputados": int(df["chave"].nunique()),
                  "nCasados": int(casou)},
        "serie": [{"ano": int(r.ano), "indenizado": round(float(r.indenizado), 2),
                   "glosa": round(float(r.glosa), 2),
                   "deputados": int(r.deputados), "meses": int(r.meses)}
                  for r in serie.itertuples()],
        "deputados": [{"n": r.deputado, "t": round(float(r.indenizado), 2),
                       "g": round(float(r.glosa), 2),
                       "pg": round(float(r.pctGlosa), 2),
                       "m": round(float(r.media), 2),
                       "ms": int(r.meses), "el": bool(r.eleito)}
                      for r in por_dep.itertuples()],
    }
    p = WEB / "alego_verbas.json"
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")
    print(f"\n{p.name}: {p.stat().st_size/1024:.0f} KB")

    print("\n=== quem mais recebeu, no período ===")
    t = por_dep.head(8)[["deputado", "indenizado", "media", "pctGlosa", "meses"]].copy()
    t["indenizado"] = "R$ " + (t["indenizado"] / 1000).round(0).astype(int).astype(str) + " mil"
    t["media"] = "R$ " + (t["media"] / 1000).round(1).astype(str) + " mil/mês"
    t["pctGlosa"] = t["pctGlosa"].round(2).astype(str) + "%"
    print(t.to_string(index=False))

    print("\n=== quem mais teve despesa glosada ===")
    g = por_dep[por_dep["meses"] >= 12].nlargest(6, "pctGlosa")
    for r in g.itertuples():
        print(f"   {r.deputado[:30]:<32}{r.pctGlosa:>6.2f}%  "
              f"de R$ {r.apresentado/1000:,.0f} mil apresentados")


if __name__ == "__main__":
    main()
