import React from "react";
import ReactDOM from "react-dom/client";
import { registerSW } from "virtual:pwa-register";

import { Aplicacion } from "./Aplicacion";
import "./estilos.css";

registerSW({ immediate: true });

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <Aplicacion />
  </React.StrictMode>
);
