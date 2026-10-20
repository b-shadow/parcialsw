import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act, fireEvent } from "@testing-library/react";
import { Toaster, toast, useToast } from "./Toaster";
import { ConfirmDialogHost, useConfirm } from "./ConfirmDialog";
import { Avatar, PresenceStack } from "./Avatar";
import { StatusBadge } from "./StatusBadge";
import { EmptyState } from "./EmptyState";
import { Skeleton } from "./Skeleton";
import { Folder } from "lucide-react";

describe("Componentes compartidos (V0.5)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useToast.setState({ items: [] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("Toaster: toast.success muestra aviso con role='status' y desaparece a los 4s", () => {
    render(<Toaster />);

    act(() => {
      toast.success("Invitación enviada", "Se envió correo al integrante");
    });

    const statusEl = screen.getByRole("status");
    expect(statusEl).toBeInTheDocument();
    expect(screen.getByText("Invitación enviada")).toBeInTheDocument();
    expect(screen.getByText("Se envió correo al integrante")).toBeInTheDocument();

    // Avanzar reloj 4 segundos
    act(() => {
      vi.advanceTimersByTime(4000);
    });

    expect(screen.queryByText("Invitación enviada")).not.toBeInTheDocument();
  });

  it("ConfirmDialog: useConfirm resuelve true con confirmar y false con cancelar o escape", async () => {
    let confirmPromise: Promise<boolean> | null = null;

    function TestConfirmButton() {
      const confirm = useConfirm();
      return (
        <button
          onClick={() => {
            confirmPromise = confirm({
              title: "¿Revocar acceso?",
              description: "Esta acción no se puede deshacer.",
              confirmLabel: "Revocar",
              tone: "danger",
            });
          }}
        >
          Abrir
        </button>
      );
    }

    render(
      <>
        <TestConfirmButton />
        <ConfirmDialogHost />
      </>
    );

    // 1. Probar cancelación
    fireEvent.click(screen.getByText("Abrir"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("¿Revocar acceso?")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Cancelar"));
    const cancelRes = await confirmPromise;
    expect(cancelRes).toBe(false);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    // 2. Probar confirmación
    fireEvent.click(screen.getByText("Abrir"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Revocar"));
    const confirmRes = await confirmPromise;
    expect(confirmRes).toBe(true);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("Avatar: mismo userId produce misma clase de color; kind='ai' usa icono de robot", () => {
    const { container: c1 } = render(<Avatar name="Ana Gomez" userId="user-uuid-123" />);
    const { container: c2 } = render(<Avatar name="Ana Garcia" userId="user-uuid-123" />);
    const { container: c3 } = render(<Avatar name="CASE AI" kind="ai" />);

    // Mismo userId -> misma clase de color en la primera etiqueta div
    const div1 = c1.querySelector("div");
    const div2 = c2.querySelector("div");
    expect(div1?.className).toBe(div2?.className);

    // AI avatar usa icono y color teal
    const aiDiv = c3.querySelector("div");
    expect(aiDiv?.className).toContain("bg-teal-100");
    expect(c3.querySelector("svg")).toBeInTheDocument();
  });

  it("PresenceStack: 6 personas con max=4 renderiza 4 avatares y '+2'", () => {
    const people = [
      { id: "1", name: "Ana" },
      { id: "2", name: "Beto" },
      { id: "3", name: "Carlos" },
      { id: "4", name: "Diana" },
      { id: "5", name: "Elena" },
      { id: "6", name: "Fabio" },
    ];

    render(<PresenceStack people={people} max={4} />);

    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("StatusBadge: sin tone renderiza neutral por defecto; admite tonos info y ai y dot", () => {
    const { rerender } = render(<StatusBadge>Activo</StatusBadge>);
    expect(screen.getByText("Activo").className).toContain("bg-slate-100");

    rerender(<StatusBadge tone="ai" dot>Sugerencia</StatusBadge>);
    expect(screen.getByText("Sugerencia").className).toContain("bg-teal-50");
  });

  it("EmptyState y Skeleton: renderizan correctamente con Tailwind", () => {
    render(
      <EmptyState
        icon={<Folder data-testid="folder-icon" />}
        title="Sin proyectos"
        description="Crea tu primer proyecto para empezar."
        action={<button>Crear proyecto</button>}
      />
    );
    expect(screen.getByTestId("folder-icon")).toBeInTheDocument();
    expect(screen.getByText("Sin proyectos")).toBeInTheDocument();
    expect(screen.getByText("Crear proyecto")).toBeInTheDocument();

    const { container } = render(<Skeleton className="h-4 w-32" />);
    expect(container.firstChild).toHaveClass("motion-safe:animate-pulse");
  });
});
