// hooks/useCompanyTripsSummary.ts
import { useState, useEffect } from "react";
import { apiFetch } from "~/utils/api"; // Asegúrate de que el path sea correcto
import useAuth from "../use-auth";

interface CompanySummary {
  empresa_id: number;
  empresa: string;
  trips: number;
  days: number;
  nonExemptDays: number;
}

export default function useCompanyTripsSummary() {
  const { token } = useAuth();
  const [data, setData] = useState<CompanySummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch("/api/users/report/viajes/", {}, true);
        if (!response.ok) throw new Error("Error al obtener el resumen de viajes por empresa");
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error("❌ Error al cargar resumen por empresa:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { data, loading };
}
