"""Emendas de deputado ESTADUAL em Pernambuco.

Fonte: `dados.pe.gov.br`, conjunto "Emendas Parlamentares Estaduais" (pacote
7c721673-...), publicado pela SEPLAG. Um CSV por exercicio, **2012 a 2026** —
quinze anos, contra sete em Goias.

**Pernambuco e' o oposto de Goias em qualidade de publicacao**, e vale registrar
porque muda o custo de replicar: PE publica dicionario de dados versionado, com
descricao campo a campo, e o esquema e' estavel entre anos. Em Goias o esquema
mudava todo ano e as colunas tiveram de ser achadas por busca. Aqui os nomes sao
os do dicionario.

E os campos de valor batem com a definicao federal sem traducao:
`valor_pago + valor_rp_pago` e' o mesmo "saiu do caixa" que usamos no Portal da
Transparencia — pago no exercicio mais restos a pagar efetivamente pagos.

**Dois conjuntos vizinhos que NAO sao isto**, e confundi-los seria somar
orcamentos diferentes:

- "Emendas Individuais e de Bancada" — emenda FEDERAL destinada a Pernambuco,
  operada no Transferegov. Ja esta no Emendometro federal.
- "Emendas Especiais - PIX" — recursos que o estado RECEBE por transferencia
  especial federal. Tambem federal, do outro lado do balcao.

So "Emendas Parlamentares Estaduais" e' dinheiro do orcamento do estado indicado
por deputado estadual.
"""
import io
import json
import re
import subprocess
import sys
import unicodedata
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")
geo = import_module("04_geo")

UF = "PE"
PACOTE = "7c721673-6f32-467b-853f-297ec1399705"
API = f"https://dados.pe.gov.br/api/3/action/package_show?id={PACOTE}"
ORIGEM = cfg.RAW / "emendas_pe"
SAIDA = cfg.PROCESSED / "emendas_pe_estadual.csv"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def chave_pessoa(t):
    return re.sub(r"^(DEP\.?|DEPUTAD[OA])\s+", "", sem_acento(t)).strip()


def curl(url, destino=None):
    cmd = ["curl.exe", "-sS", "-L", "--fail", "--max-time", "300",
           "-H", f"User-Agent: {UA}"]
    if destino:
        cmd += ["-o", str(destino)]
    r = subprocess.run(cmd + [url], capture_output=True)
    return r.returncode, r.stdout


def baixar():
    ORIGEM.mkdir(parents=True, exist_ok=True)
    rc, raw = curl(API)
    if rc != 0:
        raise SystemExit("o portal de PE não respondeu")
    pk = json.loads(raw)["result"]
    baixados = []
    for r in pk.get("resources", []):
        fmt = (r.get("format") or "").upper().lstrip(".")
        nome = r.get("name") or ""
        # so' os CSV de exercicio; metadados e JSON ficam fora
        if fmt != "CSV" or "etadado" in nome:
            continue
        ano = re.search(r"(20\d\d)", nome)
        if not ano:
            continue
        f = ORIGEM / f"pe_{ano.group(1)}.csv"
        if not f.exists():
            rc, _ = curl(r["url"], f)
            if rc != 0:
                print(f"  falhou {ano.group(1)}")
                continue
        baixados.append((int(ano.group(1)), f))
    return sorted(baixados)


def ler(f):
    for enc in ("utf-8-sig", "latin-1"):
        try:
            cab = f.read_bytes()[:8000].decode(enc).splitlines()[0]
        except (UnicodeDecodeError, IndexError):
            continue
        sep = max((";", ",", "\t", "|"), key=cab.count)
        try:
            d = pd.read_csv(f, sep=sep, encoding=enc, dtype=str,
                            on_bad_lines="skip", low_memory=False)
        except Exception:
            continue
        d.columns = [sem_acento(c).lower().replace(" ", "_") for c in d.columns]
        return d
    return None


