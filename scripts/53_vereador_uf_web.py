"""Camara municipal de TODOS os municipios de uma UF: `web/{UF}/cidades/*.json`.

Generaliza `25_vereador_web.py`, que monta um arquivo por capital, para um
arquivo por municipio. Goias e' o piloto: 246 cidades.

**A armadilha que so' aparece quando se sai da capital.** Em 2000 e 2004 o
`SQ_CANDIDATO` do TSE nao e' identificador nacional - e' um contador por
municipio. O SQ 164 de 2000 e' 63 pessoas diferentes em 63 cidades; o SQ 7 de
2004 e' 89 pessoas. Na pipeline das capitais isso era invisivel, porque cada
arquivo ja' vinha filtrado para UMA cidade e ali dentro o SQ e' unico. Ao abrir
para 246 municipios, agrupar por SQ fundiria vereadores de cidades diferentes
num so'. Aqui a chave e' o par (municipio, SQ) - verificado: em todos os sete
pleitos, nenhum par carrega mais de um nome.

**A memoria de pessoa tambem e' por cidade.** `25_` reconhece reincidencia
comparando o nome sem acento com o pleito anterior. Num estado inteiro isso
casaria o "JOSE DA SILVA" de Anapolis com o de Rio Verde e inventaria uma
carreira que nao existe. Cada municipio e' montado isolado, entao a memoria
nunca atravessa fronteira municipal.

**Oito municipios de Goias nao tem totalizacao publicada em 2024.** Aguas
Lindas de Goias, Buriti Alegre, Cavalcante, Ipora, Jatai, Santo Antonio do
Descoberto, Sao Domingos e Valparaiso de Goias: em `votacao_candidato_munzona`
eles nao aparecem com cargo 13, e em `consulta_cand` todos os seus candidatos
tem `DS_SIT_TOT_TURNO = #NULO`. Nao e' falha de leitura - e' o dado publico: 23
municipios do Brasil estao nessa situacao (8 em GO, 8 no MA, 4 no PA, 1 em PE,
PI e SE).

Aguas Lindas tem 200 mil habitantes e Valparaiso 170 mil. Some-las da lista
seria fazer duas das maiores cidades do estado desaparecerem sem uma palavra -
que e' a ausencia silenciosa que este projeto recusa em toda parte. Elas entram
com os votos, que `votacao_secao` publica por inteiro, e SEM eleito, que o TSE
nao publicou. O arquivo carrega `semTotalizacao: true` para que a tela diga
isso, em vez de mostrar uma camara vazia e deixar o leitor concluir o que
quiser.

**Itapaci nao tem eleicao de vereador registrada em 2000.** Tem em 2004. E' um
municipio num pleito, e esta' dito aqui porque um ano faltando no grafico de um
lugar so' e' indistinguivel de um defeito.
"""
import json
import sys
import unicodedata
import zipfile
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")
ext = import_module("52_vereador_uf")

