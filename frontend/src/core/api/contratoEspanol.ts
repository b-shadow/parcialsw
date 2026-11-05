import campos from "./nombresContrato.json";

const nombres = campos as Record<string, string>;
const inversos = Object.fromEntries(
  Object.entries(nombres).map(([anterior, nuevo]) => [nuevo, anterior])
) as Record<string, string>;

function traducir(valor: unknown, mapa: Record<string, string>): unknown {
  if (Array.isArray(valor)) return valor.map((item) => traducir(item, mapa));
  if (valor === null || typeof valor !== "object" || Object.getPrototypeOf(valor) !== Object.prototype) {
    return valor;
  }
  return Object.fromEntries(
    Object.entries(valor).map(([clave, item]) => [mapa[clave] ?? clave, traducir(item, mapa)])
  );
}

export const contratoAlEspanol = (valor: unknown): unknown => traducir(valor, nombres);
export const contratoAlCodigo = (valor: unknown): unknown => traducir(valor, inversos);
