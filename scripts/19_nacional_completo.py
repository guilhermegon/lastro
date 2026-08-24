"""Modelo completo de Goias replicado para as 26 UFs, nos cinco cargos.

Produz, por UF:

  {UF}/{cargo}.json   candidatos com vetor municipal, indices, partidos, pleito
  {UF}/padroes.json   serie dos eleitos, tipologia, janela de captura, custo
  {UF}/cruzamentos.json  escala por cargo, arrasto entre cargos, duplas

Restricoes que moldam o desenho:

1. MEMORIA. Sao 4 GB livres e o maior arquivo nacional tem 960 MB em disco. Com
   `usecols` e colunas categoricas ele cai para 0,25 GB, e processamos um par
   (cargo, ano) por vez, guardando so o resultado compacto.

2. TAMANHO NA WEB. Um arquivo por UF *e por cargo*, nao um por UF. Assim o front
   baixa so o cargo que esta na tela: Goias no estadual sao ~530 KB, e nao os
   ~1,5 MB dos cinco cargos somados.

3. CADEIRAS VARIAM POR UF. Sao Paulo elege 94 deputados estaduais e Roraima 24;
   federal vai de 8 a 70. Nao da para constante - e' contado do proprio dado, e
   conferido contra o total de eleitos.
"""
import json
import sys
import unicodedata
from collections import defaultdict
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

DESTINO = cfg.PROCESSED / "web"
CARGOS = ["presidente", "governador", "senador", "federal", "estadual"]
MAJORITARIOS = {"presidente", "governador", "senador"}
MIN_VOTOS_SIMILARIDADE = 500
MIN_VOTOS_RIVAL = 1000
SIT_ELEITO = ("ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA", "MEDIA")

COLS = ["SG_UF", "NR_TURNO", "SQ_CANDIDATO", "NM_CANDIDATO", "NM_URNA_CANDIDATO",
        "SG_PARTIDO", "NM_MUNICIPIO", "DS_SIT_TOT_TURNO",
        "QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]
CATEG = ["SG_UF", "SG_PARTIDO", "NM_MUNICIPIO", "DS_SIT_TOT_TURNO"]


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def carregar_adjacencia():
    """Vem de 20_adjacencia.py, que a deriva da malha COMPLETA do IBGE.

    Nao se calcula adjacencia sobre a geometria simplificada usada no desenho:
    a simplificacao apaga vertices e em Goias a media de vizinhos caia de 5,3
    para 3,7, o que mediria o desenho e nao o territorio.
    """
    f = cfg.PROCESSED / "nac_adjacencia.json"
    if not f.exists():
        raise SystemExit("rode 20_adjacencia.py antes")
    bruto = json.loads(f.read_text())
    return {uf: {int(k): set(v) for k, v in d.items()} for uf, d in bruto.items()}


def carregar(cargo, ano):
    f = cfg.INTERIM / f"votos_br_{cargo}_{ano}.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f, usecols=lambda c: c in COLS,
                    dtype={c: "category" for c in CATEG}, low_memory=False)
    for c in ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"):
        if c not in d.columns:
            d[c] = 0
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    col = ("QT_VOTOS_NOMINAIS" if d["QT_VOTOS_NOMINAIS"].sum() > 0
           else "QT_VOTOS_NOMINAIS_VALIDOS")
    d["votos"] = d[col]
    if "NR_TURNO" in d.columns:
        d["NR_TURNO"] = pd.to_numeric(d["NR_TURNO"], errors="coerce").fillna(1)
    else:
        d["NR_TURNO"] = 1
    return d


