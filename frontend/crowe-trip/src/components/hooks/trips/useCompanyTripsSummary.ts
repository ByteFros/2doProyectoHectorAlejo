2// hooks/useCompanyTripsSummary.ts
import { useState, useEffect } from "react";
import useAuth from "../use-auth";

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
    fetch("http://127.0.0.1:8000/api/users/report/viajes/", {
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
