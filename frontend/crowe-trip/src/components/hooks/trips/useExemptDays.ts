// hooks/useExemptDays.ts

import { useState, useEffect } from 'react';
import useAuth from '../use-auth';
import { apiRequest } from '@config/api';

interface ExemptDays {
  exempt: number;
  nonExempt: number;
}

export default function useExemptDays() {
  const { token } = useAuth();
  const [data, setData] = useState<ExemptDays>({ exempt: 0, nonExempt: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    apiRequest('/users/report/exempt-days/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => res.json())
      .then((json: ExemptDays) => setData(json))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return { data, loading };
}
