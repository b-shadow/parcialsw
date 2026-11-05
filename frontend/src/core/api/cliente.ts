import axios from "axios";

import { entorno } from "../config/entorno";
import { useAlmacenAutenticacion } from "../auth/almacenAutenticacion";
import { contratoAlCodigo, contratoAlEspanol } from "./contratoEspanol";

export const clienteApi = axios.create({
  baseURL: entorno.apiBaseUrl,
  headers: {
    "Content-Type": "application/json"
  }
});

clienteApi.interceptors.request.use((config) => {
  config.headers.set("X-Contrato-Idioma", "es");
  if (config.data && typeof config.data === "object" && !(config.data instanceof FormData)) {
    config.data = contratoAlEspanol(config.data);
  }
  const token = useAlmacenAutenticacion.getState().token ?? window.localStorage.getItem("case_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

clienteApi.interceptors.response.use(
  (response) => {
    response.data = contratoAlCodigo(response.data);
    return response;
  },
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response) {
      error.response.data = contratoAlCodigo(error.response.data);
    }
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      useAlmacenAutenticacion.getState().logout();
    }
    return Promise.reject(error);
  }
);
