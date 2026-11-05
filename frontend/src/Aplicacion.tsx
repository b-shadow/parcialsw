import { BrowserRouter } from "react-router-dom";
import { useEffect } from "react";

import { RutasAplicacion } from "./core/routes/rutas";
import { useAlmacenTema } from "./core/theme/almacenTema";

export function Aplicacion() {
  const mode = useAlmacenTema((state) => state.mode);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", mode === "dark");
    document.documentElement.dataset.theme = mode;
    document.documentElement.style.colorScheme = mode;
  }, [mode]);

  return (
    <BrowserRouter>
      <RutasAplicacion />
    </BrowserRouter>
  );
}
