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
geo = import_module("04_geo")

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


# O que o arquivo escreve quando nao sabe o autor. Nao e' nome de gente.
#
# As formas estao NORMALIZADAS, porque a comparacao acontece depois da chave:
# `chave_pessoa("#N/D")` da' "N D", ja' sem a pontuacao. Escrever "#N/D" aqui
# nunca casaria — foi o que aconteceu na primeira tentativa.
AUSENTE = {"N D", "N A", "NAO INFORMADO", "NAO IDENTIFICADO", "", "NAN"}


def chave_pessoa(t):
    """Chave de pessoa: o normalizador DO PROJETO, sem o titulo de tratamento.

    Usava um `sem_acento` local, que so' tirava acento. Resultado: "DR. GEORGE
    MORAIS" do arquivo da assembleia nao casava com "DR GEORGE MORAIS" do TSE,
    porque um traz ponto e o outro nao. O `04_geo.normalizar` tira pontuacao
    desde sempre — foi escrito para o pareamento de municipios, e e' o mesmo
    problema.

    E' a terceira vez neste projeto que duplicar esta funcao custa pares: antes
    foram SAO JOAO D'ALIANCA no `56_` e as grafias do TSE contra o IBGE. A
    licao: chave de pareamento tem um dono so'.

    O prefixo de tratamento sai porque e' cargo, nao nome: o arquivo do Espirito
    Santo escreve "Dep. Allan Ferreira" e o TSE, "ALLAN FERREIRA".
    """
    return re.sub(r"^(DEP|DEPUTADO|DEPUTADA)\s+", "", geo.normalizar(t)).strip()


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
    por, completos = {}, {}
    for ano, b in d.items():
        for ficha in b["fichas"]:
            if not ficha.get("el"):
                continue
            comp = chave_pessoa(ficha.get("completo", ""))
            for k in {chave_pessoa(ficha["n"]), comp}:
                if k:
                    por.setdefault(k, set()).add(int(ano))
            # o completo entra num indice a parte: e' dele que o arquivo da
            # assembleia recorta o nome do autor (ver `casar_por_recorte`)
            if comp:
                completos.setdefault(comp, {"anos": set(), "urna": ficha["n"]})
                completos[comp]["anos"].add(int(ano))
    return por, completos


def casar_por_recorte(nome, completos):
    """Os tokens do autor aparecem EM ORDEM entre os do nome completo.

    Mesma regra do `30_emendas_ingest.py` no federal, e pelo mesmo motivo: o
    arquivo escreve um recorte do nome completo, que nao e' o de urna nem o
    inteiro. Regra de ESTRUTURA, nunca de semelhanca de texto — par errado nao
    perde dado, poe dado no lugar errado.

    Tres travas: dois tokens no minimo, o ultimo token (sobrenome) obrigatorio
    dentro do completo, e unicidade — recorte que serve a dois nao serve a
    nenhum.
    """
    toks = nome.split()
    if len(toks) < 2:
        return None

    def subseq(pequeno, grande):
        it = iter(grande)
        return all(t in it for t in pequeno)

    achados = []
    for comp, r in completos.items():
        g = comp.split()
        if toks[-1] in g and subseq(toks, g):
            achados.append(r)
    if not achados or len({r["urna"] for r in achados}) > 1:
        return None
    anos = set()
    for r in achados:
        anos |= r["anos"]
    return anos


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
        el, completos = eleitos_estaduais(uf)
        n_recorte = n_ausente = 0

        blocos = {}
        for ano, ga in d.groupby("ano"):
            tot = np.zeros(n)
            for c, v in ga.groupby("cod_ibge")["valor"].sum().items():
                tot[pos[c]] = v

            fichas = []
            for autor, gg in ga.groupby("autor_norm"):
                # "#N/D" e' o marcador de ausencia do arquivo de origem, nao um
                # nome. Publicado como autor, cria um parlamentar que nao
                # existe. O dinheiro continua no total do municipio — ele foi
                # gasto —, so' nao inventa autoria. Sao 13 linhas e R$ 1,04 mi
                # de R$ 4.004 mi em Goias: 0,03%, e nao e' o tamanho que decide.
                if autor in AUSENTE:
                    n_ausente += len(gg)
                    continue
                por_mun = gg.groupby("cod_ibge")["valor"].sum()
                por_mun = por_mun[por_mun > 0]
                if por_mun.empty:
                    continue
                v = por_mun.to_numpy(dtype=float)
                p = v / v.sum()
                anos_el = el.get(autor, set())
                if not anos_el:
                    # segunda passada: recorte do nome completo — ver
                    # `casar_por_recorte`
                    r = casar_por_recorte(autor, completos)
                    if r:
                        anos_el = r
                        n_recorte += 1
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
              f"municípios | fichas casadas com eleito: {casados}/{total_f}"
              + (f", {n_recorte} por recorte do nome" if n_recorte else "")
              + (f" | {n_ausente} linhas sem autor no arquivo, fora da lista"
                 if n_ausente else ""))

    print(f"\nemendas_estadual.json em {len(feito)} UF(s): {', '.join(feito) or '—'}")
    if feito:
        print("O seletor de esfera só aparece nessas; nas outras o Emendômetro "
              "segue só federal.")


if __name__ == "__main__":
    main()
