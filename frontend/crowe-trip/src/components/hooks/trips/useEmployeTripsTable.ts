// hooks/useEmployeeTripsTable.ts
import { useEffect, useState } from "react";
import { apiFetch } from "~/utils/api"; // Ajusta el path si es necesario
import useAuth from "../use-auth";

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
        const response = await apiFetch("/api/users/report/empleados/", {}, true);
        if (!response.ok) throw new Error("Error al obtener el resumen de viajes");

        const summary: EmployeeTrip[] = await response.json();
        setEmployees(summary);
      } catch (err) {
        console.error("❌ Error cargando el resumen de viajes:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [token]);

  return { employees, loading };
}
