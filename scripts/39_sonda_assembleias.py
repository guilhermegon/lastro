"""Quais assembleias legislativas oferecem API ou dados abertos?

Levantamento proprio: nao existe catalogo publico disso. A sondagem de portais
do Executivo (`36_`) respondeu sobre emenda; esta responde sobre o Legislativo
estadual como um todo — quem publica, em que formato, e o que.

**O que a sonda faz.** Para cada UF, tenta um conjunto de caminhos que
concentram dado aberto em portais legislativos brasileiros:
`/dados-abertos`, `/api`, subdominios `dadosabertos.` e `transparencia.`, e o
padrao CKAN `/api/3/action/package_list`. Registra o codigo HTTP, o tipo de
conteudo e se a resposta parece API (JSON) ou pagina.

**O que ela NAO faz**, e precisa ficar dito: responder 200 nao significa ter
dado util. A ALEGO tem API documentada com dezesseis assuntos e **nenhum** e'
emenda parlamentar. A sonda mede a existencia da porta, nao o que ha atras dela.
Confirmar exige abrir, uma por uma — foi assim que Pernambuco e Bahia cairam.

Os dominios sao os oficiais de cada casa. Onde a assembleia usa `.gov.br` em vez
de `.leg.br`, os dois sao tentados.
"""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

SAIDA = cfg.PROCESSED / "assembleias.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# dominio oficial de cada casa; alguns respondem nos dois sufixos
CASAS = {
    "AC": ("ALEAC", ["al.ac.leg.br"]),
    "AL": ("ALE/AL", ["al.al.leg.br"]),
    "AM": ("ALE/AM", ["ale.am.leg.br", "ale.am.gov.br"]),
    "AP": ("ALAP", ["al.ap.leg.br"]),
    "BA": ("ALBA", ["al.ba.leg.br", "al.ba.gov.br"]),
    "CE": ("ALECE", ["al.ce.leg.br", "al.ce.gov.br"]),
    "DF": ("CLDF", ["cl.df.gov.br"]),
    "ES": ("ALES", ["al.es.gov.br"]),
    "GO": ("ALEGO", ["al.go.leg.br", "transparencia.al.go.leg.br"]),
    "MA": ("ALEMA", ["al.ma.leg.br"]),
    "MG": ("ALMG", ["almg.gov.br", "dadosabertos.almg.gov.br"]),
    "MS": ("ALEMS", ["al.ms.gov.br", "al.ms.leg.br"]),
    "MT": ("ALMT", ["al.mt.leg.br", "al.mt.gov.br"]),
    "PA": ("ALEPA", ["alepa.pa.leg.br", "alepa.pa.gov.br"]),
    "PB": ("ALPB", ["al.pb.leg.br"]),
    "PE": ("ALEPE", ["alepe.pe.leg.br", "alepe.pe.gov.br"]),
    "PI": ("ALEPI", ["al.pi.leg.br"]),
    "PR": ("ALEP", ["assembleia.pr.leg.br"]),
    "RJ": ("ALERJ", ["alerj.rj.leg.br", "alerj.rj.gov.br"]),
    "RN": ("ALRN", ["al.rn.leg.br"]),
    "RO": ("ALE/RO", ["al.ro.leg.br"]),
    "RR": ("ALE/RR", ["al.rr.leg.br"]),
    "RS": ("AL/RS", ["al.rs.leg.br", "al.rs.gov.br"]),
    "SC": ("ALESC", ["alesc.sc.gov.br", "alesc.sc.leg.br"]),
    "SE": ("ALESE", ["al.se.leg.br"]),
    "SP": ("ALESP", ["al.sp.leg.br", "al.sp.gov.br"]),
    "TO": ("ALETO", ["al.to.leg.br"]),
}

CAMINHOS = [
    ("/dados-abertos", "pagina"),
    ("/dadosabertos", "pagina"),
    ("/transparencia/dados-abertos", "pagina"),
    # a API da ALEGO mora em /api/transparencia, dois niveis abaixo — sondar
    # so' "/api" dava zero APIs num levantamento em que eu ja sabia de uma
    ("/api", "api"),
    ("/api/transparencia", "api"),
    ("/api/v1", "api"),
    ("/api/dados-abertos", "api"),
    ("/ws/dados_abertos", "api"),
    ("/api/3/action/package_list", "ckan"),
]
# prefixos aplicados AO DOMINIO DA CASA, nunca ao dominio do estado: cortar
# "ale.am.gov.br" para "am.gov.br" levava a sonda ao Executivo, e o
# levantamento e' sobre o Legislativo
SUBDOMINIOS = ["dadosabertos.", "transparencia.", "dados."]


