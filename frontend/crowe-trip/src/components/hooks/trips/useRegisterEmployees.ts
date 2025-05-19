// hooks/useRegisterEmployees.ts
import { useState } from 'react';
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
      const res = await fetch('http://127.0.0.1:8000/api/users/empleados/nuevo/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const errData = await res.json();
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
      const res = await fetch('http://127.0.0.1:8000/api/users/empleados/batch-upload/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
        },
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
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
