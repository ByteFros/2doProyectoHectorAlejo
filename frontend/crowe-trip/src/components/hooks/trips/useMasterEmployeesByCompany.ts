// hooks/useMasterEmployeesByCompany.ts
import { useState } from "react";
import { apiFetch } from "~/utils/api"; // Ajusta si es necesario
import useAuth from "../use-auth";

interface EmployeeTrip {
  name: string;
  trips: number;
  travelDays: number;
  exemptDays: number;
  nonExemptDays: number;
}

export default function useMasterEmployeesByCompany() {
  const { token } = useAuth();
  const [employees, setEmployees] = useState<EmployeeTrip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEmployeesByCompany = async (companyId: string) => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch(
        `/api/users/report/empresa/${companyId}/empleados/viajes/`,
        {},
        true
      );

      if (!response.ok) {
        throw new Error("Error al obtener información de los empleados");
      }

      const data: EmployeeTrip[] = await response.json();
      setEmployees(data);
    } catch (err) {
      console.error("❌ Error cargando los empleados", err);
      setError("No se pudo cargar la información de los empleados");
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  };

  return { employees, loading, error, fetchEmployeesByCompany };
}
