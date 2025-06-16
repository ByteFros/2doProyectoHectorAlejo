// hooks/useTripsPerMonth.ts
import { useState, useEffect } from 'react';
import useAuth from '../use-auth';
import { apiRequest } from '@config/api';

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
    apiRequest('/users/report/trips-per-month/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return { data, loading };
}
