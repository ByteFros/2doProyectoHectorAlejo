// hooks/useMasterEmployeesByCompany.ts
import { useState } from "react";
import useAuth from "../use-auth";
import { apiRequest } from '@config/api';

interface EmployeeTrip {
  name: string;
  trips: number;
  travelDays: number; // Notar que esto corresponde a 'days' en la tabla
  exemptDays: number;
  nonExemptDays: number;
}

export default function useMasterEmployeesByCompany() {
  const { token } = useAuth();
  const [employees, setEmployees] = useState<EmployeeTrip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Función para obtener los empleados de una empresa específica
  const fetchEmployeesByCompany = async (companyId: string) => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      // Esta URL debería ser modificada para apuntar al endpoint correcto para usuarios MASTER
      const res = await apiRequest(`/users/report/empresa/${companyId}/empleados/viajes/`, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (!res.ok) {
        throw new Error("Error al obtener información de los empleados");
      }

      const data = await res.json();
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