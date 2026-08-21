"""Mapa de Goiania por local de votacao: junta voto por secao a coordenadas.

Por que isto existe: nao ha malha publica de zona eleitoral, entao nao da para
desenhar Goiania por zona. Mas o TSE publica `eleitorado_local_votacao` com
NR_LATITUDE/NR_LONGITUDE por secao, e `votacao_secao` com o voto de cada
candidato em cada secao. Juntando os dois por (zona, secao) sai um mapa de
PONTOS - cada ponto e' um local de votacao - que e' mais fino que zona e nao
depende de nenhum poligono.

Duas armadilhas do dado, tratadas aqui:

1. Coordenada ausente vem como -1.0, nao como vazio. Somar ou plotar sem filtrar
   joga pontos no Atlantico, na altura do Golfo da Guine.
2. NR_LOCAL_VOTACAO se repete entre zonas - a chave de local e' (zona, local),
   nao o numero sozinho.

Só faz sentido para os anos em que o TSE publica coordenadas; por isso o ano e'
parametro e o padrao e' 2024.
"""
import subprocess
import sys
import unicodedata
import zipfile
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

ANO = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
CD_VEREADOR = 13
CIDADE = "GOIANIA"

URL_LOCAIS = ("https://cdn.tse.jus.br/estatistica/sead/odsele/"
              "eleitorado_locais_votacao/eleitorado_local_votacao_{ano}.zip")
