"""Portao da extracao nacional: ela tem de reproduzir a de Goias, exatamente.

O teste-ouro (06_verifica.py) garante que o recorte de Goias bate com o painel
original do TSE/GO. Este script estende essa garantia ao modo nacional: para
cada cargo e cada ano, o subconjunto de Goias dentro do arquivo do Brasil tem de
ser identico ao arquivo so de Goias - mesmo total, mesmos candidatos, mesmos
municipios.

Foi escrito depois de duas duplicacoes silenciosas seguidas no modo nacional:

  1. o membro `_BRASIL.csv` do zip entrou na lista de UFs e dobrou tudo;
  2. corrigido isso, o mesmo membro continuou sendo anexado inteiro pelo bloco
     que busca presidente - e em 1998, 2006, 2010 e 2014 ele traz todos os
     cargos, nao so o cargo 1, entao dobrou de novo, mas so nesses anos.

Nenhuma das duas apareceu como erro. As duas apareceram como numero grande.
"""
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

COLS_VOTO = ["QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]


def resumo(df):
    """Assinatura comparavel de um recorte: totais e cardinalidades."""
    col = ("QT_VOTOS_NOMINAIS" if df["QT_VOTOS_NOMINAIS"].sum() > 0
           else "QT_VOTOS_NOMINAIS_VALIDOS")
    return {
        "votos": int(df[col].sum()),
        "candidatos": int(df["SQ_CANDIDATO"].nunique()),
        "municipios": int(df["CD_MUNICIPIO"].nunique()),
        "linhas": int(len(df)),
    }


def ler(caminho):
    d = pd.read_csv(caminho, dtype=str, low_memory=False)
    for c in COLS_VOTO:
        if c not in d.columns:
            d[c] = 0
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    return d


def main():
    falhas, checados, ausentes = [], 0, []
    for cargo in cfg.CARGOS.values():
        for ano in cfg.ANOS:
            fgo = cfg.INTERIM / f"votos_go_{cargo}_{ano}.csv"
            fbr = cfg.INTERIM / f"votos_br_{cargo}_{ano}.csv"
            if not fgo.exists() or not fbr.exists():
                ausentes.append(f"{cargo}/{ano}")
                continue
            go = resumo(ler(fgo))
            br_todo = ler(fbr)
            br = resumo(br_todo[br_todo["SG_UF"] == cfg.UF])
            checados += 1
            if go != br:
                dif = {k: (go[k], br[k]) for k in go if go[k] != br[k]}
                falhas.append((cargo, ano, dif))
                print(f"  FALHA {cargo}/{ano}: (goias, nacional) -> {dif}")
            else:
                print(f"  ok    {cargo}/{ano}: {go['votos']} votos, "
                      f"{go['candidatos']} candidatos")

            # plausibilidade: o total do pais nao pode passar do eleitorado
            uf_col = br_todo["SG_UF"].nunique()
            col = ("QT_VOTOS_NOMINAIS" if br_todo["QT_VOTOS_NOMINAIS"].sum() > 0
                   else "QT_VOTOS_NOMINAIS_VALIDOS")
            total_br = int(br_todo[col].sum())
            teto = 160_000_000     # eleitorado brasileiro, ordem de grandeza
            if cargo in ("estadual", "federal") and total_br > teto:
                falhas.append((cargo, ano, {"total_br_implausivel": total_br}))
                print(f"  FALHA {cargo}/{ano}: total nacional {total_br:,} "
                      f"acima do eleitorado - sinal de duplicacao ({uf_col} UFs)")

    print(f"\n{checados} combinacoes cargo/ano conferidas")
    if ausentes:
        print(f"sem par para conferir: {ausentes}")
    if falhas:
        raise SystemExit(f"\nVALIDACAO NACIONAL FALHOU em {len(falhas)} casos")
    print("VALIDACAO NACIONAL PASSOU: o recorte de Goias no arquivo do Brasil "
          "e identico ao arquivo de Goias.")


if __name__ == "__main__":
    main()
