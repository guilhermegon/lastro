"""Verba indenizatoria da ALMG (Minas Gerais): o grao mais completo dos tres.

A mesma verba ja levantada em Goias (`40_`) e no DF (`41_`), agora em Minas. A
comparacao entre as tres casas e' o achado, porque cada uma publica um pedaco
diferente do mesmo objeto:

    Goias   total mensal por deputado, com apresentado e indenizado
            -> da a GLOSA, nao da a categoria, nao da o fornecedor
    DF      nota a nota, com fornecedor e categoria
            -> da o DESTINO, nao da a glosa, e publica so parte dos deputados
    Minas   deputado x mes x categoria, com detalhe nota a nota dentro
            -> da os TRES: glosa (valorDespesa vs valorReembolsado),
               categoria (descTipoDespesa) e fornecedor (nomeEmitente/cpfCnpj)

**Minas e' a unica das tres que amarra as tres dimensoes ao mesmo tempo**, e por
isso e' a unica onde da' para perguntar "qual fornecedor atende quantos
deputados" — pergunta que o DF nao responde por nao ter autor, e que Goias nao
responde por nao ter fornecedor.

**A janela e' POR MANDATO, e eu li errado da primeira vez.** Amostrei um
deputado, vi 18 meses, e escrevi que a ALMG mantinha uma janela movel de 18
meses por politica de publicacao. Estava errado nas duas metades. Medindo os 77:
a mediana e' de **88 meses** por deputado, o maximo e' 91, e o minimo 18 — que
era justamente o deputado que amostrei.

O arquivo comeca em **2019-02**, inicio da legislatura 2019-2022, e a janela de
cada um acompanha o tempo dele de mandato: 48 deputados tem serie desde 2019, 22
desde fevereiro de 2023 (inicio da legislatura seguinte) e o resto entrou no
meio, por substituicao. Nao ha' janela movel nenhuma — ha' um arquivo que
comeca numa legislatura e vai ate' o ultimo mes fechado.

**A consequencia e' que a serie temporal existe**, e a primeira versao deste
script se recusava a publica-la com base numa limitacao que eu tinha inventado.
O erro e' o de sempre com cara nova: generalizar de uma amostra de um.

**O bruto fica em disco.** A varredura leva 44 minutos ao ritmo que a ALMG
permite; guardar as 141 mil notas em parquet faz qualquer reanalise custar
segundos em vez de outra varredura.

**O limite de requisicao e' publicado e obedecido aqui.** A ALMG declara no
proprio site: no maximo duas requisicoes simultaneas e um segundo entre o fim de
uma e o inicio da proxima, sob pena de bloqueio sem aviso. Sao dois workers com
pausa de um segundo por requisicao. Sao 5.408 requisicoes e a varredura leva
44 minutos; apressar seria trocar o acesso de todo mundo por meia hora minha.

**Falha de rede nao e' ausencia de dado.** Tres tentativas por requisicao — a
primeira varredura da ALEGO devolveu 37 de 96 meses por ler timeout como
"nao existe", e dois anos inteiros sumiram silenciosamente.
"""
import json
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

B = "https://dadosabertos.almg.gov.br/api/v2"
WEB = cfg.PROCESSED / "web" / "MG"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
# a casa publica o limite; dois workers com 1s por requisicao fica dentro dele
WORKERS = 2
PAUSA = 1.0


def get(url):
    for tentativa in range(3):
        r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "90",
                            "-H", f"User-Agent: {UA}", url],
                           capture_output=True)
        time.sleep(PAUSA)
        if r.returncode == 0 and r.stdout:
            try:
                return json.loads(r.stdout)
            except json.JSONDecodeError:
                pass
        time.sleep(PAUSA * (tentativa + 1))
    return None


def data(x):
    """O JSON da ALMG embrulha data em {'@class': 'sql-timestamp', '$': ...}."""
    if isinstance(x, dict):
        return x.get("$")
    return x


def deputados():
    d = get(f"{B}/deputados/em_exercicio?formato=json")
    return (d or {}).get("list") or []


def datas(idd):
    d = get(f"{B}/prestacao_contas/verbas_indenizatorias/deputados/{idd}"
            f"/datas?formato=json")
    saida = []
    for r in (d or {}).get("listaFechamentoVerba") or []:
        s = data(r.get("dataReferencia"))
        if s:
            saida.append((int(s[:4]), int(s[5:7])))
    return sorted(set(saida))


