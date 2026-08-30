"""A zona eleitoral como territorio: quais municipios formam cada uma.

A zona e' a unidade que o TSE usa para organizar a eleicao, e o painel ja'
mostrava voto por zona sem nunca dizer ONDE ela fica. A resposta obvia seria
"nao ha' malha de zona publicada", e foi o que este projeto escreveu na tela por
semanas. Medindo, a frase estava certa e a conclusao errada.

**A zona nao cabe dentro do municipio: ela contem municipios.** Em Goias, 68 das
92 zonas cobrem mais de um municipio — a zona 8 cobre oito. E 242 dos 246
municipios pertencem a UMA zona so'. Ou seja, para a grande maioria a zona e' a
uniao de municipios inteiros, e isso e' desenhavel com a malha municipal que ja'
esta' em disco. Nao e' aproximacao nem interpolacao: e' a fronteira exata,
herdada de poligonos que ninguem precisou inventar.

**As excecoes sao quatro, e sao as cidades grandes.** Goiania tem 9 zonas,
Anapolis e Aparecida 3, Rio Verde 2. Nessas, a zona parte o municipio e nao ha'
area: 17 das 92 zonas caem nesse caso. Elas saem marcadas como divididas, e o
mapa nao finge fronteira dentro da cidade — quem quiser ver zona ali usa o mapa
de urnas, onde cada local de votacao tem a zona dele.

**Por que colorir, e por que poucas cores.** Noventa e duas categorias nominais
nao tem paleta possivel. A saida e' a mesma dos mapas politicos desde sempre:
colorir de modo que zonas VIZINHAS nunca compartilhem cor, o que exige uma
mao-cheia de cores e nao noventa. A cor aqui nao identifica a zona — ela apenas
separa uma da outra. Quem identifica e' o rotulo, no toque.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

ANO = 2024

# O normalizador do projeto, e nao um escrito aqui. A primeira versao deste
# script tinha o seu proprio — so tirava acento — e o portao pegou dois
# municipios: SAO JOAO D ALIANCA e SITIO D ABADIA. O TSE escreve o apostrofo
# como espaco, o IBGE como apostrofo. O `04_geo.normalizar` ja trata disso
# desde sempre, porque e o mesmo pareamento. Duplicar funcao de chave e como
# duplicar a chave: as duas divergem, e a divergencia aparece como buraco no
# mapa.
sem_acento = geo.normalizar


def colorir(vizinhas, ordem):
    """Welsh-Powell: as mais conectadas primeiro, cada uma na menor cor livre.

    Guloso e' suficiente aqui — o grafo de zonas vem de um mapa, e mapa e'
    quase planar. O numero de cores que ele gasta e' impresso no fim, e se
    passar de seis vale olhar, porque a essa altura o olho ja' nao separa."""
    cor = {}
    for z in ordem:
        usadas = {cor[v] for v in vizinhas[z] if v in cor}
        c = 0
        while c in usadas:
            c += 1
        cor[z] = c
    return cor


