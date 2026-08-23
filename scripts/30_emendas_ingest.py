"""Emendas parlamentares: baixa, normaliza e casa o autor com o deputado eleito.

Fonte: Portal da Transparencia, conjunto "Emendas Parlamentares", arquivo unico
(`/download-de-dados/emendas-parlamentares/UNICO`, ~29 MB). Nao ha particao por
ano: o arquivo traz 2015 a 2026 inteiro.

**A decisao que define o Emendometro, e por que ela nao e' de estilo.**

O arquivo oferece duas geografias, e elas respondem perguntas diferentes:

  Localidade de aplicacao   onde o recurso e' aplicado. Semantica certa para o
                            mapa, mas so' 10,5% do dinheiro individual tem
                            municipio: 76% esta declarado como "MULTIPLO", uma
                            emenda espalhada por varias cidades que o arquivo
                            nao nomeia.

  Municipio do favorecido   quem recebeu o pagamento. Cobre 100% do dinheiro e
                            e' INUTIL como mapa: Brasilia concentra 36,4% das
                            emendas individuais, porque e' o endereco do Fundo
                            Nacional de Saude e dos intermediarios. Um mapa
                            assim diz "Brasilia recebeu um terco das emendas do
                            pais" - verdade sobre a transferencia bancaria,
                            falso sobre onde o dinheiro chegou.

Por isso o municipio aqui vem SEMPRE da localidade de aplicacao, nunca do
favorecido, e o front declara a cobertura na tela. A UF, essa sim, esta em 100%
do dinheiro - inclusive nas linhas MULTIPLO - e e' o nivel em que o Emendometro
e' completo.

**O valor que conta e' o que saiu do caixa.** Empenhado e' compromisso, nao
gasto: sao R$ 308,6 bi empenhados contra R$ 259,5 bi efetivamente pagos. Usamos
`Valor Pago + Valor Restos A Pagar Pagos`, que e' o dinheiro que de fato saiu,
somando o que foi pago no proprio ano e o que foi pago depois via restos.

**O casamento com o voto.** 887 dos 1.492 autores de emenda individual (59%)
casam com um deputado federal eleito entre 2014 e 2022 pelo nome de urna. Os que
sobram sao senadores, deputados de antes de 2014 e suplentes que assumiram - a
diferenca e' esperada, nao defeito. O casamento e' por nome sem acento, a mesma
chave que o resto do projeto usa para pessoa, porque a grafia varia entre bases.
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

URL = "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO"
ZIP = cfg.RAW / "emendas_parlamentares.zip"
MEMBRO = "EmendasParlamentares.csv"
SAIDA = cfg.PROCESSED / "emendas.csv"
CASAMENTO = cfg.PROCESSED / "emendas_autor_deputado.csv"

COLS = ["Código da Emenda", "Ano da Emenda", "Tipo de Emenda",
        "Código do Autor da Emenda", "Nome do Autor da Emenda",
        "Localidade de aplicação do recurso", "Código Município IBGE",
        "Município", "UF", "Nome Função", "Nome Subfunção",
        "Valor Empenhado", "Valor Pago", "Valor Restos A Pagar Pagos"]


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def dinheiro(s):
    """"1.234.567,89" -> 1234567.89. Formato brasileiro, sem excecao."""
    return pd.to_numeric(s.astype(str).str.replace(".", "", regex=False)
                         .str.replace(",", ".", regex=False),
                         errors="coerce").fillna(0.0)


def baixar():
    if ZIP.exists():
        try:
            with zipfile.ZipFile(ZIP):
                return
        except zipfile.BadZipFile:
            ZIP.unlink()
    cmd = ["curl.exe", "-sS", "-L", "--fail", "--max-time", "1800", "-o", str(ZIP)]
    for h in cfg.CURL_HEADERS:
        cmd += ["-H", h]
    cmd.append(URL)
    for t in range(1, 4):
        print(f"baixando emendas... (tentativa {t})", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        # validar abrindo, e nao pelo tamanho: zip truncado ja passou por
        # teste de bytes neste projeto
        if r.returncode == 0 and ZIP.exists():
            try:
                with zipfile.ZipFile(ZIP):
                    return
            except zipfile.BadZipFile:
                pass
        ZIP.unlink(missing_ok=True)
    raise RuntimeError("download das emendas falhou em 3 tentativas")


def normalizar():
    with zipfile.ZipFile(ZIP) as zf:
        with zf.open(MEMBRO) as fh:
            d = pd.read_csv(fh, sep=";", encoding="latin-1", dtype=str,
                            low_memory=False)
    d.columns = [c.strip() for c in d.columns]
    faltam = [c for c in COLS if c not in d.columns]
    if faltam:
        raise SystemExit(f"o arquivo mudou de esquema; faltam: {faltam}")
    d = d[COLS].copy()

    d["ano"] = pd.to_numeric(d["Ano da Emenda"], errors="coerce").astype("Int64")
    d["empenhado"] = dinheiro(d["Valor Empenhado"])
    # o que de fato saiu: pago no ano + restos a pagar efetivamente pagos
    d["pago"] = dinheiro(d["Valor Pago"]) + dinheiro(d["Valor Restos A Pagar Pagos"])

    cod = d["Código Município IBGE"].fillna("").str.strip()
    d["cod_ibge"] = cod.where(cod.str.fullmatch(r"\d{7}") & (cod != "0000000"))
    d["multiplo"] = d["Localidade de aplicação do recurso"].fillna("") == "MÚLTIPLO"

    uf = d["UF"].fillna("").str.strip().map(sem_acento)
    d["uf"] = uf.map(_SIGLA).where(uf.map(_SIGLA).notna())

    d["individual"] = d["Tipo de Emenda"].str.startswith("Emenda Individual")
    d["autor_norm"] = d["Nome do Autor da Emenda"].map(sem_acento)

    d = d.rename(columns={
        "Código da Emenda": "cod_emenda", "Tipo de Emenda": "tipo",
        "Código do Autor da Emenda": "cod_autor",
        "Nome do Autor da Emenda": "autor", "Município": "municipio",
        "Nome Função": "funcao", "Nome Subfunção": "subfuncao",
        "Localidade de aplicação do recurso": "localidade"})
    return d[["cod_emenda", "ano", "tipo", "individual", "cod_autor", "autor",
              "autor_norm", "localidade", "cod_ibge", "municipio", "uf",
              "multiplo", "funcao", "subfuncao", "empenhado", "pago"]]


_SIGLA = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM",
    "BAHIA": "BA", "CEARA": "CE", "DISTRITO FEDERAL": "DF",
    "ESPIRITO SANTO": "ES", "GOIAS": "GO", "MARANHAO": "MA",
    "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG",
    "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR", "PERNAMBUCO": "PE",
    "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO", "RORAIMA": "RR",
    "SANTA CATARINA": "SC", "SAO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}


def casar_com_eleitos(d):
    """Autor de emenda -> deputado federal eleito, por nome sem acento.

    Guarda de qual UF e em que pleitos a pessoa foi eleita: e' isso que permite
    perguntar se a emenda foi para o mesmo chao que deu o voto.
    """
    web = cfg.PROCESSED / "web"
    por_nome = {}
    for p in sorted(web.glob("*/federal.json")):
        uf = p.parent.name
        dd = json.loads(p.read_text(encoding="utf-8"))
        for ano, b in dd.items():
            for f in b["fichas"]:
                if not f.get("el"):
                    continue
                for chave in {sem_acento(f["n"]), sem_acento(f.get("completo", ""))}:
                    if not chave:
                        continue
                    r = por_nome.setdefault(chave, {"uf": set(), "anos": set(),
                                                    "urna": f["n"], "sq": []})
                    r["uf"].add(uf)
                    r["anos"].add(int(ano))
                    r["sq"].append(f["sq"])

    autores = (d[d["individual"]].groupby(["autor_norm", "autor"], as_index=False)
               .agg(emendas=("cod_emenda", "nunique"), pago=("pago", "sum")))
    linhas = []
    for r in autores.itertuples():
        m = por_nome.get(r.autor_norm)
        linhas.append({
            "autor_norm": r.autor_norm, "autor": r.autor,
            "emendas": r.emendas, "pago": round(r.pago, 2),
            "eleito": m is not None,
            # ambiguo: o mesmo nome de urna eleito em mais de uma UF. Nao da
            # para atribuir a emenda a um territorio sem escolher, e escolher
            # aqui seria inventar.
            "ambiguo": bool(m and len(m["uf"]) > 1),
            "uf_eleito": "|".join(sorted(m["uf"])) if m else "",
            "anos_eleito": "|".join(str(a) for a in sorted(m["anos"])) if m else "",
        })
    return pd.DataFrame(linhas).sort_values("pago", ascending=False)


def main():
    baixar()
    d = normalizar()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(SAIDA, index=False, encoding="utf-8")

    ind = d[d["individual"]]
    bi = lambda v: f"R$ {v/1e9:.1f} bi"
    print(f"\n{SAIDA.name}: {len(d):,} linhas, {d['ano'].min()}–{d['ano'].max()}")
    print(f"  empenhado {bi(d['empenhado'].sum())} | pago {bi(d['pago'].sum())}")
    print(f"  individuais: {len(ind):,} linhas, {bi(ind['pago'].sum())}, "
          f"{ind['autor'].nunique():,} autores")
    print(f"  com município: {ind['cod_ibge'].notna().mean()*100:.1f}% das linhas, "
          f"{ind.loc[ind['cod_ibge'].notna(),'pago'].sum()/ind['pago'].sum()*100:.1f}% do dinheiro")
    print(f"  com UF:        {ind['uf'].notna().mean()*100:.1f}% das linhas, "
          f"{ind.loc[ind['uf'].notna(),'pago'].sum()/ind['pago'].sum()*100:.1f}% do dinheiro")

    c = casar_com_eleitos(d)
    c.to_csv(CASAMENTO, index=False, encoding="utf-8")
    casou = c[c["eleito"]]
    print(f"\n{CASAMENTO.name}: {len(c):,} autores")
    print(f"  casam com deputado federal eleito: {len(casou):,} "
          f"({len(casou)/len(c)*100:.0f}%), {bi(casou['pago'].sum())} "
          f"({casou['pago'].sum()/c['pago'].sum()*100:.0f}% do dinheiro individual)")
    amb = c[c["ambiguo"]]
    if len(amb):
        print(f"  ambíguos (mesmo nome eleito em mais de uma UF): {len(amb)} — "
              f"{', '.join(amb['autor'].head(4))}")


if __name__ == "__main__":
    main()
