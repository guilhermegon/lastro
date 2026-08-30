"""Voto de vereador por LOCAL DE VOTACAO em TODOS os municipios de uma UF.

Generaliza `51_urnas_capital.py`, que faz uma cidade por vez, para o estado
inteiro a partir de UM par de downloads. Goias e' o piloto: 246 municipios.

**O defeito que a primeira generalizacao produziu, e que este arquivo conserta.**
`51_` carrega uma constante `CAIXA` com os limites de Goias, usada para rejeitar
a sentinela `-1` que o TSE grava onde nao sabe a coordenada. Rodar aquele script
nas 26 capitais rejeitou 100% das coordenadas de todas elas - Sao Paulo, Recife
e Belem caem fora da caixa de Goias - e mesmo assim os 26 arquivos foram
gravados, com "352 sem coordenada" no relatorio e codigo de saida zero. Um mapa
vazio que se anuncia como sucesso e' pior que um erro, porque ninguem vai
procurar.

A correcao nao e' uma caixa maior. E' **a caixa de cada municipio, tirada da
malha do IBGE que o projeto ja' versiona**: um ponto so' e' aceito se cai no
retangulo do proprio municipio, com uma folga de 0,05 grau (~5 km) para a
imprecisao do geocodigo do TSE. Isso rejeita a sentinela sem cita-la, rejeita a
escola trocada de estado, e nao depende de eu lembrar de trocar um numero.

**Tres armadilhas herdadas de `51_`, todas medidas e todas ainda ativas aqui:**

1. **O turno duplica.** O arquivo de locais traz 1o e 2o turno com linhas
   identicas. Somar os dois dava 2.060.548 eleitores em Goiania, o dobro dos
   1.030.274 reais.
2. **A chave da secao e' (zona, secao), nao a secao**, e a do local e' (zona,
   local). Em Goiania sao 612 numeros de secao distintos para 3.040 pares, e 94
   numeros de local para 353 pares. Contar por numero daria um mapa com um
   quarto dos pontos.
3. **Local que existe no voto e nao no cadastro nao e' descartado.** Entra com
   coordenada nula: fica fora do desenho e dentro da contagem. Descartar
   perderia voto em silencio e a soma por local deixaria de fechar com o total
   do candidato.

**Os eleitos vem do arquivo de vereador ja' publicado**, por municipio. Nos oito
municipios sem totalizacao em 2024 nao ha eleito nenhum a marcar - o mapa deles
mostra o total por local e os candidatos mais votados, que e' o que existe.
"""
import json
import subprocess
import sys
import unicodedata
import zipfile
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

CD_VEREADOR = 13
ANO = 2024
LOCAIS = ("https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao"
          "/eleitorado_local_votacao_{ano}.zip")
SECAO = ("https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao"
         "/votacao_secao_{ano}_{uf}.zip")
# folga sobre a caixa do municipio: o geocodigo do TSE erra alguns quarteiroes,
# e uma caixa justa demais rejeitaria escola de verdade na divisa
FOLGA = 0.05
# so' entram no payload os candidatos que importam para a tela; o resto vive no
# total por local, que e' o denominador de tudo
TOP_POR_CIDADE = 90


# O nome do municipio e' chave de pareamento, e o TSE grafa o mesmo municipio de
# dois jeitos em dois arquivos do mesmo ano: `eleitorado_local_votacao` escreve
# "SAO JOAO D'ALIANCA" e `votacao_secao` escreve "SAO JOAO D ALIANCA". Por isso
# a normalizacao vem de `04_geo`, que tira pontuacao e colapsa espaco, e nao de
# um `sem_acento` que so' tira acento: com o segundo, duas cidades de Goias
# sairam sem mapa nenhum.

def sem_acento(t):
    """So' acento: e' a chave de NOME DE PESSOA, verificada pelo teste-ouro."""
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def chave_mun(t):
    """Chave de NOME DE MUNICIPIO - ver nota acima."""
    return geo.normalizar(t)


