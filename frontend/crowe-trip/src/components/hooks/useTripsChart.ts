// hooks/useTripsChart.ts
import { useState, useEffect } from "react";
import useAuth from "./use-auth";

export default function useTripsChart() {
  const { token } = useAuth();
  const [monthlyData, setMonthlyData] = useState<number[]>(Array(12).fill(0));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/users/viajes/over/", {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!res.ok) throw new Error("Error al obtener viajes");

        const data = await res.json();

        const monthCounter = Array(12).fill(0);
        data.forEach((viaje: any) => {
          const mes = new Date(viaje.fecha_inicio).getMonth();
          const dias = viaje.dias_viajados || 1;
          monthCounter[mes] += dias;
        });

        setMonthlyData(monthCounter);
      } catch (err) {
        console.error("Error cargando viajes finalizados", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { monthlyData, loading };
}
