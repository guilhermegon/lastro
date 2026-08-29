import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * O Radar é aplicação à parte, e isso não é organização: é o que faz o produto
 * fechado ser fechado.
 *
 * A Cloudflare constrói `app/` e publica `app/dist`. Nada daqui entra naquele
 * diretório, então nada daqui vai ao ar junto com o site aberto. Fosse o Radar
 * uma aba a mais em `app/`, o JavaScript e os JSON dele seriam baixáveis por
 * qualquer um — tirar a aba da barra esconde o botão, não o arquivo.
 *
 * Os componentes são compartilhados por alias, não copiados: um gráfico que
 * divergisse entre os dois produtos seria pior que um gráfico feio.
 */
export default defineConfig({
  plugins: [react()],
  base: "./",
  resolve: {
    alias: {
      "@app": new URL("../app/src", import.meta.url).pathname,
    },
  },
  server: { fs: { allow: [".."] } },
  build: { outDir: "dist", assetsInlineLimit: 0 },
});
