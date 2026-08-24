"""Propoe correcoes de pareamento para revisao humana. NAO grava o override.

`26_audita_pareamento.py` diz quais nomes do TSE nao acham par no IBGE. Propor o
par por semelhanca de texto e' perigoso: um par errado NAO perde voto, ele poe
voto no municipio errado, some no mapa e passa por certo.

**O que esses orfaos sao.** A primeira hipotese - municipio do IBGE que ficou
sem par - esta errada: sao 153 nomes orfaos no TSE contra 5 municipios do IBGE
sem voto nenhum. Ou seja, quase todo alvo JA recebe voto. O que acontece e' que
**o TSE mudou a grafia ao longo da serie**: "MOJI GUACU" nos pleitos antigos e
"MOGI GUACU" nos recentes. A grafia nova pareia, a velha nao, e o municipio
perde so os anos antigos. O buraco nao e' no mapa de um ano - e' na linha do
tempo, que e' pior de enxergar.

**O teste que decide.** Se duas grafias sao o mesmo lugar, elas nunca aparecem
no mesmo arquivo: um municipio nao vota duas vezes no mesmo pleito. Se aparecem
juntas, sao lugares diferentes e o par proposto esta errado. Toda sugestao aqui
passa por esse crivo, e o que reprova vai para decisao manual.

Metodos, do mais seguro para o menos:

  colapso    identicos ao remover espacos - resolve "Sant'Ana" contra "SANTANA".
  apostrofo  "D'X" tratado como "DO X" - "Espigao D'Oeste" / "ESPIGAO DO OESTE".
  prefixo    um alvo unico comeca com (ou e' comecado por) o nome do TSE -
             "CAMPOS" -> "Campos dos Goytacazes".
  parecido   distancia de edicao alta e alvo unico - "PIRACUNUNGA" ->
             "Pirassununga".
  AMBIGUO    varios alvos, nenhum, ou reprovado na coocorrencia. Decisao manual.

A saida e' um CSV de trabalho. O arquivo que vale continua sendo
`municipios_tse_ibge.csv`, feito a mao e versionado.
"""
import difflib
import re
import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")
aud = import_module("26_audita_pareamento")

CORTE = 0.82


def colapsar(s):
    return s.replace(" ", "")


def desapostrofar(s):
    """"ESPIGAO D OESTE" -> "ESPIGAODOOESTE"; o TSE escreve a preposicao."""
    return colapsar(re.sub(r"\bD (?=[AEIOU])", "DO ", s))


def varrer():
    """orfaos, e quem aparece em cada arquivo — para o teste de coocorrencia."""
    mapa, cods = aud.indices_uf()
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    # chave (uf, nome): "LUISIANIA" existe no PR e em SP apontando para
    # municipios diferentes, e uma chave so de nome nao cabe os dois
    corr = {(u, n): c for u, n, c in
            zip(ov["uf"], ov["nome_norm_tse"], ov["cod_ibge"])}
    orfaos = {}
    presenca = defaultdict(set)          # (uf, nome_norm) -> {"cargo/ano"}

    for cargo in aud.CARGOS:
        for ano in cfg.ANOS:
            f = cfg.INTERIM / f"votos_br_{cargo}_{ano}.csv"
            if not f.exists():
                continue
            marca = f"{cargo}/{ano}"
            d = pd.read_csv(f, usecols=lambda c: c in aud.COLS, dtype=str,
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
            for uf, g in d.groupby("SG_UF"):
                uf = str(uf)
                if uf not in mapa:
                    continue
                for nome in g["nome_norm"].unique():
                    presenca[(uf, str(nome))].add(marca)
                cod = g["nome_norm"].map(mapa[uf])
                falta = cod.isna()
                if falta.any():
                    sug = g.loc[falta, "nome_norm"].map(
                        lambda n: corr.get((uf, n)))
                    cod = cod.fillna(sug.where(sug.isin(cods[uf])))
                for nome, gg in g[cod.isna()].groupby("nome_norm"):
                    k = (uf, str(nome))
                    orfaos[k] = orfaos.get(k, 0) + int(gg["votos"].sum())
            del d
        print(f"[{cargo}] varrido", flush=True)
    return orfaos, presenca


def casar(nome, alvos):
    """alvos: {nome_norm_ibge: (cod, nome_original)} — a UF inteira."""
    chaves = list(alvos)
    for metodo, chave in (("colapso", colapsar), ("apostrofo", desapostrofar)):
        alvo = chave(nome)
        iguais = [k for k in chaves if chave(k) == alvo]
        if len(iguais) == 1:
            return metodo, iguais[0]

    pref = [k for k in chaves if k.startswith(nome + " ") or nome.startswith(k + " ")]
    if len(pref) == 1:
        return "prefixo", pref[0]

    perto = difflib.get_close_matches(nome, chaves, n=3, cutoff=CORTE)
    if len(perto) == 1:
        return "parecido", perto[0]
    return "AMBIGUO", " | ".join(perto)


def main():
    orfaos, presenca = varrer()
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    por_uf = {uf: {r.nome_norm: (r.cod_ibge, r.nome) for r in g.itertuples()}
              for uf, g in dim.groupby("uf")}

    linhas, reprovados = [], 0
    for (uf, nome), votos in sorted(orfaos.items(), key=lambda x: -x[1]):
        metodo, achado = casar(nome, por_uf.get(uf, {}))
        cod, oficial = por_uf.get(uf, {}).get(achado, ("", achado))

        # o crivo: um municipio nao vota duas vezes no mesmo pleito
        junto = sorted(presenca[(uf, nome)] & presenca[(uf, achado)]) if cod else []
        if junto:
            reprovados += 1
            metodo, cod, oficial = "AMBIGUO", "", f"{oficial} (junto em {junto[0]})"

        linhas.append({"uf": uf, "nome_norm_tse": nome, "votos": votos,
                       "metodo": metodo, "cod_ibge": cod, "nome_ibge": oficial,
                       "anos_tse": len(presenca[(uf, nome)])})

    out = pd.DataFrame(linhas)
    f = cfg.OVERRIDES / "_sugestoes_pareamento.csv"
    out.to_csv(f, index=False, encoding="utf-8")

    print(f"\n{len(out)} nomes sem par, {out['votos'].sum():,} votos")
    print(f"{reprovados} propostas reprovadas por aparecerem no mesmo arquivo\n")
    print(out.groupby("metodo")
             .agg(nomes=("uf", "size"), votos=("votos", "sum"))
             .sort_values("votos", ascending=False).to_string())

    amb = out[out["cod_ibge"] == ""]
    print(f"\n=== {len(amb)} sem proposta, {amb['votos'].sum():,} votos ===")
    if len(amb):
        print(amb[["uf", "nome_norm_tse", "votos", "nome_ibge"]]
              .to_string(index=False))
    print(f"\nrevisar: {f}")


if __name__ == "__main__":
    main()
