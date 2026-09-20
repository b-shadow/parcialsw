import { BrowserRouter } from "react-router-dom";
import { useEffect } from "react";

import { AppRoutes } from "./core/routes/routes";
import { useThemeStore } from "./core/theme/themeStore";

export function App() {
  const mode = useThemeStore((state) => state.mode);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", mode === "dark");
    document.documentElement.dataset.theme = mode;
    document.documentElement.style.colorScheme = mode;
  }, [mode]);

  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
