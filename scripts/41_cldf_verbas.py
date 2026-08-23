"""Verba indenizatoria dos deputados distritais, e a comparacao com Goias.

Fonte: `dados.cl.df.gov.br`, conjunto "Verbas Indenizatorias" da Camara
Legislativa do DF, em CKAN. Um CSV por ano, 2019 a 2026 — mesmo periodo que a
serie da ALEGO, o que torna a comparacao possivel.

**As duas casas publicam a mesma verba em graos diferentes, e isso decide o que
da' para comparar e o que nao da'.**

    ALEGO   total por deputado e por mes, com `valor_apresentado` e
            `valor_indenizado` — a diferenca revela a GLOSA
    CLDF    nota a nota, com fornecedor, CNPJ, data e classificacao — revela
            NO QUE o dinheiro e' gasto

Glosa nao existe no DF (so' ha o valor pago) e classificacao de despesa nao
existe em Goias. Cada casa responde uma pergunta que a outra nao responde, e
somar as duas seria inventar um dado que nenhuma publica.

**Duas ressalvas medidas, e a segunda mata a comparacao por deputado:**

1. **68,3% do valor nao tem classificacao.** A tabela de "no que gasta" fala de
   31,7% do dinheiro, e a tela precisa dizer isso — senao insinua uma cobertura
   que nao tem. As categorias tambem chegam com grafia dupla ("Locacao de
   Veiculos" e "Locacao de Veiculo"), e sao normalizadas aqui.

2. **A CLDF tem 24 distritais, e o arquivo traz de 13 a 26 por ano.** Em 2024
   sao tres. Nao e' rotatividade: e' publicacao parcial. Logo **nao da' para
   comparar o gasto medio por deputado com Goias** — a mediana sairia de um
   subconjunto que muda de tamanho todo ano, e a diferenca de 3x que aparece no
   calculo ingenuo seria artefato, nao achado. A comparacao fica de fora ate'
   que a cobertura seja explicada.

Como o dado e' por comprovante, contagem de linha tambem nao mede nada: um
deputado com muitas notas pequenas aparece com muitas linhas.
"""
import io
import json
import re
import subprocess
import sys
import unicodedata
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

PACOTE = "verbas-indenizatorias"
API = f"https://dados.cl.df.gov.br/api/3/action/package_show?id={PACOTE}"
SAIDA = cfg.PROCESSED / "cldf_verbas.csv"
WEB = cfg.PROCESSED / "web" / "DF"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def chave_pessoa(t):
    """O DF prefixa "Deputado"/"Deputada" no nome; Goias nao prefixa."""
    return re.sub(r"^(DEP\.?|DEPUTAD[OA])\s+", "", sem_acento(t)).strip()


def curl(url):
    for _ in range(3):
        r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "180",
                            "-H", f"User-Agent: {UA}", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
    return b""


def dinheiro(s):
    t = s.astype(str).str.strip().str.replace("R$", "", regex=False)
    br = t.str.contains(r",\d{1,4}$", regex=True, na=False)
    t = t.where(~br, t.str.replace(".", "", regex=False)
                      .str.replace(",", ".", regex=False))
    t = t.where(br, t.str.replace(",", "", regex=False))
    return pd.to_numeric(t, errors="coerce").fillna(0.0)