def baixa(url, destino):
    if destino.exists() and destino.stat().st_size > 1e6:
        try:
            with zipfile.ZipFile(destino):
                return True
        except zipfile.BadZipFile:
            destino.unlink()
    cmd = ["curl.exe", "-sS", "-L", "--max-time", "3600", "-o", str(destino)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(url)
    subprocess.run(cmd, capture_output=True)
    if not destino.exists():
        return False
    try:
        with zipfile.ZipFile(destino):
            return True
    except zipfile.BadZipFile:
        destino.unlink(missing_ok=True)
        return False


def um_csv(zipe, cols=None):
    with zipfile.ZipFile(zipe) as z:
        alvo = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(alvo) as f:
            return pd.read_csv(f, sep=";", encoding="latin-1", quotechar='"',
                               low_memory=False, usecols=cols)


def caixas_da_malha(uf):
    """(latMin, latMax, lonMin, lonMax) por nome normalizado, da malha do IBGE."""
    f = cfg.PROCESSED / f"{uf.lower()}_municipios.geojson"
    if not f.exists():
        return {}
    g = json.loads(f.read_text(encoding="utf-8"))
    out = {}
    for feat in g["features"]:
        xs, ys = [], []
        geom = feat["geometry"]
        aneis = ([geom["coordinates"]] if geom["type"] == "Polygon"
                 else geom["coordinates"])
        for poli in aneis:
            for anel in poli:
                for x, y in anel:
                    xs.append(x)
                    ys.append(y)
        if not xs:
            continue
        out[chave_mun(feat["properties"]["nome_norm"])] = (
            min(ys) - FOLGA, max(ys) + FOLGA, min(xs) - FOLGA, max(xs) + FOLGA)
    return out


def uma_cidade(nome_norm, L, V, caixa, eleitos, nome_bonito):
    """Monta o payload de um municipio. Devolve None se nao ha local nenhum."""
    Lm = L[L["NM_NORM"] == nome_norm]
    if Lm.empty:
        return None
    Lm = Lm.copy()
    if caixa:
        a, b, c, d_ = caixa
        Lm["ok"] = Lm["lat"].between(a, b) & Lm["lon"].between(c, d_)
    else:
        Lm["ok"] = False

    loc = (Lm.groupby(["NR_ZONA", "NR_LOCAL_VOTACAO"], as_index=False)
           .agg(nome=("NM_LOCAL_VOTACAO", "first"),
                bairro=("NM_BAIRRO", "first"),
                lat=("lat", "first"), lon=("lon", "first"),
                ok=("ok", "all"),
                secoes=("NR_SECAO", "nunique"),
                eleitores=("QT_ELEITOR_SECAO", "sum")))

    Vm = V[V["NM_NORM"] == nome_norm]
    if Vm.empty:
        return None
    Vm = Vm.copy()

    idx = {(int(r.NR_ZONA), int(r.NR_LOCAL_VOTACAO)): i
           for i, r in enumerate(loc.itertuples())}
    chave = list(zip(Vm["NR_ZONA"].astype(int), Vm["NR_LOCAL_VOTACAO"].astype(int)))
    Vm["i"] = [idx.get(k) for k in chave]

    # local no voto e ausente do cadastro entra sem coordenada - ver docstring
    extras = []
    falt = Vm[Vm["i"].isna()]
    if len(falt):
        novos = (falt.groupby(["NR_ZONA", "NR_LOCAL_VOTACAO"], as_index=False)
                 .agg(nome=("NM_LOCAL_VOTACAO", "first")))
        for r in novos.itertuples():
            i = len(loc) + len(extras)
            idx[(int(r.NR_ZONA), int(r.NR_LOCAL_VOTACAO))] = i
            extras.append({"n": str(r.nome)[:52], "b": "", "z": int(r.NR_ZONA),
                           "lat": None, "lon": None, "e": 0})
        Vm["i"] = [idx.get(k) for k in chave]
    Vm = Vm.dropna(subset=["i"])
    if Vm.empty:
        return None
    Vm["i"] = Vm["i"].astype(int)

    nLocais = len(loc) + len(extras)
    tot = Vm.groupby("i")["QT_VOTOS"].sum()
    totalLocal = [int(tot.get(i, 0)) for i in range(nLocais)]

    porcand = Vm.groupby("SQ_CANDIDATO")["QT_VOTOS"].sum().sort_values(ascending=False)
    # os eleitos primeiro, e depois os mais votados ate' o teto: quem exerce o
    # mandato nunca cai por corte de payload
    ordem = ([s for s in porcand.index if str(s) in eleitos]
             + [s for s in porcand.index if str(s) not in eleitos])
    ordem = ordem[:max(TOP_POR_CIDADE, len(eleitos))]

    fichas = []
    for sq in ordem:
        g = Vm[Vm["SQ_CANDIDATO"] == sq]
        s = g.groupby("i")["QT_VOTOS"].sum()
        s = s[s > 0].sort_index()
        if s.empty:
            continue
        fichas.append({
            "sq": str(sq), "n": str(g["NM_VOTAVEL"].iloc[0]),
            "el": str(sq) in eleitos,
            "t": int(g["QT_VOTOS"].sum()),
            "li": [int(x) for x in s.index],
            "lv": [int(x) for x in s.values],
        })
    fichas.sort(key=lambda f: -f["t"])

    return {
        "cidade": nome_bonito, "uf": None, "ano": ANO,
        "eleitores": int(loc["eleitores"].sum()),
        "secoes": int(loc["secoes"].sum()),
        "semCoordenada": int((~loc["ok"]).sum()) + len(extras),
        "semCadastro": len(extras),
        "locais": [{"n": str(r.nome)[:52], "b": str(r.bairro)[:34],
                    "z": int(r.NR_ZONA),
                    "lat": round(float(r.lat), 5) if r.ok else None,
                    "lon": round(float(r.lon), 5) if r.ok else None,
                    "e": int(r.eleitores)} for r in loc.itertuples()] + extras,
        "totalLocal": totalLocal,
        "fichas": fichas,
    }


def main():
    uf = (sys.argv[1] if len(sys.argv) > 1 else "GO").upper()
    cfg.RAW.mkdir(parents=True, exist_ok=True)

    caixas = caixas_da_malha(uf)
    print(f"{uf}: {len(caixas)} caixas municipais da malha do IBGE", flush=True)
    if not caixas:
        raise SystemExit(f"sem malha para {uf} - a validacao de coordenada "
                         f"depende dela, e sem ela o mapa sai vazio em silencio")

    zl = cfg.RAW / f"locais_{ANO}.zip"
    print(f"locais de votacao {ANO}...", flush=True)
    if not baixa(LOCAIS.format(ano=ANO), zl):
        raise SystemExit("falhou o download dos locais")
    L = um_csv(zl, cols=["SG_UF", "NM_MUNICIPIO", "NR_TURNO", "NR_ZONA",
                         "NR_SECAO", "NR_LOCAL_VOTACAO", "NM_LOCAL_VOTACAO",
                         "NM_BAIRRO", "NR_LATITUDE", "NR_LONGITUDE",
                         "QT_ELEITOR_SECAO"])
    L = L[L["SG_UF"] == uf].copy()
    # SO' O 1o TURNO: o arquivo repete as mesmas linhas no 2o - ver docstring
    L = L[pd.to_numeric(L["NR_TURNO"], errors="coerce") == 1]
    L["lat"] = pd.to_numeric(L["NR_LATITUDE"], errors="coerce")
    L["lon"] = pd.to_numeric(L["NR_LONGITUDE"], errors="coerce")
    L["NM_NORM"] = L["NM_MUNICIPIO"].map(chave_mun)
    print(f"  {len(L):,} secoes em {L['NM_NORM'].nunique()} municipios",
          flush=True)

    zs = cfg.RAW / f"secao_{ANO}_{uf}.zip"
    print(f"votacao por secao {uf} {ANO}...", flush=True)
    if not baixa(SECAO.format(ano=ANO, uf=uf), zs):
        raise SystemExit("falhou o download da votacao por secao")
    V = um_csv(zs, cols=["NM_MUNICIPIO", "NR_TURNO", "CD_CARGO", "NR_ZONA",
                         "NR_LOCAL_VOTACAO", "NM_LOCAL_VOTACAO",
                         "SQ_CANDIDATO", "NM_VOTAVEL", "QT_VOTOS"])
    V = V[(pd.to_numeric(V["CD_CARGO"], errors="coerce") == CD_VEREADOR)
          & (pd.to_numeric(V["NR_TURNO"], errors="coerce") == 1)].copy()
    V["QT_VOTOS"] = pd.to_numeric(V["QT_VOTOS"], errors="coerce").fillna(0)
    V["NM_NORM"] = V["NM_MUNICIPIO"].map(chave_mun)
    print(f"  {len(V):,} linhas em {V['NM_NORM'].nunique()} municipios",
          flush=True)

    dim = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype=str)
    nomes = dict(zip(dim["nome_norm"].map(chave_mun), dim["nome"]))
    cods = dict(zip(dim["nome_norm"].map(chave_mun), dim["cod_ibge"]))

    saida = cfg.PROCESSED / "web" / uf / "urnas"
    saida.mkdir(parents=True, exist_ok=True)
    cidades_dir = cfg.PROCESSED / "web" / uf / "cidades"

    feitos, bytes_tot, sem_coord, indice = 0, 0, [], []
    for nn in sorted(caixas):
        cod = cods.get(nn)
        if not cod:
            continue
        eleitos = set()
        fver = cidades_dir / f"{cod}.json"
        if fver.exists():
            ver = json.loads(fver.read_text(encoding="utf-8"))
            for f in (ver.get("anos", {}).get(str(ANO), {}) or {}).get("fichas", []):
                if f.get("el"):
                    eleitos.add(str(f.get("sq")))
        obj = uma_cidade(nn, L, V, caixas.get(nn), eleitos, nomes.get(nn, nn))
        if obj is None:
            print(f"    {nomes.get(nn, nn)}: sem local ou sem voto", flush=True)
            continue
        obj["uf"] = uf
        obj["cod"] = cod
        p = saida / f"{cod}.json"
        p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
        feitos += 1
        bytes_tot += p.stat().st_size
        comcoord = len(obj["locais"]) - obj["semCoordenada"]
        if comcoord == 0:
            sem_coord.append(nomes.get(nn, nn))
        indice.append({"cod": cod, "locais": len(obj["locais"]),
                       "comCoord": comcoord, "eleitos": len(eleitos)})

    (saida / "indice.json").write_text(
        json.dumps({"uf": uf, "ano": ANO, "cidades": indice},
                   separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    print(f"\n{feitos} cidades | {bytes_tot/1024/1024:.2f} MB | "
          f"media {bytes_tot/max(feitos,1)/1024:.0f} KB", flush=True)
    tot_l = sum(c["locais"] for c in indice)
    tot_c = sum(c["comCoord"] for c in indice)
    print(f"locais: {tot_l:,} | com coordenada {tot_c:,} "
          f"({tot_c/max(tot_l,1)*100:.1f}%)", flush=True)
    # o gate: se muita cidade sai sem UM ponto, a caixa esta' errada de novo
    if sem_coord:
        print(f"\nSEM NENHUMA COORDENADA em {len(sem_coord)} cidade(s): "
              f"{', '.join(sem_coord[:20])}", flush=True)
    if tot_c < tot_l * 0.5:
        raise SystemExit(f"ABORTADO: so' {tot_c/max(tot_l,1)*100:.0f}% dos "
                         f"locais tem coordenada. Foi assim que 26 capitais "
                         f"sairam com mapa vazio e codigo de saida zero.")


if __name__ == "__main__":
    main()
