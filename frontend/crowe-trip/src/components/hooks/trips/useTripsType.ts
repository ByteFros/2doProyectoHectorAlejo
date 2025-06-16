// hooks/useTripsType.ts
import { useState, useEffect } from 'react';
import useAuth from '../use-auth';
import { apiRequest } from '@config/api';

interface TripsType {
  national: number;
  international: number;
}

export default function useTripsType() {
  const { token } = useAuth();
  const [data, setData] = useState<TripsType>({ national: 0, international: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    apiRequest('/users/report/trips-type/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => res.json())
      .then((json: TripsType) => setData(json))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return { data, loading };
}