ANOS = ext.ANOS
SIT_ELEITO = ("ELEITO", "ELEITO POR QP", "ELEITO POR MEDIA", "MEDIA")
COLS_VOTO = ext.COLS_VOTO
TOP_NAO_ELEITOS = 60
CD_VEREADOR = 13
ANO_SECAO = 2024


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


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    if n == 0 or x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def montar_ano(ano, d, lin, nomelin, chave_ant, vetores, sem_tot=False):
    """Um pleito de UMA cidade. `d` ja' vem filtrado para o municipio.

    `vetores` e' CUMULATIVO e chaveado por (ano, sq), nunca so' pelo ano
    anterior: quem nao concorre num pleito e volta no seguinte ainda tem de
    se comparar com a propria base de antes. E a chave carrega o ano porque
    em 2000 e 2004 o SQ e' um contador por municipio - sem o ano, o SQ 164 de
    2000 casaria com o vetor do SQ 164 de 2004, que e' outra pessoa.
    """
    sit = d["DS_SIT_TOT_TURNO"].fillna("").map(sem_acento)
    eleito = (pd.Series(False, index=d.index) if sem_tot
              else sit.str.startswith("ELEITO") | sit.isin(SIT_ELEITO))
    d = d.assign(eleito=eleito, sigla=d["SG_PARTIDO"].fillna("").map(sem_acento))
    d["pnorm"] = d["sigla"].map(lin).fillna(d["sigla"])

    zonas = sorted(d.loc[d["votos"] > 0, "NR_ZONA"].unique().tolist())
    if not zonas:
        return None
    pos = {z: i for i, z in enumerate(zonas)}

    info = d.sort_values("votos", ascending=False).groupby(
        "SQ_CANDIDATO", as_index=False).first()
    porz = d.groupby(["SQ_CANDIDATO", "NR_ZONA"], as_index=False)["votos"].sum()
    porz = porz[porz["votos"] > 0]
    if porz.empty:
        return None
    tot = porz.groupby("SQ_CANDIDATO")["votos"].sum()

    fichas = []
    for r in info.itertuples():
        g = porz[porz["SQ_CANDIDATO"] == r.SQ_CANDIDATO]
        if g.empty:
            continue
        v = g["votos"].to_numpy(dtype=float)
        p = v / v.sum()
        vet = np.zeros(len(zonas))
        for z, x in zip(g["NR_ZONA"], g["votos"]):
            vet[pos[z]] = x
        vetores[(ano, str(r.SQ_CANDIDATO))] = vet
        fichas.append({
            "sq": str(r.SQ_CANDIDATO),
            "n": str(r.NM_URNA_CANDIDATO), "completo": str(r.NM_CANDIDATO),
            "p": str(r.SG_PARTIDO), "pn": nomelin.get(r.pnorm, r.pnorm),
            "el": bool(r.eleito), "t": int(tot[r.SQ_CANDIDATO]),
            "zi": [pos[z] for z in g["NR_ZONA"]],
            "zv": [int(x) for x in g["votos"]],
            "nz": int(len(v)),
            "ef": round(float(1 / (p ** 2).sum()), 2),
            "t1": round(float(p.max() * 100), 2),
            "gi": round(gini(v), 4),
            "reduto": int(g.loc[g["votos"].idxmax(), "NR_ZONA"]),
            "chave": sem_acento(r.NM_CANDIDATO),
        })
    if not fichas:
        return None

    # reincidencia por nome sem acento: a grafia com acento varia entre pleitos
    # no mesmo arquivo do TSE e quebra o pareamento de pessoa
    for f in fichas:
        ant = chave_ant.get(f["chave"])
        f["re"] = ant is not None
        f["sim"] = None
        if ant is not None:
            x, y = vetores.get(ant), vetores[(ano, f["sq"])]
            # so' compara se o numero de zonas bate: redesenho de zona invalida
            # a comparacao, e um numero aqui seria falso
            if x is not None and x.shape == y.shape:
                nx, ny = np.linalg.norm(x), np.linalg.norm(y)
                if nx and ny:
                    f["sim"] = round(float(x @ y / (nx * ny)), 4)
    # a memoria cobre TODOS os candidatos, nao so os guardados: quem nao se
    # elegeu num pleito e voltou no seguinte tem de ser reconhecido
    for f in fichas:
        chave_ant[f["chave"]] = (ano, f["sq"])

    fichas.sort(key=lambda f: -f["t"])
    el = [f for f in fichas if f["el"]]
    guardar = el + [f for f in fichas if not f["el"]][:TOP_NAO_ELEITOS]
    guardar.sort(key=lambda f: -f["t"])
    for f in guardar:
        f.pop("chave", None)

    total = int(tot.sum())
    partidos = []
    for pn, g in info.groupby("pnorm"):
        sq = set(g["SQ_CANDIDATO"])
        v = int(tot[tot.index.isin(sq)].sum())
        if len(g) < 2:
            continue
        partidos.append({"nome": nomelin.get(pn, pn), "nc": int(len(g)),
                         "ne": int(g["eleito"].sum()), "votos": v,
                         "puxador": round(float(tot[tot.index.isin(sq)].max())
                                          / max(v, 1) * 100, 2)})
    partidos.sort(key=lambda x: -x["votos"])

    bloco = {
        "pleito": {
            "nCand": int(len(info)), "cadeiras": len(el), "total": total,
            "ultimo": min((f["t"] for f in el), default=0),
            "maior": max((f["t"] for f in fichas), default=0),
            "qe": round(total / len(el), 1) if el else 0.0,
            "nz": len(zonas),
            "rePct": (round(float(np.mean([f["re"] for f in el])) * 100, 1)
                      if el else 0.0),
        },
        "zonas": zonas,
        "fichas": guardar,
        "partidos": partidos[:12],
    }
    if sem_tot:
        # a tela precisa distinguir "camara sem eleito" de "eleito nao
        # publicado", que sao coisas opostas com a mesma aparencia
        bloco["semTotalizacao"] = True
    return bloco


