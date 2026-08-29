"""Publica o dado do Radar em `radar/public/dados/`, fora do site aberto.

O par do `22_`, para o produto fechado. A diferença que importa não é de código,
é de destino: o `22_` escreve em `app/public/dados`, que a Cloudflare constrói e
põe no ar; este escreve em `radar/public/dados`, que nenhum deploy toca.

**Por que a separação é de arquivo e não de tela.** Num site estático, tirar a
aba esconde o botão e não o arquivo: antes desta mudança, `/dados/GO/padroes.json`
respondia 200 para qualquer um que digitasse o endereço. Um produto fechado cujo
dado responde 200 não é um produto fechado.

**E isto ainda não é controle de acesso.** É separação de build: garante que o
dado do Radar não vai ao ar junto com o site aberto. Publicar o Radar para
clientes exige uma camada de autenticação — Cloudflare Access na frente do
Worker, ou um Worker que valide token antes de servir o JSON. Enquanto ela não
existe, o Radar roda local e não é publicado.
"""
import json
import shutil
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

ORIGEM = cfg.PROCESSED / "radar"
PUBLICO = cfg.ROOT / "app" / "public" / "dados"
DESTINO = cfg.ROOT / "radar" / "public" / "dados"


def main():
    if not ORIGEM.exists():
        raise SystemExit("rode 22_publicar_web.py antes — é ele que separa o "
                         "dado do Radar do dado do site aberto")

    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    ufs = sorted(p.name for p in ORIGEM.iterdir() if p.is_dir())
    n = 0
    for uf in ufs:
        shutil.copytree(ORIGEM / uf, DESTINO / uf)
        n += sum(1 for _ in (DESTINO / uf).glob("*.json"))

    # O índice vem do site aberto: é a lista de UFs e o agregado nacional, e o
    # Radar precisa dele para saber o nome dos estados. Não é dado fechado —
    # é o mesmo arquivo, copiado para o Radar não depender do outro build.
    ix = PUBLICO / "indice.json"
    if ix.exists():
        shutil.copy2(ix, DESTINO / "indice.json")
    else:
        print("  AVISO: indice.json não encontrado; rode 22_ antes")

    total = sum(p.stat().st_size for p in DESTINO.rglob("*.json"))
    print(f"{len(ufs)} UFs, {n} arquivos, {total/1024:.0f} KB em {DESTINO}")

    # Gate: se algum destes voltar a aparecer no build público, o produto
    # fechado deixou de ser fechado sem ninguém perceber.
    vazou = [f"{uf}/{nome}.json" for uf in ufs for nome in ("padroes", "cruzamentos")
             if (PUBLICO / uf / f"{nome}.json").exists()]
    if vazou:
        raise SystemExit(
            f"{len(vazou)} arquivo(s) do Radar estão no build PÚBLICO: "
            f"{vazou[:4]}. O 22_ deveria tê-los movido.")
    print("gate: nenhum arquivo do Radar no build público")


if __name__ == "__main__":
    main()
