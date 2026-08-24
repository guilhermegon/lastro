"""Gasto administrativo da ALEGO: quanto custa a Casa, e no que ela gasta.

Consome quatro assuntos da API de Goias que descrevem a Assembleia como orgao,
nao como conjunto de mandatos:

    orcamentos      quanto foi autorizado e executado, por ano
    diarias         hospedagem e deslocamento, por beneficiario e motivo
    terceirizados   quadro terceirizado, com empresa e funcao
    contratos       contratos vigentes, com fornecedor e valor

**Por que isto e' o que as assembleias tem para dar.** O levantamento das 27
casas (`39_`) mostrou que nenhuma publica emenda parlamentar — a emenda e'
indicacao sobre o orcamento do Executivo. O que elas publicam e' a si mesmas:
folha, diaria, verba de gabinete, contrato, licitacao. Entao e' esse o dado que
existe, e a pergunta que ele responde e' "quanto custa o Legislativo estadual e
no que esse dinheiro vai".

**O campo `total` das diarias NAO pode ser somado, e isso e' achado sobre a
fonte.** A maior "diaria" do conjunto e' de R$ 2.676.075,25 para 1,5 diarias
de um assessor, com motivo sobre edicao de um evento. Ha 128 registros (0,6%)
com valor por diaria acima de R$ 5 mil, e eles concentram R$ 13,46 mi dos
R$ 32,46 mi — **41% da soma vem de menos de 1% dos registros**, e esses
registros nao sao diarias. Por isso publicamos o valor TIPICO e a contagem,
nunca o somatorio.

**Tres cuidados que o dado exige:**

1. **Diaria e' por beneficiario, nao por deputado.** O campo `cargo` distingue
   parlamentar de servidor, e misturar os dois responderia outra pergunta. A
   separacao e' feita aqui e declarada na tela.
2. **Terceirizado vem por `ano_mes`**, um registro por pessoa por mes. Contar
   linhas conta pessoa-mes, nao pessoa — o distinto por nome e' o que mede
   quadro.
3. **Contrato vigente e' fotografia, nao serie.** O endpoint devolve o que esta
   valendo hoje; nao da' para reconstruir historico com ele.
"""
import json
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

B = "https://transparencia.al.go.leg.br/api/transparencia"
WEB = cfg.PROCESSED / "web" / "GO"
ANOS = range(2019, 2027)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t))
    return " ".join("".join(c for c in t
                            if not unicodedata.combining(c)).upper().split())


def get(url):
    """Tres tentativas: falha de rede lida como ausencia de dado ja custou
    dois anos inteiros neste projeto."""
    for _ in range(3):
        r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "120",
                            "-H", f"User-Agent: {UA}", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            try:
                return json.loads(r.stdout)
            except json.JSONDecodeError:
                pass
    return None


def lista(d):
    if d is None:
        return []
    return d if isinstance(d, list) else next(
        (v for v in d.values() if isinstance(v, list)), [])


def num(x):
    return pd.to_numeric(str(x).replace(",", "."), errors="coerce")


def orcamento():
    linhas = []
    for ano in ANOS:
        for r in lista(get(f"{B}/orcamentos.json?ano={ano}&todos=true")):
            r = dict(r)
            r["ano"] = int(r.get("ano") or ano)
            linhas.append(r)
    if not linhas:
        return pd.DataFrame()
    d = pd.DataFrame(linhas)
    # ha DOIS registros por ano: a ALEGO e o FEMAL (fundo especial). Somar os
    # dois responderia outra pergunta; aqui interessa a Casa.
    d["orgao"] = d["tipo"].map(
        lambda t: (t or {}).get("chave") if isinstance(t, dict) else str(t))
    d = d[d["orgao"] == "alego"].drop_duplicates(subset=["ano"], keep="last")
    # o proprio arquivo traz o total pronto; somar colunas duplicava e produzia
    # NaN quando uma delas vinha nula
    for c in ("total_autorizado", "total", "total_pessoal",
              "total_outras_despesas", "total_investimentos"):
        if c in d.columns:
            d[c] = d[c].map(num)
    return d.sort_values("ano")


