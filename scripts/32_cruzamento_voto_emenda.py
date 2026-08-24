"""O deputado manda emenda para onde tirou voto?

Cruza, por municipio, o mapa de VOTO de cada deputado federal eleito com o mapa
de EMENDA individual do mandato que aquela eleicao abriu:

    eleito em 2014  ->  exercicios 2015 a 2018
    eleito em 2018  ->  exercicios 2019 a 2022
    eleito em 2022  ->  exercicios 2023 a 2026

**A armadilha, e por que a medida ingenua nao serve.** Goiania recebe muito voto
E muita emenda de quase todo deputado goiano, porque e' grande. Qualquer medida
de sobreposicao entre os dois mapas sai alta para todo mundo, e o numero
diria "os deputados mandam dinheiro para onde tem voto" quando esta dizendo
"cidade grande e' grande nas duas contas".

**A correcao e' uma linha de base pareada.** Para cada deputado calculamos:

  observado   fatia da emenda DELE que caiu nos municipios onde ELE mais votou
  nulo        a mesma fatia, medida contra o reduto de CADA OUTRO deputado da
              mesma UF e do mesmo pleito - a mediana dessas medidas
  excesso     observado menos nulo

O nulo carrega o efeito do tamanho da cidade por construcao: se a emenda vai
para as cidades grandes por serem grandes, ela cai no reduto dos outros tambem,
e o excesso vai a zero. So' sobra excesso se o dinheiro seguiu **aquele** mapa
de voto em particular.

**O denominador que nao pode sumir.** So' 10,5% do dinheiro de emenda individual
e' rastreavel ate' um municipio (ver TKT-0005). Este cruzamento fala do que e'
rastreavel, e o arquivo carrega quanto isso representa para cada deputado - sem
esse numero ao lado, o resultado insinua uma cobertura que nao tem.
"""
import json
import sys
import unicodedata
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

WEB = cfg.PROCESSED / "web"
EMENDAS = cfg.PROCESSED / "emendas.csv"
# eleicao -> exercicios do mandato que ela abriu
MANDATO = {2014: (2015, 2018), 2018: (2019, 2022), 2022: (2023, 2026)}
TOP_REDUTO = 10      # quantos municipios de maior votacao contam como "reduto"
MIN_EMENDA = 200_000  # abaixo disso a carteira municipal e' anedota, nao padrao
# Municipios minimos para o par entrar na afericao. Com um municipio so', a
# medida so' pode dar 0% ou 100% e o resultado vira ruido de denominador -
# 17% dos pares estavam nesse caso. O `nm` continua em cada linha para a tela
# poder apertar mais.
MIN_MUNICIPIOS = 3


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def fatia_no_reduto(emenda, reduto):
    """Fracao do dinheiro de `emenda` que caiu nos indices de `reduto`."""
    tot = emenda.sum()
    if tot <= 0:
        return None
    return float(emenda[reduto].sum() / tot)


