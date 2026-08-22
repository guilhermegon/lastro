"""Publica `data/processed/web/` em `app/public/dados/` e monta o índice.

O índice é o único arquivo que o front baixa sempre, então carrega só o que serve
para desenhar a primeira tela e o comparativo nacional: lista de UFs, malha do
Brasil por UF e o agregado por estado e pleito. Tudo mais vem sob demanda.

O agregado nacional é montado aqui, a partir dos arquivos por UF já validados, em
vez de vir de um pipeline paralelo — assim não existe a possibilidade de o
comparativo nacional discordar da tela do estado.
"""
import json
import shutil
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

ORIGEM = cfg.PROCESSED / "web"
DESTINO = cfg.ROOT / "app" / "public" / "dados"
CARGOS = ["presidente", "governador", "senador", "federal", "estadual"]


def main():
    if not ORIGEM.exists():
        raise SystemExit("rode 19_nacional_completo.py e 21_padroes_cruzamentos.py antes")

    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    ufs_dir = sorted(p.name for p in ORIGEM.iterdir() if p.is_dir())
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv", dtype={"cod_ibge": str})
    nomes_uf = {}
    try:
        nac = import_module("14_nacional")
        nomes_uf = {u["sigla"]: u["nome"] for u in nac.get(nac.LISTA_UF)}
    except Exception:
        pass

    agregado, resumo = [], []
    for uf in ufs_dir:
        shutil.copytree(ORIGEM / uf, DESTINO / uf)
        base = json.loads((ORIGEM / uf / "base.json").read_text(encoding="utf-8"))
        n_mun = len(base["municipios"])
        est = ORIGEM / uf / "estadual.json"
        if est.exists():
            d = json.loads(est.read_text(encoding="utf-8"))
            pad = json.loads((ORIGEM / uf / "padroes.json").read_text(encoding="utf-8"))
            serie = {s["ano"]: s for s in pad["serie"]}
            for ano, bloco in d.items():
                p = bloco["pleito"]
                s = serie.get(int(ano), {})
                agregado.append({
                    "uf": uf, "ano": int(ano), "cad": p["cadeiras"],
                    "cand": p["nCand"], "tot": p["totalUF"], "nmun": n_mun,
                    "qe": p["qe"], "ult": p["ultimo"],
                    "ef": s.get("ef"), "t1": s.get("t1"), "fr": s.get("fr"),
                })
        cargos = [c for c in CARGOS if (ORIGEM / uf / f"{c}.json").exists()]
        r = {"s": uf, "n": nomes_uf.get(uf, uf), "nm": n_mun, "cargos": cargos}
        # a capital so entra no indice se o arquivo existir: e' ela que liga a
        # aba de vereador, e o DF nao tem nenhuma das duas coisas
        if (ORIGEM / uf / "vereador.json").exists():
            v = json.loads((ORIGEM / uf / "vereador.json").read_text(encoding="utf-8"))
            r["capital"] = v["cidade"]
        resumo.append(r)

    indice = {
        "anos": cfg.ANOS,
        "cargos": CARGOS,
        "ufs": resumo,
        "agregado": agregado,
        "malhaUF": json.loads((cfg.PROCESSED / "nac_malha_uf.json").read_text()),
    }
    f = DESTINO / "indice.json"
    f.write_text(json.dumps(indice, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")

    total = sum(x.stat().st_size for x in DESTINO.rglob("*.json"))
    maior = max((x.stat().st_size, x.relative_to(DESTINO).as_posix())
                for x in DESTINO.rglob("*.json"))
    print(f"indice.json: {f.stat().st_size/1024:.0f} KB "
          f"({len(resumo)} UFs, {len(agregado)} linhas de agregado)")
    print(f"total publicado: {total/1024/1024:.1f} MB")
    print(f"maior arquivo: {maior[1]} com {maior[0]/1024:.0f} KB")
    print()
    com_ver = sum(1 for r in resumo if "capital" in r)
    com_riv = sum(1 for uf in ufs_dir
                  if (DESTINO / uf / "rivais_estadual.json").exists()
                  or (DESTINO / uf / "rivais_federal.json").exists())
    print(f"vereador em {com_ver} capitais, rivais em {com_riv} UFs")
    print()
    for uf in ("RR", "GO", "SP"):
        p = DESTINO / uf
        if not p.exists():
            continue
        def kb(nome):
            q = p / nome
            return q.stat().st_size / 1024 if q.exists() else 0
        print(f"  abertura em {uf}: índice {f.stat().st_size/1024:.0f} KB "
              f"+ base {kb('base.json'):.0f} KB + estadual {kb('estadual.json'):.0f} KB"
              f"  |  rivais {kb('rivais_estadual.json'):.0f} KB, "
              f"vereador {kb('vereador.json'):.0f} KB")


if __name__ == "__main__":
    main()