def main():
    raw = curl(API)
    if not raw:
        raise SystemExit("o portal do DF não respondeu")
    pk = json.loads(raw)["result"]
    # so' CSV: o XLSX repete o mesmo ano e entraria somando duas vezes
    recs = []
    for r in pk.get("resources", []):
        if (r.get("format") or "").upper() != "CSV":
            continue
        nome = r.get("name") or ""
        m = re.search(r"(20\d\d)", nome)
        if not m:
            continue
        recs.append((int(m.group(1)), nome, r["url"]))
    # quando o mesmo ano tem dois CSVs (ano fechado e parcial), fica o maior
    por_ano = {}
    for ano, nome, url in recs:
        buf = curl(url)
        if not buf:
            print(f"  {ano}: download falhou"); continue
        if ano not in por_ano or len(buf) > len(por_ano[ano][1]):
            por_ano[ano] = (nome, buf)

    partes = []
    print(f"{'ano':<7}{'arquivo':<40}{'linhas':>9}{'deputados':>11}")
    for ano in sorted(por_ano):
        nome, buf = por_ano[ano]
        d = None
        for enc in ("utf-8-sig", "latin-1"):
            try:
                d = pd.read_csv(io.BytesIO(buf), sep=";", encoding=enc,
                                dtype=str, on_bad_lines="skip", low_memory=False)
                break
            except Exception:
                continue
        if d is None or "NOME_PARLAMENTAR" not in [c.strip() for c in d.columns]:
            print(f"{ano:<7}{nome[:39]:<40}{'sem coluna de parlamentar':>20}")
            continue
        d.columns = [c.strip() for c in d.columns]
        out = pd.DataFrame({
            "ano": ano,
            "deputado": d["NOME_PARLAMENTAR"].astype(str).str.strip(),
            "fornecedor": d.get("NOME_PRESTADOR", pd.Series([""] * len(d))).astype(str).str.strip(),
            "classificacao": d.get("CLASSIFICACAO", pd.Series([""] * len(d))).astype(str).str.strip(),
            "data": d.get("DATA_COMPROVANTE", pd.Series([""] * len(d))).astype(str),
            "valor": dinheiro(d.get("VALOR_DESPESA", pd.Series(["0"] * len(d)))),
        })
        out = out[out["deputado"].str.len() > 2]
        out = out[out["valor"] > 0]
        print(f"{ano:<7}{nome[:39]:<40}{len(out):>9,}{out['deputado'].nunique():>11}")
        partes.append(out)

    if not partes:
        raise SystemExit("nenhum ano utilizável")
    df = pd.concat(partes, ignore_index=True)
    df["chave"] = df["deputado"].map(chave_pessoa)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, index=False, encoding="utf-8")

    print(f"\n{len(df):,} comprovantes | {df['chave'].nunique()} deputados | "
          f"{int(df['ano'].min())}–{int(df['ano'].max())} | "
          f"R$ {df['valor'].sum()/1e6:.1f} mi")

    por_dep = (df.groupby(["chave", "deputado"], as_index=False)
               .agg(total=("valor", "sum"), notas=("valor", "size"),
                    anos=("ano", "nunique")))
    por_dep["media"] = por_dep["total"] / por_dep["anos"].replace(0, 1) / 12
    por_dep = por_dep.sort_values("total", ascending=False)

    # grafia dupla no mesmo arquivo: normalizar antes de agrupar
    df["cat"] = df["classificacao"].map(sem_acento)
    semcat = df["cat"].isin(("", "NAN"))
    df.loc[semcat, "cat"] = ""
    cat = (df[~semcat].groupby("cat", as_index=False)
           .agg(valor=("valor", "sum"), n=("valor", "size"))
           .sort_values("valor", ascending=False))
    vsem = float(df.loc[semcat, "valor"].sum())

    obj = {
        "fonte": "CKAN da Câmara Legislativa do DF, verbas-indenizatorias",
        "periodo": [int(df["ano"].min()), int(df["ano"].max())],
        "grao": "comprovante",
        "total": {"valor": round(float(df["valor"].sum()), 2),
                  "notas": int(len(df)),
                  "nDeputados": int(df["chave"].nunique()),
                  # o denominador da tabela de categorias viaja junto
                  "semCategoria": round(vsem, 2),
                  "pctSemCategoria": round(vsem / float(df["valor"].sum()) * 100, 1)},
        # a Casa tem 24 distritais; o arquivo traz de 13 a 26 por ano
        "cobertura": [{"ano": int(a), "deputados": int(g["chave"].nunique())}
                      for a, g in df.groupby("ano")],
        "comparavel": False,
        "serie": [{"ano": int(a), "valor": round(float(g["valor"].sum()), 2),
                   "notas": int(len(g)), "deputados": int(g["chave"].nunique())}
                  for a, g in df.groupby("ano")],
        "categorias": [{"n": str(r.cat)[:44],
                        "v": round(float(r.valor), 2), "q": int(r.n)}
                      for r in cat.head(14).itertuples()],
        "deputados": [{"n": r.deputado, "t": round(float(r.total), 2),
                       "m": round(float(r.media), 2), "q": int(r.notas),
                       "a": int(r.anos)}
                      for r in por_dep.itertuples()],
    }
    WEB.mkdir(parents=True, exist_ok=True)
    p = WEB / "cldf_verbas.json"
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")
    print(f"{p.name}: {p.stat().st_size/1024:.0f} KB")

    tot = float(df["valor"].sum())
    print("")
    print(f"sem classificacao: R$ {vsem/1e6:.2f} mi ({vsem/tot*100:.1f}% do valor)")
    print("=== no que o DF gasta, entre o que E' classificado ===")
    for r in cat.head(8).itertuples():
        print(f"   {str(r.cat)[:36]:<38}"
              f"R$ {r.valor/1e6:>5.2f} mi  {r.valor/(tot-vsem)*100:>5.1f}%  "
              f"{r.n:>6,} notas")

    print("")
    print("=== por que NAO comparamos o gasto por deputado com Goias ===")
    cob = df.groupby("ano")["chave"].nunique()
    print(f"   a CLDF tem 24 distritais; o arquivo traz de {cob.min()} a "
          f"{cob.max()} por ano")
    print("   " + ", ".join(f"{a}:{n}" for a, n in cob.items()))
    print("   Isso nao e' rotatividade, e' publicacao parcial. Uma mediana por")
    print("   deputado sairia de subconjunto que muda de tamanho todo ano, e a")
    print("   diferenca do calculo ingenuo seria artefato, nao achado.")


if __name__ == "__main__":
    main()
