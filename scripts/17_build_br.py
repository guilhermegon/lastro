"""Injeta o payload nacional no template e grava a pagina do Brasil."""
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

MARCA = "/*__DADOS__*/"
tpl = (cfg.DIST / "template_br.html").read_text(encoding="utf-8")
dados = (cfg.DIST / "dados_br.json").read_text(encoding="utf-8")
if MARCA not in tpl:
    raise SystemExit(f"marcador {MARCA} nao encontrado")
saida = cfg.DIST / "lastro_brasil.html"
saida.write_text(tpl.replace(MARCA, dados), encoding="utf-8")
mb = saida.stat().st_size / 1024 / 1024
print(f"{saida.name}: {mb:.1f} MB")
if mb > 16:
    raise SystemExit("ACIMA DO TETO DE 16 MB")
