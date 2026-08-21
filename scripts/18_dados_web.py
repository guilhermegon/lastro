"""Fatia o payload nacional em arquivos por UF, para o front carregar sob demanda.

A pagina unica embutia 13,3 MB e carregava tudo antes de mostrar qualquer coisa.
Aqui o mesmo dado vira:

  indice.json      lista de UFs, agregado nacional e malha do Brasil  (~120 KB)
  uf/{SIGLA}.json  municipios, geometria e eleitos daquele estado     (~90-900 KB)

O front baixa o indice na abertura e so o estado que o usuario escolher. Em
Goias isso e' 13,3 MB -> ~0,5 MB na primeira tela. Em Roraima, menos ainda.

Roda depois de 16_payload_br.py, de quem reaproveita o JSON ja montado.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

DESTINO = cfg.ROOT / "app" / "public" / "dados"


def main():
    origem = cfg.DIST / "dados_br.json"
    if not origem.exists():
        raise SystemExit(f"rode 16_payload_br.py antes: {origem} nao existe")
    d = json.loads(origem.read_text(encoding="utf-8"))

    (DESTINO / "uf").mkdir(parents=True, exist_ok=True)

    indice = {
        "anos": d["anos"],
        "ufs": d["ufs"],
        "agregado": d["agregado"],
        "malhaUF": d["malhaUF"],
    }
    p = DESTINO / "indice.json"
    p.write_text(json.dumps(indice, separators=(",", ":"), ensure_ascii=False),
                 encoding="utf-8")
    print(f"indice.json: {p.stat().st_size/1024:.0f} KB "
          f"({len(indice['ufs'])} UFs, {len(indice['agregado'])} linhas de agregado)")

    total = 0
    for u in d["ufs"]:
        sg = u["s"]
        bloco = {
            "uf": sg,
            "nome": u["n"],
            "municipios": d["municipios"].get(sg, []),
            "geo": d["geo"].get(sg, []),
            "eleitos": d["eleitos"].get(sg, {}),
            "totais": d["totais"].get(sg, {}),
        }
        f = DESTINO / "uf" / f"{sg}.json"
        f.write_text(json.dumps(bloco, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
        kb = f.stat().st_size / 1024
        total += kb
        print(f"  {sg}: {kb:>7.0f} KB  ({len(bloco['municipios'])} municipios)")

    print(f"\ntotal por UF: {total/1024:.1f} MB somando todos")
    print(f"primeira tela (indice + maior UF): "
          f"{(p.stat().st_size/1024 + max((DESTINO / 'uf' / f'{u[chr(115)]}.json').stat().st_size/1024 for u in d['ufs']))/1024:.2f} MB")


if __name__ == "__main__":
    main()
