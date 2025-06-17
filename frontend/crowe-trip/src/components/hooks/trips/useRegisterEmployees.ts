// hooks/useRegisterEmployees.ts
import { useState } from 'react';
import { apiFetch } from '~/utils/api'; // Asegúrate de ajustar el path
import useAuth from '../use-auth';

interface EmployeePayload {
  nombre: string;
  apellido: string;
  dni: string;
  email?: string;
}

export default function useRegisterEmployees() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const registerSingleEmployee = async (data: EmployeePayload) => {
    clearMessages();
    setLoading(true);

    try {
      const response = await apiFetch(
        '/api/users/empleados/nuevo/',
        {
          method: 'POST',
          body: JSON.stringify(data),
        },
        true
      );

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Error al registrar empleado');
      }

      setSuccess('Empleado registrado correctamente.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const registerEmployeesFromCSV = async (file: File) => {
    clearMessages();
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiFetch(
        '/api/users/empleados/batch-upload/',
        {
          method: 'POST',
          body: formData,
        },
        true // Token incluido automáticamente
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al subir CSV');
      }

      setSuccess(`${data.empleados_registrados?.length || 0} empleados agregados correctamente.`);

      if (data.errores?.length > 0) {
        setError(`${data.errores.length} errores al procesar el archivo.`);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return {
    registerSingleEmployee,
    registerEmployeesFromCSV,
    loading,
    error,
    success,
    clearMessages,
  };
}
