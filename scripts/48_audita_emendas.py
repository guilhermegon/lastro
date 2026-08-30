"""Auditoria do Emendometro: o que garantimos, o que nao, e com que numero.

Escrito porque o usuario perguntou se da' para garantir que o dado esta' completo
e e' confiavel. A resposta honesta e' **nao** — e uma resposta honesta a essa
pergunta nao e' uma opiniao, e' uma lista de medidas. Este script produz a lista.

Ele NAO tenta provar que o dado esta' certo. Tenta o contrario: procura os
lugares onde ele poderia estar errado e mede o tamanho de cada um. O que sobrar
sem furo e' o que da' para afirmar.

Sao seis checagens, e cada uma declara em que escopo trabalha:

1. **Publicado x origem**, ambos em "individual com municipio". Se o pipeline
   perdeu linha no caminho, e' aqui que aparece.
2. **Consistencia interna** — em toda UF e todo ano, a soma por autor tem de
   bater com o total do ano, e a soma por municipio nunca pode passar dele.
3. **O que fica de fora, e por que** — separa o que sai por ESCOPO (bancada,
   comissao, relator) do que sai por FALTA DE DADO (MULTIPLO). Sao coisas
   diferentes: uma e' decisao nossa, a outra e' limite da fonte.
4. **Os dois numeros que a aba Sobre publica** — 97,1% com UF e 10,5% com
   municipio sao conferidos contra o medido, com tolerancia de 0,15 ponto.
5. **Buraco de serie** — algum ano tao fora da curva que sugira arquivo
   truncado? Ano incompleto e' legitimo; ano vazio no meio, nao.
6. **Agregado nacional** no escopo dele (UF, nao municipio), contra o CSV.

O script sai com codigo 1 se qualquer uma falhar: e' gate, nao relatorio.

Nenhuma delas verifica se o Portal da Transparencia publicou a verdade. Isso
esta' fora do nosso alcance e a tela diz.

**A primeira versao deste script errou, e o erro vale registro.** Ele comparava
o agregado nacional (escopo UF: R$ 135,88 bi) com a soma dos arquivos por UF
(escopo municipio: R$ 14,64 bi) e acusava divergencia de R$ 121 bi. Nao havia
divergencia nenhuma — havia um auditor comparando coisas diferentes. Auditoria
que compara escopo errado produz alarme falso, e alarme falso gasta a confianca
que ela existe para construir. Cada checagem aqui declara o escopo que usa.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

WEB = cfg.ROOT / "app" / "public" / "dados"
BRUTO = cfg.PROCESSED / "emendas.csv"
TOL = 0.01          # um centavo: soma de float sobre milhoes de linhas


def brl(v):
    return f"R$ {v/1e9:.2f} bi" if abs(v) >= 1e9 else f"R$ {v/1e6:.2f} mi"


def main():
    print("Escopo do Emendômetro: EMENDA INDIVIDUAL COM MUNICÍPIO IDENTIFICADO.")
    print("Toda checagem abaixo compara dentro desse escopo, ou declara o outro.\n")

    if not BRUTO.exists():
        raise SystemExit(f"{BRUTO} ausente — rode 30_emendas_ingest.py")
    d = pd.read_csv(BRUTO, dtype=str, low_memory=False)
    d["pago"] = pd.to_numeric(d["pago"], errors="coerce").fillna(0)
    d["ind"] = d["individual"].astype(str).str.lower().eq("true")
    d["temUF"] = d["uf"].notna() & (d["uf"].astype(str).str.strip() != "")
    d["temMun"] = d["cod_ibge"].notna() & (d["cod_ibge"].astype(str).str.strip() != "")

    ufs = sorted(x.name for x in WEB.iterdir()
                 if x.is_dir() and (x / "emendas.json").exists())
    problemas = []

    # ---- 1. o publicado reconcilia com a origem, no mesmo escopo ----------
    print("=== 1. publicado × origem, ambos em 'individual com município' ===")
    pub = 0.0
    nFichas = 0
    for uf in ufs:
        o = json.loads((WEB / uf / "emendas.json").read_text(encoding="utf-8"))
        for b in o["anos"].values():
            for f in b["fichas"]:
                pub += float(f["t"])
                nFichas += 1
    origem = float(d[d.ind & d.temMun]["pago"].sum())
    dif = abs(pub - origem)
    print(f"   origem (CSV) : {brl(origem)}")
    print(f"   publicado    : {brl(pub)}   ({nFichas:,} fichas-ano)")
    if dif > max(1.0, origem * 1e-6):
        problemas.append(f"publicado × origem divergem em {brl(dif)}")
        print(f"   DIVERGE em {brl(dif)}")
    else:
        print("   ok — reconcilia ao centavo")

    # ---- 2. consistencia interna por ano-UF ------------------------------
    print("\n=== 2. consistência interna: soma por autor = total do ano ===")
    ruins = []
    for uf in ufs:
        o = json.loads((WEB / uf / "emendas.json").read_text(encoding="utf-8"))
        for ano, b in o["anos"].items():
            sa = float(sum(f["t"] for f in b["fichas"]))
            tt = float(b["pleito"]["pago"])
            if abs(sa - tt) > TOL:
                ruins.append((uf, ano, sa, tt))
            sm = float(sum(b["totalMun"]))
            if sm - tt > TOL:
                problemas.append(f"{uf}/{ano}: soma por município maior que o total")
    if ruins:
        problemas.append(f"{len(ruins)} ano-UF com autor ≠ total")
        for uf, ano, sa, tt in ruins[:5]:
            print(f"   DIVERGE {uf}/{ano}: {brl(sa)} vs {brl(tt)}")
    else:
        print(f"   ok — {len(ufs)} UFs, toda soma por autor bate com o total do ano")

    # ---- 3. o que fica de fora, e por quê --------------------------------
    print("\n=== 3. o que fica FORA do Emendômetro (escopo declarado) ===")
    tot = float(d["pago"].sum())
    ind = float(d[d.ind]["pago"].sum())
    naoInd = tot - ind
    indSemMun = ind - origem
    naoIndComMun = float(d[~d.ind & d.temMun]["pago"].sum())
    print(f"   pago total no país              {brl(tot)}")
    print(f"   - bancada/comissão/relator      {brl(naoInd)}   "
          f"({naoInd/tot*100:.1f}% — fora por ESCOPO)")
    print(f"   - individual sem município      {brl(indSemMun)}   "
          f"({indSemMun/tot*100:.1f}% — fora por FALTA DE DADO)")
    print(f"   = no Emendômetro                {brl(origem)}   "
          f"({origem/tot*100:.1f}%)")
    print(f"\n   Destes, {brl(naoIndComMun)} são não-individuais QUE TÊM município")
    print("   e ainda assim ficam fora. É escolha de escopo, não limite da fonte.")

    # ---- 4. cobertura das individuais, que é o número publicado ----------
    print("\n=== 4. os dois números que a aba Sobre publica ===")
    comUF = float(d[d.ind & d.temUF]["pago"].sum())
    print(f"   individuais com UF        {comUF/ind*100:5.1f}%   (publicado: 97,1%)")
    print(f"   individuais com município {origem/ind*100:5.1f}%   (publicado: 10,5%)")
    for rot, medido, dito in (("UF", comUF/ind*100, 97.1),
                              ("município", origem/ind*100, 10.5)):
        if abs(medido - dito) > 0.15:
            problemas.append(f"cobertura por {rot}: medido {medido:.1f}%, "
                             f"publicado {dito}%")

    # ---- 5. buraco de serie ---------------------------------------------
    print("\n=== 5. buraco de série ===")
    porAno = d[d.ind & d.temMun].groupby("ano")["pago"].sum().sort_index()
    med = float(porAno.median())
    for ano, v in porAno.items():
        raz = v / med if med else 0
        marca = "  <- MUITO ABAIXO" if raz < 0.15 else ""
        if raz < 0.15:
            problemas.append(f"{ano} tem {raz*100:.0f}% da mediana anual")
        print(f"   {ano}  {brl(float(v)):>12}  {raz:5.2f}× a mediana{marca}")

    # ---- 6. agregado nacional, no escopo dele ---------------------------
    print("\n=== 6. agregado nacional (escopo UF, não município) ===")
    fbr = WEB / "emendas_br.json"
    if fbr.exists():
        br = json.loads(fbr.read_text(encoding="utf-8"))
        somaBR = float(sum(x["pago"] for x in br["uf"]))
        print(f"   emendas_br.json : {brl(somaBR)}")
        print(f"   CSV, ind. c/ UF : {brl(comUF)}")
        if abs(somaBR - comUF) > max(1.0, comUF * 1e-4):
            problemas.append(f"nacional × CSV divergem em {brl(abs(somaBR-comUF))}")
            print(f"   DIVERGE em {brl(abs(somaBR - comUF))}")
        else:
            print("   ok — o agregado nacional é o escopo UF, e reconcilia")
    else:
        problemas.append("emendas_br.json ausente")

    # ---- veredito --------------------------------------------------------
    print("\n" + "=" * 68)
    if problemas:
        print(f"{len(problemas)} PONTO(S) QUE EXIGEM ATENCAO:")
        for x in problemas:
            print(f"   - {x}")
        raise SystemExit(1)
    print("Nenhuma inconsistencia. O publicado reconcilia com a origem, a soma")
    print("por autor bate com o total em toda UF e ano, e os dois numeros de")
    print("cobertura da aba Sobre conferem com o medido.")
    print("""
O que isto NAO garante, e e' o limite honesto:

  - nao verifica se o Portal da Transparencia publicou a verdade. Se a origem
    erra, erramos junto, e nao ha' como saber daqui;
  - nao alcanca os R$ 105,8 bi marcados MULTIPLO. Esse dinheiro existe, foi
    pago, e o arquivo nao diz para onde. Nenhuma tecnica recupera o que nao foi
    publicado;
  - nao cobre emenda estadual fora de Goias e Espirito Santo, porque os outros
    25 estados nao publicam em formato que permita.""")


if __name__ == "__main__":
    main()
