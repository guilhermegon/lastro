"""Quanto voto se perde no pareamento TSE -> IBGE, por UF e por pleito.

Existe porque a perda e' SILENCIOSA. Em `19_nacional_completo.py` e em
`23_rivais.py` a linha cujo municipio nao parou com a malha do IBGE e'
descartada (`g[g["cod_ibge"].notna()]`), e o mapa resultante fica com aparencia
de certo: o municipio some do total sem que nada avise. Foi assim que apareceu
uma diferenca de 6.496 votos no total de Sao Paulo em 2022 - pequena em
proporcao, e exatamente o tipo de coisa que nao se descobre olhando o desenho.

O teste-ouro de Goias (`06_verifica.py`) nao pega isso: ele valida GO, onde o
pareamento e' 246/246 por construcao. Este script cobre as outras 26 unidades.

Nao corrige nada. Reporta, e o que ele achar vira linha em
`data/overrides/municipios_tse_ibge.csv`, que e' feito a mao e versionado.
"""
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

CARGOS = ["presidente", "governador", "senador", "federal", "estadual"]
COLS = ["SG_UF", "NM_MUNICIPIO", "QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS",
        "NR_TURNO"]


def indices_uf():
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    mapa = {uf: dict(zip(g["nome_norm"], g["cod_ibge"]))
            for uf, g in dim.groupby("uf")}
    cods = {uf: set(g["cod_ibge"]) for uf, g in dim.groupby("uf")}
    return mapa, cods


def main():
    mapa, cods = indices_uf()
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    # chave (uf, nome): "LUISIANIA" existe no PR e em SP apontando para
    # municipios diferentes, e uma chave so de nome nao cabe os dois
    corr = {(u, n): c for u, n, c in
            zip(ov["uf"], ov["nome_norm_tse"], ov["cod_ibge"])}

    orfaos = {}
    total_perdido = 0
    for cargo in CARGOS:
        for ano in cfg.ANOS:
            f = cfg.INTERIM / f"votos_br_{cargo}_{ano}.csv"
            if not f.exists():
                continue
            d = pd.read_csv(f, usecols=lambda c: c in COLS, dtype=str,
                            low_memory=False)
            for c in ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"):
                if c not in d.columns:
                    d[c] = 0
                d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
            col = ("QT_VOTOS_NOMINAIS" if d["QT_VOTOS_NOMINAIS"].sum() > 0
                   else "QT_VOTOS_NOMINAIS_VALIDOS")
            d["votos"] = d[col]
            if "NR_TURNO" in d.columns:
                d = d[pd.to_numeric(d["NR_TURNO"], errors="coerce").fillna(1) == 1]
            d = d.assign(nome_norm=d["NM_MUNICIPIO"].astype(str).map(geo.normalizar))

            perdido_ano = 0
            for uf, g in d.groupby("SG_UF"):
                uf = str(uf)
                if uf not in mapa:
                    continue
                cod = g["nome_norm"].map(mapa[uf])
                falta = cod.isna()
                if falta.any():
                    sug = g.loc[falta, "nome_norm"].map(
                        lambda n: corr.get((uf, n)))
                    cod = cod.fillna(sug.where(sug.isin(cods[uf])))
                orf = g[cod.isna()]
                if orf.empty:
                    continue
                v = int(orf["votos"].sum())
                perdido_ano += v
                for nome, gg in orf.groupby("nome_norm"):
                    k = (uf, str(nome))
                    a = orfaos.setdefault(k, {"votos": 0, "linhas": 0,
                                              "onde": set()})
                    a["votos"] += int(gg["votos"].sum())
                    a["linhas"] += len(gg)
                    a["onde"].add(f"{cargo}/{ano}")
            total_perdido += perdido_ano
            print(f"[{cargo}/{ano}] {perdido_ano:,} votos sem par", flush=True)
            del d

    print(f"\n=== total nao pareado: {total_perdido:,} votos ===")
    if not orfaos:
        print("nenhum municipio orfao — pareamento completo")
        return

    print(f"{len(orfaos)} nomes distintos sem par:\n")
    print(f"{'UF':<4}{'nome do TSE':<34}{'votos':>12}{'linhas':>9}  aparece em")
    for (uf, nome), a in sorted(orfaos.items(), key=lambda x: -x[1]["votos"]):
        onde = sorted(a["onde"])
        resumo = f"{len(onde)} arquivos" if len(onde) > 3 else ", ".join(onde)
        print(f"{uf:<4}{nome[:33]:<34}{a['votos']:>12,}{a['linhas']:>9}  {resumo}")

    print("\nCada linha acima vira uma correcao em "
          "data/overrides/municipios_tse_ibge.csv (nome_norm_tse -> cod_ibge).")


if __name__ == "__main__":
    main()
