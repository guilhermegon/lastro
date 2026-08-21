"""Monta o JSON compacto que alimenta o painel HTML.

Estrategia de tamanho: os eleitos de cada cargo entram com detalhe municipal
completo (vetor esparso de votos); os demais candidatos entram apenas com o
total estadual, que ja basta para quociente e eficiencia. Os municipios viram
indices inteiros 0..245 para nao repetir codigo IBGE dezenas de milhares de
vezes. No Senado os eleitos sao 1 ou 2 por pleito, entao entram todos os
candidatos - uma lista de um nome so nao serviria para nada.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

SAIDA = cfg.DIST / "dados.json"


def sfx(cargo):
    return "" if cargo == "estadual" else f"_{cargo}"


def bloco_cargo(cargo, mun, idx):
    """Monta a estrutura de um cargo, no mesmo formato para os tres."""
    s = sfx(cargo)
    fato = pd.read_csv(cfg.PROCESSED / f"fato_votos{s}.csv", dtype={"cod_ibge": str})
    met = pd.read_csv(cfg.PROCESSED / f"metricas_candidato{s}.csv")
    mm = pd.read_csv(cfg.PROCESSED / f"metricas_municipio{s}.csv",
                     dtype={"cod_ibge": str})
    mp = pd.read_csv(cfg.PROCESSED / f"metricas_partido{s}.csv")
    ple = pd.read_csv(cfg.PROCESSED / f"dim_pleito{s}.csv")
    riv = (pd.read_csv(cfg.PROCESSED / "rivais.csv")
           if cargo == "estadual" else None)

    met = met.assign(chave=met["nome"].astype(str).map(geo.normalizar))
    anos = {}
    for ano in cfg.ANOS:
        m_ano = met[met["ano"] == ano]
        if m_ano.empty:      # presidente nao tem 1998 neste conjunto do TSE
            continue
        # No Senado a lista de eleitos tem 1 ou 2 nomes; mostrar so eles tornaria
        # a aba inutil, entao entram todos os candidatos daquele pleito.
        # Nos majoritarios os "eleitos" sao 1 ou 2; listar so eles tornaria a
        # aba inutil, entao entram todos os candidatos do pleito.
        sel = (m_ano if cargo in cfg.CARGOS_MAJORITARIOS
               else m_ano[m_ano["eleito"]])
        sel = sel.sort_values("votos_total", ascending=False)
        por_cand = {sq: g for sq, g in fato[fato["ano"] == ano].groupby("sq_candidato")}

        lista = []
        for r in sel.itertuples():
            g = por_cand.get(r.sq_candidato)
            if g is None:
                continue
            g = g.sort_values("cod_ibge")
            item = {
                "sq": int(r.sq_candidato),
                "nome": r.nome_urna if isinstance(r.nome_urna, str) else r.nome,
                "completo": r.nome,
                "chave": geo.normalizar(r.nome),
                "partido": r.sigla_partido,
                "linhagem": r.nome_linhagem,
                "situacao": r.situacao,
                "eleito": bool(r.eleito),
                "venceuGO": bool(getattr(r, "venceu_go", False)),
                "total": int(r.votos_total),
                "nmun": int(r.n_municipios),
                "top1": r.top1_share, "top5": r.top5_share,
                "efet": r.n_municipios_efetivo, "gini": r.gini_municipal,
                "dom": r.dominancia_ponderada, "dommax": r.dominancia_max,
                "dom25": int(r.n_mun_dominio_25), "contig": r.contiguidade,
                "reduto": r.reduto_nome, "tipo": r.tipologia,
                "sim": (None if pd.isna(r.similaridade_pleito_anterior)
                        else r.similaridade_pleito_anterior),
                "var": (None if pd.isna(r.variacao_votos_pct) else r.variacao_votos_pct),
                "mi": [idx[c] for c in g["cod_ibge"]],
                "mv": [int(v) for v in g["votos"]],
            }
            if riv is not None:
                r2 = riv[(riv["ano"] == ano) & (riv["sq_candidato"] == r.sq_candidato)]
                item["rivais"] = [{
                    "n": t.rival, "p": t.rival_partido, "b": t.rival_banda,
                    "el": bool(t.rival_eleito), "lado": t.lado,
                    "pr": t.pressao, "af": t.afinidade, "mun": t.municipios_disputados,
                } for t in r2.sort_values("pressao", ascending=False).itertuples()]
            lista.append(item)

        mmy = mm[mm["ano"] == ano].set_index("cod_ibge")
        p = ple[ple["ano"] == ano].iloc[0]
        partidos = (mp[(mp["ano"] == ano) & (mp["n_candidatos"] >= 3)]
                    .sort_values("votos_total", ascending=False))

        anos[str(ano)] = {
            "eleitos": lista,
            "totalMun": [int(mmy["total_nominais"].get(c, 0)) for c in mun["cod_ibge"]],
            "top1Mun": [float(mmy["top1_share"].get(c, 0)) for c in mun["cod_ibge"]],
            "efetMun": [float(mmy["n_candidatos_efetivo"].get(c, 0))
                        for c in mun["cod_ibge"]],
            "pleito": {
                "totalUF": int(p.total_nominais_uf), "nCand": int(p.n_candidatos),
                "qe": float(p.quociente_eleitoral_aprox),
                "ultimo": int(p.votos_ultimo_eleito),
                "maisVotado": int(p.votos_mais_votado),
                "cadeiras": int(p.n_cadeiras),
                "votosPorEleitor": cfg.VOTOS_POR_ELEITOR[cargo][ano],
            },
            "partidos": [{
                "nome": r.nome_linhagem, "nc": int(r.n_candidatos),
                "ne": int(r.n_eleitos), "votos": int(r.votos_total),
                "puxador": r.share_puxador,
                "sim": (None if pd.isna(r.similaridade_media_intrapartido)
                        else r.similaridade_media_intrapartido),
            } for r in partidos.itertuples()],
        }

    # Mesma razao do 11_cruzado: nos majoritarios a serie util e' a do mais
    # votado em Goias, nao a do vencedor nacional (nem sempre o mesmo) nem uma
    # lista vazia nos anos sem resultado no arquivo.
    if cargo in cfg.CARGOS_MAJORITARIOS and "venceu_go" in met.columns:
        el = met[met["venceu_go"]]
    else:
        el = met[met["eleito"]]
    if el.empty:
        el = met
    serie = [{
        "ano": ano,
        "efet": round(float(g["n_municipios_efetivo"].median()), 2),
        "top1": round(float(g["top1_share"].median()), 2),
        "dom": round(float(g["dominancia_ponderada"].median()), 2),
        "contig": round(float(g["contiguidade"].median()), 2),
        "nmun": round(float(g["n_municipios"].median()), 1),
        "reinc": round(float(g["reincidente"].mean()) * 100, 1),
        "tipos": g["tipologia"].value_counts().to_dict(),
    } for ano, g in ((a, el[el["ano"] == a]) for a in cfg.ANOS) if len(g)]

    pessoas = set(el["chave"])
    serie_pessoal = {}
    for r in met[met["chave"].isin(pessoas)].itertuples():
        serie_pessoal.setdefault(r.chave, []).append({
            "ano": int(r.ano), "votos": int(r.votos_total),
            "partido": r.sigla_partido, "eleito": bool(r.eleito),
            "situacao": r.situacao,
        })
    for v in serie_pessoal.values():
        v.sort(key=lambda d: d["ano"])

    return {"dados": anos, "serie": serie, "seriePessoal": serie_pessoal}


def bloco_cruzado(mm_estadual):
    esc = pd.read_csv(cfg.PROCESSED / "cruz_escala.csv")
    dob = pd.read_csv(cfg.PROCESSED / "cruz_dobradinhas.csv")
    base = pd.read_csv(cfg.PROCESSED / "cruz_base.csv")
    arr = pd.read_csv(cfg.PROCESSED / "cruz_arrasto.csv")

    return {
        "escala": [{"cargo": r.cargo, "ano": int(r.ano),
                    "efet": r.mun_efetivo, "top1": r.top1_share,
                    "nmun": r.n_municipios, "dom": r.dominancia}
                   for r in esc.itertuples()],
        "base": [{"ano": int(r.ano), "par": r.par, "mediana": r.base_mediana}
                 for r in base.itertuples()],
        "dobradinhas": [{
            "ano": int(r.ano), "e": r.estadual, "ep": r.est_partido,
            "eel": bool(r.est_eleito), "f": r.federal, "fp": r.fed_partido,
            "fel": bool(r.fed_eleito), "mp": bool(r.mesmo_partido),
            "af": r.afinidade, "mun": r.municipios,
        } for r in dob.sort_values("afinidade", ascending=False).itertuples()],
        "mesmoPartido": [{"ano": int(a), "pct": round(float(g["mesmo_partido"].mean()) * 100, 1),
                          "n": int(len(g))}
                         for a, g in dob.groupby("ano")],
        "arrasto": [{"ano": int(r.ano), "partido": r.partido,
                     "n": int(r.n_municipios), "r": r.correlacao}
                    for r in arr.itertuples()],
    }


def bloco_vereador():
    """Goiania e' um municipio so: aqui a geografia disponivel e' a zona
    eleitoral, nao o municipio. Sem malha de zona publicada, nao ha mapa - a
    distribuicao territorial entra como barras por zona."""
    cand = pd.read_csv(cfg.PROCESSED / "ver_candidato.csv",
                       dtype={"zona_reduto": str, "sq": str})
    cand["zona_reduto"] = cand["zona_reduto"].str.replace(r"\.0$", "", regex=True)
    # sq como texto nos dois lados: lido como numero de um lado e texto do outro,
    # o join falha em silencio e candidatos somem da lista.
    fato = pd.read_csv(cfg.PROCESSED / "ver_fato_zona.csv",
                       dtype={"zona": str, "sq": str})
    ple = pd.read_csv(cfg.PROCESSED / "ver_pleito.csv")
    part = pd.read_csv(cfg.PROCESSED / "ver_partido.csv")
    anos = sorted(cand["ano"].unique().tolist())

    cand = cand[cand["votos_total"] >= 100]
    por = {sq: g for sq, g in fato.groupby(["ano", "sq"])}

    cands, zonas = {}, {}
    for ano in anos:
        z = sorted(fato[fato["ano"] == ano]["zona"].unique(),
                   key=lambda x: int(x))
        zonas[str(ano)] = z
        lista = []
        for r in cand[cand["ano"] == ano].sort_values(
                "votos_total", ascending=False).itertuples():
            g = por.get((ano, r.sq))
            if g is None:
                continue
            mapa = dict(zip(g["zona"], g["votos"]))
            lista.append({
                "sq": str(r.sq),
                "nome": r.nome_urna if isinstance(r.nome_urna, str) else r.nome,
                "completo": r.nome, "chave": r.chave,
                "partido": r.sigla, "linhagem": r.nome_linhagem,
                "situacao": r.situacao, "eleito": bool(r.eleito),
                "total": int(r.votos_total),
                "nz": int(r.n_zonas), "efetz": r.zonas_efetivas,
                "top1z": r.top1_zona, "gini": r.gini_zona,
                "reduto": str(r.zona_reduto),
                "sim": None if pd.isna(r.similaridade_anterior) else r.similaridade_anterior,
                "var": None if pd.isna(r.variacao_pct) else r.variacao_pct,
                "zv": [int(mapa.get(x, 0)) for x in z],
            })
        cands[str(ano)] = lista

    el = cand[cand["eleito"]]
    serie = [{"ano": int(a),
              "efetz": round(float(g["zonas_efetivas"].median()), 2),
              "top1z": round(float(g["top1_zona"].median()), 2),
              "reinc": round(float(g["reincidente"].mean()) * 100, 1)}
             for a, g in el.groupby("ano")]

    pessoas = set(el["chave"])
    sp = {}
    for r in cand[cand["chave"].isin(pessoas)].itertuples():
        sp.setdefault(r.chave, []).append({
            "ano": int(r.ano), "votos": int(r.votos_total),
            "partido": r.sigla, "eleito": bool(r.eleito)})
    for v in sp.values():
        v.sort(key=lambda d: d["ano"])

    # Mapa de pontos de Goiania: so existe para os anos em que o TSE publica
    # coordenada de local de votacao. Ausente, a aba cai para as barras por zona.
    locais, votoLocal = None, None
    fl = cfg.PROCESSED / "ver_locais_2024.csv"
    fv = cfg.PROCESSED / "ver_voto_local_2024.csv"
    if fl.exists() and fv.exists():
        lo = pd.read_csv(fl, dtype={"zona": str, "local": str})
        vo = pd.read_csv(fv, dtype={"sq": str, "local": str})
        lo = lo.reset_index(drop=True)
        pos = {k: i for i, k in enumerate(lo["local"])}
        locais = {
            "ano": 2024,
            "pontos": [{"n": r.nome, "b": r.bairro, "z": r.zona,
                        "lat": round(float(r.lat), 5), "lon": round(float(r.lon), 5),
                        "ns": int(r.n_secoes)} for r in lo.itertuples()],
        }
        votoLocal = {}
        for sq, g in vo.groupby("sq"):
            votoLocal[str(sq)] = {"i": [pos[x] for x in g["local"] if x in pos],
                                  "v": [int(x) for x, k in zip(g["votos"], g["local"])
                                        if k in pos]}

    return {
        "anos": anos, "zonas": zonas, "cands": cands, "serie": serie,
        "locais": locais, "votoLocal": votoLocal,
        "seriePessoal": sp,
        "pleitos": {str(int(r.ano)): {
            "nCand": int(r.n_candidatos), "nEleitos": int(r.n_eleitos),
            "total": int(r.total_nominais), "ultimo": int(r.votos_ultimo_eleito),
            "maisVotado": int(r.votos_mais_votado), "qe": r.quociente_aprox,
            "nZonas": int(r.n_zonas), "reinc": r.reincidentes_pct,
        } for r in ple.itertuples()},
        "partidos": {str(int(a)): [{
            "nome": t.nome_linhagem, "nc": int(t.n_candidatos),
            "ne": int(t.n_eleitos), "votos": int(t.votos),
            "puxador": t.share_puxador,
            "sim": None if pd.isna(t.similaridade) else t.similaridade,
        } for t in g[g["n_candidatos"] >= 3].sort_values(
            "votos", ascending=False).itertuples()]
            for a, g in part.groupby("ano")},
    }


def main():
    mun = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype={"cod_ibge": str})
    gj = json.loads((cfg.PROCESSED / "go_municipios.geojson").read_text(
        encoding="utf-8"))
    mun = mun.sort_values("cod_ibge").reset_index(drop=True)
    idx = {c: i for i, c in enumerate(mun["cod_ibge"])}

    por_cod = {f["properties"]["cod_ibge"]: f for f in gj["features"]}
    geometrias = []
    for cod in mun["cod_ibge"]:
        g = por_cod[cod]["geometry"]
        polys = ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])
        geometrias.append([[[round(x, 4), round(y, 4)] for x, y in anel[0]]
                           for anel in polys])

    cargos = {c: bloco_cargo(c, mun, idx) for c in
              ("estadual", "federal", "senador", "governador", "presidente")}

    mm = pd.read_csv(cfg.PROCESSED / "metricas_municipio.csv",
                     dtype={"cod_ibge": str})
    cortes = [0, 2000, 5000, 10000, 15000, 25000, 50000, 10 ** 9]
    rotulos = ["ate 2 mil", "2-5 mil", "5-10 mil", "10-15 mil",
               "15-25 mil", "25-50 mil", "mais de 50 mil"]
    mm2 = mm.assign(faixa=pd.cut(mm["total_nominais"], cortes, labels=rotulos))
    captura = {"faixas": rotulos, "anos": []}
    for ano in cfg.ANOS:
        g = mm2[mm2["ano"] == ano].groupby("faixa", observed=False)
        captura["anos"].append({
            "ano": ano,
            "top1": [None if pd.isna(x) else round(float(x), 1)
                     for x in g["top1_share"].median().reindex(rotulos)],
            "n": [int(x) for x in g.size().reindex(rotulos).fillna(0)],
        })

    payload = {
        "uf": cfg.UF, "anos": cfg.ANOS, "nCadeiras": cfg.N_CADEIRAS,
        "faixasVotacao": cfg.FAIXAS_VOTACAO,
        "faixasInfluencia": cfg.FAIXAS_INFLUENCIA,
        "municipios": [{"cod": r.cod_ibge, "nome": r.nome, "micro": r.microrregiao}
                       for r in mun.itertuples()],
        "geo": geometrias,
        "cargos": cargos,
        "cruz": bloco_cruzado(mm),
        "vereador": bloco_vereador(),
        "captura": captura,
    }
    SAIDA.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
    print(f"{SAIDA.name}: {SAIDA.stat().st_size/1024:.0f} KB")
    for c, b in cargos.items():
        n = sum(len(d["eleitos"]) for d in b["dados"].values())
        pares = sum(len(e["mi"]) for d in b["dados"].values() for e in d["eleitos"])
        print(f"  {c}: {n} fichas, {pares} pares candidato-municipio")


if __name__ == "__main__":
    main()