def cabeca(url):
    """GET curto: codigo, content-type e um pedaco do corpo."""
    r = subprocess.run(
        ["curl.exe", "-sS", "-L", "--max-time", "25", "-o", "-",
         "-w", "\n@@@%{http_code}|%{content_type}", "-H", f"User-Agent: {UA}", url],
        capture_output=True)
    saida = r.stdout.decode("utf-8", errors="replace")
    m = re.search(r"@@@(\d{3})\|([^\n]*)$", saida)
    if not m:
        return 0, "", ""
    return int(m.group(1)), m.group(2), saida[: m.start()]


def sondar(item):
    uf, (sigla, dominios) = item
    achados = []
    for dom in dominios:
        for caminho, tipo in CAMINHOS:
            cod, ct, corpo = cabeca(f"https://{dom}{caminho}")
            if cod != 200 or not corpo.strip():
                continue
            ehjson = "json" in ct.lower() or corpo.lstrip()[:1] in "[{"
            achados.append({"url": f"https://{dom}{caminho}",
                            "tipo": "API" if ehjson else "página",
                            "bytes": len(corpo)})
        # prefixo no dominio da propria casa, e depois os caminhos de API
        # dentro do subdominio de transparencia — que e' onde a ALEGO guarda
        for sub in SUBDOMINIOS:
            if dom.startswith(sub):
                continue
            alvo = f"{sub}{dom}"
            for caminho in ("", "/dados-abertos", "/api/transparencia", "/api"):
                cod, ct, corpo = cabeca(f"https://{alvo}{caminho}")
                if cod != 200 or not corpo.strip():
                    continue
                ehjson = "json" in ct.lower() or corpo.lstrip()[:1] in "[{"
                achados.append({"url": f"https://{alvo}{caminho}",
                                "tipo": "API" if ehjson else "página",
                                "bytes": len(corpo)})
    # remove duplicata por url
    vistos, unicos = set(), []
    for a in achados:
        if a["url"] in vistos:
            continue
        vistos.add(a["url"]); unicos.append(a)
    return uf, {"sigla": sigla, "dominios": dominios, "achados": unicos}


def main():
    print(f"sondando {len(CASAS)} assembleias legislativas...\n", flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        fora = dict(ex.map(sondar, CASAS.items()))

    SAIDA.write_text(json.dumps(fora, indent=1, ensure_ascii=False),
                     encoding="utf-8")

    com_api = [u for u, r in fora.items()
               if any(a["tipo"] == "API" for a in r["achados"])]
    com_pag = [u for u, r in fora.items()
               if r["achados"] and u not in com_api]
    sem = [u for u, r in fora.items() if not r["achados"]]

    print(f"{'UF':<4}{'casa':<9}{'achados':>8}  o quê")
    for uf in sorted(fora):
        r = fora[uf]
        marca = "API" if uf in com_api else ("página" if r["achados"] else "—")
        amostra = ", ".join(a["url"].split("//")[1][:38] for a in r["achados"][:2])
        print(f"{uf:<4}{r['sigla']:<9}{len(r['achados']):>8}  {marca:<7} {amostra}")

    print(f"\n{len(com_api)} com resposta em JSON (API)")
    print(f"{len(com_pag)} com página de dados abertos, sem JSON no caminho testado")
    print(f"{len(sem)} sem nada nos caminhos testados")
    print(f"\ncom API: {', '.join(sorted(com_api)) or 'nenhuma'}")
    print("\nRessalva: responder 200 não é ter dado útil. A ALEGO tem API com")
    print("dezesseis assuntos e nenhum é emenda parlamentar. Isto mede a porta,")
    print("não o que há atrás dela.")
    print(f"\n{SAIDA.name} gravado.")


if __name__ == "__main__":
    main()
