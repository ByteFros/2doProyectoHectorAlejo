// hooks/usePendingCompanies.ts
import { useState, useEffect } from 'react';
import useAuth from '~/components/hooks/use-auth';

interface Company {
    id: number;
    nombre_empresa: string;
}

export default function usePendingCompanies() {
    const { token } = useAuth();
    const [data, setData] = useState<Company[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token) return;
        fetch('http://127.0.0.1:8000/api/users/report/companies/pending/', {
            headers: { Authorization: `Token ${token}` },
        })
            .then(res => res.json())
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [token]);

    return { data, loading };
}
