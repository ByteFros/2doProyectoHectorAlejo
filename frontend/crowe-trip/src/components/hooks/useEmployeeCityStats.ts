// hooks/useEmployeeCityStats.ts
import { useEffect, useState } from "react";
import useAuth from "./use-auth";
import { apiRequest } from '@config/api';

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
        const res = await apiRequest("/users/empleados/ciudades/", {
          headers: {
            Authorization: `Token ${token}`,
          },
        });

        if (!res.ok) throw new Error("Error al obtener ciudades del empleado");

        const data = await res.json();
        setCities(data);
      } catch (err) {
        console.error("❌ Error en fetch de ciudades por empleado", err);
        setError("No se pudo cargar la información de ciudades");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { cities, loading, error };
}
