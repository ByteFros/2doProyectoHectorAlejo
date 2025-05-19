// hooks/useCompanies.ts
import { useState, useEffect, useCallback } from 'react';
import useAuth from './use-auth';

export interface Empresa {
  id: number;
  nombre: string;
  nif: string;
  domicilio: string;
  autogestion: boolean;
}

export default function useCompanies() {
  const { token } = useAuth();
  const [companies, setCompanies] = useState<Empresa[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCompanies = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/users/empresas/', {
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!res.ok) throw new Error('Error al cargar empresas');

      const data = await res.json();
      const formatted = data.map((e: any) => ({
        id: e.id,
        nombre: e.nombre_empresa,
        nif: e.nif,
        domicilio: e.address,
        autogestion: e.permisos,
      }));

      setCompanies(formatted);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const deleteCompany = async (id: number) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/users/empresas/${id}/`, {
        method: 'DELETE',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!res.ok) throw new Error('Error al eliminar empresa');
      setCompanies((prev) => prev.filter((emp) => emp.id !== id));
    } catch (err: any) {
      console.error(err);
    }
  };

  const toggleAutogestion = async (id: number, current: boolean) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/users/empresas/${id}/`, {
        method: 'PUT',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ permisos: !current }),
      });

      if (!res.ok) throw new Error('Error al actualizar permisos');

      setCompanies((prev) =>
        prev.map((emp) =>
          emp.id === id ? { ...emp, autogestion: !current } : emp
        )
      );
    } catch (err: any) {
      console.error(err);
    }
  };

  return { companies, loading, error, deleteCompany, toggleAutogestion, refetch: fetchCompanies };
}