def ler_ano(uf, ano, mapa, corr):
    """Interim do ano, com `cod_ibge` resolvido e `votos` na coluna certa."""
    f = cfg.INTERIM / f"veruf_{uf}_{ano}.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f, dtype=str, low_memory=False)
    for c in COLS_VOTO:
        if c not in d.columns:
            d[c] = 0
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype("int64")
    # a coluna util muda ao longo da serie (2000 usa VALIDOS, 2004 usa
    # NOMINAIS): resolver por soma do ano, nunca por regra fixa
    col = ("QT_VOTOS_NOMINAIS" if d["QT_VOTOS_NOMINAIS"].sum() > 0
           else "QT_VOTOS_NOMINAIS_VALIDOS")
    d["votos"] = d[col]
    d["NR_ZONA"] = pd.to_numeric(d["NR_ZONA"], errors="coerce").fillna(0).astype(int)
    d["NM_NORM"] = d["NM_MUNICIPIO"].map(chave_mun)
    # grafia antiga do TSE ("VALPARAISO" ate 2004, "VALPARAISO DE GOIAS"
    # depois) resolve pelo mesmo override manual que o resto do projeto usa
    d["cod"] = d["NM_NORM"].map(lambda n: corr.get((uf, n)) or mapa.get(n))
    orfas = d[d["cod"].isna()]
    if len(orfas):
        print(f"    [{ano}] SEM PAREAMENTO: "
              f"{sorted(set(orfas['NM_NORM']))}", flush=True)
        d = d.dropna(subset=["cod"])
    return d


