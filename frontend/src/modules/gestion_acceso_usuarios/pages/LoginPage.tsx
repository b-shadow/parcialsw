import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";

import { useAuthStore } from "../../../core/auth/authStore";
import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { authService } from "../services/authService";
import { validateEmail, validatePassword } from "../validations/authValidation";

export function LoginPage() {
  const navigate = useNavigate();
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);
  const [email, setEmail] = useState("editor@example.com");
  const [password, setPassword] = useState("Password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!validateEmail(email) || !validatePassword(password)) {
      setError("Credenciales con formato invalido.");
      return;
    }
    setLoading(true);
    try {
      const token = await authService.login({ email, password });
      setToken(token.access_token);
      const user = await authService.me();
      setUser(user);
      navigate("/proyectos");
    } catch {
      setError("No se pudo iniciar sesion con esos datos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-panel px-4 text-ink">
      <Panel className="w-full max-w-md p-6 shadow-sm">
        <div className="mb-6">
          <p className="text-sm font-semibold text-accent">CASE Inteligente</p>
          <h1 className="mt-1 text-2xl font-semibold">Inicio de sesion</h1>
        </div>
        <form className="grid gap-4" onSubmit={handleSubmit}>
          <Input label="Correo" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          <Input
            label="Contrasena"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          <Button disabled={loading} icon={<LogIn size={18} aria-hidden="true" />} type="submit">
            {loading ? "Ingresando" : "Ingresar"}
          </Button>
        </form>
        <p className="mt-5 text-sm text-slate-600">
          Sin cuenta activa:{" "}
          <Link className="font-medium text-accent" to="/registro">
            crear usuario
          </Link>
        </p>
      </Panel>
    </main>
  );
}
