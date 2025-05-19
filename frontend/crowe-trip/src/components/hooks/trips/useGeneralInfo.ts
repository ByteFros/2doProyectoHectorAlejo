// hooks/useGeneralInfo.ts
import { useState, useEffect } from 'react';
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
    fetch('http://127.0.0.1:8000/api/users/report/general-info/', {
      headers: { Authorization: `Token ${token}` },
    })
      .then(res => res.json())
      .then((json: GeneralInfo) => setData(json))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return { data, loading };
}
