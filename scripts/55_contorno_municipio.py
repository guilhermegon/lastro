"""Poe o contorno do municipio no arquivo de urnas de cada cidade.

O mapa de urnas nasceu sem chao: uma nuvem de circulos enquadrada na propria
nuvem. Funcionava como grafico e nao como mapa - o leitor via onde os pontos
estao uns em relacao aos outros, e nao onde estao no municipio. Sem fronteira,
"as urnas estao todas de um lado" e "as urnas estao espalhadas" tem exatamente
a mesma aparencia, porque o enquadramento se ajusta ao que existe.

Com o contorno, o enquadramento passa a ser o municipio, e a distribuicao vira
afirmacao: numa cidade rural os pontos se juntam num canto e o resto do
territorio fica vazio - o que e' o fato, nao um artefato de escala.

**Antes de desenhar, a pergunta que decidia se isto podia existir: as urnas
caem dentro do proprio municipio?** Um contorno errado e' pior que contorno
nenhum, porque o leitor acredita na fronteira que voce desenhou. Medido nos 246
municipios de Goias: **2.459 locais com coordenada, 4 fora - 0,16%**. E os
quatro estao a **60 a 90 metros** da fronteira (Divinopolis de Goias 70 m,
Itapaci 60 m, Trindade 90 m, Luziania 80 m), o que a esse zoom da' um pixel.
Nao e' coordenada errada do TSE, e' precisao de limite entre duas bases
diferentes. Ficam desenhados onde o TSE disse que estao.

**Por que a malha bruta, sem simplificar.** O `04_geo.py` simplifica a 0,004
para o coropletico estadual, onde 246 municipios dividem a mesma tela e 62
vertices bastam. Aqui um municipio ocupa a tela inteira. Medi o custo de
simplificar a malha bruta: de 32.384 vertices para 32.150 a 0,001 grau - 0,7%.
A malha "intermediaria" do IBGE ja' vem simplificada na origem, e todo vertice
dela e' significativo. Nao ha' o que economizar, entao vai como esta': mediana
de 109 vertices por cidade, cerca de 2 KB no arquivo que a tela ja' baixa.

**Escreve no arquivo de urnas, e nao num arquivo proprio.** O contorno so' e'
desenhado junto com os pontos; um arquivo a parte custaria uma requisicao para
entregar 2 KB que a outra requisicao ja' poderia ter trazido.

Rode depois do `54_urnas_uf.py`, que e' quem cria os arquivos. Reexecutar o
`54_` apaga o contorno - este script e' idempotente e barato, entao a ordem e'
sempre `54_` e depois `55_`.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

MALHA = cfg.RAW / "malha_go_bruta.geojson"


def aneis_externos(geom):
    """So os aneis externos. Buracos (ilhas internas) nao existem em municipio
    brasileiro continental, e desenhar anel interno como se fosse externo
    inventaria uma fronteira - melhor ignorar do que arriscar."""
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        return [c[0]]
    if t == "MultiPolygon":
        return [p[0] for p in c]
    raise ValueError(f"geometria inesperada: {t}")


def compacto(anel):
    """5 casas decimais = ~1 metro. Mais que isso e' ruido no arquivo."""
    return [[round(x, 5), round(y, 5)] for x, y in anel]


def main():
    if not MALHA.exists():
        raise SystemExit(f"malha bruta ausente: {MALHA}\n"
                         "Rode 04_geo.py, que e' quem baixa do IBGE.")

    bruta = json.loads(MALHA.read_text(encoding="utf-8"))
    porcod = {}
    for f in bruta["features"]:
        cod = str(f["properties"].get("codarea") or f["properties"].get("id"))
        porcod[cod] = aneis_externos(f["geometry"])
    print(f"malha: {len(porcod)} municipios")

    destino = cfg.PROCESSED / "web" / cfg.UF / "urnas"
    if not destino.is_dir():
        raise SystemExit(f"sem arquivos de urna em {destino} - rode 54_ antes")

    escritos = semmalha = 0
    fracoes = []
    for arq in sorted(destino.glob("*.json")):
        if not arq.stem.isdigit():
            continue          # indice.json
        d = json.loads(arq.read_text(encoding="utf-8"))
        cod = str(d.get("cod") or arq.stem)
        aneis = porcod.get(cod)
        if aneis is None:
            print(f"   SEM MALHA para {cod} ({d.get('cidade')})")
            semmalha += 1
            continue

        d["geo"] = [compacto(a) for a in aneis]
        arq.write_text(json.dumps(d, separators=(",", ":"), ensure_ascii=False),
                       encoding="utf-8")
        escritos += 1

        # quanto da caixa do municipio os pontos ocupam - e' o numero que diz
        # se o contorno vai deixar o mapa vazio demais em cidade rural
        pts = [(l["lon"], l["lat"]) for l in d["locais"]
               if l.get("lat") is not None and l.get("lon") is not None]
        if len(pts) >= 2:
            todos = [p for a in aneis for p in a]
            mx = max(p[0] for p in todos) - min(p[0] for p in todos)
            my = max(p[1] for p in todos) - min(p[1] for p in todos)
            px = max(p[0] for p in pts) - min(p[0] for p in pts)
            py = max(p[1] for p in pts) - min(p[1] for p in pts)
            if mx > 0 and my > 0:
                fracoes.append(((px / mx) * (py / my), d.get("cidade")))

    print(f"contorno gravado em {escritos} cidades"
          + (f", {semmalha} sem malha" if semmalha else ""))

    if fracoes:
        fracoes.sort()
        import statistics
        med = statistics.median(f for f, _ in fracoes)
        print(f"\narea da caixa dos pontos sobre a caixa do municipio: "
              f"mediana {med*100:.1f}%")
        print("as cinco em que os pontos mais se concentram num canto:")
        for f, nome in fracoes[:5]:
            print(f"   {nome:<28} {f*100:5.2f}%")
        print("\nIsto NAO e' defeito do mapa: e' o fato de a cidade votar toda")
        print("na sede. Sem contorno, esse fato nao aparecia.")


if __name__ == "__main__":
    main()
