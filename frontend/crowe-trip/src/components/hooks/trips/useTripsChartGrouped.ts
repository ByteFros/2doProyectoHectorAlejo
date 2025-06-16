// hooks/useTripsChartGrouped.ts
import { useState, useEffect } from "react";
import useAuth from "../use-auth";
import { apiRequest } from '@config/api';

interface Dataset {
  label: string;
  data: number[]; // 12 months
  backgroundColor: string;
}

interface ChartData {
  labels: string[];
  datasets: Dataset[];
}

interface CompanySummary {
  empresa: string;
  trips: number;
  days: number;
  nonExemptDays: number;
}

const colors = [
  "#4e73df", "#1cc88a", "#36b9cc", "#f6c23e", "#e74a3b",
  "#858796", "#fd7e14", "#20c997", "#6610f2", "#6f42c1",
  "#17a2b8", "#343a40",
];

export default function useTripsChartGrouped() {
  const { token } = useAuth();
  const [data, setData] = useState<ChartData>({ labels: [], datasets: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const res = await apiRequest("/users/viajes/over/", {
          headers: {
            Authorization: `Token ${token}`,
          },
        });

        if (!res.ok) throw new Error("Error al obtener viajes");

        const viajes = await res.json();
        const monthLabels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

        const groupedData: { [empresa: string]: number[] } = {};

        viajes.forEach((viaje: any) => {
          const empresa = viaje.empresa?.nombre_empresa || "Desconocida";
          const mes = new Date(viaje.fecha_inicio).getMonth();
          const dias = viaje.dias_viajados || 1;

          if (!groupedData[empresa]) {
            groupedData[empresa] = Array(12).fill(0);
          }

          groupedData[empresa][mes] += dias;
        });

        const datasets: Dataset[] = Object.entries(groupedData).map(([empresa, dataArr], index) => ({
          label: empresa,
          data: dataArr,
          backgroundColor: colors[index % colors.length],
        }));

        setData({ labels: monthLabels, datasets });
      } catch (err) {
        console.error("Error agrupando viajes por empresa/mes", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { data, loading };
}
