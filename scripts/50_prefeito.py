"""Prefeito eleito por municipio — o pleito municipal que faltava no painel.

O painel tinha o vereador das 26 capitais e nao tinha o executivo municipal. O
prefeito completa o pleito de 2024 e traz uma geografia que nenhum outro cargo
deste projeto tem: **quem governa cada municipio**. Presidente, governador e
senador sao um vencedor por UF; deputado e' voto espalhado. Prefeito e' um
vencedor por municipio — 5.570 disputas separadas no mesmo mapa.

**O que este script produz, e o que ele NAO produz.** Produz o vencedor de cada
municipio: nome, partido, votos e margem sobre o segundo. Nao produz o vetor
municipal de cada candidato, que nos outros cargos e' o coracao do produto —
aqui nao existe: um candidato a prefeito disputa um municipio so'. A pergunta
"onde este candidato tirou voto" nao se aplica; a pergunta que se aplica e'
"quem ganhou aqui, e por quanto".

**Segundo turno existe e importa.** Municipio com mais de 200 mil eleitores tem
segundo turno, e quem venceu no primeiro pode perder no segundo. O vencedor e'
lido do ULTIMO turno disputado em cada municipio, nao do primeiro — pegar o
primeiro daria o mapa errado justamente nas capitais, que sao onde mais gente
mora.

**A margem e' sobre o segundo colocado do mesmo turno.** Em segundo turno ela e'
naturalmente menor, porque sobraram dois; comparar margem de primeiro turno com
margem de segundo mede o formato da disputa, nao a folga do vencedor. O turno
fica no arquivo para a tela poder separar.

**O mais votado nem sempre e' o prefeito, e essa foi a armadilha.** A primeira
versao deste script deu o vencedor de cada municipio como "quem somou mais voto".
O gate de conferencia disparou em 8 municipios de 2024, e abrindo, o padrao e'
outro: em Tucurui (PA), Itaguai (RJ), Merces (MG), Macedonia, Martinopolis,
Narandiba e Sarutaia (SP), **ninguem esta' marcado como eleito** — a disputa
inteira aparece como NAO ELEITO. Sao eleicoes anuladas, sub judice ou com
candidatura indeferida, em que o TSE nao declarou prefeito.

Dar o mais votado como prefeito ali seria inventar um prefeito que nao existe, e
o mapa nao teria como avisar: ficaria colorido igual aos outros 5.553. Entao a
regra e': **vence quem o TSE declara eleito**; nao havendo nenhum, o municipio
sai marcado como *sem prefeito declarado* e a tela mostra isso — nao um vencedor
inventado, nao um branco silencioso.

**O esquema muda de ano para ano** — e' a licao que o `49_` pagou caro. As
colunas sao lidas do proprio arquivo, nunca presumidas.
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

CD_PREFEITO = 11
ANOS = [2000, 2004, 2008, 2012, 2016, 2020, 2024]
URL = ("https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona"
       "/votacao_candidato_munzona_{ano}.zip")
SAIDA = cfg.INTERIM
SIT_ELEITO = ("ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA", "MEDIA",
              "ELEITO 1O TURNO", "ELEITO 2O TURNO")


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


def baixa(ano, destino):
    cmd = ["curl.exe", "-sS", "-L", "--max-time", "2400", "-o", str(destino)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(URL.format(ano=ano))
    r = subprocess.run(cmd, capture_output=True)
    return r.returncode == 0 and destino.exists() and destino.stat().st_size > 1e6


def le_zip(zipe, ano):
    """Um CSV por UF; 2000 pode trazer BRASIL, como 1998 trouxe."""
    partes = []
    with zipfile.ZipFile(zipe) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        porUF = [n for n in nomes if n.upper().endswith(f"_{ano}_BRASIL.CSV") is False]
        alvo = porUF or nomes
        for n in alvo:
            with z.open(n) as f:
                d = pd.read_csv(f, sep=";", encoding="latin-1", quotechar='"',
                                low_memory=False)
            d["CD_CARGO"] = pd.to_numeric(d.get("CD_CARGO"), errors="coerce")
            d = d[d["CD_CARGO"] == CD_PREFEITO]
            if len(d):
                partes.append(d)
    return pd.concat(partes, ignore_index=True) if partes else None


def vencedores(d):
    """O vencedor de cada municipio, no ULTIMO turno que ele disputou."""
    d["NR_TURNO"] = pd.to_numeric(d["NR_TURNO"], errors="coerce")
    voto = ("QT_VOTOS_NOMINAIS_VALIDOS"
            if d.get("QT_VOTOS_NOMINAIS_VALIDOS") is not None
            and pd.to_numeric(d["QT_VOTOS_NOMINAIS_VALIDOS"],
                              errors="coerce").fillna(0).sum() > 0
            else "QT_VOTOS_NOMINAIS")
    d["votos"] = pd.to_numeric(d[voto], errors="coerce").fillna(0)

    # zona -> municipio
    chaves = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_TURNO",
              "SQ_CANDIDATO", "NM_URNA_CANDIDATO", "SG_PARTIDO",
              "DS_SIT_TOT_TURNO"]
    chaves = [c for c in chaves if c in d.columns]
    g = d.groupby(chaves, dropna=False, as_index=False)["votos"].sum()

    # o ultimo turno de CADA municipio — ver docstring
    ult = (g.groupby(["SG_UF", "CD_MUNICIPIO"], as_index=False)["NR_TURNO"]
           .max().rename(columns={"NR_TURNO": "turnoFinal"}))
    g = g.merge(ult, on=["SG_UF", "CD_MUNICIPIO"])
    g = g[g["NR_TURNO"] == g["turnoFinal"]]

    g["sit"] = (g["DS_SIT_TOT_TURNO"].map(sem_acento)
                if "DS_SIT_TOT_TURNO" in g else "")
    g["eleito"] = g["sit"].str.startswith("ELEITO") | g["sit"].isin(SIT_ELEITO)
    g = g.sort_values(["SG_UF", "CD_MUNICIPIO", "eleito", "votos"],
                      ascending=[True, True, False, False])

    # Vence quem o TSE DECLARA eleito, nao quem somou mais voto — ver docstring.
    # A ordenacao poe o eleito na frente; se nao houver nenhum, o primeiro e' so'
    # o mais votado e o municipio sai marcado como sem prefeito declarado.
    primeiro = g.groupby(["SG_UF", "CD_MUNICIPIO"], as_index=False).nth(0)

    # o segundo colocado, para a margem, e' o mais votado ENTRE OS DEMAIS
    resto = g.merge(primeiro[["SG_UF", "CD_MUNICIPIO", "SQ_CANDIDATO"]]
                    .assign(_e=1), on=["SG_UF", "CD_MUNICIPIO", "SQ_CANDIDATO"],
                    how="left")
    resto = resto[resto["_e"].isna()].sort_values(
        ["SG_UF", "CD_MUNICIPIO", "votos"], ascending=[True, True, False])
    segundo = (resto.groupby(["SG_UF", "CD_MUNICIPIO"], as_index=False).nth(0)
               [["SG_UF", "CD_MUNICIPIO", "votos", "SG_PARTIDO"]]
               .rename(columns={"votos": "votos2", "SG_PARTIDO": "partido2"}))

    r = primeiro.merge(segundo, on=["SG_UF", "CD_MUNICIPIO"], how="left")
    r["votos2"] = r["votos2"].fillna(0)
    # `semEleito` e' o que a tela usa para nao pintar um vencedor que nao existe
    r["semEleito"] = ~r["eleito"]
    tot = r["votos"] + r["votos2"]
    r["margem"] = ((r["votos"] - r["votos2"]) / tot.replace(0, pd.NA) * 100).round(2)
    return r


def main():
    cfg.RAW.mkdir(parents=True, exist_ok=True)
    alvos = [int(a) for a in sys.argv[1:]] or ANOS
    for ano in alvos:
        saida = SAIDA / f"prefeito_{ano}.csv"
        if saida.exists():
            print(f"{ano}: {saida.name} já existe, pulando")
            continue
        zipe = cfg.RAW / f"munzona_{ano}.zip"
        print(f"{ano}: baixando...", flush=True)
        if not baixa(ano, zipe):
            print(f"   FALHOU o download")
            zipe.unlink(missing_ok=True)
            continue
        print(f"   {zipe.stat().st_size/1e6:.0f} MB, lendo o cargo 11...", flush=True)
        try:
            d = le_zip(zipe, ano)
        finally:
            zipe.unlink(missing_ok=True)
        if d is None or d.empty:
            print("   nenhum prefeito encontrado")
            continue

        r = vencedores(d)
        r.to_csv(saida, index=False, encoding="utf-8")
        seg = int((r["turnoFinal"] == 2).sum())
        sem = int(r["semEleito"].sum())
        print(f"   {len(r):,} municípios | {seg} decididos em 2º turno | "
              f"{r.loc[~r['semEleito'], 'SG_PARTIDO'].nunique()} partidos",
              flush=True)
        if sem:
            print(f"   {sem} município(s) SEM prefeito declarado pelo TSE — "
                  f"eleição anulada, sub judice ou candidatura indeferida:")
            for _, x in r[r["semEleito"]].iterrows():
                print(f"      {x['SG_UF']} {x['NM_MUNICIPIO']}")
        print(f"   {saida.name}: {saida.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
