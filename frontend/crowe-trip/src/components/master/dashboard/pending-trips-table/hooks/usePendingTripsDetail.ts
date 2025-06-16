// hooks/usePendingTripsDetail.ts
import { useState, useEffect } from 'react';
import useAuth from '~/components/hooks/use-auth';
import { buildApiUrl } from '../../../../../config/api';

export interface PendingTrip {
  id: number;
  tripDates: [string, string];
  destination: string;
  info: string;
  notes: string[];
  companyVisited: string;
  employeeName: string;
  employeeId: number; // Añadido para facilitar el filtrado de empleados
}

export default function usePendingTripsDetail(employeeId?: number) {
  const { token } = useAuth();
  const [trips, setTrips] = useState<PendingTrip[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);

    const url = new URL(buildApiUrl('/users/viajes/pending/'));
    if (employeeId) url.searchParams.append('empleado', String(employeeId));

    fetch(url.toString(), {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Error al cargar viajes pendientes');
        return res.json();
      })
      .then(({ count, trips }: { count: number; trips: PendingTrip[] }) => {
        setCount(count);
        setTrips(trips);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, employeeId]);

  return { trips, count, loading };
}