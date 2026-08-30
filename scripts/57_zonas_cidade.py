"""A zona eleitoral DENTRO da cidade, derivada dos locais de votacao.

O `56_zonas_uf.py` desenha a zona no estado, onde ela e' uniao de municipios
inteiros e a fronteira e' exata. Dentro de uma cidade que contem varias zonas
— Goiania com 9, Anapolis e Aparecida com 3, Rio Verde com 2 — nao existe malha
publicada, e este projeto vinha dizendo que por isso nao havia mapa.

**Eu media errado, e o usuario trouxe a prova.** Um infografico do TRE/GO mostra
as 9 zonas de Goiania como manchas contiguas e limpas. Minha conclusao anterior
— "as zonas se interpenetram" — vinha de SOBREPOSICAO DE CAIXAS delimitadoras,
que nao prova interpenetracao nenhuma: duas regioes compactas e vizinhas tem
caixas cruzadas quase sempre, porque a caixa de uma regiao em L cobre area que
nao e' dela.

A medida certa e' de vizinhanca, e ela diz o contrario:

    cidade                 locais  zonas   vizinho mais proximo   bairros de
                                           na mesma zona          uma zona so
    Goiania                   349      9            91,7%          176/176
    Anapolis                  118      3            92,4%           74/77
    Aparecida de Goiania      106      3            92,5%           81/82
    Rio Verde                  70      2            87,1%           41/46

**Em Goiania, 100% dos bairros estao inteiramente numa zona so'** — que e'
exatamente o que o infografico do TRE afirma ao listar bairros por zona. A zona
ocupa mancha continua, e mancha continua tem fronteira desenhavel.

**O QUE ISTO E', E O QUE NAO E'.** A fronteira aqui e' a particao por local de
votacao mais proximo (Voronoi), dissolvida por zona: cada ponto do territorio
pertence a zona da urna mais perto dele. **Nao e' o limite oficial do TRE.** Ela
coincide com o oficial no miolo de cada zona e diverge junto da divisa, onde o
limite verdadeiro segue rua e bairro. A tela diz isso.

Alternativas descartadas: decalcar a imagem do TRE nao e' reproduzivel por
script, e a regra do projeto e' que todo numero e todo desenho saiam de codigo;
usar malha de bairro exigiria uma camada que o IBGE nao publica em API nacional.

**Sem scipy e sem shapely.** A celula de Voronoi e' obtida por recorte sucessivo
de meio-plano (Sutherland-Hodgman) a partir da caixa da cidade: para cada par de
pontos, corta-se a celula pela mediatriz. Sao ~350 pontos, ~122 mil recortes de
poligonos pequenos.

**O recorte pelo contorno do municipio nao e' feito aqui.** As celulas saem
retangulares na borda, e quem as apara e' o proprio SVG, com `clipPath` no
contorno que ja' publicamos. Recortar poligono nao-convexo em Python exigiria
uma biblioteca de geometria; o navegador faz isso de graca e sem erro.
"""
import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

# margem alem da caixa do municipio: as celulas de borda precisam sobrar para
# o `clipPath` ter o que aparar
FOLGA = 0.04


def recorta(poli, ax, ay, bx, by):
    """Sutherland-Hodgman: fica o lado do plano que contem A.

    A reta e' a mediatriz de AB. Guarda-se `>= 0` para o lado de A, entao um
    vertice exatamente sobre a mediatriz permanece — o que mantem celulas
    vizinhas com a MESMA aresta, e e' isso que faz a fronteira interna casar
    depois. Se o teste fosse `> 0`, as duas celulas produziriam arestas
    ligeiramente diferentes e a dissolucao por zona deixaria fresta.
    """
    mx, my = (ax + bx) / 2, (ay + by) / 2
    nx, ny = ax - bx, ay - by            # normal apontando para A
    c = nx * mx + ny * my

    def dentro(p):
        return nx * p[0] + ny * p[1] >= c

    saida = []
    n = len(poli)
    for i in range(n):
        p, q = poli[i - 1], poli[i]
        dp, dq = dentro(p), dentro(q)
        if dp != dq:
            den = nx * (q[0] - p[0]) + ny * (q[1] - p[1])
            if den:
                t = (c - nx * p[0] - ny * p[1]) / den
                saida.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
        if dq:
            saida.append(q)
    return saida


def colorir(vizinhas, ordem):
    """A mesma regra do `56_`: vizinha nunca repete cor. Ver aquele arquivo."""
    cor = {}
    for z in ordem:
        usadas = {cor[v] for v in vizinhas[z] if v in cor}
        c = 0
        while c in usadas:
            c += 1
        cor[z] = c
    return cor


