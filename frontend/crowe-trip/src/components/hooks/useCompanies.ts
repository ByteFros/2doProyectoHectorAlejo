// hooks/useCompanies.ts
import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta si cambia la ruta
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
      const response = await apiFetch('/api/users/empresas/', {}, true);
      if (!response.ok) throw new Error('Error al cargar empresas');

      const data = await response.json();
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
      const response = await apiFetch(`/api/users/empresas/${id}/`, {
        method: 'DELETE',
      }, true);

      if (!response.ok) throw new Error('Error al eliminar empresa');
      setCompanies((prev) => prev.filter((emp) => emp.id !== id));
    } catch (err: any) {
      console.error('❌ Error al eliminar empresa:', err);
    }
  };

  const toggleAutogestion = async (id: number, current: boolean) => {
    try {
      const response = await apiFetch(`/api/users/empresas/${id}/`, {
        method: 'PUT',
        body: JSON.stringify({ permisos: !current }),
      }, true);

      if (!response.ok) throw new Error('Error al actualizar permisos');

      setCompanies((prev) =>
        prev.map((emp) =>
          emp.id === id ? { ...emp, autogestion: !current } : emp
        )
      );
    } catch (err: any) {
      console.error('❌ Error al cambiar autogestión:', err);
    }
  };

  return {
    companies,
    loading,
    error,
    deleteCompany,
    toggleAutogestion,
    refetch: fetchCompanies,
  };
}
