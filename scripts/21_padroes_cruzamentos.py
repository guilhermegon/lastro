"""Padrões e Cruzamentos por UF, derivados dos arquivos de cargo já gravados.

Lê `web/{UF}/{cargo}.json` e produz dois arquivos pequenos por estado:

  padroes.json      série dos eleitos, tipologia, janela de captura, custo da cadeira
  cruzamentos.json  escala por cargo, arrasto entre cargos, duplas estadual/federal

Por que server-side e não no navegador: as duas análises cruzam cargos, e o front
baixa **um cargo por vez** de propósito. Calcular ali obrigaria a baixar os cinco
arquivos só para desenhar dois gráficos — em São Paulo, 4,9 MB para mostrar uma
tabela. Aqui saem ~15 KB por estado.

Duas ressalvas embutidas nos próprios dados, porque sem elas o número engana:

- **Municípios efetivos não se comparam entre UFs.** Roraima tem 15 municípios e
  Minas 853; um estado com 15 não pode ter 16 efetivos. Por isso vai junto a
  fração do estado ocupada, que é comparável.
- **Semelhança de cosseno não se compara entre escalas.** Sobre 15 municípios ela
  é mecanicamente maior que sobre 853. Serve para ordenar partidos dentro de um
  mesmo estado e pleito, não entre estados.
"""
import json
import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

WEB = cfg.PROCESSED / "web"
CARGOS = ["presidente", "governador", "senador", "federal", "estadual"]
MAJORITARIOS = {"presidente", "governador", "senador"}
CORTES = [0, 2000, 5000, 10000, 15000, 25000, 50000, 10 ** 9]
ROTULOS = ["até 2 mil", "2-5 mil", "5-10 mil", "10-15 mil",
           "15-25 mil", "25-50 mil", "mais de 50 mil"]
MIN_PAR = 3000


def ler(uf, cargo):
    f = WEB / uf / f"{cargo}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def mediana(v):
    return round(float(np.median(v)), 2) if len(v) else None


def faixa_de(total):
    for i in range(1, len(CORTES)):
        if total <= CORTES[i]:
            return i - 1
    return len(ROTULOS) - 1


def vetor(ficha, n):
    v = np.zeros(n)
    for i, x in zip(ficha["mi"], ficha["mv"]):
        v[i] = x
    return v


def padroes(uf, dados, n_mun):
    est = dados.get("estadual", {})
    serie, tipos_por_ano, captura, custo = [], [], [], []

    for ano in map(str, cfg.ANOS):
        d = est.get(ano)
        if not d:
            continue
        el = [f for f in d["fichas"] if f["el"]]
        if not el:
            continue
        serie.append({
            "ano": int(ano),
            "ef": mediana([f["ef"] for f in el]),
            "t1": mediana([f["t1"] for f in el]),
            "dom": mediana([f["dom"] for f in el]),
            "contig": mediana([f["contig"] for f in el]),
            "nm": mediana([f["nm"] for f in el]),
            # fração do estado: é o número comparável entre UFs
            "fr": round(float(np.median([f["ef"] for f in el])) / max(n_mun, 1) * 100, 2),
        })
        cont = defaultdict(int)
        for f in el:
            cont[f["tipo"]] += 1
        tipos_por_ano.append({"ano": int(ano), "tipos": dict(cont), "n": len(el)})

        # janela de captura: fatia do maior candidato por porte do município
        porte = defaultdict(list)
        for m in d["mm"]:
            if m:
                porte[faixa_de(m["tot"])].append(m["t1"])
        captura.append({
            "ano": int(ano),
            "t1": [mediana(porte[i]) for i in range(len(ROTULOS))],
            "n": [len(porte[i]) for i in range(len(ROTULOS))],
        })

        p = d["pleito"]
        custo.append({"ano": int(ano), "cad": p["cadeiras"], "cand": p["nCand"],
                      "tot": p["totalUF"], "qe": p["qe"], "ult": p["ultimo"]})

    return {"serie": serie, "tipologia": tipos_por_ano,
            "captura": {"faixas": ROTULOS, "anos": captura}, "custo": custo}


