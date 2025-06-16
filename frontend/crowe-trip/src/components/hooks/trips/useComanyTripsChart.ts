import { useState, useEffect } from "react";
import useAuth from "../use-auth";
import { apiRequest } from '@config/api';

interface ChartData {
    labels: string[];
    datasets: {
        label: string;
        data: number[];
        backgroundColor: string;
        borderRadius?: number;
    }[];
}

export default function useCompanyTripsChart() {
    const { token } = useAuth();
    const [data, setData] = useState<ChartData>({ labels: [], datasets: [] });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token) return;

        const fetchData = async () => {
            try {
                const res = await apiRequest("/users/report/trips-per-month/", {
                    headers: {
                        Authorization: `Token ${token}`,
                    },
                });

                if (!res.ok) throw new Error("Error al obtener datos del reporte");

                const result = await res.json();

                const monthLabels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
                const viajesPorMes = Array(12).fill(0);

                result.forEach((item: { month: string, totalDays: number }) => {
                    const monthIndex = parseInt(item.month.split('-')[1], 10) - 1; // ➤ 0-based index
                    viajesPorMes[monthIndex] = item.totalDays;
                });

                setData({
                    labels: monthLabels,
                    datasets: [
                        {
                            label: "Días viajados por mes",
                            data: viajesPorMes,
                            backgroundColor: "rgba(75, 192, 192, 0.6)",
                            borderRadius: 4,
                        },
                    ],
                });
            } catch (err) {
                console.error("❌ Error cargando datos de viajes", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [token]);

    return { data, loading };
}
