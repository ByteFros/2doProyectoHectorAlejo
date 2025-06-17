const API_URL = import.meta.env.VITE_API_URL;

if (!API_URL) {
  throw new Error("❌ VITE_API_URL no está definido. Verifica tu archivo .env");
}

export const apiFetch = async (
  endpoint: string,
  options: RequestInit = {},
  requireAuth = false
) => {
  const token = localStorage.getItem("token");

  let headers: Record<string, string> = {};

  if (options.headers instanceof Headers) {
    options.headers.forEach((value, key) => {
      headers[key] = value;
    });
  } else if (options.headers && typeof options.headers === "object" && !Array.isArray(options.headers)) {
    headers = { ...options.headers as Record<string, string> };
  }

  // ⚠️ Solo forzar Content-Type si no es FormData
  const isFormData = options.body instanceof FormData;
  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (requireAuth && token) {
    headers["Authorization"] = `Token ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  return response;
};
