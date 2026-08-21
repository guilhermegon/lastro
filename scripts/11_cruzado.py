"""Ondas e sinergias entre estadual, federal e Senado.

Tres perguntas, tres medidas:

1. ONDA - cada cargo tem uma escala natural de disputa? Compara concentracao
   territorial entre os tres. A hipotese e' que a eleicao majoritaria (Senado)
   se decide por movimento estadual uniforme, e a proporcional por base local.
   A medida e' o mesmo numero efetivo de municipios ja usado no painel.

2. SINERGIA (dobradinha) - pares estadual/federal cujo mapa municipal e'
   praticamente o mesmo. E' o indicio classico de campanha casada dividindo a
   mesma maquina local. Cosseno entre os vetores, com corte de votacao para
   evitar ruido.

3. ARRASTO - a votacao de um cargo prediz a do outro no mesmo municipio? Mede
   pela correlacao, dentro de cada partido e ano, entre a fatia municipal do
   partido no estadual e no federal. Alto = maquina coordenada; baixo = as duas
   disputas correm soltas uma da outra.

Cuidado que o script toma: dobradinha nao e' provada por sobreposicao. Dois
candidatos da mesma regiao tem mapas parecidos mesmo sem combinacao nenhuma.
Por isso o resultado sempre reporta se o par e' do mesmo partido ou nao, e a
comparacao relevante e' contra a sobreposicao tipica entre candidatos quaisquer
daquele ano - que o script calcula como linha de base.
"""
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

MIN_VOTOS = 3000       # corte para entrar nas comparacoes de par
TOP_PARES = 25


def sfx(cargo):
    return "" if cargo == "estadual" else f"_{cargo}"


def carregar(cargo):
    return (pd.read_csv(cfg.PROCESSED / f"fato_votos{sfx(cargo)}.csv",
                        dtype={"cod_ibge": str}),
            pd.read_csv(cfg.PROCESSED / f"metricas_candidato{sfx(cargo)}.csv"))


def matriz(fato, met, codigos, pos):
    idx = {sq: i for i, sq in enumerate(met["sq_candidato"])}
    M = np.zeros((len(met), len(codigos)))
    sub = fato[fato["sq_candidato"].isin(idx)]
    for r in sub.itertuples():
        M[idx[r.sq_candidato], pos[r.cod_ibge]] = r.votos
    return M


