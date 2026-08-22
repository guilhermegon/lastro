"""Rivais territoriais dos eleitos, em todas as UFs, nos cargos proporcionais.

Generaliza `10_rivais.py`, que so fazia Goias no estadual. A pergunta continua
sendo "quem disputa o mesmo chao que este eleito?", e nao "quem teve votacao
parecida em tamanho" - por isso a medida e' sobreposicao entre vetores
municipais, nunca diferenca de totais.

Duas medidas, que respondem coisas diferentes:

  afinidade (cosseno)  quanto os dois mapas tem o mesmo FORMATO. Simetrica.
  pressao              quanto do voto DESTE eleito esta em municipios onde o
                       rival tambem e' forte, ponderado pela forca do rival ali.
                       NAO e' simetrica: um gigante pressiona um pequeno muito
                       mais do que o contrario.

So os proporcionais entram. Nos majoritarios cada partido lanca um nome e a
disputa nao se da dentro de uma lista - "rival" ali seria o proprio adversario
da eleicao, que a tela do cargo ja mostra inteiro.

A separacao entre aliado e adversario NAO sai do dado eleitoral: vem de
`data/overrides/partidos_espectro.csv`, cinco bandas. E' juizo externo e
discutivel - trocar o arquivo troca a leitura, sem tocar no codigo. Por isso a
saida carrega junto o controle que impede ler demais no resultado.

**A afericao, que e' o ponto.** Em Goias o rival n.1 saiu aliado na maioria dos
casos, e isso parece achado ate' se perguntar quantas candidaturas ja estao na
mesma faixa ideologica: se dois tercos estao, "aliado" venceria por acaso. Por
isso gravamos, por pleito:

  esperado   fracao media de candidaturas na mesma banda do eleito - o acaso
  observado  fracao de eleitos cujo rival n.1 e' de fato aliado

e, mais importante, o **teste pareado**: para o MESMO eleito, o aliado mais
pressionante pressiona mais que o adversario mais pressionante? Esse controla a
composicao por completo, e e' o unico numero aqui que sobrevive sozinho.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

WEB = cfg.PROCESSED / "web"
CARGOS = ["estadual", "federal"]
MIN_VOTOS = 1000   # abaixo disso o vetor municipal e' ruido, nao geografia
# Com poucos municipios nao ha geografia a medir: no Distrito Federal, que e'
# um municipio so, o cosseno entre dois candidatos quaisquer da exatamente
# 1,000 e "quem disputa o mesmo chao" vira "quem teve mais voto". O painel
# pareceria certo e estaria ordenando outra coisa.
MIN_MUNICIPIOS = 3
TOP = 6            # quantos rivais guardar de cada lado
COLS = ["SG_UF", "NM_MUNICIPIO", "SQ_CANDIDATO", "NM_URNA_CANDIDATO",
        "SG_PARTIDO", "DS_SIT_TOT_TURNO", "NR_TURNO",
        "QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]


def carregar(cargo, ano):
    f = cfg.INTERIM / f"votos_br_{cargo}_{ano}.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f, usecols=lambda c: c in COLS, dtype=str, low_memory=False)
    for c in ("QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"):
        if c not in d.columns:
            d[c] = 0
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    # A coluna de votos muda ao longo da serie: 1998 zera QT_VOTOS_NOMINAIS e
    # 2002 nao traz a _VALIDOS. Resolver por soma, nunca por ano fixo.
    col = ("QT_VOTOS_NOMINAIS" if d["QT_VOTOS_NOMINAIS"].sum() > 0
           else "QT_VOTOS_NOMINAIS_VALIDOS")
    d["votos"] = d[col]
    if "NR_TURNO" in d.columns:
        d["NR_TURNO"] = pd.to_numeric(d["NR_TURNO"], errors="coerce").fillna(1)
    else:
        d["NR_TURNO"] = 1
    return d[d["NR_TURNO"] == 1]


def indices_uf():
    """Mesma ordenacao de municipios que 19_ usa, para os indices baterem."""
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    mapa, indice, nomes = {}, {}, {}
    for uf, g in dim.groupby("uf"):
        g = g.sort_values("cod_ibge")
        mapa[uf] = dict(zip(g["nome_norm"], g["cod_ibge"]))
        indice[uf] = {c: i for i, c in enumerate(g["cod_ibge"])}
        nomes[uf] = list(g["nome"])
    return mapa, indice, nomes


def processar(g, idx, n_mun, escore, banda, lin):
    """Fichas de rival de um (UF, cargo, ano), ou None se nao houver disputa."""
    n = n_mun
    if n < MIN_MUNICIPIOS:
        return None
    tot = g.groupby("SQ_CANDIDATO", observed=True)["votos"].sum()
    vivos = tot[tot >= MIN_VOTOS].index
    if len(vivos) < 4:
        return None
    g = g[g["SQ_CANDIDATO"].isin(vivos)]
    info = g.sort_values("votos", ascending=False).groupby(
        "SQ_CANDIDATO", observed=True).first()
    ordem = list(info.index)
    pos = {sq: i for i, sq in enumerate(ordem)}

    M = np.zeros((len(ordem), n))
    for r in g.itertuples():
        M[pos[r.SQ_CANDIDATO], idx[r.cod_ibge]] += r.votos

    totais = M.sum(axis=1, keepdims=True)
    totais[totais == 0] = 1.0
    norma = np.linalg.norm(M, axis=1, keepdims=True)
    norma[norma == 0] = 1.0
    U = M / norma
    AFIN = U @ U.T
    np.fill_diagonal(AFIN, 0.0)

    total_mun = M.sum(axis=0)
    total_mun[total_mun == 0] = 1.0
    FORCA = M / total_mun                 # fatia do candidato em cada municipio
    PRESSAO = (M / totais) @ FORCA.T      # assimetrica, de proposito
    np.fill_diagonal(PRESSAO, 0.0)

    pnorm = info["SG_PARTIDO"].astype(str).map(
        lambda s: lin.get(s.upper().strip(), s.upper().strip()))
    esc = pnorm.map(escore).fillna(3).astype(int).to_numpy()
    bnd = pnorm.map(banda).fillna("centro").to_numpy()
    eleito = (info["DS_SIT_TOT_TURNO"].astype(str).str.upper()
              .str.contains("ELEITO|MEDIA", regex=True, na=False)).to_numpy()
    nome = info["NM_URNA_CANDIDATO"].astype(str).to_numpy()
    part = info["SG_PARTIDO"].astype(str).to_numpy()
    votos = M.sum(axis=1)

    fichas, pares = {}, []
    for i in np.where(eleito)[0]:
        dist = np.abs(esc - esc[i])
        saida = {}
        for lado, mask in (("al", dist <= 1), ("ad", dist >= 2)):
            c = np.where(mask)[0]
            c = c[c != i]
            if not len(c):
                continue
            sel = c[np.argsort(-PRESSAO[i, c])][:TOP]
            lista = []
            for j in sel:
                if PRESSAO[i, j] <= 0:
                    continue
                contato = M[i] * FORCA[j]
                top = [k for k in np.argsort(-contato)[:3] if contato[k] > 0]
                lista.append({
                    "n": nome[j], "p": part[j], "b": bnd[j],
                    "el": bool(eleito[j]), "t": int(votos[j]),
                    "af": round(float(AFIN[i, j]), 4),
                    "pr": round(float(PRESSAO[i, j]) * 100, 2),
                    # indice do municipio, nao o nome: base.json ja tem os
                    # nomes e repeti-los aqui custava 11 MB no pais
                    "mun": [int(k) for k in top],
                })
            if lista:
                saida[lado] = lista
        if saida:
            fichas[str(ordem[i])] = {"b": bnd[i], **saida}
            pares.append((saida.get("al", [{}])[0].get("pr"),
                          saida.get("ad", [{}])[0].get("pr")))

    # O acaso: que fracao das candidaturas ja esta na mesma banda do eleito?
    esperado = (float(np.mean([
        float((np.abs(np.delete(esc, i) - esc[i]) <= 1).mean())
        for i in np.where(eleito)[0]])) * 100) if eleito.any() else None
    observado = (float(np.mean([(a or 0) >= (b or 0) for a, b in pares])) * 100
                 if pares else None)
    dupla = [(a, b) for a, b in pares if a is not None and b is not None]
    pareado = (round(float(np.median([a - b for a, b in dupla])), 2)
               if dupla else None)

    return {
        "fichas": fichas,
        "afericao": {
            "n": int(eleito.sum()),
            "esperado": round(esperado, 1) if esperado is not None else None,
            "observado": round(observado, 1) if observado is not None else None,
            "pareado": pareado,
            "nPar": len(dupla),
            "aliadoMais": int(sum(1 for a, b in dupla if a > b)),
        },
    }


def main():
    mapa, indice, nomes = indices_uf()
    linhagem = pd.read_csv(cfg.OVERRIDES / "partidos_linhagem.csv")
    lin = dict(zip(linhagem["sigla_epoca"].astype(str).str.upper().str.strip(),
                   linhagem["partido_norm"]))
    esp = pd.read_csv(cfg.OVERRIDES / "partidos_espectro.csv")
    escore = dict(zip(esp["partido_norm"], esp["escore"]))
    banda = dict(zip(esp["partido_norm"], esp["banda"]))
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    corr = dict(zip(ov["nome_norm_tse"], ov["cod_ibge"]))

    saida = {uf: {c: {} for c in CARGOS} for uf in indice}
    for cargo in CARGOS:
        for ano in cfg.ANOS:
            d = carregar(cargo, ano)
            if d is None:
                continue
            d = d.assign(nome_norm=d["NM_MUNICIPIO"].astype(str).map(geo.normalizar))
            for uf, g in d.groupby("SG_UF"):
                uf = str(uf)
                if uf not in mapa:
                    continue
                cod = g["nome_norm"].map(mapa[uf])
                falta = cod.isna()
                if falta.any():
                    # O override so vale para codigo DESTA UF: "VALPARAISO"
                    # existe em GO e em SP, e a correcao de GO ja vazou para SP.
                    sug = g.loc[falta, "nome_norm"].map(corr)
                    cod = cod.fillna(sug.where(sug.isin(set(indice[uf]))))
                g = g.assign(cod_ibge=cod)
                g = g[g["cod_ibge"].notna()]
                if g.empty:
                    continue
                r = processar(g, indice[uf], len(nomes[uf]), escore, banda, lin)
                if r:
                    saida[uf][cargo][str(ano)] = r
            print(f"[{cargo}/{ano}] {len(d):,} linhas", flush=True)
            del d

    # Um arquivo por UF E por cargo: quem abre o estadual de Sao Paulo nao deve
    # pagar pelo federal. Num arquivo so, SP custava 4 MB para desenhar um
    # painel lateral.
    total, gravados, maior = 0, 0, (0, "")
    for uf, d in saida.items():
        for cargo in CARGOS:
            if not d[cargo]:
                continue
            p = WEB / uf / f"rivais_{cargo}.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(d[cargo], separators=(",", ":"),
                                    ensure_ascii=False), encoding="utf-8")
            tam = p.stat().st_size
            total += tam
            gravados += 1
            maior = max(maior, (tam, f"{uf}/{cargo}"))
    print(f"\n{gravados} arquivos de rivais, {total/1024/1024:.1f} MB no total")
    print(f"maior: {maior[1]} com {maior[0]/1024:.0f} KB")

    print("\n=== o rival n.1 e' aliado? observado vs acaso (estadual) ===")
    print(f"{'UF':<4}{'ano':<6}{'acaso':>8}{'observado':>11}"
          f"{'pareado':>10}{'aliado+':>12}")
    for uf in ("GO", "SP", "MG", "RR"):
        for ano, r in sorted(saida.get(uf, {}).get("estadual", {}).items()):
            a = r["afericao"]
            print(f"{uf:<4}{ano:<6}{a['esperado']:>7}%{a['observado']:>10}%"
                  f"{a['pareado']:>+10} pp{a['aliadoMais']:>7}/{a['nPar']}")


if __name__ == "__main__":
    main()
