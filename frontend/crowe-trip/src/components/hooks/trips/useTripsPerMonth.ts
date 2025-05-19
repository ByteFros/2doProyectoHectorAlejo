// hooks/useTripsPerMonth.ts
import { useState, useEffect } from 'react';
import useAuth from '../use-auth';

interface MonthData {
  month: string;      // '2025-03'
  totalDays: number;
}

export default function useTripsPerMonth() {
  const { token } = useAuth();
  const [data, setData] = useState<MonthData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    fetch('http://127.0.0.1:8000/api/users/report/trips-per-month/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return { data, loading };
}
