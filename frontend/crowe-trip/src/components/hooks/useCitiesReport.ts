// hooks/useCitiesReport.ts
import { useEffect, useState } from "react";
import useAuth from "./use-auth";

interface CityStats {
  city: string;
  days: number;
}

export default function useCitiesReport() {
  const { token } = useAuth();
  const [cities, setCities] = useState<CityStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchCities = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/users/viajes/over/", {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!res.ok) throw new Error("Error al obtener viajes");

        const data = await res.json();

        const cityMap: Record<string, number> = {};

        data.forEach((viaje: any) => {
          const destino = viaje.destino.split(",")[0].trim(); // solo ciudad
          const dias = viaje.dias_viajados || 1;
          cityMap[destino] = (cityMap[destino] || 0) + dias;
        });

        const result = Object.entries(cityMap).map(([city, days]) => ({ city, days }));
        setCities(result);
      } catch (err) {
        console.error("Error al cargar ciudades", err);
      } finally {
        setLoading(false);
      }
    };

    fetchCities();
  }, [token]);

  return { cities, loading };
}
