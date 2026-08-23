"""Gasto administrativo da Camara Legislativa do DF: quanto custa a Casa.

O par do `42_` (ALEGO). A CLDF nao tem API: publica CKAN com CSV, e o que ela
da' e' mais fundo do que Goias em uma dimensao e mais raso em outra.

    total-de-despesas    empenhado, liquidado e pago por mes, 2022 em diante
    duodecimo            repasse recebido e previsto por mes — a receita da Casa
    terceirizados        pessoa-mes com empresa e CNPJ, ago/2023 em diante
    quadro de pessoal    FOLHA NOMINAL mensal: cada pessoa, cargo, lotacao e
                         remuneracao, 108 arquivos mensais

**A folha nominal e' o que nenhuma outra das tres casas publica.** Goias da'
total de pessoal no orcamento; o DF da' nome a nome, com lotacao — o que permite
separar quadro proprio de quadro de gabinete, que e' a divisao que interessa num
Legislativo e que o numero agregado esconde.

**Uma pessoa aparece varias vezes no mesmo mes, e contar linhas conta
pagamento, nao gente.** O mes tem varias folhas (001 principal, 021, 020, 099...)
e 2.623 matriculas viram 5.052 linhas. Foi assim que a primeira versao deste
script relatou "48 deputados distritais" num Distrito Federal que tem 24. O
distinto e' por matricula.

**O bruto e' piso, nao total.** So a folha principal detalha os creditos; as
folhas secundarias trazem as colunas de credito zeradas e apenas o liquido — em
julho de 2026, R$ 4,9 mi pagos cujo bruto o arquivo nao informa. Somar as
colunas de credito entao nao duplica (as secundarias somam zero), mas tambem nao
alcanca tudo. O numero publicado e' declarado como minimo.

**Os nomes dos arquivos nao seguem um padrao, e presumir que seguem apaga
dados.** Os 108 meses aparecem como `2017-09 - Quadro Desmonstrativo de Pessoal`,
`2022-01`, `2024-08 ` (com espaco no fim), `2025-7` (sem zero) e ate' `2022-2025`,
que e' um intervalo e nao um mes. Um `\d{4}-\d{2}` estrito — que foi o primeiro
que escrevi — descartava quatro meses de 2025 em silencio e comecava a serie em
2022, cortando cinco anos que estao publicados.

**A folha confere com o outro arquivo da Casa.** Em julho de 2026 a folha bruta
da' R$ 59,85 mi e a despesa paga da CLDF, que vem de arquivo independente, da'
R$ 77,82 mi. A folha e' 77% do que a Casa pagou no mes — proporcao plausivel, com
o resto em custeio, terceirizado e investimento. Sao duas fontes que poderiam
divergir e nao divergem.

**O esquema da folha muda ao longo dos nove anos, e casar coluna por nome
literal quebra.** Sao 20 colunas em 2018, 21 em 2020 e 23 de 2022 em diante. O
acento se move dentro do proprio cabecalho — `Vencimentos, Subsidio ou Provento`
em 2020 era `Vencimentos, Subsidio ou Provento` com acento em 2018, e
`Remuneracao do Cargo em Comissao` era `Remuneracao` acentuado. A coluna `Folha`
so aparece em 2020; `Tipo Lotacao` so em 2022. Por isso as colunas sao
encontradas por nome NORMALIZADO (sem acento, sem caixa), e o recorte por
gabinete — que depende de `Tipo Lotacao` — so vale de 2022 em diante e e'
declarado como tal.

**Os auxilios ficam de fora do bruto, nos nove anos.** Alimentacao, transporte e
pre-escolar mudam de posicao no arquivo (em 2018 vinham no bloco de creditos, de
2020 em diante depois dos descontos). Incluir por posicao daria series
incomparaveis; excluir sempre da' uma serie internamente consistente, que e' o
que a comparacao entre anos exige.

**Nao somamos a coluna `Liquido`.** Liquido e' o que cai na conta da pessoa,
depois de IRRF e previdencia. O que a Casa gasta e' o bruto. Publicar liquido
como custo subestimaria a folha em cerca de um terco, e o erro passaria
despercebido porque o numero sai redondo e plausivel.

**O ano corrente e' parcial e isso fica declarado.** O arquivo de despesas vai
ate' o mes de fechamento mais recente; comparar o total de 2026 com o de 2025
mediria o calendario, nao o gasto. As series aqui excluem o ano incompleto dos
totais anuais e o dizem na tela.

**Terceirizado vem por pessoa-mes**, um registro por pessoa por mes — a mesma
armadilha de Goias. Contar linhas conta permanencia, nao tamanho de quadro.

**Nao baixamos os 107 meses de folha**, que vao de setembro de 2017 a julho
de 2026. Sao ~1 MB cada. Para composicao basta o
mes mais recente; para serie basta o mesmo mes de cada ano, que compara periodo
comparavel do calendario. Baixar tudo custaria 100 MB para responder a mesma
pergunta.
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

CKAN = "https://dados.cl.df.gov.br/api/3/action"
WEB = cfg.PROCESSED / "web" / "DF"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

MESES = ["Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
# as colunas de credito da folha; o custo da Casa e' a soma delas, nao o liquido
BRUTO = ["Vencimentos, Subsidio ou Provento", "Remuneracao do Cargo em Comissao",
         "Vantagens Periodicas e Eventuais", "Vantagens Pessoais",
         "Outros Creditos"]


def sem_acento(t):
    if t is None or (isinstance(t, float) and t != t):
        return ""
    t = unicodedata.normalize("NFKD", str(t))
    t = "".join(c for c in t if not unicodedata.combining(c)).strip().upper()
    # pandas entrega NaN como a string "NAN" depois do str(); sem isto vira uma
    # categoria de gente chamada NAN
    return "" if t in ("NAN", "NONE", "NAT") else t


def baixa(url):
    for _ in range(3):
        r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "180",
                            "-H", f"User-Agent: {UA}", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
    return None


def pacote(nome):
    b = baixa(f"{CKAN}/package_show?id={nome}")
    try:
        return json.loads(b)["result"]["resources"]
    except Exception:
        return []


def csv(b, sep=";", enc="latin-1"):
    return pd.read_csv(io.BytesIO(b), sep=sep, encoding=enc, dtype=str)


def brl(s):
    """1.234.567,89 -> 1234567.89. Vazio vira NaN, nunca zero: zero e' um
    valor, ausencia nao e'."""
    t = s.astype(str).str.strip().str.replace(r"[R$\s]", "", regex=True)
    t = t.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(t, errors="coerce")


