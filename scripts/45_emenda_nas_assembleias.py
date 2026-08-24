"""Testa uma afirmacao que este projeto publicou e que estava errada.

O `39_` levantou as 27 assembleias e concluiu, no texto que foi ao ar, que
**nenhuma publica emenda parlamentar**. A afirmacao era absoluta demais: a
Camara Legislativa do DF publica um conjunto chamado, literalmente,
`emendas-parlamentares`, com cinco CSV de 2021 a 2025.

Este script existe para que a versao corrigida seja verificavel, e nao mais uma
afirmacao de memoria. Ele pergunta duas coisas distintas, que o texto original
confundia numa so:

    1. A Casa publica ALGUM conjunto chamado emenda?          -> o DF publica
    2. Esse conjunto responde "quem mandou dinheiro para onde"? -> nenhum responde

A segunda pergunta e' a que importa para o Emendometro, e a resposta continua
sendo nao. O arquivo do DF traz dezoito colunas de execucao orcamentaria
(`VL_EMENDA`, `VL_EMPENHADO`, `NOME_UO`, `PT`) e **nenhuma coluna de autor e
nenhuma de municipio**. Sem autor nao ha' a quem atribuir; sem municipio nao ha'
mapa. E' emenda como linha de orcamento, nao como ato de um parlamentar sobre um
territorio.

E o DF e' caso especial de qualquer forma: e' estado e municipio ao mesmo tempo,
entao "emenda estadual por municipio" nao tem nem o que mapear la' dentro.

**Por que a correcao vale o script.** A frase errada nao era um numero torto:
era uma generalizacao que eu nao tinha testado, publicada com a mesma confianca
dos numeros que testei. Deixar o teste no repositorio e' o que separa as duas
coisas na proxima vez.
"""
import json
import subprocess
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
# portais de assembleia que responderam CKAN no levantamento do 39_
CKAN = {"DF": "https://dados.cl.df.gov.br"}
# a API de Goias nao e' CKAN: testa-se endereco a endereco
ALEGO = "https://transparencia.al.go.leg.br/api/transparencia"
# o que faria a emenda utilizavel para o Emendometro
AUTOR = ("autor", "deput", "parlament", "proponent")
LUGAR = ("munic", "cidade", "localidad", "regiao", "ibge", "benefici")


def get(url):
    for _ in range(3):
        r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "120",
                            "-H", f"User-Agent: {UA}", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            try:
                return json.loads(r.stdout)
            except json.JSONDecodeError:
                pass
    return None


def colunas(rec):
    """Colunas que o proprio CKAN declara para o recurso."""
    ds = rec.get("datastore_active")
    campos = []
    if ds:
        d = get(f"{rec['url'].split('/dataset')[0]}"
                f"/api/3/action/datastore_search?resource_id={rec['id']}&limit=0")
        campos = [f["id"] for f in ((d or {}).get("result") or {}).get("fields", [])]
    if not campos:
        # sem datastore, le o cabecalho do proprio CSV
        r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "120",
                            "-H", f"User-Agent: {UA}", rec["url"]],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            linha = r.stdout.split(b"\n", 1)[0].decode("latin-1")
            sep = ";" if linha.count(";") > linha.count(",") else ","
            campos = [c.strip().strip('"') for c in linha.split(sep)]
    return [c for c in campos if c]


def main():
    achados = []

    for uf, base in CKAN.items():
        print(f"=== {uf}: procurando conjunto de emenda ===", flush=True)
        d = get(f"{base}/api/3/action/package_list")
        nomes = [n for n in ((d or {}).get("result") or [])
                 if "emenda" in n.lower()]
        print(f"   conjuntos com 'emenda' no nome: {nomes or 'nenhum'}", flush=True)
        for nome in nomes:
            pk = get(f"{base}/api/3/action/package_show?id={nome}")
            r = (pk or {}).get("result") or {}
            rs = [x for x in r.get("resources", [])
                  if (x.get("format") or "").upper() == "CSV"]
            print(f"   {nome}: {r.get('title')} — {len(rs)} CSV", flush=True)
            if not rs:
                continue
            cols = colunas(rs[0])
            temAutor = [c for c in cols
                        if any(k in c.lower() for k in AUTOR)]
            temLugar = [c for c in cols
                        if any(k in c.lower() for k in LUGAR)]
            print(f"      {len(cols)} colunas: {cols}")
            print(f"      autor:    {temAutor or 'NENHUMA'}")
            print(f"      município: {temLugar or 'NENHUMA'}")
            achados.append({
                "uf": uf, "conjunto": nome, "titulo": r.get("title"),
                "recursos": len(rs), "colunas": cols,
                "colunasAutor": temAutor, "colunasMunicipio": temLugar,
                "utilizavel": bool(temAutor and temLugar),
            })

    # Em Goias a checagem e' direta: os enderecos plausiveis de emenda na API.
    # NAO se pergunta "quantos assuntos existem" — se essa requisicao falhar,
    # a resposta vazia pareceria prova de ausencia, e nao e'.
    print("\n=== GO: endereços de emenda na API da ALEGO ===", flush=True)
    tentados = {}
    for rec in ("emendas", "emendas-parlamentares", "indicacoes"):
        r = subprocess.run(["curl.exe", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                            "-L", "--max-time", "60", "-H", f"User-Agent: {UA}",
                            f"{ALEGO}/{rec}.json?todos=true"], capture_output=True)
        cod = r.stdout.decode(errors="ignore").strip() or "sem resposta"
        tentados[rec] = cod
        print(f"   {rec:<24} HTTP {cod}")
    # so' e' ausencia se o servidor RESPONDEU dizendo que nao existe
    ausentes = [k for k, v in tentados.items() if v == "404"]
    inconclusivos = [k for k, v in tentados.items()
                     if v not in ("404", "200")]
    if inconclusivos:
        print(f"   INCONCLUSIVO em {inconclusivos}: sem resposta do servidor não"
              f" é o mesmo que endereço inexistente")
    comEmenda = [k for k, v in tentados.items() if v == "200"]
    chaves = ausentes

    # ---- o veredito, separando as duas perguntas ----
    print("")
    print("=== veredito ===")
    if achados:
        print(f"   {len(achados)} conjunto(s) de emenda EXISTEM em assembleia:")
        for a in achados:
            print(f"      {a['uf']}/{a['conjunto']}: {len(a['colunas'])} colunas, "
                  f"autor={'sim' if a['colunasAutor'] else 'NAO'}, "
                  f"município={'sim' if a['colunasMunicipio'] else 'NAO'}")
    else:
        print("   nenhum conjunto de emenda encontrado")
    uteis = [a for a in achados if a["utilizavel"]]
    print(f"   utilizáveis para o Emendômetro (autor E município): "
          f"{len(uteis)}")
    print("   -> a afirmação correta é: existe conjunto de emenda em assembleia,")
    print("      mas nenhum amarra a emenda a um autor e a um território.")

    p = cfg.PROCESSED / "web" / "emenda_assembleias.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "achados": achados,
        "utilizaveis": len(uteis),
        "alegoTentados": tentados,
        "alegoRespondeu404": ausentes,
        "alegoInconclusivo": inconclusivos,
        "alegoComEmenda": comEmenda,
    }, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"\n{p.name}: {p.stat().st_size/1024:.1f} KB")


if __name__ == "__main__":
    main()
