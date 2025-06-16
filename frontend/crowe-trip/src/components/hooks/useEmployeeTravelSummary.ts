// hooks/useEmployeeTravelSummary.ts
import { useEffect, useState } from "react";
import useAuth from "./use-auth";
import { apiRequest } from '@config/api';

interface TravelSummary {
    national: number;
    international: number;
    total: number;
    total_days: number;
  }
  
export default function useEmployeeTravelSummary() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<TravelSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const res = await apiRequest("/users/report/trips-type/", {
          headers: {
            Authorization: `Token ${token}`,
          },
        });

        if (!res.ok) throw new Error("Error al obtener resumen de viajes");

        const data = await res.json();
        setSummary(data);
      } catch (err) {
        console.error("❌ Error al cargar resumen de viajes", err);
        setSummary(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { summary, loading };
}