def cruzamentos(uf, dados, n_mun):
    escala, arrasto, duplas, base = [], [], [], []

    for cargo in CARGOS:
        for ano, d in dados.get(cargo, {}).items():
            # nos majoritários o perfil comparável é o do mais votado no estado,
            # não o do vencedor nacional — que nem sempre é o mesmo
            if cargo in MAJORITARIOS:
                alvo = [f for f in d["fichas"] if f["sq"] == d.get("vencedorUF")]
            else:
                alvo = [f for f in d["fichas"] if f["el"]]
            if not alvo:
                continue
            escala.append({
                "cargo": cargo, "ano": int(ano),
                "ef": mediana([f["ef"] for f in alvo]),
                "t1": mediana([f["t1"] for f in alvo]),
                "fr": round(float(np.median([f["ef"] for f in alvo])) / max(n_mun, 1) * 100, 2),
            })

    # arrasto: a fatia municipal do partido no estadual prevê a do federal?
    for ano in map(str, cfg.ANOS):
        de, df = dados.get("estadual", {}).get(ano), dados.get("federal", {}).get(ano)
        if not de or not df:
            continue
        def por_partido(d):
            # `pm` vem de 19_ e soma TODOS os candidatos do partido. As fichas
            # guardadas nos cargos proporcionais sao so as dos eleitos, e somar
            # so eleitos subestima quem tem muita gente sem se eleger - foi o
            # que fez o PT sair 0,344 aqui contra 0,617 no pipeline de Goias.
            acc = {}
            for nome, esp in d.get("pm", {}).items():
                v = np.zeros(n_mun)
                v[esp["i"]] = esp["v"]
                acc[nome] = v
            if not acc:
                return {}
            tot = np.sum(list(acc.values()), axis=0)
            tot[tot == 0] = 1
            return {p: v / tot for p, v in acc.items()}
        pe, pf = por_partido(de), por_partido(df)
        # Presenca minima. Sem isto o topo do arrasto vira ruido: um partido
        # com voto em 12 municipios facilmente correlaciona 0,73 entre os dois
        # cargos, e apareceria acima do PT sem significar nada. Exigimos
        # presenca em pelo menos metade dos municipios do estado, nos dois
        # cargos. Metade e' o corte: com presenca em 76 de 246, a Unidade
        # Popular correlacionava 0,73 e aparecia acima do PT sem que isso
        # dissesse nada sobre maquina territorial.
        minimo = max(10, n_mun // 2)
        for p in set(pe) & set(pf):
            a, b = pe[p], pf[p]
            presenca = min(int((a > 0).sum()), int((b > 0).sum()))
            if presenca < minimo or a.std() == 0 or b.std() == 0:
                continue
            arrasto.append({"ano": int(ano), "partido": p, "nm": presenca,
                            "r": round(float(np.corrcoef(a, b)[0, 1]), 3)})

    # duplas estadual/federal com mapa quase igual, e a linha de base
    for ano in map(str, cfg.ANOS):
        de, df = dados.get("estadual", {}).get(ano), dados.get("federal", {}).get(ano)
        if not de or not df:
            continue
        fe = [f for f in de["fichas"] if f["t"] >= MIN_PAR]
        ff = [f for f in df["fichas"] if f["t"] >= MIN_PAR]
        if not fe or not ff:
            continue
        A = np.vstack([vetor(f, n_mun) for f in fe])
        B = np.vstack([vetor(f, n_mun) for f in ff])
        na, nb = np.linalg.norm(A, axis=1, keepdims=True), np.linalg.norm(B, axis=1, keepdims=True)
        na[na == 0] = 1; nb[nb == 0] = 1
        S = (A / na) @ (B / nb).T
        base.append({"ano": int(ano), "mediana": round(float(np.median(S)), 4)})
        for i, f in enumerate(fe):
            j = int(np.argmax(S[i]))
            duplas.append({
                "ano": int(ano), "e": f["n"], "ep": f["p"],
                "f": ff[j]["n"], "fp": ff[j]["p"],
                "mp": f["pn"] == ff[j]["pn"],
                "af": round(float(S[i, j]), 4),
            })

    mesmo = []
    for ano in sorted({d["ano"] for d in duplas}):
        g = [d for d in duplas if d["ano"] == ano]
        mesmo.append({"ano": ano, "pct": round(sum(d["mp"] for d in g) / len(g) * 100, 1),
                      "n": len(g)})

    return {"escala": escala, "arrasto": arrasto, "base": base,
            "duplas": sorted(duplas, key=lambda d: -d["af"])[:200],
            "mesmoPartido": mesmo}


def main():
    ufs = sorted(p.name for p in WEB.iterdir() if p.is_dir())
    total = 0
    for uf in ufs:
        base = json.loads((WEB / uf / "base.json").read_text(encoding="utf-8"))
        n = len(base["municipios"])
        dados = {c: ler(uf, c) for c in CARGOS}

        p = padroes(uf, dados, n)
        c = cruzamentos(uf, dados, n)
        for nome, obj in (("padroes", p), ("cruzamentos", c)):
            f = WEB / uf / f"{nome}.json"
            f.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                         encoding="utf-8")
            total += f.stat().st_size
        print(f"  {uf}: padrões {len(p['serie'])} pleitos, "
              f"escala {len(c['escala'])} pontos, arrasto {len(c['arrasto'])} pares",
              flush=True)

    print(f"\ntotal dos dois arquivos em todas as UFs: {total/1024:.0f} KB")


if __name__ == "__main__":
    main()