URL_SECAO = ("https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/"
             "votacao_secao_{ano}_{uf}.zip")


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def baixar(url, destino):
    if destino.exists():
        try:
            with zipfile.ZipFile(destino):
                return destino
        except zipfile.BadZipFile:
            destino.unlink()
    cmd = ["curl.exe", "-sS", "--fail", "--max-time", "1800", "-o", str(destino)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(url)
    for t in range(1, 4):
        print(f"baixando {destino.name} (tentativa {t})...", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and destino.exists():
            try:
                with zipfile.ZipFile(destino):
                    return destino
            except zipfile.BadZipFile:
                pass
        destino.unlink(missing_ok=True)
    raise RuntimeError(f"download de {destino.name} falhou")


def ler_zip(zp, filtro_uf=True):
    with zipfile.ZipFile(zp) as zf:
        csvs = [n for n in zf.namelist() if n.upper().endswith(".CSV")]
        alvo = next((n for n in csvs if f"_{cfg.UF}" in n.upper()), csvs[0])
        print(f"  lendo {alvo}", flush=True)
        with zf.open(alvo) as fh:
            df = pd.read_csv(fh, sep=";", encoding="latin-1", quotechar='"',
                             dtype=str, low_memory=False)
    df.columns = [c.strip().upper() for c in df.columns]
    if filtro_uf and "SG_UF" in df.columns:
        df = df[df["SG_UF"] == cfg.UF]
    return df


def main():
    # ---------- locais com coordenada ----------
    zp = baixar(URL_LOCAIS.format(ano=ANO), cfg.RAW / f"locais_{ANO}.zip")
    loc = ler_zip(zp, filtro_uf=True)
    zp.unlink(missing_ok=True)

    loc = loc[loc["NM_MUNICIPIO"].map(sem_acento) == CIDADE].copy()
    for c in ("NR_LATITUDE", "NR_LONGITUDE"):
        loc[c] = pd.to_numeric(loc[c], errors="coerce")
    antes = len(loc)
    # -1.0 e' o sentinela de coordenada ausente do TSE, nao uma coordenada.
    loc = loc[(loc["NR_LATITUDE"] < -5) & (loc["NR_LONGITUDE"] < -30)]
    print(f"locais: {antes} secoes -> {len(loc)} com coordenada valida "
          f"({antes - len(loc)} descartadas por coordenada ausente)")

    loc["chave"] = loc["NR_ZONA"] + "-" + loc["NR_SECAO"]
    loc["local"] = loc["NR_ZONA"] + "-" + loc["NR_LOCAL_VOTACAO"]
    pontos = (loc.groupby("local", as_index=False)
                 .agg(zona=("NR_ZONA", "first"),
                      nome=("NM_LOCAL_VOTACAO", "first"),
                      bairro=("NM_BAIRRO", "first"),
                      endereco=("DS_ENDERECO", "first"),
                      lat=("NR_LATITUDE", "median"),
                      lon=("NR_LONGITUDE", "median"),
                      n_secoes=("NR_SECAO", "nunique")))
    print(f"locais de votacao distintos em {CIDADE}: {len(pontos)}")

    # ---------- votos por secao ----------
    zp = baixar(URL_SECAO.format(ano=ANO, uf=cfg.UF), cfg.RAW / f"secao_{ANO}.zip")
    sec = ler_zip(zp, filtro_uf=True)
    zp.unlink(missing_ok=True)

    sec = sec[(sec["NM_MUNICIPIO"].map(sem_acento) == CIDADE) &
              (pd.to_numeric(sec["CD_CARGO"], errors="coerce") == CD_VEREADOR)].copy()
    sec["votos"] = pd.to_numeric(sec["QT_VOTOS"], errors="coerce").fillna(0)
    sec["chave"] = sec["NR_ZONA"] + "-" + sec["NR_SECAO"]
    print(f"votacao_secao: {len(sec)} linhas de vereador em {CIDADE}")

    sec = sec.merge(loc[["chave", "local"]].drop_duplicates("chave"),
                    on="chave", how="left")
    orfas = sec["local"].isna().sum()
    if orfas:
        print(f"AVISO {orfas} linhas sem local com coordenada -> descartadas "
              f"({orfas / len(sec) * 100:.1f}%)")
    sec = sec[sec["local"].notna()]

    # votacao_secao mistura candidatos com branco/nulo (sq -1) e voto de legenda
    # (sq -3, um por partido). Sem filtrar, "VOTO BRANCO" viraria o candidato mais
    # votado da cidade. So sobrevive quem consta da lista de candidaturas.
    cand = pd.read_csv(cfg.PROCESSED / "ver_candidato.csv", dtype={"sq": str})
    validos = set(cand.loc[cand["ano"] == ANO, "sq"])
    porloc = (sec.groupby(["SQ_CANDIDATO", "NM_VOTAVEL", "local"], as_index=False)
                 ["votos"].sum())
    porloc = porloc[porloc["votos"] > 0]
    porloc = porloc.rename(columns={"SQ_CANDIDATO": "sq", "NM_VOTAVEL": "nome"})
    antes_f = int(porloc["votos"].sum())
    porloc = porloc[porloc["sq"].isin(validos)]
    print(f"filtro de votaveis: {antes_f} -> {int(porloc['votos'].sum())} votos "
          f"(removidos branco, nulo e legenda)")

    pontos.to_csv(cfg.PROCESSED / f"ver_locais_{ANO}.csv", index=False,
                  encoding="utf-8")
    porloc.to_csv(cfg.PROCESSED / f"ver_voto_local_{ANO}.csv", index=False,
                  encoding="utf-8")

    print(f"\nver_locais_{ANO}.csv: {len(pontos)} pontos")
    print(f"ver_voto_local_{ANO}.csv: {len(porloc)} pares candidato-local, "
          f"{porloc['sq'].nunique()} candidatos")
    print(f"\ncobertura: {int(porloc['votos'].sum())} votos mapeados")
    print("\nbbox de Goiania:",
          f"lat [{pontos['lat'].min():.4f}, {pontos['lat'].max():.4f}]",
          f"lon [{pontos['lon'].min():.4f}, {pontos['lon'].max():.4f}]")
    print("\nlocais com mais secoes:")
    print(pontos.nlargest(5, "n_secoes")[
        ["nome", "bairro", "zona", "n_secoes"]].to_string(index=False))


if __name__ == "__main__":
    main()
