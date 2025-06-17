// hooks/useEmployeeCityStats.ts
import { useEffect, useState } from "react";
import { apiFetch } from "~/utils/api"; // Ajusta si es necesario
import useAuth from "./use-auth";

interface CityStats {
  city: string;
  trips: number;
  days: number;
  nonExemptDays: number;
  exemptDays: number;
}

export default function useEmployeeCityStats() {
  const { token } = useAuth();
  const [cities, setCities] = useState<CityStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch("/api/users/empleados/ciudades/", {}, true);
        if (!response.ok) throw new Error("Error al obtener ciudades del empleado");

        const data: CityStats[] = await response.json();
        setCities(data);
      } catch (err) {
        console.error("❌ Error en fetch de ciudades por empleado:", err);
        setError("No se pudo cargar la información de ciudades");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { cities, loading, error };
}