def ler_secao_2024(uf, alvos, mapa, corr):
    """Os municipios sem totalizacao, montados de `votacao_secao` + `consulta_cand`.

    Duas fontes porque nenhuma sozinha basta: a de secao tem o voto e nao tem
    partido nem nome de urna; a de candidatura tem os dois e nao tem voto. O
    par (municipio, SQ_CANDIDATO) une as duas.
    """
    zs = cfg.RAW / f"secao_{ANO_SECAO}_{uf}.zip"
    zc = cfg.RAW / f"consulta_cand_{ANO_SECAO}.zip"
    # ABORTA, nao avisa. Sem estes dois zips os municipios sem totalizacao
    # ficam sem o pleito de 2024 — e antes o script seguia, imprimia um aviso e
    # saia com codigo ZERO. Quem rodasse depois veria "246 cidades" e concluiria
    # que deu certo, com Aguas Lindas (200 mil habitantes) sem 2024.
    #
    # E' o mesmo modo de falha que este projeto ja pagou duas vezes: o
    # `51_urnas_capital.py` gravou 26 mapas vazios com saida zero por usar a
    # caixa geografica de Goias nas outras capitais, e uma verificacao com
    # `usecols` mascarou quatro arquivos do interim corrompidos. Falha silenciosa
    # com codigo zero e' pior que erro: ela e' lida como sucesso.
    #
    # O resto do repositorio ja segue esta regra — o `49_` aborta se a contagem
    # de campos divergir, o `56_` se um municipio ficar sem par, o `47_` se um
    # arquivo do Radar vazar. Este era a excecao.
    faltam = [f.name for f in (zs, zc) if not f.exists()]
    if faltam:
        raise SystemExit(
            f"ABORTADO: falta em data/raw: {', '.join(faltam)}\n"
            f"Sem eles, os {len(alvos)} municipios sem totalizacao de "
            f"{ANO_SECAO} sairiam sem o pleito, e a saida diria "
            f"'{len(alvos)} de fora' no meio de um relatorio de sucesso.\n"
            "Rode 54_urnas_uf.py, que baixa os dois, ou reponha os arquivos.")

    with zipfile.ZipFile(zs) as z:
        nome = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(nome) as fh:
            V = pd.read_csv(fh, sep=";", encoding="latin-1", quotechar='"',
                            dtype=str, low_memory=False,
                            usecols=["NM_MUNICIPIO", "NR_ZONA", "CD_CARGO",
                                     "NR_TURNO", "SQ_CANDIDATO", "QT_VOTOS"])
    V["NM_NORM"] = V["NM_MUNICIPIO"].map(chave_mun)
    V = V[V["NM_NORM"].isin(alvos)
          & (pd.to_numeric(V["CD_CARGO"], errors="coerce") == CD_VEREADOR)
          & (pd.to_numeric(V["NR_TURNO"], errors="coerce") == 1)].copy()
    V["votos"] = pd.to_numeric(V["QT_VOTOS"], errors="coerce").fillna(0).astype("int64")
    V["NR_ZONA"] = pd.to_numeric(V["NR_ZONA"], errors="coerce").fillna(0).astype(int)

    with zipfile.ZipFile(zc) as z:
        alvo = [n for n in z.namelist()
                if n.upper().endswith(f"_{ANO_SECAO}_{uf}.CSV")][0]
        with z.open(alvo) as fh:
            C = pd.read_csv(fh, sep=";", encoding="latin-1", quotechar='"',
                            dtype=str, low_memory=False)
    C["NM_NORM"] = C["NM_UE"].map(chave_mun)
    C = C[C["NM_NORM"].isin(alvos)
          & (pd.to_numeric(C["CD_CARGO"], errors="coerce") == CD_VEREADOR)]
    C = C.drop_duplicates("SQ_CANDIDATO")[
        ["SQ_CANDIDATO", "NM_CANDIDATO", "NM_URNA_CANDIDATO", "SG_PARTIDO",
         "NM_NORM"]]

    # voto de legenda tem NR_VOTAVEL de partido e nenhum SQ de candidato: o
    # merge interno o descarta, que e' o certo — legenda nao e' pessoa
    d = V.merge(C, on=["SQ_CANDIDATO", "NM_NORM"], how="inner")
    d["DS_SIT_TOT_TURNO"] = ""
    d["cod"] = d["NM_NORM"].map(lambda n: corr.get((uf, n)) or mapa.get(n))
    perdidos = int(V["votos"].sum() - d["votos"].sum())
    print(f"    secao 2024: {len(alvos)} municipios, "
          f"{d['SQ_CANDIDATO'].nunique():,} candidatos, "
          f"{int(d['votos'].sum()):,} votos "
          f"({perdidos:,} de legenda/especiais, fora)", flush=True)
    return d


