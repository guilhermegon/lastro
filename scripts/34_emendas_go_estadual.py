"""Piloto: emendas de deputado ESTADUAL em Goias (`RAS 00 TKT 0006`).

Fonte: dados abertos de Goias, conjunto "Emendas Parlamentares - SERINT"
(`dadosabertos.go.gov.br`, pacote 74a44295-...). E' a base da Assembleia
Legislativa, nao de uma secretaria — o nome do orgao engana.

**O que o piloto descobriu, e e' o resultado principal.** O esquema muda todo
ano. Nao e' uma variacao de rotulo, sao arquivos diferentes:

    ano    separador  colunas  autor  municipio  valor
    2019   ;            5      nao    nao        sim
    2020   ;            5      sim    nao        sim
    2021   ;           17      sim    nao        sim
    2022   ;           18      sim    nao        sim
    2023   ;           15      sim    SIM        sim
    2024   ;           25      sim    SIM        sim
    2025   TAB         25      sim    SIM        sim

**Mas os arquivos de 2024 e 2025 sao despejos MULTI-ANO**: trazem exercicios
antigos com municipio preenchido. Por isso a cobertura municipal existe de 2020
a 2025 — 246 municipios em 2022 — mesmo com os arquivos daqueles anos nao tendo
a coluna. Foi medindo que isso apareceu; olhando so' os cabecalhos, eu tinha
concluido "municipio so' a partir de 2023", e estava errado.

Por isso as colunas sao encontradas por BUSCA, e nao por posicao ou nome exato:
com sete esquemas em sete anos, uma tabela de nomes fixos quebraria no proximo
arquivo publicado. Se o essencial faltar num ano, o ano e' reportado e deixado
de fora, nunca preenchido com zero.

**O municipio vem por NOME**, nao por codigo do IBGE — ao contrario do federal.
Entao o pareamento volta, e com ele o risco de perder voto em silencio que
custou 23 milhoes no outro lado. Aqui o alvo e' fechado (246 municipios de
Goias) e o pareamento e' conferido: o que nao casar e' impresso, nunca somido.
"""
import io
import json
import re
import sys
import unicodedata
import zipfile
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

ORIGEM = cfg.RAW / "emendas_go"
SAIDA = cfg.PROCESSED / "emendas_go_estadual.csv"
WEB = cfg.PROCESSED / "web" / "GO"

# padroes de busca, do mais especifico para o mais generico
COLUNAS = {
    # "Autor da Emenda" em 2023 nao casava com nenhum padrao antigo, e o ano
    # inteiro caiu fora em silencio. Padrao amplo, do especifico para o generico.
    "autor": [r"autor.*deputad", r"deputado.*autor", r"^autor", r"deputado"],
    "municipio": [r"munic.*benefici", r"^munic"],
    "emenda": [r"n.?\s*emenda", r"^emenda$", r"numero.*emenda"],
    "objeto": [r"objeto"],
    "tipo": [r"tipo.*emenda"],
    "funcao": [r"fun..o.*nome", r"^fun..o", r"fun..o.*area"],
    "valor": [r"valor.*emenda", r"valor.*empenho", r"^valor$", r"valor"],
    "pago": [r"valor.*pago", r"op.*saldo", r"liquida..o.*saldo"],
    "ano": [r"exerc.cio", r"ano.*emenda"],
}


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def chave_pessoa(t):
    """Chave de pessoa: o normalizador DO PROJETO, menos o titulo de tratamento.

    UMA funcao, tres arquivos, e ela precisa ser identica nos tres: o `34_` e o
    `38_` gravam `autor_norm` no CSV, e o `35_` monta com ela o indice de
    eleitos. Divergiram uma vez — o `35_` passou a tirar pontuacao e os outros
    nao —, e o Espirito Santo caiu de 157 para 148 fichas casadas sem que nada
    acusasse. Por isso as tres delegam ao mesmo `04_geo.normalizar`.

    O prefixo sai porque e' cargo, nao nome: a base do estado escreve
    "DEP. ALVARO GUIMARAES" e "Dep. Allan Ferreira"; o TSE nao usa prefixo.
    """
    return re.sub(r"^(DEP|DEPUTADO|DEPUTADA)\s+", "", geo.normalizar(t)).strip()


