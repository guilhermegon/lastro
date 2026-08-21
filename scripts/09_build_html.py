"""Injeta o payload no template e grava o HTML autocontido do painel."""
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
cfg = import_module("00_config")

MARCA = "/*__DADOS__*/"
tpl = (cfg.DIST / "template.html").read_text(encoding="utf-8")
dados = (cfg.DIST / "dados.json").read_text(encoding="utf-8")
if MARCA not in tpl:
    raise SystemExit(f"marcador {MARCA} nao encontrado no template")
saida = cfg.DIST / "rastro_go.html"
saida.write_text(tpl.replace(MARCA, dados), encoding="utf-8")
print(f"{saida.name}: {saida.stat().st_size/1024:.0f} KB")