def despesas():
    rs = [r for r in pacote("total-de-despesas")
          if (r.get("format") or "").upper() == "CSV"]
    if not rs:
        return pd.DataFrame()
    d = csv(baixa(rs[0]["url"]))
    d.columns = [sem_acento(c) for c in d.columns]
    d["ano"] = pd.to_numeric(d["ANO"], errors="coerce")
    ordem = {sem_acento(m): i + 1 for i, m in enumerate(MESES)}
    d["mes"] = d["MES"].map(lambda x: ordem.get(sem_acento(x)))
    for c in ("EMPENHADO", "LIQUIDADO", "PAGO"):
        d[c.lower()] = brl(d[c])
    return d.dropna(subset=["ano", "mes"]).sort_values(["ano", "mes"])


def duodecimo():
    rs = [r for r in pacote("duodecimo-orcamentario")
          if (r.get("format") or "").upper() == "CSV"]
    if not rs:
        return pd.DataFrame()
    d = csv(baixa(rs[0]["url"]), enc="utf-8-sig")
    d.columns = [sem_acento(c) for c in d.columns]
    d["ano"] = pd.to_numeric(d["ANO"], errors="coerce")
    ordem = {sem_acento(m): i + 1 for i, m in enumerate(MESES)}
    d["mes"] = d["MES"].map(lambda x: ordem.get(sem_acento(x)))
    for c in d.columns:
        if c.startswith("REPASSES") or c.startswith("TOTAL"):
            d[c] = brl(d[c])
    return d.dropna(subset=["ano", "mes"])


