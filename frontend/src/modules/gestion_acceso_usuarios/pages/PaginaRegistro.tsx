import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";

import { useAlmacenAutenticacion } from "../../../core/auth/almacenAutenticacion";
import { Boton } from "../../../shared/components/Boton";
import { Entrada } from "../../../shared/components/Entrada";
import { Panel } from "../../../shared/components/Panel";
import { servicioAutenticacion } from "../services/servicioAutenticacion";
import { validarCorreo, validarContrasena } from "../validations/validacionAutenticacion";

export function PaginaRegistro() {
  const navigate = useNavigate();
  const setToken = useAlmacenAutenticacion((state) => state.setToken);
  const setUser = useAlmacenAutenticacion((state) => state.setUser);
  const [fullName, setFullName] = useState("Editor UML");
  const [email, setEmail] = useState("editor@example.com");
  const [password, setPassword] = useState("Password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (fullName.trim().length < 3 || !validarCorreo(email) || !validarContrasena(password)) {
      setError("Datos de registro invalidos.");
      return;
    }
    setLoading(true);
    try {
      await servicioAutenticacion.register({ full_name: fullName, email, password });
      const token = await servicioAutenticacion.login({ email, password });
      setToken(token.access_token);
      const user = await servicioAutenticacion.me();
      setUser(user);
      navigate("/proyectos/nuevo");
    } catch {
      setError("No se pudo registrar el usuario.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-panel px-4 text-ink">
      <Panel className="w-full max-w-md p-6 shadow-sm">
        <div className="mb-6">
          <p className="text-sm font-semibold text-accent">CASE Inteligente</p>
          <h1 className="mt-1 text-2xl font-semibold">Registro</h1>
        </div>
        <form className="grid gap-4" onSubmit={handleSubmit}>
          <Entrada label="Nombre completo" value={fullName} onChange={(event) => setFullName(event.target.value)} />
          <Entrada label="Correo" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          <Entrada
            label="Contrasena"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          <Boton disabled={loading} icon={<UserPlus size={18} aria-hidden="true" />} type="submit">
            {loading ? "Registrando" : "Crear cuenta"}
          </Boton>
        </form>
        <p className="mt-5 text-sm text-slate-600">
          Usuario existente:{" "}
          <Link className="font-medium text-accent" to="/login">
            iniciar sesion
          </Link>
        </p>
      </Panel>
    </main>
  );
}