def main():
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv", dtype={"cod_ibge": str})
    geom = json.loads((cfg.PROCESSED / "nac_geo_municipal.json").read_text())
    linhagem = pd.read_csv(cfg.OVERRIDES / "partidos_linhagem.csv")
    lin = dict(zip(linhagem["sigla_epoca"].map(sem_acento), linhagem["partido_norm"]))
    nomelin = dict(zip(linhagem["partido_norm"], linhagem["nome_linhagem"]))
    espectro = pd.read_csv(cfg.OVERRIDES / "partidos_espectro.csv")
    escore = dict(zip(espectro["partido_norm"], espectro["escore"]))
    banda = dict(zip(espectro["partido_norm"], espectro["banda"]))

    ufs = sorted(dim["uf"].unique())
    adj = carregar_adjacencia()
    mapa, indice, nomes, viz = {}, {}, {}, {}
    for uf, g in dim.groupby("uf"):
        g = g.sort_values("cod_ibge")
        mapa[uf] = dict(zip(g["nome_norm"], g["cod_ibge"]))
        indice[uf] = {c: i for i, c in enumerate(g["cod_ibge"])}
        nomes[uf] = list(g["nome"])
        viz[uf] = adj.get(uf, {})
    print(f"{len(ufs)} UFs, adjacência da malha completa", flush=True)

    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    # chave (uf, nome): "LUISIANIA" existe no PR e em SP apontando para
    # municipios diferentes, e uma chave so de nome nao cabe os dois
    corr = {(u, n): c for u, n, c in
            zip(ov["uf"], ov["nome_norm_tse"], ov["cod_ibge"])}
    cods = {uf: set(indice[uf]) for uf in ufs}

    # resultado[uf][cargo][ano] = bloco
    resultado = {uf: {c: {} for c in CARGOS} for uf in ufs}
    vetores = {uf: {c: {} for c in CARGOS} for uf in ufs}

    for cargo in CARGOS:
        for ano in cfg.ANOS:
            d = carregar(cargo, ano)
            if d is None:
                continue
            # vencedor vem de todos os turnos; a geografia, do primeiro
            venc = set(zip(
                d.loc[d["DS_SIT_TOT_TURNO"].astype(str).map(sem_acento)
                      .str.startswith("ELEITO"), "SG_UF"].astype(str),
                d.loc[d["DS_SIT_TOT_TURNO"].astype(str).map(sem_acento)
                      .str.startswith("ELEITO"), "SQ_CANDIDATO"]))
            d = d[d["NR_TURNO"] == 1]
            d = d.assign(nome_norm=d["NM_MUNICIPIO"].astype(str).map(geo.normalizar))

            for uf, g in d.groupby("SG_UF", observed=True):
                uf = str(uf)
                if uf not in mapa:
                    continue
                cod = g["nome_norm"].map(mapa[uf])
                falta = cod.isna()
                if falta.any():
                    sug = g.loc[falta, "nome_norm"].map(
                        lambda n: corr.get((uf, n)))
                    cod = cod.fillna(sug.where(sug.isin(cods[uf])))
                g = g.assign(cod_ibge=cod)
                g = g[g["cod_ibge"].notna()]
                if g.empty:
                    continue
                bloco = processar_uf(g, uf, ano, cargo, indice[uf], nomes[uf],
                                     viz[uf], venc, lin, nomelin, escore, banda)
                if bloco:
                    resultado[uf][cargo][str(ano)] = bloco["dados"]
                    vetores[uf][cargo][str(ano)] = bloco["vetores"]
            print(f"[{cargo}/{ano}] {len(d):,} linhas processadas", flush=True)
            del d

    gravar(resultado, vetores, ufs, nomes, indice, geom, dim)


