// hooks/useGeneralInfo.ts
import { useState, useEffect } from 'react';
import { apiFetch } from '~/utils/api'; // Ajusta el path si es necesario
import useAuth from '../use-auth';

interface GeneralInfo {
  companies: number;
  employees: number;
  international_trips: number;
  national_trips: number;
}

export default function useGeneralInfo() {
  const { token } = useAuth();
  const [data, setData] = useState<GeneralInfo>({
    companies: 0,
    employees: 0,
    international_trips: 0,
    national_trips: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      try {
        const response = await apiFetch('/api/users/report/general-info/', {}, true);
        if (!response.ok) throw new Error('Error al obtener la información general');
        const result: GeneralInfo = await response.json();
        setData(result);
      } catch (error) {
        console.error('❌ Error al cargar información general:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  return { data, loading };
}