def main():
    if not EMENDAS.exists():
        raise SystemExit("rode 30_emendas_ingest.py antes")
    em = pd.read_csv(EMENDAS, dtype={"cod_ibge": str}, low_memory=False)
    em = em[em["individual"].astype(str).str.lower().isin(("true", "1"))]
    em = em[em["cod_ibge"].notna()]
    em["ano"] = pd.to_numeric(em["ano"], errors="coerce")

    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    idx, nomes = {}, {}
    for uf, g in dim.groupby("uf"):
        g = g.sort_values("cod_ibge")
        idx[uf] = {c: i for i, c in enumerate(g["cod_ibge"])}
        nomes[uf] = list(g["nome"])

    # quanto de emenda cada autor teve no total, para declarar a cobertura
    total_autor = (pd.read_csv(EMENDAS, low_memory=False)
                   .pipe(lambda d: d[d["individual"].astype(str).str.lower()
                                     .isin(("true", "1"))])
                   .groupby(em["autor_norm"].name if False else "autor_norm")["pago"]
                   .sum().to_dict())

    resumo, por_uf = [], {}
    for p in sorted(WEB.glob("*/federal.json")):
        uf = p.parent.name
        if uf not in idx:
            continue
        n = len(nomes[uf])
        pos = idx[uf]
        federal = json.loads(p.read_text(encoding="utf-8"))
        linhas = []

        for ano_str, bloco in federal.items():
            ano = int(ano_str)
            if ano not in MANDATO:
                continue
            de, ate = MANDATO[ano]
            jan = em[(em["uf"] == uf) & (em["ano"] >= de) & (em["ano"] <= ate)]
            if jan.empty:
                continue
            por_autor = {a: g for a, g in jan.groupby("autor_norm")}

            eleitos = [f for f in bloco["fichas"] if f.get("el")]
            if len(eleitos) < 3:
                continue

            # vetor de voto e reduto de cada eleito, uma vez so'
            fichas = []
            for f in eleitos:
                v = np.zeros(n)
                for i, x in zip(f["mi"], f["mv"]):
                    v[i] = x
                if v.sum() <= 0:
                    continue
                red = np.argsort(-v)[:TOP_REDUTO]
                fichas.append({"f": f, "v": v, "red": red,
                               "chave": sem_acento(f["n"]),
                               "completo": sem_acento(f.get("completo", ""))})

            for a in fichas:
                g = por_autor.get(a["chave"])
                if g is None:
                    g = por_autor.get(a["completo"])
                if g is None or g.empty:
                    continue
                e = np.zeros(n)
                for c, val in g.groupby("cod_ibge")["pago"].sum().items():
                    if c in pos:
                        e[pos[c]] = val
                if e.sum() < MIN_EMENDA:
                    continue

                obs = fatia_no_reduto(e, a["red"])
                # a linha de base: o MESMO dinheiro medido contra o reduto dos
                # outros. E' isto que desconta o tamanho da cidade.
                outros = [fatia_no_reduto(e, b["red"]) for b in fichas
                          if b is not a]
                outros = [x for x in outros if x is not None]
                if obs is None or len(outros) < 2:
                    continue
                nulo = float(np.median(outros))
                tot_aut = float(total_autor.get(a["chave"], 0.0))
                linhas.append({
                    "ano": ano, "n": a["f"]["n"], "p": a["f"]["p"],
                    "obs": round(obs * 100, 2),
                    "nulo": round(nulo * 100, 2),
                    "exc": round((obs - nulo) * 100, 2),
                    "emenda": round(float(e.sum()), 2),
                    "nm": int((e > 0).sum()),
                    # a cobertura DESTE deputado: quanto do dinheiro dele
                    # chegou a ser rastreado ate' um municipio
                    "cob": round(float(e.sum()) / tot_aut * 100, 1) if tot_aut else None,
                    "reduto": nomes[uf][int(a["red"][0])],
                })

        if linhas:
            linhas.sort(key=lambda r: -r["exc"])
            por_uf[uf] = linhas
            for r in linhas:
                resumo.append({**r, "uf": uf})

    if not resumo:
        raise SystemExit("nenhum cruzamento — confira 30_ e os arquivos federais")

    df = pd.DataFrame(resumo)

    def afere(g):
        if len(g) < 3:
            return None
        return {"n": len(g),
                "obs": round(float(np.median([r["obs"] for r in g])), 2),
                "nulo": round(float(np.median([r["nulo"] for r in g])), 2),
                "exc": round(float(np.median([r["exc"] for r in g])), 2),
                "pond": round(float(np.average([r["exc"] for r in g],
                                               weights=[r["emenda"] for r in g])), 2),
                "acima": int(sum(1 for r in g if r["exc"] > 0)),
                "cob": round(float(np.median([r["cob"] for r in g
                                              if r["cob"] is not None] or [0])), 1)}

    # A escada de robustez, gravada junto: se o efeito fosse artefato de
    # denominador pequeno, ele encolheria ao exigir mais municipios. Ele cresce.
    escada = []
    for corte in (1, 3, 5, 10):
        a = afere([r for r in resumo if r["nm"] >= corte])
        if a:
            escada.append({"minMun": corte, **a})

    for uf, linhas in por_uf.items():
        firmes = [r for r in linhas if r["nm"] >= MIN_MUNICIPIOS]
        obj = {"deputados": linhas,
               "afericao": afere(firmes) or afere(linhas) or {"n": 0},
               "minMun": MIN_MUNICIPIOS, "topReduto": TOP_REDUTO,
               "escada": escada}
        f = WEB / uf / "voto_emenda.json"
        f.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")

    print(f"{len(df):,} pares deputado/mandato em {df['uf'].nunique()} UFs\n")
    print("=== o dinheiro segue o voto? mediana por pleito ===")
    print(f"{'pleito':<8}{'n':>5}{'observado':>11}{'nulo':>9}{'excesso':>10}{'acima de zero':>15}")
    for ano, g in df.groupby("ano"):
        print(f"{ano:<8}{len(g):>5}{g['obs'].median():>10.1f}%{g['nulo'].median():>8.1f}%"
              f"{g['exc'].median():>+9.1f} pp", f"{(g['exc'] > 0).sum():>7} de {len(g)}")
    print(f"\nno conjunto: mediana do excesso {df['exc'].median():+.1f} pp, "
          f"positivo em {(df['exc']>0).sum():,} de {len(df):,} casos")
    print(f"cobertura mediana do dinheiro rastreado por deputado: "
          f"{df['cob'].median():.1f}%")
    print("\n=== os dez maiores excessos ===")
    d = df.nlargest(10, "exc")
    print(f"{'UF':<4}{'deputado':<24}{'pleito':>7}{'obs':>7}{'nulo':>7}{'exc':>8}  reduto")
    for r in d.itertuples():
        print(f"{r.uf:<4}{r.n[:23]:<24}{r.ano:>7}{r.obs:>6.0f}%{r.nulo:>6.0f}%"
              f"{r.exc:>+7.0f}pp  {r.reduto[:22]}")


if __name__ == "__main__":
    main()
