// hooks/useTripsChart.ts
import { useState, useEffect } from "react";
import { apiFetch } from "~/utils/api"; // Asegúrate que el path es correcto
import useAuth from "./use-auth";

export default function useTripsChart() {
  const { token } = useAuth();
  const [monthlyData, setMonthlyData] = useState<number[]>(Array(12).fill(0));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch("/api/users/viajes/over/", {}, true);
        if (!response.ok) throw new Error("Error al obtener viajes");

        const data = await response.json();

        const monthCounter = Array(12).fill(0);
        data.forEach((viaje: any) => {
          const mes = new Date(viaje.fecha_inicio).getMonth();
          const dias = viaje.dias_viajados || 1;
          monthCounter[mes] += dias;
        });

        setMonthlyData(monthCounter);
      } catch (err) {
        console.error("❌ Error cargando viajes finalizados:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { monthlyData, loading };
}