def terceirizados():
    rs = [r for r in pacote("terceirizados")
          if (r.get("format") or "").upper() == "CSV"]
    if not rs:
        return pd.DataFrame()
    d = csv(baixa(rs[0]["url"]))
    d = d[[c for c in d.columns if not str(c).startswith("Unnamed")]]
    d.columns = [sem_acento(c) for c in d.columns]
    d = d.dropna(subset=["NOME"])
    return d


def competencia(nome):
    """(ano, mes) do nome do recurso, que nao segue padrao — ver docstring.

    Aceita `2022-01`, `2025-7`, `2024-08 ` e `2017-09 - Quadro ...`.
    Rejeita `2022-2025`, que e' intervalo: o segundo grupo tem de ser mes."""
    m = re.match(r"^\s*(\d{4})-(\d{1,2})(?!\d)", str(nome or ""))
    if not m:
        return None
    ano, mes = int(m.group(1)), int(m.group(2))
    if not (1 <= mes <= 12) or not (2000 <= ano <= 2100):
        return None
    return ano, mes


def folha():
    """Mes mais recente para composicao; mesmo mes de cada ano para serie."""
    rs = []
    for r in pacote("quadro-demonstrativo-de-pessoal-mensal"):
        if (r.get("format") or "").upper() != "CSV":
            continue
        c = competencia(r.get("name"))
        if c:
            rs.append((c, r))
    if not rs:
        return None, []
    rs.sort(key=lambda x: x[0], reverse=True)
    (_, alvo), recente = rs[0][0], rs[0][1]
    # mesmo mes de calendario em cada ano: comparar julho com julho, nao com
    # dezembro, que carrega decimo terceiro
    serie, vistos = [], set()
    for (ano, mes), r in rs:
        if mes == alvo and ano not in vistos:
            vistos.add(ano)
            serie.append(((ano, mes), r))
    serie.sort(key=lambda x: x[0])
    print(f"  {len(rs)} meses publicados, de {rs[-1][0][0]}-{rs[-1][0][1]:02d} "
          f"a {rs[0][0][0]}-{rs[0][0][1]:02d}; série usa o mês {alvo:02d} de "
          f"{len(serie)} anos", flush=True)
    return recente, serie


def col(d, *pistas):
    """Acha a coluna pelo nome normalizado — o cabecalho muda de acento e de
    caixa entre os anos, e casar literal apaga a coluna em silencio."""
    norm = {sem_acento(c).replace(",", " "): c for c in d.columns}
    for pista in pistas:
        alvo = sem_acento(pista).replace(",", " ")
        for k, v in norm.items():
            if k.startswith(alvo):
                return v
    return None


def le_folha(r):
    b = baixa(r["url"])
    if not b:
        return None
    d = pd.read_csv(io.BytesIO(b), sep=",", encoding="utf-8-sig", dtype=str)
    achadas = []
    d["bruto"] = 0.0
    for pista in BRUTO:
        c = col(d, pista)
        if c is None:
            continue
        achadas.append(c)
        d["bruto"] += pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    if not achadas:
        return None
    cl = col(d, "Liquido")
    d["liquido"] = (pd.to_numeric(d[cl], errors="coerce").fillna(0.0)
                    if cl else 0.0)
    ct = col(d, "Tipo")
    d["tipo"] = d[ct].map(sem_acento) if ct else ""
    # `Tipo Lotacao` so existe de 2022 em diante; sem ela o recorte por gabinete
    # nao existe, e ficar sem e' melhor do que inventar a partir do nome livre
    clot = col(d, "Tipo Lotacao")
    d["lot"] = d[clot].map(sem_acento) if clot else None
    cm = col(d, "Matricula")
    d["mat"] = d[cm].astype(str).str.strip() if cm else d.index.astype(str)
    return d


