// hooks/useEmployeeTripsTable.ts
import { useEffect, useState } from "react";
import useAuth from "../use-auth";
import { apiRequest } from '@config/api';

interface EmployeeTrip {
  name: string;
  trips: number;
  travelDays: number;
  exemptDays: number;
  nonExemptDays: number;
}

export default function useEmployeeTripsTable() {
  const { token } = useAuth();
  const [employees, setEmployees] = useState<EmployeeTrip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchSummary = async () => {
      try {
        const res = await apiRequest("/users/report/empleados/", {
          headers: {
            Authorization: `Token ${token}`,
          },
        });

        if (!res.ok) throw new Error("Error al obtener el resumen de viajes");

        const summary = await res.json();

        setEmployees(summary); // ✅ Usa los datos tal cual llegan del backend
      } catch (err) {
        console.error("❌ Error cargando el resumen de viajes", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [token]);

  return { employees, loading };
}