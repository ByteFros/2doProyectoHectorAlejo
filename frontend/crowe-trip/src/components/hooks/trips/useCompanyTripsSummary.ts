// hooks/useCompanyTripsSummary.ts
import { useState, useEffect } from "react";
import useAuth from "../use-auth";
import { apiRequest } from '@config/api';

interface CompanySummary {
  empresa_id: number;
  empresa: string;
  trips: number;
  days: number;
  nonExemptDays: number;
}

export default function useCompanyTripsSummary() {
  const { token } = useAuth();
  const [data, setData] = useState<CompanySummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    apiRequest("/users/report/viajes/", {
      headers: {
        Authorization: `Token ${token}`,
      },
    })
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return { data, loading };
}