def achar(cols, padroes):
    """Primeira coluna que casa, na ordem de especificidade dos padroes."""
    normal = {c: sem_acento(c).lower() for c in cols}
    for p in padroes:
        for c in cols:
            if re.search(p, normal[c]):
                return c
    return None


def dinheiro(s):
    """Formato brasileiro. Notacao cientifica aparece em coluna de sequencial,
    nunca em valor — se aparecer aqui, vira nulo em vez de virar um numero
    gigante e silencioso."""
    t = s.astype(str).str.strip()
    t = t.where(~t.str.contains("E+", regex=False), None)
    return pd.to_numeric(t.str.replace(".", "", regex=False)
                         .str.replace(",", ".", regex=False), errors="coerce")


def fontes():
    for p in sorted(ORIGEM.iterdir()):
        if p.suffix.lower() == ".csv":
            yield p.name, p.read_bytes()
        elif p.suffix.lower() == ".zip":
            # o pacote "2019 - 2023" repete os anos que ja vem soltos
            if "2019 - 2023" in p.name or "2019-2023" in p.name:
                continue
            with zipfile.ZipFile(p) as zf:
                for m in zf.namelist():
                    if m.lower().endswith(".csv"):
                        yield m, zf.read(m)


def ler(nome, buf):
    for enc in ("utf-8-sig", "latin-1"):
        try:
            cab = buf[:8000].decode(enc).splitlines()[0]
        except (UnicodeDecodeError, IndexError):
            continue
        sep = max((";", "\t", ",", "|"), key=cab.count)
        try:
            d = pd.read_csv(io.BytesIO(buf), sep=sep, encoding=enc, dtype=str,
                            quotechar='"', on_bad_lines="skip", low_memory=False)
        except Exception:
            continue
        d.columns = [c.strip().strip('"') for c in d.columns]
        return d
    return None