def normalizar_linhas(M):
    n = np.linalg.norm(M, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return M / n


def main():
    mun = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype={"cod_ibge": str})
    codigos = sorted(mun["cod_ibge"])
    pos = {c: i for i, c in enumerate(codigos)}
    nomes = dict(zip(mun["cod_ibge"], mun["nome"]))

    dados = {}
    for c in cfg.CARGOS.values():
        try:
            dados[c] = carregar(c)
        except FileNotFoundError:
            print(f"[{c}] sem tabelas processadas - fora da comparacao")

    # ---------- 1. onda: escala de disputa por cargo ----------
    print("=" * 78)
    print("1. ESCALA DA DISPUTA - municipios efetivos dos ELEITOS, por cargo")
    print("=" * 78)
    escala = []
    for cargo, (_, met) in dados.items():
        # Nos majoritarios "eleito" pode ser 0 (presidente em 2006 e 2010, sem
        # resultado no arquivo do TSE) ou referir-se ao vencedor NACIONAL, que
        # nao e' quem Goias elegeu. O perfil comparavel aqui e' o do mais votado
        # no estado, sempre definido.
        if cargo in cfg.CARGOS_MAJORITARIOS and "venceu_go" in met.columns:
            el = met[met["venceu_go"]]
        else:
            el = met[met["eleito"]]
        for ano, g in el.groupby("ano"):
            escala.append({
                "cargo": cargo, "ano": ano, "n_eleitos": len(g),
                "mun_efetivo": round(float(g["n_municipios_efetivo"].median()), 2),
                "top1_share": round(float(g["top1_share"].median()), 2),
                "n_municipios": round(float(g["n_municipios"].median()), 1),
                "dominancia": round(float(g["dominancia_ponderada"].median()), 2),
            })
    esc = pd.DataFrame(escala)
    print(esc.pivot(index="ano", columns="cargo", values="mun_efetivo").to_string())
    print("\ntop1_share mediano (fatia do maior municipio):")
    print(esc.pivot(index="ano", columns="cargo", values="top1_share").to_string())
    esc.to_csv(cfg.PROCESSED / "cruz_escala.csv", index=False, encoding="utf-8")

    # ---------- 2. sinergia: pares entre cargos ----------
    print("\n" + "=" * 78)
    print("2. SINERGIA - pares estadual/federal com mapa quase igual")
    print("=" * 78)
    pares = []
    linhas_base = []
    for ano in cfg.ANOS:
        blocos = {}
        for cargo, (fato, met) in dados.items():
            m = met[(met["ano"] == ano) & (met["votos_total"] >= MIN_VOTOS)].copy()
            if m.empty:
                continue
            m = m.reset_index(drop=True)
            f = fato[fato["ano"] == ano]
            blocos[cargo] = (m, normalizar_linhas(matriz(f, m, codigos, pos)),
                             matriz(f, m, codigos, pos))

        combinacoes = [("estadual", "federal"), ("estadual", "senador"),
                       ("estadual", "governador"), ("federal", "governador"),
                       ("federal", "senador"), ("governador", "presidente"),
                       ("estadual", "presidente")]
        for a, b in combinacoes:
            if a not in blocos or b not in blocos:
                continue
            (ma, Ua, Ma), (mb, Ub, Mb) = blocos[a], blocos[b]
            if not len(ma) or not len(mb):
                continue
            S = Ua @ Ub.T
            linhas_base.append({"ano": ano, "par": f"{a}x{b}",
                                "base_mediana": round(float(np.median(S)), 4),
                                "n_a": len(ma), "n_b": len(mb)})
            if a != "estadual" or b != "federal":
                continue
            for i in range(len(ma)):
                j = int(np.argmax(S[i]))
                contato = Ma[i] * (Mb[j] / max(Mb[j].sum(), 1))
                top = np.argsort(-contato)[:3]
                pares.append({
                    "ano": ano,
                    "estadual": ma["nome_urna"].iloc[i],
                    "est_partido": ma["sigla_partido"].iloc[i],
                    "est_eleito": bool(ma["eleito"].iloc[i]),
                    "est_votos": int(ma["votos_total"].iloc[i]),
                    "federal": mb["nome_urna"].iloc[j],
                    "fed_partido": mb["sigla_partido"].iloc[j],
                    "fed_eleito": bool(mb["eleito"].iloc[j]),
                    "fed_votos": int(mb["votos_total"].iloc[j]),
                    "mesmo_partido": bool(ma["partido_norm"].iloc[i] ==
                                          mb["partido_norm"].iloc[j]),
                    "afinidade": round(float(S[i, j]), 4),
                    "municipios": " | ".join(nomes[codigos[k]] for k in top
                                             if contato[k] > 0),
                })
    par = pd.DataFrame(pares)
    base = pd.DataFrame(linhas_base)
    par.to_csv(cfg.PROCESSED / "cruz_dobradinhas.csv", index=False, encoding="utf-8")
    base.to_csv(cfg.PROCESSED / "cruz_base.csv", index=False, encoding="utf-8")

    print("\nsobreposicao TIPICA entre dois candidatos quaisquer (mediana):")
    print(base.pivot(index="ano", columns="par", values="base_mediana").to_string())

    print("\nafinidade do melhor par de cada estadual, mediana por ano:")
    print(par.groupby("ano")["afinidade"].median().round(4).to_string())

    print("\nquantos dos melhores pares sao do MESMO partido:")
    q = par.groupby("ano")["mesmo_partido"].agg(["sum", "size"])
    q["pct"] = (q["sum"] / q["size"] * 100).round(1)
    print(q.to_string())

    print("\n2022 - as dez duplas estadual/federal mais coladas:")
    d = par[par["ano"] == 2022].nlargest(10, "afinidade")
    print(d[["estadual", "est_partido", "federal", "fed_partido", "mesmo_partido",
             "afinidade", "municipios"]].to_string(index=False))

    # ---------- 3. arrasto: o partido anda junto entre os cargos? ----------
    print("\n" + "=" * 78)
    print("3. ARRASTO - a fatia municipal do partido no estadual prediz a do federal?")
    print("=" * 78)
    arr = []
    for ano in cfg.ANOS:
        quadro = {}
        if "estadual" not in dados or "federal" not in dados:
            continue
        for cargo in ("estadual", "federal"):
            fato, met = dados[cargo]
            m = met[met["ano"] == ano][["sq_candidato", "partido_norm"]]
            f = fato[fato["ano"] == ano].merge(m, on="sq_candidato")
            g = f.groupby(["partido_norm", "cod_ibge"], as_index=False)["votos"].sum()
            tot = g.groupby("cod_ibge")["votos"].transform("sum")
            g["fatia"] = g["votos"] / tot
            quadro[cargo] = g
        j = quadro["estadual"].merge(quadro["federal"], on=["partido_norm", "cod_ibge"],
                                     suffixes=("_est", "_fed"))
        for part, g in j.groupby("partido_norm"):
            if len(g) < 30 or g["fatia_est"].std() == 0 or g["fatia_fed"].std() == 0:
                continue
            arr.append({"ano": ano, "partido": part, "n_municipios": len(g),
                        "correlacao": round(float(np.corrcoef(
                            g["fatia_est"], g["fatia_fed"])[0, 1]), 3)})
    a = pd.DataFrame(arr)
    a.to_csv(cfg.PROCESSED / "cruz_arrasto.csv", index=False, encoding="utf-8")
    print("\ncorrelacao mediana entre partidos, por ano:")
    print(a.groupby("ano")["correlacao"].median().round(3).to_string())
    print("\n2022, partidos com mais municipios:")
    print(a[a["ano"] == 2022].nlargest(10, "n_municipios").to_string(index=False))


if __name__ == "__main__":
    main()
