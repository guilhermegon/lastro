"""Publica `data/processed/web/` em `app/public/dados/` e monta o índice.

O índice é o único arquivo que o front baixa sempre, então carrega só o que serve
para desenhar a primeira tela e o comparativo nacional: lista de UFs, malha do
Brasil por UF e o agregado por estado e pleito. Tudo mais vem sob demanda.

O agregado nacional é montado aqui, a partir dos arquivos por UF já validados, em
vez de vir de um pipeline paralelo — assim não existe a possibilidade de o
comparativo nacional discordar da tela do estado.

**Os arquivos indexados por ano são partidos em um arquivo por ano.** A tela
mostra um pleito de cada vez, mas o arquivo trazia os sete. Medido em São Paulo,
o pior caso do país: a aba do estadual baixava 4.815 KB — 1.089 KB já
comprimidos — para desenhar um ano. Partido, são 1.399 KB (333 KB servidos):
**69% a menos na primeira tela**. O total em disco não muda; muda o que cada
visitante puxa.

Não é otimização de bytes — comprimir mais os mesmos arquivos renderia 4%, porque
o gzip do servidor já corta 79%. É deixar de mandar seis anos que ninguém pediu.

O app busca o ano aberto primeiro e os outros seis em segundo plano, então a
troca de pleito continua instantânea depois dos primeiros segundos.
"""
import json
import shutil
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

ORIGEM = cfg.PROCESSED / "web"
DESTINO = cfg.ROOT / "app" / "public" / "dados"
CARGOS = ["presidente", "governador", "senador", "federal", "estadual"]


# O que alimenta o Radar, o produto fechado. NAO vai para o build publico.
#
# Tirar a aba do site nao torna o dado privado: num site estatico tudo que esta
# em `dist/` responde 200 para qualquer um. Medido antes desta mudanca —
# `/dados/GO/padroes.json` estava no ar. Entao a separacao e' feita aqui, no
# arquivo, e nao na tela.
#
# Estes seguem para `data/processed/radar/`, fora de `app/public`, e o produto
# fechado se serve de la' quando tiver por onde autenticar.
RADAR = ["padroes", "cruzamentos"]

# arquivos cuja chave de primeiro nivel e' o ano do pleito; o resto do dado
# (base, emendas) nao tem essa forma e fica inteiro
POR_ANO = ["presidente", "governador", "senador", "federal", "estadual",
           "rivais_estadual", "rivais_federal"]


def separa_radar(uf):
    """Move o dado do produto fechado para fora do que vai ao ar."""
    destino = cfg.PROCESSED / "radar" / uf
    destino.mkdir(parents=True, exist_ok=True)
    movidos = 0
    for nome in RADAR:
        f = DESTINO / uf / f"{nome}.json"
        if f.exists():
            shutil.copy2(f, destino / f"{nome}.json")
            f.unlink()
            movidos += 1
    return movidos


def parte_por_ano(pasta):
    """`estadual.json` vira `estadual/2022.json` e irmaos. Ver docstring.

    O monolito e' apagado: manter os dois dobraria o disco e abriria a chance de
    a tela ler um e o indice o outro."""
    cortados = 0
    for nome in POR_ANO:
        f = pasta / f"{nome}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        anos = [k for k in d if str(k).isdigit()]
        # se nao for a forma esperada, nao mexe: melhor servir grande do que
        # servir errado
        if len(anos) != len(d) or not anos:
            continue
        dir_ = pasta / nome
        dir_.mkdir(exist_ok=True)
        for ano in anos:
            (dir_ / f"{ano}.json").write_text(
                json.dumps(d[ano], separators=(",", ":"), ensure_ascii=False),
                encoding="utf-8")
        # a lista de anos vive aqui e nao no indice: uma UF pode nao ter um
        # cargo num pleito, e o app precisa saber disso sem tentar e levar 404
        (dir_ / "anos.json").write_text(
            json.dumps(sorted(int(a) for a in anos), separators=(",", ":")),
            encoding="utf-8")
        f.unlink()
        cortados += 1
    return cortados


