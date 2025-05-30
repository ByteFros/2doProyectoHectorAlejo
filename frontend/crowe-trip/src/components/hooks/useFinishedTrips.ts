// hooks/useFinishedTrips.ts
import { useEffect, useState } from 'react';
import useAuth from './use-auth';

export interface FinishedTrip {
  id: number;
  destino: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: string;
  motivo: string;
  dias_viajados: number;
  empresa_visitada?: string;
  empleado?: any; // puedes tipar esto luego si el serializer lo incluye
}

export default function useFinishedTrips() {
  const { token } = useAuth();
  const [trips, setTrips] = useState<FinishedTrip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    const fetchTrips = async () => {
      setLoading(true);
      try {
        const res = await fetch('http://127.0.0.1:8000/api/users/viajes/over/', {
          headers: {
            Authorization: `Token ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!res.ok) throw new Error('Error al cargar viajes finalizados');

        const data = await res.json();
        setTrips(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTrips();
  }, [token]);

  return { trips, loading, error };
}
