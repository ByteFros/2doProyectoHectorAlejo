// hooks/useEmployees.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta si el path cambia
import useAuth from './use-auth';

export interface Employee {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  dni: string;
  empresa: string;
  username: string;
}

export default function useEmployees(
  empresaId: number | null,
  role?: "MASTER" | "EMPRESA" | "EMPLEADO" | null
) {
  const { token } = useAuth();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEmployees = async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const endpoint =
        role === "MASTER" && empresaId !== null
          ? `/api/users/empresas/${empresaId}/empleados/`
          : `/api/users/empleados/`;

      const response = await apiFetch(endpoint, {}, true);

      if (!response.ok) throw new Error("Error al cargar empleados");

      const data: Employee[] = await response.json();
      setEmployees(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteEmployeeById = async (id: number) => {
    try {
      const response = await apiFetch(
        `/api/users/empleados/${id}/`,
        { method: "DELETE" },
        true
      );

      if (!response.ok) throw new Error("Error al eliminar empleado");

      setEmployees((prev) => prev.filter((emp) => emp.id !== id));
    } catch (err: any) {
      console.error("❌ Error eliminando empleado:", err.message);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, [empresaId, token]);

  return { employees, loading, error, fetchEmployees, deleteEmployeeById };
}
