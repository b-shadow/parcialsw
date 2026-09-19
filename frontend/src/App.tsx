import { BrowserRouter } from "react-router-dom";

import { AppRoutes } from "./core/routes/routes";

export function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
