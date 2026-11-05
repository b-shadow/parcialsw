export function validarCorreo(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function validarContrasena(password: string) {
  return password.length >= 8;
}
