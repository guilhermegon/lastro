"""Payload nacional: 27 UFs, deputado estadual, 1998-2022, com mapa municipal.

Medido antes de decidir o corte, nao estimado:

  geometria municipal do Brasil (tolerancia 0.012)   2,3 MB
  detalhe dos eleitos, os 7 pleitos, empacotado      9,6 MB
  totais por municipio + nomes + agregados           ~0,7 MB
  ----------------------------------------------------------
  total                                              ~12,6 MB   (teto: 16 MB)

Cabe. Por isso aqui nao ha corte de anos: os 27 estados recebem os sete pleitos,
que e' o que "mesmo tratamento" quer dizer.

O que fica de fora, e por que: os outros quatro cargos e o painel de vereador de
Goiania. Incluir os cinco cargos para todas as UFs projetava ~89 MB. O deputado
estadual e' o cargo do painel original e o unico em que o mapa municipal tem
massa para fazer sentido em qualquer estado.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

SAIDA = cfg.DIST / "dados_br.json"


def totais_por_municipio(dim):
    """Denominador do mapa de influencia: soma de TODOS os candidatos, nao so
    dos eleitos. Exige uma passada pelos arquivos nacionais."""
    mapa = {uf: dict(zip(g["nome_norm"], g["cod_ibge"]))
            for uf, g in dim.groupby("uf")}
    cod_por_uf = {uf: set(g["cod_ibge"]) for uf, g in dim.groupby("uf")}
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    corr = dict(zip(ov["nome_norm_tse"], ov["cod_ibge"]))

    saida = {}
    for ano in cfg.ANOS:
        f = cfg.INTERIM / f"votos_br_estadual_{ano}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f, dtype=str, low_memory=False,
                        usecols=["SG_UF", "NM_MUNICIPIO", "QT_VOTOS_NOMINAIS",
                                 "QT_VOTOS_NOMINAIS_VALIDOS"])
        for c in ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"):
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
        col = ("QT_VOTOS_NOMINAIS" if d["QT_VOTOS_NOMINAIS"].sum() > 0
               else "QT_VOTOS_NOMINAIS_VALIDOS")
        d["nome_norm"] = d["NM_MUNICIPIO"].map(geo.normalizar)
        for uf, g in d.groupby("SG_UF"):
            if uf not in mapa:
                continue
            cod = g["nome_norm"].map(mapa[uf])
            falta = cod.isna()
            if falta.any():
                sug = g.loc[falta, "nome_norm"].map(corr)
                cod.loc[falta] = sug.where(sug.isin(cod_por_uf[uf]))
            g = g.assign(cod_ibge=cod)
            g = g[g["cod_ibge"].notna()]
            soma = g.groupby("cod_ibge")[col].sum()
            saida.setdefault(uf, {})[str(ano)] = soma.to_dict()
        print(f"  [{ano}] totais municipais somados", flush=True)
    return saida


def main():
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    agr = pd.read_csv(cfg.PROCESSED / "nac_agregado.csv")
    det = json.loads((cfg.PROCESSED / "nac_eleitos_detalhe.json").read_text())
    geom = json.loads((cfg.PROCESSED / "nac_geo_municipal.json").read_text())
    malha_uf = json.loads((cfg.PROCESSED / "nac_malha_uf.json").read_text())

    ufs = sorted(agr["uf"].unique())
    nomes_uf = dict(zip(agr["uf"], agr["uf_nome"]))

    municipios, indice = {}, {}
    for uf, g in dim.groupby("uf"):
        g = g.sort_values("cod_ibge")
        municipios[uf] = [{"n": r.nome, "c": r.cod_ibge} for r in g.itertuples()]
        indice[uf] = {c: i for i, c in enumerate(g["cod_ibge"])}

    tot = totais_por_municipio(dim)
    totais = {}
    for uf in ufs:
        totais[uf] = {}
        for ano in cfg.ANOS:
            d = tot.get(uf, {}).get(str(ano))
            if not d:
                continue
            v = [0] * len(municipios[uf])
            for cod, x in d.items():
                if cod in indice[uf]:
                    v[indice[uf][cod]] = int(x)
            totais[uf][str(ano)] = v

    eleitos = {}
    for x in det:
        uf, ano = x["uf"], str(x["ano"])
        eleitos.setdefault(uf, {}).setdefault(ano, []).append({
            "n": x["nome"], "p": x["partido"], "pn": x["partido_norm"],
            "t": x["total"], "nm": x["nmun"], "t1": x["top1"], "t5": x["top5"],
            "ef": x["efet"], "gi": x["gini"],
            "r": indice[uf].get(x["reduto"], -1),
            "mi": x["mi"], "mv": x["mv"],
        })
    for uf in eleitos:
        for ano in eleitos[uf]:
            eleitos[uf][ano].sort(key=lambda c: -c["t"])

    payload = {
        "anos": cfg.ANOS,
        "ufs": [{"s": u, "n": nomes_uf.get(u, u),
                 "nm": len(municipios.get(u, []))} for u in ufs],
        "municipios": {u: municipios[u] for u in ufs if u in municipios},
        "geo": {u: geom[u] for u in ufs if u in geom},
        "malhaUF": malha_uf,
        "eleitos": eleitos,
        "totais": totais,
        "agregado": [{"uf": r.uf, "ano": int(r.ano), "cad": int(r.n_cadeiras),
                      "cand": int(r.n_candidatos), "tot": int(r.total_nominais),
                      "nmun": int(r.n_municipios), "qe": r.quociente,
                      "ult": int(r.ultimo_eleito),
                      "ef": r.efet, "t1": r.top1, "gi": r.gini}
                     for r in agr.itertuples()],
    }
    SAIDA.write_text(json.dumps(payload, separators=(",", ":"),
                                ensure_ascii=False), encoding="utf-8")
    mb = SAIDA.stat().st_size / 1024 / 1024
    print(f"\n{SAIDA.name}: {mb:.1f} MB")
    print(f"  UFs: {len(ufs)} | municipios: {sum(len(v) for v in municipios.values())}")
    print(f"  eleitos: {sum(len(a) for u in eleitos.values() for a in u.values())}")
    if mb > 15:
        print("  AVISO acima de 15 MB - perto do teto de 16 MB da pagina")


if __name__ == "__main__":
    main()
