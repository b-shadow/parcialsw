import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, LockKeyhole, LogIn, Mail, Network } from "lucide-react";

import { useAuthStore } from "../../../core/auth/authStore";
import { useThemeStore } from "../../../core/theme/themeStore";
import { ThemeToggle } from "../../../shared/components/ThemeToggle";
import { cn } from "../../../shared/utils/cn";
import { authService } from "../services/authService";
import { validateEmail, validatePassword } from "../validations/authValidation";
import loginLeftImage from "../../../../assets/login-izquierda.png";

export function LoginPage() {
  const navigate = useNavigate();
  const isDark = useThemeStore((state) => state.mode === "dark");
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);
  const [email, setEmail] = useState("editor@example.com");
  const [password, setPassword] = useState("Password123");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
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

  const pageTone = isDark
    ? "bg-[#07111f] text-slate-100"
    : "bg-[linear-gradient(135deg,#f8fbff_0%,#eef6f7_48%,#f7f8fb_100%)] text-[#172033]";
  const cardTone = isDark
    ? "border-slate-700 bg-[#172033] shadow-[0_24px_80px_rgba(0,0,0,0.42)]"
    : "border-slate-300 bg-white/96 shadow-[0_24px_80px_rgba(15,23,42,0.16)]";
  const titleTone = isDark ? "text-white" : "text-[#172033]";
  const bodyTone = isDark ? "text-slate-300" : "text-slate-600";
  const labelTone = isDark ? "text-slate-300" : "text-slate-700";
  const fieldTone = isDark
    ? "border-slate-600 bg-[#08111f] text-slate-300 focus-within:border-teal-400 focus-within:ring-teal-400/15"
    : "border-slate-300 bg-white text-slate-500 focus-within:border-accent focus-within:ring-teal-100";
  const fieldAddonTone = isDark ? "bg-[#111a2b] text-slate-400" : "bg-slate-50 text-slate-500";
  const inputTone = isDark ? "text-white placeholder:text-slate-500" : "text-[#172033] placeholder:text-slate-400";
  const dividerTone = isDark ? "bg-slate-700" : "bg-slate-300";

  return (
    <main className={cn("grid min-h-screen lg:grid-cols-[1.5fr_1fr]", pageTone)}>
      <section className="relative hidden min-h-screen overflow-hidden bg-[#071c33] lg:block">
        <img
          alt="CASE Inteligente: modelado UML, generacion automatica y colaboracion"
          className="h-full w-full object-cover"
          src={loginLeftImage}
        />
      </section>

      <section className="relative flex min-h-screen flex-col overflow-hidden px-5 py-6">
        <div
          className={cn(
            "pointer-events-none absolute inset-0",
            isDark
              ? "bg-[radial-gradient(circle_at_20%_20%,rgba(20,184,166,0.14),transparent_34%),radial-gradient(circle_at_78%_74%,rgba(37,99,235,0.16),transparent_34%)]"
              : "bg-[radial-gradient(circle_at_20%_20%,rgba(20,184,166,0.10),transparent_34%),radial-gradient(circle_at_80%_78%,rgba(37,99,235,0.08),transparent_32%)]"
          )}
        />
        <div className="relative z-10 mx-auto mb-4 flex w-full max-w-xl justify-end">
          <ThemeToggle />
        </div>
        <div className={cn("relative z-10 mx-auto my-auto w-full max-w-xl rounded-[28px] border p-8 backdrop-blur md:p-12", cardTone)}>
          <div className="mb-12 flex items-center gap-4">
            <div className={cn("flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl text-accent", isDark ? "bg-teal-400/10" : "bg-teal-50")}>
              <Network size={34} aria-hidden="true" />
            </div>
            <div>
              <p className={cn("text-2xl font-bold tracking-tight", titleTone)}>
                CASE <span className="text-accent">Inteligente</span>
              </p>
              <p className={cn("mt-1 text-xs font-semibold uppercase tracking-[0.08em]", isDark ? "text-slate-400" : "text-slate-500")}>
                Plataforma colaborativa de modelado y generacion de codigo
              </p>
            </div>
          </div>

          <div className="mb-8">
            <h1 className={cn("text-5xl font-black leading-tight tracking-normal", titleTone)}>Bienvenido</h1>
            <p className={cn("mt-3 text-xl", bodyTone)}>Inicia sesion para continuar en CASE Inteligente</p>
          </div>

          <form className="grid gap-6" onSubmit={handleSubmit}>
            <label className={cn("grid gap-2 text-base font-bold", labelTone)}>
              Correo electronico
              <span className={cn("flex h-14 items-center gap-3 overflow-hidden rounded-lg border transition focus-within:ring-4", fieldTone)}>
                <span className={cn("flex h-full w-14 shrink-0 items-center justify-center", fieldAddonTone)}>
                  <Mail size={24} aria-hidden="true" />
                </span>
                <input
                  className={cn("h-full min-w-0 flex-1 border-0 bg-transparent pr-4 text-base font-semibold outline-none focus:ring-0", inputTone)}
                  placeholder="tu@correo.com"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </span>
            </label>

            <label className={cn("grid gap-2 text-base font-bold", labelTone)}>
              Contrasena
              <span className={cn("flex h-14 items-center gap-3 overflow-hidden rounded-lg border transition focus-within:ring-4", fieldTone)}>
                <span className={cn("flex h-full w-14 shrink-0 items-center justify-center", fieldAddonTone)}>
                  <LockKeyhole size={24} aria-hidden="true" />
                </span>
                <input
                  className={cn("h-full min-w-0 flex-1 border-0 bg-transparent text-base font-semibold outline-none focus:ring-0", inputTone)}
                  placeholder="Ingresa tu contrasena"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
                <button
                  className={cn("flex h-full w-14 shrink-0 items-center justify-center transition hover:text-accent", fieldAddonTone)}
                  onClick={() => setShowPassword((current) => !current)}
                  title={showPassword ? "Ocultar contrasena" : "Mostrar contrasena"}
                  type="button"
                >
                  {showPassword ? <EyeOff size={24} aria-hidden="true" /> : <Eye size={24} aria-hidden="true" />}
                </button>
              </span>
            </label>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <label className={cn("inline-flex items-center gap-3 text-base font-medium", bodyTone)}>
                <input
                  checked={rememberMe}
                  className="h-5 w-5 rounded border-slate-300 accent-teal-600 focus:ring-accent"
                  type="checkbox"
                  onChange={(event) => setRememberMe(event.target.checked)}
                />
                Recordarme
              </label>
              <span className="text-base font-bold text-accent">Olvidaste tu contrasena?</span>
            </div>

            {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

            <button
              className="inline-flex h-16 items-center justify-center gap-3 rounded-lg bg-accent px-6 text-xl font-bold text-white shadow-lg shadow-teal-900/15 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={loading}
              type="submit"
            >
              <LogIn size={24} aria-hidden="true" />
              {loading ? "Ingresando" : "Ingresar"}
            </button>
          </form>

          <div className={cn("my-9 h-px", dividerTone)} />
          <p className={cn("text-center text-lg", bodyTone)}>
            No tienes una cuenta?{" "}
            <Link className="font-bold text-accent" to="/registro">
              Crear usuario
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
