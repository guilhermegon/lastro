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
    """Autor de emenda -> parlamentar eleito, por nome sem acento.

    Guarda de qual UF, em que pleitos e em qual CASA a pessoa foi eleita: e'
    isso que permite perguntar se a emenda foi para o mesmo chao que deu o voto,
    e tambem separar Camara de Senado.

    **As duas casas, e nao so' a Camara.** Ate 2026-08-30 esta funcao lia apenas
    `*/federal.json`, e o docstring registrava o buraco sem registrar a
    consequencia: a ficha do senador saia com `eleito=False`, e a tela mostrava
    **"nao eleito"** para quem tinha mandato. Otto Alencar, terceiro maior autor
    individual do pais em 2024, era um deles.

    **E a casa importa por si.** Emenda individual e' das duas casas — 594
    autores por exercicio, que e' exatamente 513 + 81 — e o senador tem cota
    MAIOR. Em 2024 os tres maiores autores do pais sao senadores, com R$ 69,6
    mi cada contra mediana de R$ 37,4 mi. Sem a casa, qualquer ordenacao por
    valor poe o Senado no topo por construcao da cota, e o leitor conclui
    comportamento onde ha' regra.

    A casa vem do dado ELEITORAL, nunca da cota: inferir a casa pelo valor e
    depois explicar o valor pela casa seria circular.
    """
    web = cfg.PROCESSED / "web"
    por_nome = {}
    for cargo in ("federal", "senador"):
        for p in sorted(web.glob(f"*/{cargo}.json")):
            uf = p.parent.name
            dd = json.loads(p.read_text(encoding="utf-8"))
            for ano, b in dd.items():
                for f in b["fichas"]:
                    if not f.get("el"):
                        continue
                    comp = sem_acento(f.get("completo", ""))
                    for chave in {sem_acento(f["n"]), comp}:
                        if not chave:
                            continue
                        r = por_nome.setdefault(chave, {
                            "uf": set(), "anos": set(), "urna": f["n"],
                            "sq": [], "casas": set()})
                        # marca a entrada que E' o nome completo: so' essas
                        # entram na segunda passada, porque e' do completo que
                        # o Portal recorta o nome do autor
                        if chave == comp:
                            r["completo_de"] = chave
                        r["uf"].add(uf)
                        r["anos"].add(int(ano))
                        r["sq"].append(f["sq"])
                        r["casas"].add(cargo)
                        # partido POR PLEITO: a sigla a epoca e a de hoje. O
                        # consumidor escolhe pelo ano do exercicio — emenda de
                        # 2016 e' de quem a pessoa era em 2016.
                        r.setdefault("pt", {})[int(ano)] = (
                            f.get("p", ""), f.get("pn", ""))

    # ---------- segunda passada: recorte do nome completo ----------
    #
    # Depois de ler as duas casas, 326 de 1492 autores continuavam sem par, e
    # os maiores deles eram todos senadores. O motivo nao era falta de dado, era
    # a FORMA do nome: o Portal escreve um recorte do nome completo do TSE, que
    # nao e' nem o de urna nem o completo inteiro.
    #
    #   portal                    urna no TSE        completo no TSE
    #   RENAN CALHEIROS           RENAN              JOSE *RENAN* VASCONCELOS *CALHEIROS*
    #   CARLOS FAVARO             FAVARO             *CARLOS* HENRIQUE BAQUETA *FAVARO*
    #   STYVENSON VALENTIM        CAPITAO STYVENSON  EANN *STYVENSON VALENTIM* MENDES
    #   ZENAIDE MAIA              DR. ZENAIDE MAIA   *ZENAIDE MAIA* CALADO PEREIRA...
    #
    # A regra e' de ESTRUTURA e nao de semelhanca: os tokens do autor aparecem
    # em ordem entre os do nome completo. Semelhanca de texto e' o que este
    # projeto recusa desde o pareamento de municipios, porque par errado nao
    # perde dado — poe dado no lugar errado.
    #
    # Tres travas: dois tokens no minimo (SILVA sozinho casaria com meio
    # Congresso), o ultimo token obrigatorio dentro do completo (e' o
    # sobrenome), e UNICIDADE — recorte que serve a duas pessoas nao serve a
    # nenhuma.
    def subsequencia(pequeno, grande):
        it = iter(grande)
        return all(t in it for t in pequeno)

    completos = [(chave.split(), r) for chave, r in por_nome.items()
                 if r.get("completo_de") == chave]

    def por_recorte(nome):
        toks = nome.split()
        if len(toks) < 2:
            return None
        achados = []
        for gtoks, r in completos:
            if toks[-1] not in gtoks:
                continue
            if subsequencia(toks, gtoks):
                achados.append(r)
        if not achados:
            return None
        sqs = {sq for r in achados for sq in r["sq"]}
        nomes = {r["urna"] for r in achados}
        # mesma pessoa reeleita tem varios sq; pessoas diferentes tem nomes de
        # urna diferentes. Divergiu o nome de urna, e' ambiguo.
        if len(nomes) > 1:
            return None
        # o partido vem junto: sem isto os 100 casados por recorte ficariam com
        # nome e sem sigla, que e' meia identificacao
        junto = {"uf": set(), "anos": set(), "sq": list(sqs),
                 "urna": next(iter(nomes)), "casas": set(), "pt": {}}
        for r in achados:
            junto["uf"] |= r["uf"]
            junto["anos"] |= r["anos"]
            junto["casas"] |= r["casas"]
            junto["pt"].update(r.get("pt", {}))
        return junto

    autores = (d[d["individual"]].groupby(["autor_norm", "autor"], as_index=False)
               .agg(emendas=("cod_emenda", "nunique"), pago=("pago", "sum")))
    linhas = []
    n_recorte = 0
    for r in autores.itertuples():
        m = por_nome.get(r.autor_norm)
        if m is None:
            m = por_recorte(r.autor_norm)
            if m is not None:
                n_recorte += 1
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
            # A casa. "ambas" quando a pessoa teve mandato nas duas ao longo da
            # serie — Jader Barbalho e' o caso classico —, e ai o painel nao
            # afirma cota: diz "as duas" e deixa o leitor ver os anos.
            "casa": ("ambas" if m and len(m["casas"]) > 1
                     else (next(iter(m["casas"])) if m else "")),
            # o partido de cada pleito, serializado "ano:sigla:sigla_hoje"
            "partidos": ("|".join(f"{a}:{v[0]}:{v[1]}"
                                  for a, v in sorted(m.get("pt", {}).items()))
                         if m else ""),
        })
    if n_recorte:
        print(f"  {n_recorte} autores casados por recorte do nome completo")
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
    print(f"  casam com parlamentar eleito: {len(casou):,} "
          f"({len(casou)/len(c)*100:.0f}%), {bi(casou['pago'].sum())} "
          f"({casou['pago'].sum()/c['pago'].sum()*100:.0f}% do dinheiro individual)")
    for casa in ("federal", "senador", "ambas"):
        g = c[c["casa"] == casa]
        if len(g):
            print(f"     {casa:<9} {len(g):>5} autores, {bi(g['pago'].sum())}")
    amb = c[c["ambiguo"]]
    if len(amb):
        print(f"  ambíguos (mesmo nome eleito em mais de uma UF): {len(amb)} — "
              f"{', '.join(amb['autor'].head(4))}")


if __name__ == "__main__":
    main()