def main():
    if not ORIGEM.exists():
        raise SystemExit(f"não achei {ORIGEM} — baixe o conjunto SERINT antes")

    linhas, relato = [], []
    for nome, buf in fontes():
        d = ler(nome, buf)
        if d is None or d.empty:
            relato.append((nome, "não abriu", 0, 0)); continue
        ano_arq = re.search(r"(20\d\d)", nome)
        ano_arq = int(ano_arq.group(1)) if ano_arq else None
        m = {k: achar(d.columns, p) for k, p in COLUNAS.items()}
        if not m["autor"] or not m["valor"]:
            relato.append((nome, "sem autor ou sem valor", len(d), 0)); continue

        out = pd.DataFrame({
            "ano": (pd.to_numeric(d[m["ano"]], errors="coerce")
                    if m["ano"] else pd.Series([ano_arq] * len(d))),
            "autor": d[m["autor"]].astype(str).str.strip(),
            "municipio": d[m["municipio"]].astype(str).str.strip()
                         if m["municipio"] else None,
            "emenda": d[m["emenda"]].astype(str).str.strip() if m["emenda"] else None,
            "tipo": d[m["tipo"]].astype(str).str.strip() if m["tipo"] else None,
            "funcao": d[m["funcao"]].astype(str).str.strip() if m["funcao"] else None,
            "objeto": d[m["objeto"]].astype(str).str.slice(0, 160) if m["objeto"] else None,
            "valor": dinheiro(d[m["valor"]]),
            "pago": dinheiro(d[m["pago"]]) if m["pago"] else None,
        })
        out["ano"] = out["ano"].fillna(ano_arq)
        out = out[out["autor"].notna() & (out["autor"].str.len() > 2)]
        out = out[out["valor"].notna() & (out["valor"] > 0)]
        relato.append((nome, "ok", len(d), len(out)))
        linhas.append(out)

    print(f"{'arquivo':<42}{'situação':<24}{'lidas':>8}{'úteis':>8}")
    for nome, sit, lidas, uteis in relato:
        print(f"{nome[:41]:<42}{sit:<24}{lidas:>8,}{uteis:>8,}")

    if not linhas:
        raise SystemExit("nenhum arquivo utilizável")
    df = pd.concat(linhas, ignore_index=True)
    df["autor_norm"] = df["autor"].map(chave_pessoa)

    # ---- pareamento com a malha de Goias, conferido ----
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    go = dim[dim["uf"] == "GO"].sort_values("cod_ibge")
    mapa = dict(zip(go["nome_norm"], go["cod_ibge"]))
    pos = {c: i for i, c in enumerate(go["cod_ibge"])}
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    corr = {n: c for u, n, c in zip(ov["uf"], ov["nome_norm_tse"], ov["cod_ibge"])
            if u == "GO"}

    tem = df["municipio"].notna() & (df["municipio"].astype(str).str.len() > 2)
    nn = df.loc[tem, "municipio"].map(geo.normalizar)
    cod = nn.map(mapa)
    falta = cod.isna()
    if falta.any():
        cod = cod.fillna(nn[falta].map(corr))
    df.loc[tem, "cod_ibge"] = cod
    df["idx"] = df["cod_ibge"].map(pos)

    NAO_MUNICIPIO = re.compile(
        r"^(#N/D|CBMGO|DGPC|DGPP|CORPO DE BOMBEIROS|DESCENTRALIZACAO|"
        r"SECRETARIA|FUNDO|POLICIA|UEG|AGENCIA|SUPERINTENDENCIA|GABINETE)",
        re.I)
    orfas_todas = df.loc[tem & df["cod_ibge"].isna(), "municipio"]
    orgaos = orfas_todas[orfas_todas.map(lambda x: bool(NAO_MUNICIPIO.match(sem_acento(x))))]
    orfas = orfas_todas.drop(orgaos.index)
    if len(orgaos):
        amostra = ", ".join(sorted(orgaos.unique())[:6])
        print("")
        print(f"destinatarios que nao sao municipio ({orgaos.nunique()}): {amostra}")
        print("  sao orgaos do estado — ficam fora do mapa por natureza")
    print(f"\n{len(df):,} linhas úteis, {df['autor'].nunique()} autores, "
          f"{int(df['ano'].min())}–{int(df['ano'].max())}")
    print(f"com município: {tem.sum():,} linhas "
          f"({df.loc[tem,'valor'].sum()/df['valor'].sum()*100:.1f}% do valor)")
    if len(orfas):
        v = df.loc[orfas.index, "valor"].sum()
        print(f"NÃO PAREARAM: {orfas.nunique()} nomes, R$ {v/1e6:.1f} mi — "
              + ", ".join(sorted(orfas.unique())[:8]))
    else:
        print("pareamento completo: todo município nomeado achou par na malha")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, index=False, encoding="utf-8")
    print(f"\n{SAIDA.name}: {SAIDA.stat().st_size/1024:.0f} KB")

    print("\n=== por ano ===")
    r = df.groupby(df["ano"].astype("Int64")).agg(
        linhas=("valor", "size"), autores=("autor", "nunique"),
        municipios=("cod_ibge", "nunique"), valor=("valor", "sum"))
    r["valor"] = (r["valor"] / 1e6).round(1).astype(str) + " mi"
    print(r.to_string())

    com = df[df["idx"].notna()]
    if len(com):
        print("\n=== quem mais destinou, onde há município (2023+) ===")
        t = (com.groupby("autor").agg(valor=("valor", "sum"),
                                      mun=("cod_ibge", "nunique"),
                                      n=("valor", "size"))
             .sort_values("valor", ascending=False).head(8))
        t["valor"] = "R$ " + (t["valor"] / 1e6).round(1).astype(str) + " mi"
        print(t.to_string())


if __name__ == "__main__":
    main()
