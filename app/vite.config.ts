import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Caminho relativo: a build funciona servida de qualquer subpasta, o que
  // importa porque o destino pode ser GitHub Pages, um bucket ou o servidor de
  // um orgao, sem controle sobre a raiz.
  base: "./",
  build: { outDir: "dist", assetsInlineLimit: 0 },
});
