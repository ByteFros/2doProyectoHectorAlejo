// hooks/useSpends.ts
import { useState, useEffect } from "react";
import useAuth from "./use-auth";

export interface Gasto {
  id: number;
  concepto: string;
  monto: number;
  estado: string;
  fecha_gasto: string;
  comprobante?: string;
  viaje?: {
    id: number;
    destino: string;
    fecha_inicio: string;
    fecha_fin: string;
    estado: string;
  };
}

export interface NuevoGasto {
  concepto: string;
  monto: number;
  viaje_id: number;
  comprobante?: File;
}

const API_BASE_URL = "http://127.0.0.1:8000/api";

export default function useSpends(currentTripId?: number) {
  const { token } = useAuth();
  const [gastos, setGastos] = useState<Gasto[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchGastos = async () => {
    if (!token) {
      setError("Se requiere autenticación");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/users/gastos/`, {
        method: "GET",
        headers: {
          "Authorization": `Token ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setGastos(data);

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      setError(message);
      console.error("Error al obtener gastos:", message);
    } finally {
      setLoading(false);
    }
  };

  const crearGasto = async (gastoData: {
    concept: string;
    amount: number;
    receipt?: File;
    viaje_id: number;
  }) => {
    if (!token) return { success: false, error: "No autenticado" };
    if (!gastoData.viaje_id) return { success: false, error: "Debes declarar el id del viaje" };

    if (!gastoData.concept.trim()) return { success: false, error: "El concepto es requerido" };
    if (isNaN(gastoData.amount) || gastoData.amount <= 0)
      return { success: false, error: "El monto debe ser un número positivo" };

    console.log("📦 Enviando gasto:", {
      concepto: gastoData.concept,
      monto: gastoData.amount,
      viaje_id: gastoData.viaje_id,
      comprobante: gastoData.receipt,
    });
    

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("concepto", gastoData.concept);
      formData.append("monto", gastoData.amount.toString());
      formData.append("viaje_id", gastoData.viaje_id.toString());
      if (gastoData.receipt) {
        formData.append("comprobante", gastoData.receipt);
      }

      const response = await fetch(`${API_BASE_URL}/users/gastos/new/`, {
        method: "POST",
        headers: {
          "Authorization": `Token ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Error ${response.status}`);
      }

      const nuevoGasto = await response.json();
      setGastos(prev => [...prev, nuevoGasto]);
      return { success: true, data: nuevoGasto };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      setError(message);
      console.error("Error al crear gasto:", message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchGastos();
  }, [token]);

  return {
    gastos,
    gastosViajeActual: currentTripId ? gastos.filter(g => g.viaje?.id === currentTripId) : [],
    loading,
    error,
    crearGasto,
    fetchGastos,
  };
}