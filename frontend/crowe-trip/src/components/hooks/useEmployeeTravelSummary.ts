// hooks/useEmployeeTravelSummary.ts
import { useEffect, useState } from "react";
import { apiFetch } from "~/utils/api"; // Ajusta si cambia el path
import useAuth from "./use-auth";

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
        const response = await apiFetch("/api/users/report/trips-type/", {}, true);
        if (!response.ok) throw new Error("Error al obtener resumen de viajes");

        const data: TravelSummary = await response.json();
        setSummary(data);
      } catch (err) {
        console.error("❌ Error al cargar resumen de viajes:", err);
        setSummary(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { summary, loading };
}
