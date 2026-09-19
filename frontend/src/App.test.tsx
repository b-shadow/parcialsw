import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renderiza el acceso como primera ruta cuando no hay token", () => {
    window.localStorage.clear();
    render(<App />);
    expect(screen.getByRole("heading", { name: /inicio de sesion/i })).toBeInTheDocument();
  });
});
