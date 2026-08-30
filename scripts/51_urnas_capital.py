"""Voto de vereador por LOCAL DE VOTACAO, com coordenada — o mapa que faltava.

A aba de vereador mostrava distribuicao por zona eleitoral e dizia, com razao,
que nao ha' mapa: o TSE nao publica malha de zona. Mas publica outra coisa —
**a coordenada de cada local de votacao** — e o voto por secao. Juntando os dois,
o mapa existe: nao em poligono, em ponto.

E' um grao mais fino que qualquer outra tela deste projeto. No mapa municipal, a
unidade e' o municipio; aqui, dentro de UM municipio, sao 353 pontos em Goiania.
E' a diferenca entre saber que um vereador foi votado na cidade e ver em quais
escolas ele foi votado.

**Tres armadilhas medidas neste arquivo, e as tres produziriam numero redondo e
falso:**

1. **O turno duplica.** O arquivo de locais traz 1o e 2o turno com linhas
   identicas. Somar os dois dava 2.060.548 eleitores em Goiania — o dobro dos
   1.030.274 reais.
2. **A chave da secao e' (zona, secao), nao a secao.** Sao 612 numeros de secao
   distintos e **3.040 pares** (zona, secao): o numero se repete entre zonas. E'
   o mesmo erro que o `SQ_CANDIDATO` repetido entre anos produzia, e que este
   projeto ja' documenta.
3. **O local tambem.** 94 numeros de local distintos, **353 pares** (zona,
   local). Contar por numero daria um mapa com um quarto dos pontos.

**A coordenada tem sentinela.** O TSE grava `-1` onde nao sabe. Um `-1` lido como
numero poe a escola no Atlantico, a 1.800 km da cidade — e o mapa continuaria
parecendo certo, so' com um ponto solitario no oceano. Em Goiania sao 4 locais
sem coordenada de 353; eles saem do mapa E aparecem na contagem, nunca somem
calados.

**Local que existe no voto e nao no cadastro nao e' descartado.** Em Goiania de
2024 ha' um: a Escola Municipal Buena Vista (zona 134, local 1910), com 345
votos, presente no arquivo de secao e ausente no de locais. Descartar seria
perder 0,047% dos votos em silencio, e a soma por local deixaria de fechar com o
total do candidato — a divergencia apareceria depois, num numero que ninguem
saberia explicar. Ele entra na lista com coordenada nula: fica fora do mapa, e
dentro da contagem.

**Por que so' a capital, e so' os eleitos.** O arquivo de secao de Goias tem 1,3
milhao de linhas para 2024 — e Goias e' um estado medio. Fazer isso para as 26
capitais e todos os candidatos seria payload de centenas de MB. A tela mostra os
eleitos, que sao quem exerce o mandato, e o total por local, que e' o
denominador de todo o resto.
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

CD_VEREADOR = 13
ANO = 2024
LOCAIS = ("https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao"
          "/eleitorado_local_votacao_{ano}.zip")
SECAO = ("https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao"
         "/votacao_secao_{ano}_{uf}.zip")
# a caixa de Goias, generosa: serve para rejeitar sentinela, nao para recortar
CAIXA = (-19.6, -12.3, -53.3, -45.9)   # latMin, latMax, lonMin, lonMax


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def baixa(url, destino):
    cmd = ["curl.exe", "-sS", "-L", "--max-time", "3600", "-o", str(destino)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True)
    return r.returncode == 0 and destino.exists() and destino.stat().st_size > 1e6


def um_csv(zipe, filtro=None):
    with zipfile.ZipFile(zipe) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        alvo = next((n for n in nomes if filtro and filtro in n.upper()), nomes[0])
        with z.open(alvo) as f:
            return pd.read_csv(f, sep=";", encoding="latin-1", quotechar='"',
                               low_memory=False)


def main():
    uf = sys.argv[1] if len(sys.argv) > 1 else "GO"
    cidade = sys.argv[2] if len(sys.argv) > 2 else "GOIANIA"
    cfg.RAW.mkdir(parents=True, exist_ok=True)

    # ---- locais, com coordenada ----
    zl = cfg.RAW / f"locais_{ANO}.zip"
    print(f"locais de votação {ANO}...", flush=True)
    if not baixa(LOCAIS.format(ano=ANO), zl):
        raise SystemExit("falhou o download dos locais")
    try:
        L = um_csv(zl)
    finally:
        zl.unlink(missing_ok=True)

    L = L[(L["SG_UF"] == uf) & (L["NM_MUNICIPIO"].map(sem_acento) == cidade)]
    # SO' O 1o TURNO: o arquivo repete as mesmas linhas no 2o — ver docstring
    L = L[pd.to_numeric(L["NR_TURNO"], errors="coerce") == 1].copy()
    L["lat"] = pd.to_numeric(L["NR_LATITUDE"], errors="coerce")
    L["lon"] = pd.to_numeric(L["NR_LONGITUDE"], errors="coerce")
    a, b, c, d_ = CAIXA
    # `-1` e' sentinela do TSE, nao coordenada. A caixa rejeita sem citar o -1,
    # porque amanha a sentinela pode ser outra.
    L["ok"] = L["lat"].between(a, b) & L["lon"].between(c, d_)

    # a chave e' (zona, local), nunca o local sozinho — ver docstring
    loc = (L.groupby(["NR_ZONA", "NR_LOCAL_VOTACAO"], as_index=False)
           .agg(nome=("NM_LOCAL_VOTACAO", "first"),
                bairro=("NM_BAIRRO", "first"),
                lat=("lat", "first"), lon=("lon", "first"),
                ok=("ok", "all"),
                secoes=("NR_SECAO", "nunique"),
                eleitores=("QT_ELEITOR_SECAO", "sum")))
    print(f"  {len(loc)} locais | {int(loc.ok.sum())} com coordenada | "
          f"{int(loc.eleitores.sum()):,} eleitores | "
          f"{int(loc.secoes.sum()):,} seções", flush=True)

    # ---- voto por seção ----
    zs = cfg.RAW / f"secao_{ANO}_{uf}.zip"
    print(f"votação por seção {uf} {ANO}...", flush=True)
    if not baixa(SECAO.format(ano=ANO, uf=uf), zs):
        raise SystemExit("falhou o download da votação por seção")
    try:
        V = um_csv(zs)
    finally:
        zs.unlink(missing_ok=True)

    V = V[(V["NM_MUNICIPIO"].map(sem_acento) == cidade)
          & (pd.to_numeric(V["CD_CARGO"], errors="coerce") == CD_VEREADOR)
          & (pd.to_numeric(V["NR_TURNO"], errors="coerce") == 1)].copy()
    V["QT_VOTOS"] = pd.to_numeric(V["QT_VOTOS"], errors="coerce").fillna(0)
    print(f"  {len(V):,} linhas de voto | "
          f"{V['SQ_CANDIDATO'].nunique():,} candidaturas", flush=True)

    # quem exerce o mandato: os eleitos, lidos do arquivo de vereador ja' publicado
    fver = cfg.PROCESSED / "web" / uf / "vereador.json"
    eleitos = set()
    if fver.exists():
        ver = json.loads(fver.read_text(encoding="utf-8"))
        for f in (ver.get("anos", {}).get(str(ANO), {}) or {}).get("fichas", []):
            if f.get("el"):
                eleitos.add(str(f.get("sq")))
    print(f"  {len(eleitos)} eleitos conhecidos", flush=True)

    idx = {(int(r.NR_ZONA), int(r.NR_LOCAL_VOTACAO)): i
           for i, r in enumerate(loc.itertuples())}
    V["k"] = list(zip(pd.to_numeric(V["NR_ZONA"], errors="coerce").astype("Int64"),
                      pd.to_numeric(V["NR_LOCAL_VOTACAO"],
                                    errors="coerce").astype("Int64")))
    V["i"] = V["k"].map(lambda k: idx.get((k[0], k[1])) if pd.notna(k[0]) else None)

    # Local presente no voto e ausente no cadastro entra sem coordenada — ver
    # docstring. Descartar perderia voto em silencio e quebraria a soma.
    falt = V[V["i"].isna()]
    extras = []
    if len(falt):
        novos = (falt.groupby(["NR_ZONA", "NR_LOCAL_VOTACAO"], as_index=False)
                 .agg(nome=("NM_LOCAL_VOTACAO", "first"),
                      votos=("QT_VOTOS", "sum")))
        print(f"  {len(novos)} local(is) no voto e não no cadastro, "
              f"{int(novos.votos.sum()):,} votos — entram sem coordenada:")
        for r in novos.itertuples():
            i = len(loc) + len(extras)
            idx[(int(r.NR_ZONA), int(r.NR_LOCAL_VOTACAO))] = i
            extras.append({"n": str(r.nome)[:52], "b": "", "z": int(r.NR_ZONA),
                           "lat": None, "lon": None, "e": 0})
            print(f"     zona {int(r.NR_ZONA)} · {str(r.nome)[:44]} "
                  f"({int(r.votos):,} votos)")
        V["i"] = V["k"].map(lambda k: idx.get((k[0], k[1]))
                            if pd.notna(k[0]) else None)
    V = V.dropna(subset=["i"])
    V["i"] = V["i"].astype(int)

    # total por local: o denominador de tudo
    nLocais = len(loc) + len(extras)
    tot = V.groupby("i")["QT_VOTOS"].sum()
    totalLocal = [float(tot.get(i, 0)) for i in range(nLocais)]

    fichas = []
    if eleitos:
        E = V[V["SQ_CANDIDATO"].astype(str).isin(eleitos)]
        for sq, g in E.groupby("SQ_CANDIDATO"):
            s = g.groupby("i")["QT_VOTOS"].sum()
            s = s[s > 0].sort_index()
            fichas.append({
                "sq": str(sq),
                "n": str(g["NM_VOTAVEL"].iloc[0]),
                "t": float(g["QT_VOTOS"].sum()),
                "li": [int(x) for x in s.index],
                "lv": [float(x) for x in s.values],
            })
        fichas.sort(key=lambda f: -f["t"])

    obj = {
        "cidade": cidade.title(), "uf": uf, "ano": ANO,
        "eleitores": int(loc.eleitores.sum()),
        "secoes": int(loc.secoes.sum()),
        "semCoordenada": int((~loc.ok).sum()) + len(extras),
        "semCadastro": len(extras),
        "locais": [{"n": str(r.nome)[:52], "b": str(r.bairro)[:34],
                    "z": int(r.NR_ZONA),
                    "lat": round(float(r.lat), 5) if r.ok else None,
                    "lon": round(float(r.lon), 5) if r.ok else None,
                    "e": int(r.eleitores)} for r in loc.itertuples()] + extras,
        "totalLocal": totalLocal,
        "fichas": fichas,
    }
    saida = cfg.PROCESSED / "web" / uf / f"urnas_{ANO}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
    print(f"\n{saida.name}: {saida.stat().st_size/1024:.0f} KB | "
          f"{len(fichas)} eleitos, {nLocais} locais "
          f"({obj['semCoordenada']} sem coordenada)")
    if fichas:
        print("\n  mais votados, e onde:")
        for f in fichas[:5]:
            j = f["lv"].index(max(f["lv"]))
            print(f"    {f['n'][:30]:<32}{int(f['t']):>7,} votos | "
                  f"maior local: {obj['locais'][f['li'][j]]['n'][:30]} "
                  f"({int(max(f['lv']))})")


if __name__ == "__main__":
    main()