def uma_cidade(d):
    """Celulas e limites de uma cidade, ou None se ela tem uma zona so'."""
    pts, zonas_de = [], []
    vistos = {}
    conflito = 0
    for l in d["locais"]:
        if l.get("lat") is None or l.get("lon") is None:
            continue
        k = (round(l["lon"], 6), round(l["lat"], 6))
        if k in vistos:
            # dois locais no mesmo endereco: se as zonas divergem, o ponto e'
            # ambiguo e nao ha' o que decidir — fica o primeiro, e conta-se
            if vistos[k] != l["z"]:
                conflito += 1
            continue
        vistos[k] = l["z"]
        pts.append(k)
        zonas_de.append(l["z"])

    zs = sorted(set(zonas_de))
    if len(zs) < 2 or len(pts) < 3:
        return None

    todos = [p for a in d["geo"] for p in a]
    minX = min(p[0] for p in todos)
    maxX = max(p[0] for p in todos)
    minY = min(p[1] for p in todos)
    maxY = max(p[1] for p in todos)
    fx, fy = (maxX - minX) * FOLGA, (maxY - minY) * FOLGA
    caixa = [(minX - fx, minY - fy), (maxX + fx, minY - fy),
             (maxX + fx, maxY + fy), (minX - fx, maxY + fy)]

    celulas = []
    for i, (ax, ay) in enumerate(pts):
        cel = caixa
        for j, (bx, by) in enumerate(pts):
            if i == j:
                continue
            cel = recorta(cel, ax, ay, bx, by)
            if len(cel) < 3:
                break
        celulas.append([(round(x, 6), round(y, 6)) for x, y in cel])

    # ---------- arestas: as internas de mesma zona somem, as demais ficam ----
    de_aresta = {}
    for i, cel in enumerate(celulas):
        n = len(cel)
        for k in range(n):
            a, b = cel[k - 1], cel[k]
            if a == b:
                continue
            chave = (a, b) if a <= b else (b, a)
            de_aresta.setdefault(chave, []).append(zonas_de[i])

    limites = []
    vizinhas = {z: set() for z in zs}
    for (a, b), zz in de_aresta.items():
        if len(zz) == 2 and zz[0] != zz[1]:
            limites.append([a[0], a[1], b[0], b[1]])
            vizinhas[zz[0]].add(zz[1])
            vizinhas[zz[1]].add(zz[0])
        # len(zz)==1 e' aresta da caixa externa: o clipPath a apara
        # len(zz)==2 com zonas iguais e' costura interna: nao se desenha

    ordem = sorted(zs, key=lambda z: (-len(vizinhas[z]), z))
    cor = colorir(vizinhas, ordem)

    return {
        "cidade": d["cidade"], "cod": d.get("cod"), "ano": d.get("ano"),
        "nCores": (max(cor.values()) + 1) if cor else 0,
        "zonas": [{"z": z, "cor": cor[z],
                   "locais": sum(1 for x in zonas_de if x == z)} for z in zs],
        "celulas": [{"z": zonas_de[i], "p": [[x, y] for x, y in c]}
                    for i, c in enumerate(celulas) if len(c) >= 3],
        "limites": limites,
        "conflitos": conflito,
    }


def main():
    origem = cfg.PROCESSED / "web" / cfg.UF / "urnas"
    if not origem.is_dir():
        raise SystemExit(f"sem arquivos de urna em {origem} — rode 54_ antes")

    saida = cfg.PROCESSED / "web" / cfg.UF / "zonas_cidade"
    saida.mkdir(parents=True, exist_ok=True)

    feitas, total_kb = [], 0.0
    for arq in sorted(origem.glob("*.json")):
        if not arq.stem.isdigit():
            continue
        d = json.loads(arq.read_text(encoding="utf-8"))
        if not d.get("geo"):
            raise SystemExit(f"ABORTADO: {arq.name} sem contorno — rode 55_ antes.\n"
                             "Sem o contorno o clipPath nao existe, e as celulas "
                             "sairiam retangulares para fora da cidade.")
        r = uma_cidade(d)
        if r is None:
            continue
        f = saida / f"{arq.stem}.json"
        f.write_text(json.dumps(r, separators=(",", ":"), ensure_ascii=False),
                     encoding="utf-8")
        kb = f.stat().st_size / 1024
        total_kb += kb
        feitas.append((r["cidade"], len(r["zonas"]), len(r["celulas"]),
                       len(r["limites"]), r["nCores"], r["conflitos"], kb))

    if not feitas:
        raise SystemExit("ABORTADO: nenhuma cidade com mais de uma zona.\n"
                         "Em Goias sao quatro; se deu zero, o dado de entrada "
                         "esta' errado.")

    print(f"{'cidade':<24}{'zonas':>6}{'celulas':>9}{'limites':>9}"
          f"{'cores':>7}{'ambig':>7}{'KB':>7}")
    for nome, nz, nc, nl, cores, amb, kb in feitas:
        print(f"{nome:<24}{nz:>6}{nc:>9}{nl:>9}{cores:>7}{amb:>7}{kb:>7.0f}")
    print(f"\n{len(feitas)} cidades, {total_kb:.0f} KB")
    print("Fronteira derivada por urna mais proxima — NAO e' o limite oficial "
          "do TRE. A tela precisa dizer isso.")


if __name__ == "__main__":
    main()
