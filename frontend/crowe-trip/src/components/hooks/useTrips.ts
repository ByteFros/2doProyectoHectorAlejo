// hooks/useTrips.ts
import { useState, useEffect, useCallback } from "react";
import useAuth from "./use-auth";
import { apiFetch } from "~/utils/api"; // Ajusta si es necesario
import { Trip, Expense, Weather } from "./types";
import { getWeather } from "../../utils/web";

interface Viaje {
  id: number;
  destino: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: "PENDIENTE" | "EN_CURSO" | "FINALIZADO" | "CANCELADO";
  empresa_visitada?: string;
  motivo: string;
  dias_viajados?: number;
}

export default function useTrips() {
  const { token } = useAuth();
  const [viajes, setViajes] = useState<Viaje[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTrip, setCurrentTrip] = useState<Trip | null>(null);
  const [weather, setWeather] = useState<Weather | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [checkTripsInterval, setCheckTripsInterval] = useState<NodeJS.Timeout | null>(null);

  // Función para obtener clima (memoizada)
  const fetchAndSetWeather = useCallback(async (city: string) => {
    if (!city) return;
    
    try {
      const data = await getWeather(city);
      setWeather(data);
    } catch (err) {
      console.error("Error al obtener clima:", err);
    }
  }, []);

  // Obtener viaje en curso (memoizada)
  const getViajeEnCurso = useCallback(async () => {
    if (!token) return null;
    
    try {
      const res = await apiFetch("/api/users/viajes/en-curso/", {}, true);

      if (res.status === 204) {
        // Si no hay viaje en curso, limpiamos el estado
        if (currentTrip !== null) {
          setCurrentTrip(null);
          setWeather(null);
        }
        return null;
      }

      if (!res.ok) throw new Error("Error al obtener el viaje en curso");

      const viaje = await res.json();
      
      // Formatear el viaje según tu estructura
      const formattedTrip: Trip = {
        id: viaje.id,
        city: viaje.destino.split(",")[0].trim(),
        country: viaje.destino.split(",")[1]?.trim() || "",
        days: viaje.dias_viajados?.toString() || "1",
        reason: viaje.motivo,
        startDate: viaje.fecha_inicio,
      };

      // Solo actualizamos si hay cambios o si no había viaje antes
      if (!currentTrip || JSON.stringify(currentTrip) !== JSON.stringify(formattedTrip)) {
        console.log("✅ Viaje en curso encontrado:", formattedTrip.city);
        setCurrentTrip(formattedTrip);
        fetchAndSetWeather(formattedTrip.city);
      }
      
      return formattedTrip;
    } catch (err) {
      console.error("Error al cargar viaje en curso:", err);
      return null;
    }
  }, [token, currentTrip, fetchAndSetWeather]);

  // Cargar todos los viajes
  const fetchViajes = useCallback(async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      const res = await apiFetch("/api/users/viajes/all/", {}, true);
      if (!res.ok) throw new Error("Error al obtener viajes.");

      const data = await res.json();
      setViajes(data);
      setLoading(false);
    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  }, [token]);

  // Cargar datos iniciales al montar o cambiar token
  useEffect(() => {
    if (!token) return;

    // Cargar datos iniciales
    const initializeData = async () => {
      try {
        // Primero cargamos los viajes
        await fetchViajes();
        
        // Luego verificamos si hay un viaje en curso
        await getViajeEnCurso();
        
        // Cargar gastos del localStorage
        const storedExpenses = JSON.parse(localStorage.getItem("tripExpenses") || "[]");
        setExpenses(storedExpenses);
      } catch (err) {
        console.error("Error al inicializar datos:", err);
      }
    };

    initializeData();

    // Limpiar intervalos anteriores si existen
    if (checkTripsInterval) {
      clearInterval(checkTripsInterval);
    }

    // Configurar verificación periódica para viaje en curso
    const intervalId = setInterval(() => {
      console.log("🔄 Verificando si hay viaje en curso...");
      getViajeEnCurso();
    }, 3 * 60 * 1000); // cada 3 minutos
    
    setCheckTripsInterval(intervalId);
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [token, fetchViajes, getViajeEnCurso]);

  // Finalizar viaje
  const finalizarViaje = async (viajeId: number) => {
    if (!token) return { success: false, error: "No autenticado" };
    
    try {
      const res = await apiFetch(
        `/api/users/viajes/${viajeId}/end/`,
        { method: "PUT" },
        true
      );

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Error al finalizar el viaje.");
      }

      // Actualizar el estado de los viajes
      setViajes((prev) => prev.map(v => v.id === viajeId ? { ...v, estado: "FINALIZADO" } : v));
      
      // Si el viaje finalizado es el actual, actualizamos el estado
      if (currentTrip && currentTrip.id === viajeId) {
        setCurrentTrip(null);
        setWeather(null);
      }
      
      return { success: true };
    } catch (err) {
      console.error("Error al finalizar el viaje:", err);
      return { success: false, error: (err as Error).message };
    }
  };

  // Crear viaje
  const crearViaje = async (viajeData: Omit<Viaje, "id" | "estado">) => {
    if (!token) return { success: false, error: "No autenticado" };
    
    try {
      const res = await apiFetch(
        "/api/users/viajes/new/",
        {
          method: "POST",
          body: JSON.stringify(viajeData),
        },
        true
      );

      if (!res.ok) throw new Error("Error al crear el viaje.");

      const newViaje = await res.json();
      
      // Actualizamos la lista de viajes
      await fetchViajes();
      
      // Verificamos si el viaje creado debe iniciar hoy
      const today = new Date().toISOString().split('T')[0];
      if (viajeData.fecha_inicio === today) {
        await getViajeEnCurso();
      }
      
      return { success: true, message: "Viaje programado con éxito" };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  };

  // Cancelar viaje
  const cancelarViaje = async (viajeId: number) => {
    try {
      const res = await apiFetch(
        `/api/users/viajes/${viajeId}/cancel/`,
        { method: "PUT" },
        true
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Error al cancelar el viaje.");
      }

      // Actualizamos el estado de los viajes
      setViajes(prev => prev.map(v => v.id === viajeId ? { ...v, estado: "CANCELADO" } : v));
      
      // Si el viaje cancelado es el actual, actualizamos el estado
      if (currentTrip && currentTrip.id === viajeId) {
        setCurrentTrip(null);
        setWeather(null);
      }
      
      return { success: true };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  };

  // Iniciar viaje
  const iniciarViaje = async (viajeId: number) => {
    try {
      const res = await apiFetch(
        `/api/users/viajes/${viajeId}/start/`,
        { method: "PUT" },
        true
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Error al iniciar el viaje.");
      }

      // Actualizamos el estado de los viajes
      setViajes(prev => prev.map(v => v.id === viajeId ? { ...v, estado: "EN_CURSO" } : v));
      
      // Actualizamos el viaje en curso
      await getViajeEnCurso();
      
      return { success: true };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  };

  // Añadir gasto
  const addExpense = (expense: Expense) => {
    const updatedExpenses = [...expenses, expense];
    setExpenses(updatedExpenses);
    localStorage.setItem("tripExpenses", JSON.stringify(updatedExpenses));
  };

  // Función para forzar una actualización manualmente
  const refreshCurrentTrip = useCallback(async () => {
    console.log("🔄 Actualizando viaje manualmente...");
    return await getViajeEnCurso();
  }, [getViajeEnCurso]);

  return {
    viajes,
    loading,
    error,
    currentTrip,
    setCurrentTrip,
    getViajeEnCurso,
    refreshCurrentTrip, // Nueva función para actualizar manualmente
    crearViaje,
    cancelarViaje,
    iniciarViaje,
    finalizarViaje,
    weather,
    expenses,
    addExpense,
    setExpenses,
  };
}