def main():
    origem = cfg.INTERIM / f"veruf_{cfg.UF}_{ANO}.csv"
    if not origem.exists():
        raise SystemExit(f"{origem} nao existe — rode 52_vereador_uf.py antes")

    d = pd.read_csv(origem, usecols=["CD_MUNICIPIO", "NM_NORM", "NR_ZONA"],
                    low_memory=False)
    d["NM_NORM"] = d["NM_NORM"].map(sem_acento)

    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv", dtype={"cod_ibge": str})
    dim = dim[dim["uf"] == cfg.UF].sort_values("cod_ibge").reset_index(drop=True)
    # A MESMA ordem do `19_`: `base.json` lista os municipios ordenados por
    # cod_ibge, e o mapa da tela indexa por posicao. Qualquer outra ordem aqui
    # pintaria o municipio errado, e o mapa nao teria como avisar.
    idx = {sem_acento(n): i for i, n in enumerate(dim["nome"])}

    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    ov = ov[ov["uf"] == cfg.UF]
    apelido = {}
    for _, r in ov.iterrows():
        alvo = sem_acento(r["nome_ibge"])
        if alvo in idx:
            apelido[sem_acento(r["nome_norm_tse"])] = idx[alvo]

    porMun = {}
    faltando = set()
    for nome, z in zip(d["NM_NORM"], d["NR_ZONA"]):
        i = idx.get(nome, apelido.get(nome))
        if i is None:
            faltando.add(nome)
            continue
        porMun.setdefault(i, set()).add(int(z))

    if faltando:
        raise SystemExit(
            f"ABORTADO: {len(faltando)} nomes do TSE sem par na malha: "
            f"{sorted(faltando)[:8]}\n"
            "Um municipio sem par vira buraco branco no mapa das zonas, e o "
            "mapa nao tem como avisar. Acrescente o par em "
            "data/overrides/municipios_tse_ibge.csv.")
    # Oito municipios de Goias nao aparecem no arquivo de votacao com o cargo
    # de vereador em 2024: sao os que o TSE nao totalizou (a mesma lista que a
    # tela marca com `semTotalizacao` — ha voto e nao ha eleito). Sem zona,
    # sairiam como buraco branco no mapa.
    #
    # A zona deles vem do cadastro de LOCAIS de votacao, que existe para todos
    # e traz a zona de cada urna. E' outra fonte do mesmo TSE, e e' a mesma que
    # o mapa de urnas ja usa — nao e' inferencia, e' o cadastro.
    urnas_dir = cfg.PROCESSED / "web" / cfg.UF / "urnas"
    resgatados = []
    if urnas_dir.is_dir():
        porcod_i = {c: i for i, c in enumerate(dim["cod_ibge"])}
        for arq in sorted(urnas_dir.glob("*.json")):
            if not arq.stem.isdigit():
                continue
            i = porcod_i.get(arq.stem)
            if i is None or i in porMun:
                continue
            u = json.loads(arq.read_text(encoding="utf-8"))
            zs = {int(l["z"]) for l in u["locais"] if l.get("z") is not None}
            if zs:
                porMun[i] = zs
                resgatados.append(dim["nome"][i])
    if resgatados:
        print(f"   {len(resgatados)} sem zona no arquivo de votacao, "
              f"resgatados do cadastro de locais: {', '.join(resgatados)}")

    if len(porMun) != len(dim):
        semzona = [dim["nome"][i] for i in range(len(dim)) if i not in porMun]
        raise SystemExit(f"ABORTADO: {len(porMun)} municipios com zona, "
                         f"{len(dim)} na malha. Sem zona: {semzona[:8]}")

    # ---------- zonas ----------
    zonas = {}
    for i, zs in porMun.items():
        for z in zs:
            zonas.setdefault(z, set()).add(i)

    # exata = nenhum dos seus municipios pertence tambem a outra zona
    exata = {z: all(len(porMun[i]) == 1 for i in ms) for z, ms in zonas.items()}

    # ---------- vizinhanca entre zonas, a partir da vizinhanca municipal ----
    #
    # SO' ENTRA QUEM TEM AREA. As zonas que partem um municipio nao desenham
    # poligono nenhum — elas vivem dentro das quatro cidades grandes, onde nao
    # ha fronteira de zona publicada — entao colori-las seria gastar cor num
    # desenho que nao existe.
    #
    # E nao e' so' desperdicio: as 9 zonas de Goiania partilham o mesmo
    # municipio, o que as torna mutuamente vizinhas — uma clique de 9, que por
    # definicao exige 9 cores. A primeira versao deste script gastou 13 por
    # isso, contra o limite de seis que esta escrito ali em cima. Tirando do
    # grafo quem nao pinta, a clique some junto.
    adj = json.loads((cfg.PROCESSED / "adjacencia_municipios.json")
                     .read_text(encoding="utf-8"))
    porcod = {c: i for i, c in enumerate(dim["cod_ibge"])}
    comArea = {z for z in zonas if exata[z]}
    vizinhas = {z: set() for z in comArea}
    for cod, vs in adj.items():
        i = porcod.get(cod)
        if i is None:
            continue
        for cod2 in vs:
            j = porcod.get(cod2)
            if j is None:
                continue
            for za in porMun[i] & comArea:
                for zb in porMun[j] & comArea:
                    if za != zb:
                        vizinhas[za].add(zb)
                        vizinhas[zb].add(za)

    ordem = sorted(comArea, key=lambda z: (-len(vizinhas[z]), z))
    cor = colorir(vizinhas, ordem)
    ncores = (max(cor.values()) + 1) if cor else 0

    saida = {
        "uf": cfg.UF, "ano": ANO, "nCores": ncores,
        "zonas": [
            {"z": z, "mi": sorted(zonas[z]), "exata": bool(exata[z]),
             # `null` onde a zona nao tem area para pintar
             "cor": cor.get(z)}
            for z in sorted(zonas)
        ],
        # zona(s) de cada municipio, por indice de base.json
        "porMun": [sorted(porMun[i]) for i in range(len(dim))],
        # o codigo IBGE na MESMA ordem, para a tela achar o indice da cidade
        # aberta sem parear por nome — grafia varia, indice nao
        "cods": list(dim["cod_ibge"]),
    }

    f = cfg.PROCESSED / "web" / cfg.UF / "zonas.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(saida, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")

    nexatas = sum(1 for z in zonas if exata[z])
    partidas = sorted(z for z in zonas if not exata[z])
    multi = sorted((len(zs), i) for i, zs in porMun.items() if len(zs) > 1)
    print(f"{len(zonas)} zonas em {len(dim)} municipios, {ANO}")
    print(f"   exatas (uniao de municipios inteiros): {nexatas}")
    print(f"   que partem algum municipio: {len(partidas)} -> {partidas}")
    print(f"   municipios com mais de uma zona: {len(multi)}")
    for n, i in sorted(multi, reverse=True)[:6]:
        print(f"      {dim['nome'][i]:<22} {n} zonas")
    print(f"   cores gastas para separar as {len(comArea)} com area: {ncores}")
    if ncores > 6:
        print("   AVISO: acima de seis cores o olho ja nao separa as areas")
    print(f"   {f.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
