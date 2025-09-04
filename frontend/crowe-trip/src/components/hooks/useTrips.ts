import { useState, useEffect, useCallback } from "react";
import useAuth from "./use-auth";
import { Trip, Expense, Weather } from "./types";
import { getWeather } from "../../utils/web";
import { apiRequest } from "../../config/api";

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

    useEffect(() => {
        const fetchViajes = async () => {
            if (!token) return;
            try {
                const res = await apiRequest("/users/viajes/all/", {
                    method: "GET",
                    headers: {
                        Authorization: `Token ${token}`,
                    },
                });

                if (!res.ok) throw new Error("Error al obtener viajes.");

                const data = await res.json();
                setViajes(data);
            } catch (err) {
                setError((err as Error).message);
            } finally {
                setLoading(false);
            }
        };

        fetchViajes();
    }, [token]);

    useEffect(() => {
        const storedExpenses = JSON.parse(localStorage.getItem("tripExpenses") || "[]");
        setExpenses(storedExpenses);
    }, []);

    const fetchAndSetWeather = useCallback(async (city: string) => {
        const data = await getWeather(city);
        setWeather(data);
    }, []);

    const getViajeEnCurso = useCallback(async () => {
        console.log('🔧 [useTrips] getViajeEnCurso called');
        console.log('🔧 [useTrips] Token:', token);
        
        if (!token) {
            console.log('🔧 [useTrips] No token, returning null');
            return null;
        }
        
        try {
            console.log('🔧 [useTrips] Making request to /users/viajes/en-curso/');
            
            const res = await apiRequest("/users/viajes/en-curso/", {
                method: "GET",
                headers: {
                    Authorization: `Token ${token}`,
                },
            });
            
            console.log('🔧 [useTrips] Response status:', res.status);
            console.log('🔧 [useTrips] Response headers:', [...res.headers.entries()]);

            if (res.status === 204) {
                console.log('🔧 [useTrips] No viaje en curso (204)');
                setCurrentTrip(null);
                setWeather(null);
                return null;
            }

            if (!res.ok) {
                const errorText = await res.text();
                console.error('🔧 [useTrips] Response not OK:', errorText);
                throw new Error("Error al obtener el viaje en curso");
            }

            const viaje = await res.json();
            console.log('🔧 [useTrips] Viaje data received:', viaje);

            const formattedTrip: Trip = {
                id: viaje.id,
                city: viaje.destino.split(",")[0].trim(),
                country: viaje.destino.split(",")[1]?.trim() || "",
                days: viaje.dias_viajados?.toString() || "1",
                reason: viaje.motivo,
                startDate: viaje.fecha_inicio,
            };
            
            console.log('🔧 [useTrips] Formatted trip:', formattedTrip);

            setCurrentTrip(formattedTrip);
            fetchAndSetWeather(formattedTrip.city);
            return formattedTrip;
        } catch (err) {
            console.error("🔧 [useTrips] Error al cargar viaje en curso:", err);
            return null;
        }
    }, [token, fetchAndSetWeather]); // Depende del token y fetchAndSetWeather

    const finalizarViaje = async (viajeId: number) => {
        if (!token) return { error: "No autenticado" };
        try {
            const res = await apiRequest(`/users/viajes/${viajeId}/end/`, {
                method: "PUT",
                headers: {
                    Authorization: `Token ${token}`,
                },
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.error || "Error al finalizar el viaje.");
            }

            // Actualiza localmente el estado del viaje
            setViajes((prev) => prev.map(v => v.id === viajeId ? { ...v, estado: "FINALIZADO" } : v));
            return { success: true };
        } catch (err) {
            console.error("Error al finalizar el viaje:", err);
            return { error: (err as Error).message };
        }
    };

    const addExpense = (expense: Expense) => {
        const updatedExpenses = [...expenses, expense];
        setExpenses(updatedExpenses);
        localStorage.setItem("tripExpenses", JSON.stringify(updatedExpenses));
    };

    const crearViaje = async (viajeData: Omit<Viaje, "id" | "estado">) => {
        if (!token) return { error: "No autenticado" };
        try {
            const res = await apiRequest("/users/viajes/new/", {
                method: "POST",
                headers: {
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify(viajeData),
            });

            if (!res.ok) throw new Error("Error al crear el viaje.");

            const newViaje = await res.json();
            setViajes((prev) => [...prev, newViaje]);
            return { success: "Viaje programado con éxito" };
        } catch (err) {
            return { error: (err as Error).message };
        }
    };

    const cancelarViaje = async (viajeId: number) => { /* igual que antes */ };
    const iniciarViaje = async (viajeId: number) => { /* igual que antes */ };

    return {
        viajes,
        loading,
        error,
        currentTrip,
        setCurrentTrip,
        getViajeEnCurso,
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
