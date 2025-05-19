import { useState, useEffect } from 'react';
import useAuth from '~/components/hooks/use-auth';

export default function usePendingTripsCount() {
  const { token } = useAuth();
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    fetch('http://127.0.0.1:8000/api/users/viajes/all/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Error al obtener viajes');
        return res.json();
      })
      .then((trips: any[]) => {
        // Cuenta sólo los que estén en revisión
        const total = trips.filter(t => t.estado === 'EN_REVISION').length;
        setCount(total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return { count, loading };
}
