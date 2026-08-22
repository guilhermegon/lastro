"""Adjacência municipal das 26 UFs, derivada da malha completa.

Por que é um script separado da geometria de desenho: **adjacência é topologia,
simplificação é exibição**. A malha usada no mapa foi simplificada com tolerância
0,012 para caber na web, e isso apaga vértices — em Goiás a média de vizinhos caía
de 5,3 para 3,7, porque fronteiras inteiras deixavam de ter ponto em comum. Um
índice de contiguidade calculado sobre geometria de desenho mede o desenho, não o
território.

Aqui a malha vem na qualidade intermediária do IBGE, sem simplificar, e só a
adjacência é guardada. O peso extra fica no build, não no navegador.
"""
import json
import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
nac = import_module("14_nacional")

SAIDA = cfg.PROCESSED / "nac_adjacencia.json"


def vizinhos(features, ordem):
    """Dois municípios são vizinhos quando compartilham vértice de fronteira.

    Vértice, e não aresta: depois de qualquer simplificação as arestas deixam de
    coincidir exatamente entre polígonos vizinhos, mas os pontos de fronteira
    sobrevivem com mais frequência. Sobre a malha completa os dois critérios
    quase coincidem; o de vértice é o mais robusto dos dois.
    """
    pos = {c: i for i, c in enumerate(ordem)}
    por_ponto = defaultdict(set)
    for f in features:
        cod = str(f["properties"].get("codarea") or f["properties"].get("id"))
        i = pos.get(cod)
        if i is None:
            continue
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            for anel in poly:
                for x, y in anel:
                    por_ponto[(round(x, 5), round(y, 5))].add(i)
    viz = defaultdict(set)
    for donos in por_ponto.values():
        if len(donos) > 1:
            for a in donos:
                viz[a] |= donos - {a}
    return viz


def main():
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv", dtype={"cod_ibge": str})
    saida, relatorio = {}, []

    for uf, g in dim.groupby("uf"):
        ordem = sorted(g["cod_ibge"])
        cod_uf = ordem[0][:2]
        try:
            gj = nac.get(cfg.IBGE_MALHA_URL.format(uf=cod_uf))
        except Exception as e:
            print(f"  [{uf}] malha falhou: {e}", flush=True)
            continue
        viz = vizinhos(gj["features"], ordem)
        saida[uf] = {str(k): sorted(v) for k, v in viz.items()}
        media = sum(len(v) for v in viz.values()) / max(len(viz), 1)
        isolados = len(ordem) - len(viz)
        relatorio.append((uf, len(ordem), round(media, 1), isolados))
        print(f"  {uf}: {len(ordem):>3} municípios, média {media:.1f} vizinhos, "
              f"{isolados} sem vizinho", flush=True)

    SAIDA.write_text(json.dumps(saida, separators=(",", ":")), encoding="utf-8")
    print(f"\n{SAIDA.name}: {SAIDA.stat().st_size/1024:.0f} KB, {len(saida)} UFs")

    go = next((r for r in relatorio if r[0] == "GO"), None)
    if go:
        print(f"\nconferência contra o pipeline original de Goiás (média 5,3): "
              f"média {go[2]}")
    fora = [r for r in relatorio if r[3] > 2]
    if fora:
        print("UFs com municípios sem vizinho — esperado onde há ilha:")
        for uf, n, m, iso in fora:
            print(f"  {uf}: {iso} de {n}")


if __name__ == "__main__":
    main()