def pessoas(d):
    """Uma linha por matricula, somando o bruto das varias folhas do mes.

    Sem isto, contar linhas conta pagamento: em julho de 2026 sao 5.052 linhas
    para 2.623 pessoas, e os 24 deputados distritais viravam 48."""
    if d["lot"].isna().all():
        d = d.assign(lot="")
    g = d.groupby("mat", as_index=False).agg(
        bruto=("bruto", "sum"), liquido=("liquido", "sum"),
        tipo=("tipo", "first"), lot=("lot", "first"))
    return g


def main():
    obj = {"fonte": "Portal de Dados Abertos da CLDF (CKAN)"}

    print("despesas da Casa...", flush=True)
    de = despesas()
    if len(de):
        ult = de.iloc[-1]
        anos = (de.groupby("ano")
                .agg(pago=("pago", "sum"), empenhado=("empenhado", "sum"),
                     meses=("mes", "nunique")))
        completos = anos[anos["meses"] == 12]
        obj["despesas"] = {
            "ate": f"{int(ult.ano)}-{int(ult.mes):02d}",
            "serie": [{"ano": int(a), "pago": round(float(r.pago), 2),
                       "empenhado": round(float(r.empenhado), 2),
                       "meses": int(r.meses)} for a, r in anos.iterrows()],
            "anosCompletos": [int(a) for a in completos.index],
        }
        print("")
        print("=== despesa da CLDF (UO 1101) ===")
        for a, r in anos.iterrows():
            marca = "" if r.meses == 12 else "  <- ANO PARCIAL, %d meses" % r.meses
            print("   %d  pago R$ %7.1f mi   empenhado R$ %7.1f mi%s" % (
                a, r.pago/1e6, r.empenhado/1e6, marca))

    print("\nduodécimo...", flush=True)
    du = duodecimo()
    if len(du):
        col = next((c for c in du.columns if c.startswith("TOTAL")), None)
        prev = next((c for c in du.columns if "PREVISTO" in c), None)
        g = du.groupby("ano").agg(rec=(col, "sum"), pre=(prev, "sum"),
                                  meses=("mes", "nunique"))
        obj["duodecimo"] = [{"ano": int(a), "recebido": round(float(r.rec), 2),
                             "previsto": round(float(r.pre), 2),
                             "meses": int(r.meses)} for a, r in g.iterrows()]
        print("=== repasse recebido (duodécimo) ===")
        for a, r in g.iterrows():
            falta = "" if r.meses == 12 else "  (%d meses)" % r.meses
            print("   %d  R$ %7.1f mi de R$ %7.1f mi previstos%s" % (
                a, r.rec/1e6, r.pre/1e6, falta))

    print("\nterceirizados...", flush=True)
    te = terceirizados()
    if len(te):
        emp = (te.groupby("EMPRESA").agg(q=("NOME", "nunique"))
               .sort_values("q", ascending=False))
        obj["terceirizados"] = {
            "registros": int(len(te)), "pessoas": int(te["NOME"].nunique()),
            "empresas": int(te["EMPRESA"].nunique()),
            "meses": int(te["MES"].nunique()),
            "porEmpresa": [{"n": str(i)[:44], "q": int(r.q)}
                           for i, r in emp.head(8).iterrows()],
        }
        print("=== terceirizados ===")
        print("   %d registros pessoa-mês em %d meses | %d pessoas distintas | "
              "%d empresas" % (len(te), te["MES"].nunique(),
                               te["NOME"].nunique(), te["EMPRESA"].nunique()))

    print("\nfolha nominal...", flush=True)
    recente, serie = folha()
    if recente is not None:
        bruta = le_folha(recente)
        f = pessoas(bruta) if bruta is not None else None
        if f is not None:
            tot = float(f["bruto"].sum())
            # o que as folhas secundarias pagam sem detalhar credito: o bruto
            # publicado e' piso, e o tamanho do que falta fica medido aqui
            soLiq = float(bruta.loc[bruta["bruto"] <= 0, "liquido"].sum())
            dep = f[f["tipo"].str.contains("DEPUTAD", na=False)]
            temLot = bool(bruta["lot"].notna().any())
            gab = (f[f["lot"].str.contains("GABINETE", na=False)] if temLot
                   else f.iloc[0:0])
            portipo = (f.groupby("tipo").agg(q=("bruto", "size"),
                                             v=("bruto", "sum"))
                       .sort_values("v", ascending=False))
            obj["folha"] = {
                "mes": "%d-%02d" % competencia(recente["name"]),
                "linhas": int(len(bruta)),
                "semDetalhe": round(soLiq, 2),
                "pessoas": int(len(f)),
                "bruto": round(tot, 2),
                "deputados": int(len(dep)),
                "brutoDeputados": round(float(dep["bruto"].sum()), 2),
                "temLotacao": temLot,
                "emGabinete": int(len(gab)),
                "brutoGabinete": round(float(gab["bruto"].sum()), 2),
                "pctGabinete": round(float(gab["bruto"].sum()) / tot * 100, 1)
                if tot else 0,
                "porTipo": [{"n": str(i)[:34] or "(sem tipo)", "q": int(r.q),
                             "v": round(float(r.v), 2)}
                            for i, r in portipo.head(8).iterrows()],
            }
            print("=== folha de %d-%02d ===" % competencia(recente["name"]))
            print("   %d linhas de pagamento -> %d pessoas distintas (matrícula)"
                  % (len(bruta), len(f)))
            print("   bruto R$ %.2f mi no mês (PISO: R$ %.2f mi saem em folha"
                  " secundária que não detalha crédito)" % (tot/1e6, soLiq/1e6))
            print("   %d deputados distritais, R$ %.2f mi (%.1f%% da folha)" % (
                len(dep), dep["bruto"].sum()/1e6, dep["bruto"].sum()/tot*100))
            if temLot:
                print("   %d lotados em gabinete, R$ %.2f mi (%.1f%%)" % (
                    len(gab), gab["bruto"].sum()/1e6,
                    gab["bruto"].sum()/tot*100))
            for i, r in portipo.head(6).iterrows():
                print("   %-34s %5d pessoas   R$ %6.2f mi" % (
                    str(i)[:34] or "(sem tipo)", r.q, r.v/1e6))

        # serie: mesmo mes de calendario em cada ano
        pontos, falhas = [], []
        for (ano, mes), r in serie:
            g = le_folha(r)
            if g is None:
                # falha de download NAO e' ausencia de dado: fica registrada
                falhas.append("%d-%02d" % (ano, mes))
                continue
            q = pessoas(g)
            pontos.append({"mes": "%d-%02d" % (ano, mes),
                           "pessoas": int(len(q)),
                           "bruto": round(float(q["bruto"].sum()), 2)})
        if falhas:
            obj["folhaFalhas"] = falhas
            print("   ATENÇÃO: %d meses não baixaram: %s"
                  % (len(falhas), ", ".join(falhas)))
        if len(pontos) > 1:
            obj["folhaSerie"] = pontos
            print("\n=== folha no mesmo mês de cada ano ===")
            for p in pontos:
                print("   %s  %5d pessoas   R$ %6.2f mi" % (
                    p["mes"], p["pessoas"], p["bruto"]/1e6))

    WEB.mkdir(parents=True, exist_ok=True)
    p = WEB / "cldf_admin.json"
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")
    print(f"\n{p.name}: {p.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