def mes(idd, ano, m):
    d = get(f"{B}/prestacao_contas/verbas_indenizatorias/deputados/{idd}"
            f"/{ano}/{m}?formato=json")
    linhas = []
    for g in (d or {}).get("list") or []:
        for det in g.get("listaDetalheVerba") or []:
            linhas.append({
                "idDeputado": idd, "ano": ano, "mes": m,
                "categoria": (det.get("descTipoDespesa")
                              or g.get("descTipoDespesa") or "").strip(),
                "cod": det.get("codTipoDespesa") or g.get("codTipoDespesa"),
                "emitente": (det.get("nomeEmitente") or "").strip(),
                "cnpj": str(det.get("cpfCnpj") or "").strip(),
                "despesa": det.get("valorDespesa"),
                "reembolsado": det.get("valorReembolsado"),
                "emissao": data(det.get("dataEmissao")),
            })
    return linhas


def main():
    print("deputados em exercício...", flush=True)
    deps = deputados()
    if not deps:
        print("  a ALMG não respondeu; abortando sem gravar")
        return
    nomes = {int(d["id"]): d.get("nome", "") for d in deps}
    partidos = {int(d["id"]): d.get("partido", "") for d in deps}
    print(f"  {len(deps)}", flush=True)

    print("janela publicada por deputado...", flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        janelas = list(ex.map(datas, list(nomes)))
    tarefas = [(i, a, m) for i, j in zip(nomes, janelas) for a, m in j]
    if not tarefas:
        print("  nenhuma data devolvida; abortando sem gravar")
        return
    todos = sorted({(a, m) for _, a, m in tarefas})
    print(f"  {len(tarefas)} meses-deputado | janela {todos[0][0]}-{todos[0][1]:02d} "
          f"a {todos[-1][0]}-{todos[-1][1]:02d}", flush=True)

    print(f"itens ({len(tarefas)} requisições, ~{len(tarefas)*PAUSA/WORKERS/60:.0f} min)...",
          flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        blocos = list(ex.map(lambda t: mes(*t), tarefas))
    linhas = [x for b in blocos for x in b]
    if not linhas:
        print("  nenhum item; abortando sem gravar")
        return
    d = pd.DataFrame(linhas)
    for c in ("despesa", "reembolsado"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    print(f"  {len(d):,} notas", flush=True)

    # 44 minutos de varredura nao se joga fora: o bruto em disco faz qualquer
    # reanalise custar segundos
    cru = cfg.INTERIM / "almg_verbas_notas.parquet"
    cru.parent.mkdir(parents=True, exist_ok=True)
    try:
        d.to_parquet(cru, index=False)
        print(f"  bruto em {cru.name} ({cru.stat().st_size/1e6:.1f} MB)", flush=True)
    except Exception as e:
        cru = cru.with_suffix(".csv.gz")
        d.to_csv(cru, index=False, compression="gzip")
        print(f"  bruto em {cru.name} (parquet indisponível: {e})", flush=True)

    # ---- glosa: pedido menos pago, a mesma medida que Goias permite ----
    ped = float(d["despesa"].sum())
    pago = float(d["reembolsado"].sum())
    glosa = ped - pago

    # ---- categoria: a dimensao que Goias nao tem ----
    cat = (d.groupby("categoria")
           .agg(v=("reembolsado", "sum"), q=("reembolsado", "size"))
           .sort_values("v", ascending=False))

    # ---- fornecedor: so Minas amarra fornecedor a deputado ----
    forn = (d[d["cnpj"] != ""].groupby("cnpj")
            .agg(v=("reembolsado", "sum"),
                 deputados=("idDeputado", "nunique"),
                 nome=("emitente", "first"))
            .sort_values("deputados", ascending=False))

    # ---- por deputado: mediana mensal, nao total ----
    # o total por deputado depende de quantos meses dele foram publicados, e a
    # janela nao e' igual para todos (quem entrou depois tem menos meses)
    pormes = d.groupby(["idDeputado", "ano", "mes"])["reembolsado"].sum()
    pordep = pormes.groupby("idDeputado").agg(["median", "size"])
    pordep.columns = ["mediana", "meses"]

    obj = {
        "fonte": "API de Dados Abertos da ALMG",
        "janela": [f"{todos[0][0]}-{todos[0][1]:02d}",
                   f"{todos[-1][0]}-{todos[-1][1]:02d}"],
        "total": {
            "notas": int(len(d)),
            "deputados": int(d["idDeputado"].nunique()),
            "mesesDeputado": int(len(tarefas)),
            "pedido": round(ped, 2),
            "pago": round(pago, 2),
            "glosa": round(glosa, 2),
            "pctGlosa": round(glosa / ped * 100, 2) if ped else 0,
            "comGlosa": int((d["reembolsado"] < d["despesa"] - 0.005).sum()),
        },
        # a serie que a primeira versao se recusou a publicar por uma limitacao
        # que nao existia; anos incompletos ficam marcados, nao escondidos
        "serie": [{"ano": int(a),
                   "pago": round(float(g["reembolsado"].sum()), 2),
                   "pedido": round(float(g["despesa"].sum()), 2),
                   "deputados": int(g["idDeputado"].nunique()),
                   "meses": int(g["mes"].nunique())}
                  for a, g in d.groupby("ano")],
        "categorias": [{"n": str(i)[:70], "v": round(float(r.v), 2),
                        "q": int(r.q)} for i, r in cat.head(14).iterrows()],
        "fornecedores": {
            "distintos": int(len(forn)),
            "compartilhados": int((forn["deputados"] > 1).sum()),
            "top": [{"n": str(r.nome)[:46], "dep": int(r.deputados),
                     "v": round(float(r.v), 2)}
                    for _, r in forn.head(10).iterrows()],
        },
        "deputados": {
            "medianaMensal": round(float(pordep["mediana"].median()), 2),
            "minMensal": round(float(pordep["mediana"].min()), 2),
            "maxMensal": round(float(pordep["mediana"].max()), 2),
            "top": [{"n": nomes.get(int(i), "")[:34],
                     "p": partidos.get(int(i), ""),
                     "v": round(float(r.mediana), 2), "m": int(r.meses)}
                    for i, r in pordep.sort_values("mediana", ascending=False)
                    .head(10).iterrows()],
        },
    }

    print("")
    print("=== ALMG: verba indenizatoria ===")
    print("   janela %s a %s (movel: politica de publicacao, nao inicio da verba)"
          % tuple(obj["janela"]))
    print("   %d notas | %d deputados | %d meses-deputado" % (
        len(d), d["idDeputado"].nunique(), len(tarefas)))
    print("   pedido R$ %.2f mi | pago R$ %.2f mi | glosa R$ %.2f mi (%.2f%%)" % (
        ped/1e6, pago/1e6, glosa/1e6, obj["total"]["pctGlosa"]))
    print("")
    print("=== por ano (meses < 12 = ano incompleto) ===")
    for x in obj["serie"]:
        marca = "" if x["meses"] == 12 else "   <- %d meses" % x["meses"]
        print("   %d  pago R$ %6.2f mi | %2d deputados%s" % (
            x["ano"], x["pago"]/1e6, x["deputados"], marca))
    print("")
    print("=== no que o dinheiro vai ===")
    for c in obj["categorias"][:8]:
        print("   %-58s R$ %7.2f mi  %5.1f%%" % (
            c["n"][:58], c["v"]/1e6, c["v"]/pago*100 if pago else 0))
    print("")
    print("=== fornecedores ===")
    print("   %d CNPJ distintos | %d atendem mais de um deputado" % (
        obj["fornecedores"]["distintos"], obj["fornecedores"]["compartilhados"]))
    for f in obj["fornecedores"]["top"][:6]:
        print("   %-46s %2d deputados  R$ %.2f mi" % (f["n"], f["dep"], f["v"]/1e6))
    print("")
    print("=== por deputado (mediana mensal) ===")
    print("   mediana das medianas R$ %.2f | de R$ %.2f a R$ %.2f" % (
        obj["deputados"]["medianaMensal"], obj["deputados"]["minMensal"],
        obj["deputados"]["maxMensal"]))

    WEB.mkdir(parents=True, exist_ok=True)
    p = WEB / "almg_verbas.json"
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")
    print(f"\n{p.name}: {p.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