def dinheiro(s):
    if s is None:
        return 0.0
    t = s.astype(str).str.strip().str.replace("R$", "", regex=False)
    # o portal alterna ponto e virgula entre exercicios; decidir pela posicao
    # do ultimo separador, nao por regra fixa
    br = t.str.contains(r",\d{1,2}$", regex=True, na=False)
    t = t.where(~br, t.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    t = t.where(br, t.str.replace(",", "", regex=False))
    return pd.to_numeric(t, errors="coerce").fillna(0.0)


def main():
    arquivos = baixar()
    if not arquivos:
        raise SystemExit("nenhum CSV de exercício baixado")
    print(f"{len(arquivos)} exercícios: "
          f"{arquivos[0][0]}–{arquivos[-1][0]}\n")

    partes, relato = [], []
    for ano, f in arquivos:
        d = ler(f)
        if d is None or d.empty:
            relato.append((ano, "não abriu", 0, 0)); continue
        falta = [c for c in ("autor", "municipio") if c not in d.columns]
        if falta:
            relato.append((ano, f"sem {'/'.join(falta)}", len(d), 0)); continue
        pago = dinheiro(d.get("valor_pago")) + dinheiro(d.get("valor_rp_pago"))
        out = pd.DataFrame({
            "ano": pd.to_numeric(d.get("ano"), errors="coerce").fillna(ano),
            "autor": d["autor"].astype(str).str.strip(),
            "municipio": d["municipio"].astype(str).str.strip(),
            "emenda": d.get("codigo_alepe", pd.Series([""] * len(d))).astype(str),
            "tipo": d.get("tipo", pd.Series([""] * len(d))).astype(str),
            "funcao": d.get("tematica", pd.Series([""] * len(d))).astype(str),
            "objeto": d.get("resumo_objeto", d.get("objeto", pd.Series([""] * len(d)))).astype(str).str.slice(0, 160),
            "valor": pago,
            "empenhado": dinheiro(d.get("valor_empenhado")),
        })
        out = out[out["autor"].str.len() > 2]
        out = out[out["valor"] > 0]
        relato.append((ano, "ok", len(d), len(out)))
        partes.append(out)

    print(f"{'ano':<7}{'situação':<20}{'lidas':>9}{'com pagamento':>15}")
    for ano, sit, lidas, uteis in relato:
        print(f"{ano:<7}{sit:<20}{lidas:>9,}{uteis:>15,}")

    if not partes:
        raise SystemExit("nenhum exercício utilizável")
    df = pd.concat(partes, ignore_index=True)
    df["autor_norm"] = df["autor"].map(chave_pessoa)

    # ---- pareamento com a malha de PE, conferido ----
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    g = dim[dim["uf"] == UF].sort_values("cod_ibge")
    mapa = dict(zip(g["nome_norm"], g["cod_ibge"]))
    pos = {c: i for i, c in enumerate(g["cod_ibge"])}
    ov = pd.read_csv(cfg.OVERRIDES / "municipios_tse_ibge.csv", dtype=str)
    corr = {n: c for u, n, c in zip(ov["uf"], ov["nome_norm_tse"], ov["cod_ibge"])
            if u == UF}

    nn = df["municipio"].map(geo.normalizar)
    cod = nn.map(mapa)
    falta = cod.isna()
    if falta.any():
        cod = cod.fillna(nn[falta].map(corr))
    df["cod_ibge"] = cod
    df["idx"] = df["cod_ibge"].map(pos)

    print(f"\n{len(df):,} linhas com pagamento, {df['autor'].nunique()} autores, "
          f"{int(df['ano'].min())}–{int(df['ano'].max())}")
    print(f"R$ {df['valor'].sum()/1e6:,.0f} mi pagos | "
          f"{df['cod_ibge'].nunique()} de {len(pos)} municípios")

    orf = df.loc[df["cod_ibge"].isna(), "municipio"].value_counts()
    if len(orf):
        v = df.loc[df["cod_ibge"].isna(), "valor"].sum()
        print(f"\nsem par: {len(orf)} nomes, R$ {v/1e6:.1f} mi "
              f"({v/df['valor'].sum()*100:.2f}% do valor)")
        for nome, n in orf.head(10).items():
            print(f"   {str(nome)[:44]:<46}{n:>6} linhas")
    else:
        print("\npareamento completo")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, index=False, encoding="utf-8")
    print(f"\n{SAIDA.name}: {SAIDA.stat().st_size/1024:.0f} KB")

    print("\n=== quem mais destinou, com município ===")
    t = (df[df["idx"].notna()].groupby("autor")
         .agg(valor=("valor", "sum"), mun=("cod_ibge", "nunique"),
              n=("valor", "size"))
         .sort_values("valor", ascending=False).head(8))
    t["valor"] = "R$ " + (t["valor"] / 1e6).round(1).astype(str) + " mi"
    print(t.to_string())


if __name__ == "__main__":
    main()