def main():
    uf = (sys.argv[1] if len(sys.argv) > 1 else "GO").upper()
    dim = pd.read_csv(cfg.PROCESSED / "dim_municipio.csv", dtype=str)
    mapa = dict(zip(dim["nome_norm"].map(chave_mun), dim["cod_ibge"]))
    nomes = dict(zip(dim["cod_ibge"], dim["nome"]))
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    # chave (uf, nome): "LUISIANIA" existe no PR e em SP apontando para
    # municipios diferentes, e uma chave so' de nome nao cabe os dois
    corr = {(u, chave_mun(n)): c for u, n, c in
            zip(ov["uf"], ov["nome_norm_tse"], ov["cod_ibge"])}

    linhagem = pd.read_csv(cfg.OVERRIDES / "partidos_linhagem.csv")
    lin = dict(zip(linhagem["sigla_epoca"].map(sem_acento),
                   linhagem["partido_norm"]))
    nomelin = dict(zip(linhagem["partido_norm"], linhagem["nome_linhagem"]))

    print(f"{uf}: {len(mapa)} municipios na malha\n", flush=True)

    quadros = {}
    for ano in ANOS:
        d = ler_ano(uf, ano, mapa, corr)
        if d is None:
            continue
        quadros[ano] = d
        print(f"  {ano}: {d['cod'].nunique()} municipios, "
              f"{len(d):,} linhas", flush=True)

    # os que nao tem totalizacao no ultimo pleito entram por outra fonte
    tem24 = set(quadros.get(2024, pd.DataFrame({"cod": []}))["cod"])
    faltam24 = sorted(set(mapa.values()) - tem24)
    if faltam24:
        inv = {v: k for k, v in mapa.items()}
        alvos = {inv[c] for c in faltam24 if c in inv}
        print(f"\n  {len(faltam24)} sem totalizacao em 2024: "
              f"{', '.join(sorted(alvos))}", flush=True)
        extra = ler_secao_2024(uf, alvos, mapa, corr)
    else:
        extra = None

    saida = cfg.PROCESSED / "web" / uf / "cidades"
    saida.mkdir(parents=True, exist_ok=True)
    indice, bytes_tot = [], 0
    for cod in sorted(mapa.values()):
        anos, chave_ant, vetores = {}, {}, {}
        for ano in ANOS:
            d = quadros.get(ano)
            g = d[d["cod"] == cod] if d is not None else None
            sem_tot = False
            if (g is None or g.empty) and ano == 2024 and extra is not None:
                g = extra[extra["cod"] == cod]
                sem_tot = True
            if g is None or g.empty:
                continue
            b = montar_ano(ano, g, lin, nomelin, chave_ant, vetores, sem_tot)
            if b:
                anos[str(ano)] = b
        if not anos:
            print(f"    {nomes.get(cod, cod)}: sem dado em nenhum pleito",
                  flush=True)
            continue
        obj = {"cidade": nomes.get(cod, cod), "cod": cod, "uf": uf, "anos": anos}
        p = saida / f"{cod}.json"
        p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
        bytes_tot += p.stat().st_size
        ult = anos.get("2024") or anos[max(anos)]
        indice.append({
            "cod": cod, "nome": nomes.get(cod, cod),
            "anos": sorted(int(a) for a in anos),
            "cadeiras": ult["pleito"]["cadeiras"],
            "eleitores": None,
            "st": bool(ult.get("semTotalizacao")),
        })

    (saida / "indice.json").write_text(
        json.dumps({"uf": uf, "cidades": indice}, separators=(",", ":"),
                   ensure_ascii=False), encoding="utf-8")
    idx_kb = (saida / "indice.json").stat().st_size / 1024
    print(f"\n{len(indice)} cidades | {bytes_tot/1024/1024:.2f} MB no total | "
          f"media {bytes_tot/max(len(indice),1)/1024:.0f} KB | "
          f"indice {idx_kb:.0f} KB", flush=True)
    st = [c["nome"] for c in indice if c["st"]]
    if st:
        print(f"sem totalizacao em 2024 ({len(st)}): {', '.join(st)}", flush=True)


if __name__ == "__main__":
    main()