def main():
    if not ORIGEM.exists():
        raise SystemExit("rode 19_nacional_completo.py e 21_padroes_cruzamentos.py antes")

    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    ufs_dir = sorted(p.name for p in ORIGEM.iterdir() if p.is_dir())
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv", dtype={"cod_ibge": str})
    nomes_uf = {}
    try:
        nac = import_module("14_nacional")
        nomes_uf = {u["sigla"]: u["nome"] for u in nac.get(nac.LISTA_UF)}
    except Exception:
        pass

    agregado, resumo = [], []
    for uf in ufs_dir:
        shutil.copytree(ORIGEM / uf, DESTINO / uf)
        parte_por_ano(DESTINO / uf)
        separa_radar(uf)
        base = json.loads((ORIGEM / uf / "base.json").read_text(encoding="utf-8"))
        n_mun = len(base["municipios"])
        est = ORIGEM / uf / "estadual.json"
        if est.exists():
            d = json.loads(est.read_text(encoding="utf-8"))
            pad = json.loads((ORIGEM / uf / "padroes.json").read_text(encoding="utf-8"))
            serie = {s["ano"]: s for s in pad["serie"]}
            for ano, bloco in d.items():
                p = bloco["pleito"]
                s = serie.get(int(ano), {})
                agregado.append({
                    "uf": uf, "ano": int(ano), "cad": p["cadeiras"],
                    "cand": p["nCand"], "tot": p["totalUF"], "nmun": n_mun,
                    "qe": p["qe"], "ult": p["ultimo"],
                    "ef": s.get("ef"), "t1": s.get("t1"), "fr": s.get("fr"),
                })
        cargos = [c for c in CARGOS if (ORIGEM / uf / f"{c}.json").exists()]
        r = {"s": uf, "n": nomes_uf.get(uf, uf), "nm": n_mun, "cargos": cargos}
        # a capital so entra no indice se o arquivo existir: e' ela que liga a
        # aba de vereador, e o DF nao tem nenhuma das duas coisas
        if (ORIGEM / uf / "vereador.json").exists():
            v = json.loads((ORIGEM / uf / "vereador.json").read_text(encoding="utf-8"))
            r["capital"] = v["cidade"]
            # `ver` e' quem liga a aba. `capital` NAO serve para isso: o DF tem
            # capital e nao tem camara municipal, e a aba ficava clicavel para
            # cair num 404. Um campo para a marca no mapa, outro para a aba.
            r["ver"] = True
            # o indice da capital na ordenacao de base.json. Guardado aqui, e
            # nao procurado por nome no navegador: a grafia varia entre bases
            # e um mapa marcando a cidade errada e' pior que um sem marca.
            alvo = geo.normalizar(v["cidade"])
            for i, m in enumerate(base["municipios"]):
                if geo.normalizar(m["n"]) == alvo:
                    r["capIdx"] = i
                    break
            else:
                print(f"  AVISO {uf}: capital {v['cidade']} não achada na malha")
        elif uf == "DF":
            # o DF nao tem vereador, mas tem capital — e ela e' o unico municipio
            r["capital"] = base["municipios"][0]["n"]
            r["capIdx"] = 0
        resumo.append(r)

    # o agregado nacional de emendas viaja junto: 35 KB, e e' o unico arquivo
    # do Emendometro que a tela precisa antes de escolher um estado
    for solto in ("emendas_br.json", "assembleias.json"):
        f = ORIGEM / solto
        if f.exists():
            shutil.copy2(f, DESTINO / solto)

    indice = {
        "anos": cfg.ANOS,
        "cargos": CARGOS,
        "ufs": resumo,
        "agregado": agregado,
        "malhaUF": json.loads((cfg.PROCESSED / "nac_malha_uf.json").read_text()),
    }
    f = DESTINO / "indice.json"
    f.write_text(json.dumps(indice, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")

    total = sum(x.stat().st_size for x in DESTINO.rglob("*.json"))
    maior = max((x.stat().st_size, x.relative_to(DESTINO).as_posix())
                for x in DESTINO.rglob("*.json"))
    print(f"indice.json: {f.stat().st_size/1024:.0f} KB "
          f"({len(resumo)} UFs, {len(agregado)} linhas de agregado)")
    print(f"total publicado: {total/1024/1024:.1f} MB")
    print(f"maior arquivo: {maior[1]} com {maior[0]/1024:.0f} KB")
    print()
    com_vb = sum(1 for uf in ufs_dir
                 if (DESTINO / uf / "alego_verbas.json").exists()
                 or (DESTINO / uf / "cldf_verbas.json").exists())
    if com_vb:
        print(f"verba indenizatória (API da assembleia) em {com_vb} UF(s)")
    com_est = sum(1 for uf in ufs_dir
                  if (DESTINO / uf / "emendas_estadual.json").exists())
    if com_est:
        print(f"emendas de deputado estadual em {com_est} UF(s) — piloto")
    com_dem = sum(1 for uf in ufs_dir if (DESTINO / uf / "demografia.json").exists())
    print(f"demografia (população e área, Censo 2022) em {com_dem} UFs")
    com_em = sum(1 for uf in ufs_dir if (DESTINO / uf / "emendas.json").exists())
    print(f"emendas em {com_em} UFs"
          + (", agregado nacional publicado" if (DESTINO / "emendas_br.json").exists()
             else " — SEM agregado nacional (rode 31_)"))
    com_ver = sum(1 for r in resumo if "capital" in r)
    com_riv = sum(1 for uf in ufs_dir
                  if (DESTINO / uf / "rivais_estadual").is_dir()
                  or (DESTINO / uf / "rivais_federal").is_dir())
    print(f"vereador em {com_ver} capitais, rivais em {com_riv} UFs")
    print()
    # o que o visitante baixa para ver UM pleito — que e' o numero que a divisao
    # por ano existe para derrubar. Medir o diretorio inteiro voltaria a medir os
    # sete anos e esconderia justamente o ganho.
    ultimo = str(max(indice["anos"])) if indice.get("anos") else ""
    for uf in ("RR", "GO", "SP"):
        p = DESTINO / uf
        if not p.exists():
            continue
        def kb(*partes):
            q = p.joinpath(*partes)
            return q.stat().st_size / 1024 if q.is_file() else 0
        def kb_dir(nome):
            d = p / nome
            return (sum(x.stat().st_size for x in d.glob("*.json")) / 1024
                    if d.is_dir() else 0)
        print(f"  abertura em {uf} no pleito de {ultimo}: "
              f"índice {f.stat().st_size/1024:.0f} KB "
              f"+ base {kb('base.json'):.0f} KB "
              f"+ estadual {kb('estadual', ultimo + '.json'):.0f} KB "
              f"+ rivais {kb('rivais_estadual', ultimo + '.json'):.0f} KB")
        print(f"     (os sete anos, se fossem baixados juntos: "
              f"estadual {kb_dir('estadual'):.0f} KB "
              f"+ rivais {kb_dir('rivais_estadual'):.0f} KB)")


if __name__ == "__main__":
    main()
