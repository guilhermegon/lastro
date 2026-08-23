"""Populacao e area de cada municipio, para normalizar o mapa de emendas.

Fonte: IBGE, agregado 4714 (Censo 2022) — "Populacao Residente, Area
territorial e Densidade demografica". Uma requisicao por variavel, todos os
municipios de uma vez.

**Por que isto existe.** Um mapa de emendas em reais absolutos e' quase um mapa
de populacao: as cidades grandes recebem mais porque sao grandes. Isso nao e'
falso, mas responde "onde mora gente", nao "quem foi bem tratado". Reais por
habitante inverte o retrato — e reais por quilometro quadrado inverte de novo,
favorecendo o municipio pequeno e denso. Nenhuma das tres e' a leitura certa
sozinha; por isso as tres ficam disponiveis e o leitor troca.

Sai alinhado ao indice de `base.json` (municipios ordenados por `cod_ibge`
dentro da UF), como todo o resto do projeto, para que a divisao seja elemento a
elemento sem tabela de conversao no meio.

Municipio sem dado no Censo 2022 fica `null`, nunca zero: zero dividiria e
produziria infinito, e a tela precisa saber a diferenca entre "nao tem gente" e
"nao sei quanta gente tem".
"""
import gzip
import json
import sys
import urllib.request
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

WEB = cfg.PROCESSED / "web"
AGREGADO = 4714
PERIODO = 2022
VAR_POP = 93        # Populacao residente (pessoas)
VAR_AREA = 6318     # Area da unidade territorial (km2)
URL = ("https://servicodados.ibge.gov.br/api/v3/agregados/{ag}/periodos/{per}"
       "/variaveis/{var}?localidades=N6[all]")


def get(url):
    """GET que lida com a resposta gzipada que a API do IBGE devolve."""
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip",
                                               "User-Agent": "rastro/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
    if raw[:2] == bytes([0x1F, 0x8B]):
        raw = gzip.decompress(raw)
    return json.loads(raw)


def baixar(var):
    d = get(URL.format(ag=AGREGADO, per=PERIODO, var=var))
    fora = {}
    for bloco in d:
        for serie in bloco.get("resultados", [])[0].get("series", []):
            cod = serie["localidade"]["id"]
            v = serie["serie"].get(str(PERIODO))
            # a API devolve "-" e "..." para ausente; nao virar zero
            try:
                fora[cod] = float(str(v).replace(",", "."))
            except (TypeError, ValueError):
                fora[cod] = None
    return fora


def main():
    print("baixando população e área do Censo 2022...", flush=True)
    pop = baixar(VAR_POP)
    area = baixar(VAR_AREA)
    print(f"  população: {len(pop):,} municípios | área: {len(area):,}")

    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    total, faltando = 0, []
    for uf, g in dim.groupby("uf"):
        g = g.sort_values("cod_ibge")
        cods = list(g["cod_ibge"])
        p = [pop.get(c) for c in cods]
        a = [area.get(c) for c in cods]
        faltando += [(uf, c) for c, x, y in zip(cods, p, a)
                     if x is None or y is None]
        obj = {"pop": p, "area": [round(x, 3) if x is not None else None for x in a]}
        f = WEB / uf / "demografia.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
        total += f.stat().st_size

    n = len(dim)
    print(f"\ndemografia.json em {dim['uf'].nunique()} UFs, {total/1024:.0f} KB")
    print(f"  {n - len(faltando):,} de {n:,} municípios com população e área")
    if faltando:
        print(f"  sem dado ({len(faltando)}): "
              + ", ".join(f"{uf}/{c}" for uf, c in faltando[:8]))
    pais_pop = sum(v for v in pop.values() if v)
    pais_area = sum(v for v in area.values() if v)
    print(f"\n  confere: {pais_pop/1e6:.1f} milhões de habitantes, "
          f"{pais_area/1e6:.3f} milhões de km²")


if __name__ == "__main__":
    main()
