// hooks/usePendingTripsByEmployee.ts
import { useState, useEffect } from 'react';
import useAuth from '~/components/hooks/use-auth';

interface RawTrip {
  id: number;
  empleado: { id: number };
  estado: string;
  fecha_inicio: string;
  fecha_fin: string;
  destino: string;
  motivo: string;
  notas: { id: number; contenido: string; fecha_creacion: string }[];
  // ...otros campos que no nos interesan aquí
}

export interface PendingTrip {
  id: number;
  tripDates: [string, string];
  destination: string;
  info: string;
  notes: string[];  // por ahora vacío
}

export default function usePendingTripsByEmployee(employeeId?: number) {
  const { token } = useAuth();
  const [data, setData] = useState<PendingTrip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || !employeeId) return;

    fetch('http://127.0.0.1:8000/api/users/viajes/all/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Error al obtener viajes');
        return res.json();
      })
      .then((trips: RawTrip[]) => {
        const filtered: PendingTrip[] = trips
          .filter(t => t.empleado.id === employeeId && t.estado === 'EN_REVISION')
          .map<PendingTrip>(t => ({
            id: t.id,
            tripDates: [t.fecha_inicio, t.fecha_fin],
            destination: t.destino,
            info: t.motivo,
            notes: t.notas.map(n=>n.contenido),  // o bien haz aquí otro fetch a /viajes/{id}/notas/
          }));
        setData(filtered);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, employeeId]);

  return { data, loading };
}
