"""Quais estados publicam emendas de deputado estadual em dado aberto?

Existe para tornar decidivel o ultimo item do Marco 9. A pergunta "vale ir para
os outros 25?" nao tem resposta sem saber quantos deles sequer publicam — e
isso e' medicao, nao juizo.

**Como sonda, e por que assim.** A maioria dos portais estaduais de dados
abertos roda CKAN, que expoe `/api/3/action/package_search`. Uma consulta por
"emenda" em cada portal candidato responde de uma vez se ha conjunto, quantos, e
em que formato. Onde nao ha CKAN, a sonda registra "sem API" — que e' uma
resposta tambem: significa raspagem, e raspagem custa outra ordem de grandeza.

**O que a sonda NAO responde**, e precisa ficar claro para nao virar promessa:
achar um conjunto chamado "emendas parlamentares" nao garante que ele traga
autor e municipio. Em Goias o conjunto certo estava la' e eu mesmo o descartei
olhando o nome do orgao. Confirmar exige abrir o arquivo, um por um. A sonda
mede o piso do trabalho, nao o teto.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
SAIDA = cfg.PROCESSED / "portais_estaduais.json"

# candidatos por UF, do padrao mais comum para o menos
PORTAIS = {
    "AC": ["dados.ac.gov.br"], "AL": ["dados.al.gov.br"],
    "AM": ["dadosabertos.am.gov.br"], "AP": ["dados.ap.gov.br"],
    "BA": ["dados.ba.gov.br"], "CE": ["dados.ce.gov.br"],
    "DF": ["dados.df.gov.br"], "ES": ["dados.es.gov.br"],
    "GO": ["dadosabertos.go.gov.br"], "MA": ["dados.ma.gov.br"],
    "MG": ["dados.mg.gov.br"], "MS": ["dados.ms.gov.br"],
    "MT": ["dados.mt.gov.br"], "PA": ["dados.pa.gov.br"],
    "PB": ["dados.pb.gov.br"], "PE": ["dados.pe.gov.br"],
    "PI": ["dados.pi.gov.br"], "PR": ["dadosabertos.pr.gov.br",
                                      "www.dadosabertos.pr.gov.br"],
    "RJ": ["dados.rj.gov.br"], "RN": ["dados.rn.gov.br"],
    "RO": ["dados.ro.gov.br"], "RR": ["dados.rr.gov.br"],
    "RS": ["dados.rs.gov.br"], "SC": ["dados.sc.gov.br"],
    "SE": ["dados.se.gov.br"], "SP": ["dados.sp.gov.br",
                                      "www.dados.sp.gov.br"],
    "TO": ["dados.to.gov.br"],
}


def buscar(host):
    """Consulta CKAN. Devolve (situacao, conjuntos) — nunca levanta."""
    url = (f"https://{host}/api/3/action/package_search"
           f"?q=emenda%20parlamentar&rows=8")
    r = subprocess.run(
        ["curl.exe", "-sS", "-L", "--max-time", "45", "-H", f"User-Agent: {UA}", url],
        capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return "não respondeu", []
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return "sem API CKAN", []
    if not d.get("success"):
        return "API recusou", []
    res = d.get("result", {})
    achados = []
    for p in res.get("results", []):
        fmts = sorted({(x.get("format") or "").upper()
                       for x in p.get("resources", []) if x.get("format")})
        achados.append({"titulo": (p.get("title") or "")[:70],
                        "orgao": ((p.get("organization") or {}).get("title") or "")[:40],
                        "formatos": fmts,
                        "tabular": any(f in ("CSV", "XLSX", "XLS", "ZIP", "JSON")
                                       for f in fmts)})
    return "ok", achados


def sondar(item):
    uf, hosts = item
    for h in hosts:
        sit, achados = buscar(h)
        if sit == "ok":
            return uf, {"host": h, "situacao": sit, "conjuntos": achados}
    return uf, {"host": hosts[0], "situacao": sit, "conjuntos": []}


def main():
    print(f"sondando {len(PORTAIS)} portais estaduais...\n", flush=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        fora = dict(ex.map(sondar, PORTAIS.items()))

    SAIDA.write_text(json.dumps(fora, indent=1, ensure_ascii=False),
                     encoding="utf-8")

    com_api = [u for u, r in fora.items() if r["situacao"] == "ok"]
    com_conj = [u for u, r in fora.items() if r["conjuntos"]]
    com_tab = [u for u, r in fora.items()
               if any(c["tabular"] for c in r["conjuntos"])]

    print(f"{'UF':<4}{'portal':<28}{'situação':<16}{'conjuntos':>10}  formatos")
    for uf in sorted(fora):
        r = fora[uf]
        fmts = sorted({f for c in r["conjuntos"] for f in c["formatos"]})
        print(f"{uf:<4}{r['host'][:27]:<28}{r['situacao']:<16}"
              f"{len(r['conjuntos']):>10}  {','.join(fmts[:5])}")

    print(f"\n{len(com_api)} de {len(PORTAIS)} portais respondem CKAN")
    print(f"{len(com_conj)} têm algum conjunto com 'emenda parlamentar'")
    print(f"{len(com_tab)} têm em formato tabular (CSV/XLSX/ZIP/JSON)")
    print(f"\ncom dado tabular: {', '.join(sorted(com_tab)) or 'nenhum'}")
    print("\nRessalva: achar o conjunto não garante autor e município dentro.")
    print("Em Goiás o conjunto certo estava lá e eu o descartei pelo nome do")
    print("órgão. Confirmar exige abrir arquivo por arquivo — isto mede o piso.")
    print(f"\n{SAIDA.name} gravado.")


if __name__ == "__main__":
    main()
