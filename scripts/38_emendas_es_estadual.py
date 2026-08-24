"""Emendas de deputado ESTADUAL no Espirito Santo.

Fonte: `dados.es.gov.br`, conjunto "[Portal da Transparencia] Emendas
Parlamentares do Estado" (SEFAZ). Um CSV por exercicio, 2021 a 2026.

**O ES e' o melhor dos tres estados sondados**, e vale dizer por que, porque a
diferenca e' de publicacao e nao de tamanho:

- **Esquema estavel** nos seis exercicios. Em Goias o esquema mudava todo ano e
  as colunas tiveram de ser achadas por busca; aqui os nomes sao os mesmos.
- **Traz `CodigoMunicipio`**, nao so' o nome. O pareamento por nome — que custou
  23 milhoes de votos do outro lado do projeto — simplesmente nao acontece. O
  codigo vem com SEIS digitos, sem o verificador: "320332" e' o "3203320" do
  IBGE. Casa-se pelos seis primeiros, nunca preenchendo zero a esquerda.
- **Cobertura municipal de 98%** do valor nos exercicios maduros, contra 65,8%
  em Goias.

O portal separa dois conjuntos com nomes quase iguais: "Emendas Parlamentares
**do Estado**" (esta) e "Emendas Parlamentares **da Uniao**" (federais
destinadas ao ES, ja no Emendometro federal). So' a primeira e' dinheiro do
orcamento estadual indicado por deputado estadual.

**A armadilha que quase virou numero publicado.** O ES escreve valor com QUATRO
casas decimais: `11250,0000`. Um detector de formato que so' aceite duas trata a
virgula como separador de milhar e infla o valor dez mil vezes — o primeiro
calculo deu R$ 217 bilhoes para um estado cujo orcamento inteiro e' fracao
disso. O absurdo denunciou; um erro de 10% teria passado.
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

UF = "ES"
API = ("https://dados.es.gov.br/api/3/action/package_search"
       "?q=emendas+parlamentares&rows=6")
ORIGEM = cfg.RAW / "emendas_es"
SAIDA = cfg.PROCESSED / "emendas_es_estadual.csv"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def chave_pessoa(t):
    """O ES prefixa "Dep." em todo autor; o TSE nao usa prefixo nenhum."""
    return re.sub(r"^(DEP\.?|DEPUTAD[OA])\s+", "", sem_acento(t)).strip()


def dinheiro(s):
    """Virgula decimal com ATE QUATRO casas — o ES publica "11250,0000".

    Com o limite em duas, a virgula vira separador de milhar e o valor infla
    dez mil vezes. O padrao decide pela cauda da string, nao por regra fixa,
    porque portais alternam formato entre exercicios sem avisar.
    """
    if s is None:
        return pd.Series(dtype="float64")
    t = s.astype(str).str.strip().str.replace("R$", "", regex=False)
    br = t.str.contains(r",\d{1,4}$", regex=True, na=False)
    t = t.where(~br, t.str.replace(".", "", regex=False)
                      .str.replace(",", ".", regex=False))
    t = t.where(br, t.str.replace(",", "", regex=False))
    return pd.to_numeric(t, errors="coerce").fillna(0.0)


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
        raise SystemExit("o portal do ES não respondeu")
    fora = []
    for p in json.loads(raw)["result"]["results"]:
        # "do Estado", nunca "da União": os dois conjuntos existem lado a lado
        if "stado" not in (p.get("title") or ""):
            continue
        for r in p.get("resources", []):
            nome = r.get("name") or ""
            if (r.get("format") or "").upper() != "CSV":
                continue
            # so' os arquivos de exercicio; contratos, convenios e execucao
            # sao outro grao e entrariam somando duas vezes
            m = re.fullmatch(r"Emendas-Estaduais-(20\d\d)\.csv", nome)
            if not m:
                continue
            f = ORIGEM / f"es_{m.group(1)}.csv"
            if not f.exists() or f.stat().st_size == 0:
                rc, _ = curl(r["url"], f)
                if rc != 0 or f.stat().st_size == 0:
                    print(f"  {m.group(1)}: download vazio ou falhou")
                    continue
            fora.append((int(m.group(1)), f))
    return sorted(fora)


def main():
    arquivos = baixar()
    if not arquivos:
        raise SystemExit("nenhum exercício baixado")

    partes, relato = [], []
    for ano, f in arquivos:
        d = pd.read_csv(f, sep=";", encoding="utf-8-sig", dtype=str,
                        on_bad_lines="skip", low_memory=False)
        d.columns = [c.strip() for c in d.columns]
        falta = [c for c in ("NomeAutor", "Municipio", "CodigoMunicipio")
                 if c not in d.columns]
        if falta:
            relato.append((ano, f"sem {'/'.join(falta)}", len(d), 0))
            continue
        pago = dinheiro(d.get("ValorPago")) + dinheiro(d.get("ValorRap"))
        out = pd.DataFrame({
            "ano": pd.to_numeric(d.get("AnoEmenda"), errors="coerce").fillna(ano),
            "autor": d["NomeAutor"].astype(str).str.strip(),
            "municipio": d["Municipio"].astype(str).str.strip(),
            "cod_bruto": d["CodigoMunicipio"].astype(str).str.strip(),
            "emenda": d.get("NumeroEmenda", pd.Series([""] * len(d))).astype(str),
            "tipo": d.get("TipoEmenda", pd.Series([""] * len(d))).astype(str),
            "funcao": d.get("Funcao", pd.Series([""] * len(d))).astype(str),
            "objeto": d.get("ObjetoFinalidade",
                            pd.Series([""] * len(d))).astype(str).str.slice(0, 160),
            "valor": pago,
            "empenhado": dinheiro(d.get("ValorEmpenho")),
        })
        out = out[out["autor"].str.len() > 2]
        out = out[out["valor"] > 0]
        relato.append((ano, "ok", len(d), len(out)))
        partes.append(out)

    print(f"{'ano':<7}{'situação':<24}{'lidas':>9}{'com pagamento':>15}")
    for ano, sit, lidas, uteis in relato:
        print(f"{ano:<7}{sit:<24}{lidas:>9,}{uteis:>15,}")
    if not partes:
        raise SystemExit("nenhum exercício utilizável")

    df = pd.concat(partes, ignore_index=True)
    df["autor_norm"] = df["autor"].map(chave_pessoa)

    # ---- código do IBGE direto, sem pareamento por nome ----
    dim = pd.read_csv(cfg.PROCESSED / "nac_dim_municipio.csv",
                      dtype={"cod_ibge": str})
    g = dim[dim["uf"] == UF].sort_values("cod_ibge")
    pos = {c: i for i, c in enumerate(g["cod_ibge"])}
    # O ES publica o codigo do IBGE SEM o digito verificador: seis digitos,
    # nao sete. "320332" e' o "3203320" de Maratanzes. Casar pelos seis
    # primeiros do codigo completo, e nao preencher zero a esquerda — foi o
    # que zerou o pareamento na primeira tentativa.
    curto = {c[:6]: c for c in pos}
    if len(curto) != len(pos):
        raise SystemExit("dois municípios do ES com os mesmos 6 dígitos — "
                         "o corte não identifica sozinho")
    seis = df["cod_bruto"].str.extract(r"(\d{6})")[0]
    df["cod_ibge"] = seis.map(curto)
    df["idx"] = df["cod_ibge"].map(pos)

    fora = df.loc[df["cod_ibge"].isna() & (df["municipio"].str.len() > 2)]
    print(f"\n{len(df):,} linhas com pagamento, {df['autor'].nunique()} autores, "
          f"{int(df['ano'].min())}–{int(df['ano'].max())}")
    print(f"R$ {df['valor'].sum()/1e6:,.1f} mi | "
          f"{df['cod_ibge'].nunique()} de {len(pos)} municípios")
    print(f"com município: {df['cod_ibge'].notna().mean()*100:.1f}% das linhas, "
          f"{df.loc[df['cod_ibge'].notna(),'valor'].sum()/df['valor'].sum()*100:.1f}% do valor")
    if len(fora):
        print(f"\ncódigo fora da malha do ES: {fora['municipio'].nunique()} nomes, "
              f"R$ {fora['valor'].sum()/1e6:.2f} mi")
        for nome, n in fora["municipio"].value_counts().head(6).items():
            print(f"   {str(nome)[:40]:<42}{n:>5} linhas")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, index=False, encoding="utf-8")
    print(f"\n{SAIDA.name}: {SAIDA.stat().st_size/1024:.0f} KB")

    print("\n=== quem mais destinou ===")
    t = (df[df["idx"].notna()].groupby("autor")
         .agg(valor=("valor", "sum"), mun=("cod_ibge", "nunique"),
              n=("emenda", "nunique"))
         .sort_values("valor", ascending=False).head(8))
    t["valor"] = "R$ " + (t["valor"] / 1e6).round(2).astype(str) + " mi"
    print(t.to_string())


if __name__ == "__main__":
    main()
