// hooks/useFinalizeTripReview.ts
import { useState } from 'react';
import useAuth from '~/components/hooks/use-auth';

interface TripDayUpdate {
    id: number;
    exento: boolean;
}

interface FinalizeResult {
    success: boolean;
    message: string;
}

export default function useFinalizeTripReview() {
    const { token } = useAuth(); // ✅ usamos el hook de autenticación
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
            return { success: false, message: "No autenticado" };
        }

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/users/viajes/${viajeId}/finalizar_revision/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify({ motivo, dias }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Error inesperado del servidor');
                return { success: false, message: data.error || 'Error' };
            }

            return { success: true, message: data.message || 'Revisión finalizada' };
        } catch (err: any) {
            setError(err.message || 'Error de red');
            return { success: false, message: err.message };
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