def diarias():
    pares = [(a, m) for a in ANOS for m in range(1, 13)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        blocos = list(ex.map(
            lambda p: lista(get(f"{B}/diarias.json?ano={p[0]}&mes={p[1]}&todos=true")),
            pares))
    linhas = [x for b in blocos for x in b]
    if not linhas:
        return pd.DataFrame()
    d = pd.DataFrame(linhas)
    for c in ("total", "quantidade_diaria", "outros"):
        if c in d.columns:
            d[c] = d[c].map(num).fillna(0)
    d["ano"] = pd.to_numeric(d.get("ano"), errors="coerce")
    d["cargo_norm"] = d.get("cargo", "").map(sem_acento)
    # parlamentar e servidor respondem perguntas diferentes
    d["parlamentar"] = d["cargo_norm"].str.contains("DEPUTAD", na=False)
    return d


def main():
    print("orçamento da Casa...", flush=True)
    orc = orcamento()
    print(f"  {len(orc)} anos", flush=True)

    print("diárias...", flush=True)
    di = diarias()
    print(f"  {len(di):,} diárias, {di['ano'].nunique() if len(di) else 0} anos",
          flush=True)

    print("terceirizados e contratos...", flush=True)
    ter = pd.DataFrame(lista(get(
        f"{B}/despesas-com-pessoal/servidores-terceirizados.json"
        f"?todos=true&status_pessoa=Terceirizado")))
    con = pd.DataFrame(lista(get(
        f"{B}/contratos-e-convenios/contratos.json?todos=true&contrato_vigente=sim")))

    obj = {"fonte": "API da ALEGO", "anos": [min(ANOS), max(ANOS) - 1]}

    # ---- orçamento ----
    if len(orc):
        obj["orcamento"] = [{
            "ano": int(r.ano),
            "autorizado": round(float(getattr(r, "total_autorizado", 0) or 0), 2),
            "pessoal": round(float(getattr(r, "total_pessoal", 0) or 0), 2),
            "custeio": round(float(getattr(r, "total_outras_despesas", 0) or 0), 2),
            "investimento": round(float(getattr(r, "total_investimentos", 0) or 0), 2),
        } for r in orc.itertuples()]
        print("")
        print("=== orcamento autorizado da ALEGO ===")
        for x in obj["orcamento"]:
            if not x["autorizado"]:
                continue
            print("   %d  R$ %8.1f mi   pessoal R$ %7.1f mi (%d%%)" % (
                x["ano"], x["autorizado"]/1e6, x["pessoal"]/1e6,
                round(x["pessoal"]/x["autorizado"]*100)))

    # ---- diárias ----
    if len(di):
        di["q"] = pd.to_numeric(di.get("quantidade_diaria"), errors="coerce")
        di["unit"] = di["total"] / di["q"].replace(0, pd.NA)
        # o corte separa diaria de registro que nao e' diaria; ver docstring
        susp = (di["unit"] > 5000).fillna(False)
        limpo = di[~susp]
        par = di[di["parlamentar"]]
        srv = di[~di["parlamentar"]]
        vs = float(di.loc[susp, "total"].sum())
        vt = float(di["total"].sum())
        obj["diarias"] = {
            "n": int(len(di)),
            "nParlamentar": int(len(par)),
            "nServidor": int(len(srv)),
            # valor tipico, nao somatorio: a soma e' comandada por 0,6% dos
            # registros, que nao sao diarias
            "unitMediana": round(float(limpo["unit"].median()), 2),
            "suspeitas": int(susp.sum()),
            "valorSuspeitas": round(vs, 2),
            "valorTotalBruto": round(vt, 2),
            "pctSuspeitas": round(vs / vt * 100, 1) if vt else 0,
            "serie": [{"ano": int(a), "n": int(len(g))}
                      for a, g in di.groupby("ano") if pd.notna(a)],
        }
        print("")
        print("=== diarias ===")
        print("   %d registros | %d de parlamentar, %d de servidor" % (
            len(di), len(par), len(srv)))
        print("   valor tipico por diaria: mediana R$ %.2f" % limpo["unit"].median())
        print("   NAO somamos o campo: %d registros com valor por diaria acima" % susp.sum())
        print("   de R$ 5 mil concentram R$ %.2f mi de R$ %.2f mi (%.0f%%)" % (
            vs/1e6, vt/1e6, vs/vt*100))

    # ---- terceirizados ----
    if len(ter):
        pessoas = ter["nome"].nunique() if "nome" in ter else 0
        emp = (ter.groupby("empresa").agg(pessoas=("nome", "nunique"))
               .sort_values("pessoas", ascending=False)) if "empresa" in ter else None
        obj["terceirizados"] = {
            "registros": int(len(ter)), "pessoas": int(pessoas),
            "empresas": int(ter["empresa"].nunique()) if "empresa" in ter else 0,
            "porEmpresa": [{"n": str(i)[:46], "q": int(r.pessoas)}
                           for i, r in (emp.head(10).iterrows() if emp is not None else [])],
        }
        print(f"\n=== terceirizados ===")
        print(f"   {len(ter):,} registros pessoa-mês | {pessoas} pessoas distintas "
              f"| {obj['terceirizados']['empresas']} empresas")
        if emp is not None:
            for i, r in emp.head(5).iterrows():
                print(f"   {str(i)[:44]:<46}{r.pessoas:>5} pessoas")

    # ---- contratos vigentes ----
    if len(con):
        obj["contratos"] = {"n": int(len(con)),
                            "fornecedores": int(con["cpf_cnpj"].nunique())
                            if "cpf_cnpj" in con else 0}
        print(f"\n=== contratos vigentes: {len(con)} ===")

    WEB.mkdir(parents=True, exist_ok=True)
    p = WEB / "alego_admin.json"
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")
    print(f"\n{p.name}: {p.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