def processar_uf(g, uf, ano, cargo, idx, nomes_mun, viz, venc, lin, nomelin,
                 escore, banda):
    n = len(nomes_mun)
    agg = g.groupby("SQ_CANDIDATO", observed=True)
    info = g.sort_values("votos", ascending=False).groupby(
        "SQ_CANDIDATO", observed=True).first()
    if info.empty:
        return None

    por_cand = {sq: sub for sq, sub in g.groupby("SQ_CANDIDATO", observed=True)}
    total_mun = np.zeros(n)
    for sub in por_cand.values():
        for c, v in zip(sub["cod_ibge"], sub["votos"]):
            total_mun[idx[c]] += v

    fichas, vetores = [], {}
    for sq_bruto, sub in por_cand.items():
        # Duas chaves para a mesma coisa: `info` e' indexado pelo sq como veio
        # do groupby, e a ficha guarda str(sq). Misturar as duas fazia toda
        # consulta a `vetores` falhar em silencio - janela de captura vazia e
        # semelhanca entre partidos zerada.
        sq = str(sq_bruto)
        v = np.zeros(n)
        for c, x in zip(sub["cod_ibge"], sub["votos"]):
            v[idx[c]] = x
        total = v.sum()
        if total <= 0:
            continue
        vetores[sq] = v
        p = v / total
        ordenado = np.sort(v)[::-1]
        hhi = float((p ** 2).sum())
        efet = 1 / hhi if hhi else 0
        share = np.divide(v, total_mun, out=np.zeros_like(v), where=total_mun > 0)
        dom = float((v * share).sum() / total)
        reduto = int(np.argmax(v))
        vizinhos = viz.get(reduto, set()) | {reduto}
        contig = float(sum(v[i] for i in vizinhos)) / total

        linha = info.loc[sq_bruto]
        sit = sem_acento(linha.get("DS_SIT_TOT_TURNO", ""))
        eleito = sit.startswith("ELEITO") or sit in SIT_ELEITO or (uf, sq) in venc
        sigla = sem_acento(linha.get("SG_PARTIDO", ""))
        pn = lin.get(sigla, sigla)
        concentrado, dominante = efet <= 10, dom * 100 >= 10
        tipo = ("Concentrado-Dominante" if concentrado and dominante else
                "Concentrado-Compartilhado" if concentrado else
                "Disperso-Dominante" if dominante else "Disperso-Difuso")

        fichas.append({
            "sq": str(sq),
            "n": str(linha.get("NM_URNA_CANDIDATO") or linha.get("NM_CANDIDATO")),
            "completo": str(linha.get("NM_CANDIDATO")),
            "chave": geo.normalizar(str(linha.get("NM_CANDIDATO"))),
            "p": sigla, "pn": nomelin.get(pn, pn),
            "sit": sit, "el": bool(eleito),
            "t": int(total), "nm": int((v > 0).sum()),
            "t1": round(float(ordenado[0] / total * 100), 2),
            "t5": round(float(ordenado[:5].sum() / total * 100), 2),
            "ef": round(efet, 2), "gi": round(gini(v), 4),
            "dom": round(dom * 100, 2),
            "dommax": round(float(share.max() * 100), 2),
            "dom25": int((share >= 0.25).sum()),
            "contig": round(contig * 100, 2),
            "r": reduto, "tipo": tipo,
            "mi": [int(i) for i in np.nonzero(v)[0]],
            "mv": [int(x) for x in v[v > 0]],
        })

    fichas.sort(key=lambda f: -f["t"])
    eleitos = [f for f in fichas if f["el"]]
    mais = max((f["t"] for f in fichas), default=0)
    vencedor_uf = max(fichas, key=lambda f: f["t"])["sq"] if fichas else None
    total_uf = sum(f["t"] for f in fichas)
    cadeiras = len(eleitos) or 1

    partidos = defaultdict(list)
    for f in fichas:
        partidos[f["pn"]].append(f)
    lista_part = []
    for nome, fs in partidos.items():
        fs.sort(key=lambda f: -f["t"])
        t = sum(f["t"] for f in fs)
        fortes = [f for f in fs if f["t"] >= MIN_VOTOS_SIMILARIDADE]
        sim = None
        if len(fortes) >= 2:
            M = np.vstack([vetores[f["sq"]] if f["sq"] in vetores else
                           np.zeros(n) for f in fortes])
            nor = np.linalg.norm(M, axis=1, keepdims=True)
            nor[nor == 0] = 1
            U = M / nor
            S = U @ U.T
            iu = np.triu_indices(len(fortes), k=1)
            sim = round(float(S[iu].mean()), 4)
        lista_part.append({
            "nome": nome, "nc": len(fs), "ne": sum(1 for f in fs if f["el"]),
            "votos": t, "puxador": round(fs[0]["t"] / t * 100, 2) if t else 0,
            "sim": sim,
        })
    lista_part.sort(key=lambda x: -x["votos"])

    # metricas por municipio: captura
    mm = []
    for i in range(n):
        col = np.array([vetores[f["sq"]][i] for f in fichas if f["sq"] in vetores])
        tot = col.sum()
        if tot <= 0:
            mm.append(None)
            continue
        pr = col / tot
        h = float((pr ** 2).sum())
        mm.append({"tot": int(tot), "t1": round(float(pr.max() * 100), 2),
                   "ef": round(1 / h if h else 0, 2)})

    # Agregado por partido sobre TODOS os candidatos. O arrasto entre cargos
    # precisa disto: as fichas guardadas nos cargos proporcionais sao so as dos
    # eleitos, e somar so eleitos subestima o partido onde ele tem muita gente
    # sem se eleger.
    pm = defaultdict(lambda: np.zeros(n))
    for f in fichas:
        if f["sq"] in vetores:
            pm[f["pn"]] += vetores[f["sq"]]
    pm_esparso = {}
    for nome, v in pm.items():
        nz = np.nonzero(v)[0]
        if len(nz):
            pm_esparso[nome] = {"i": [int(i) for i in nz],
                                "v": [int(x) for x in v[nz]]}

    return {
        "vetores": {f["sq"]: vetores[f["sq"]] for f in fichas if f["sq"] in vetores},
        "dados": {
            "pm": pm_esparso,
            "fichas": fichas if cargo in MAJORITARIOS else eleitos,
            "totalMun": [int(x) for x in total_mun],
            "mm": mm,
            "vencedorUF": vencedor_uf,
            "pleito": {
                "totalUF": total_uf, "nCand": len(fichas), "cadeiras": len(eleitos),
                "qe": round(total_uf / cadeiras, 1),
                "ultimo": min((f["t"] for f in eleitos), default=0),
                "maisVotado": mais,
            },
            "partidos": [p for p in lista_part if p["nc"] >= 3],
        },
    }


