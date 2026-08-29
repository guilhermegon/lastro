import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@app/estilos/tokens.css";
import { AppRadar } from "./AppRadar";

createRoot(document.getElementById("raiz") as HTMLElement).render(
  <StrictMode>
    <AppRadar />
  </StrictMode>,
);
