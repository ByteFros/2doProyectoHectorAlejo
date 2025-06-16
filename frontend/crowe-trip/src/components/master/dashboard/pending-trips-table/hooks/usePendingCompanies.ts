// hooks/usePendingCompanies.ts
import { useState, useEffect } from 'react';
import useAuth from '~/components/hooks/use-auth';
import { apiRequest } from '../../../../../config/api';

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
        apiRequest('/users/report/companies/pending/', {
            headers: { Authorization: `Token ${token}` },
        })
            .then(res => res.json())
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [token]);

    return { data, loading };
}