def gravar(resultado, vetores, ufs, nomes, indice, geom, dim):
    DESTINO.mkdir(parents=True, exist_ok=True)
    resumo = []
    for uf in ufs:
        pasta = DESTINO / uf
        pasta.mkdir(exist_ok=True)
        base = {"uf": uf,
                "municipios": [{"n": x} for x in nomes[uf]],
                "geo": geom.get(uf, [])}
        (pasta / "base.json").write_text(
            json.dumps(base, separators=(",", ":"), ensure_ascii=False),
            encoding="utf-8")
        for cargo in CARGOS:
            anos = resultado[uf][cargo]
            if not anos:
                continue
            (pasta / f"{cargo}.json").write_text(
                json.dumps(anos, separators=(",", ":"), ensure_ascii=False),
                encoding="utf-8")
        tam = sum(f.stat().st_size for f in pasta.glob("*.json")) / 1024
        cargos_ok = [c for c in CARGOS if resultado[uf][c]]
        resumo.append((uf, tam, len(cargos_ok)))
        print(f"  {uf}: {tam:>7.0f} KB, {len(cargos_ok)} cargos", flush=True)

    total = sum(t for _, t, _ in resumo) / 1024
    print(f"\ntotal em disco: {total:.1f} MB")
    print(f"maior UF: {max(resumo, key=lambda r: r[1])}")


if __name__ == "__main__":
    main()
