// hooks/useFinalizeTripReview.ts
import { useState } from 'react';
import useAuth from '~/components/hooks/use-auth';
import { apiFetch } from '~/utils/api';

interface TripDayUpdate {
    id: number;
    exento: boolean;
}

interface FinalizeResult {
    success: boolean;
    message: string;
}

export default function useFinalizeTripReview() {
    const { token } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const finalizeReview = async (
        viajeId: number,
        dias: TripDayUpdate[],
        motivo: string
    ): Promise<FinalizeResult> => {
        setLoading(true);
        setError(null);

        if (!token) {
            setError("No hay token de autenticación.");
            setLoading(false);
            return { success: false, message: "No autenticado" };
        }

        try {
            const response = await apiFetch(`/api/users/viajes/${viajeId}/finalizar_revision/`, {
                method: 'POST',
                body: JSON.stringify({ motivo, dias }),
            }, true); // Indicamos que requiere autenticación

            const data = await response.json();

            if (!response.ok) {
                const errorMsg = data.error || 'Error inesperado del servidor';
                setError(errorMsg);
                return { success: false, message: errorMsg };
            }

            return { success: true, message: data.message || 'Revisión finalizada' };
        } catch (err: any) {
            const errorMsg = err.message || 'Error de red';
            setError(errorMsg);
            return { success: false, message: errorMsg };
        } finally {
            setLoading(false);
        }
    };

    return {
        finalizeReview,
        loading,
        error,
    };
}