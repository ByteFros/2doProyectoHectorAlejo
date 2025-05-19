import { useState, useEffect } from "react";
import { Trip, Expense, Weather } from "./types";
import { getWeather } from "../../utils/web";

// 🔹 Hook para gestionar el viaje en curso
export const useCurrentTrip = () => {
    const [currentTrip, setCurrentTrip] = useState<Trip | null>(null);

    useEffect(() => {
        let storedTrips = JSON.parse(localStorage.getItem("proximosViajes") || "[]");

        // Si no hay viajes, cargamos uno de prueba
        if (storedTrips.length === 0) {
            const todayStr = new Date().toISOString(); // fecha en formato estándar
            const testTrip: Trip = {
                id: 1,
                city: "Madrid",
                country: "España",
                days: "3",
                reason: "Viaje de prueba",
                startDate: todayStr,
            };
            storedTrips = [testTrip];
            localStorage.setItem("proximosViajes", JSON.stringify(storedTrips));
        }

        // Intentamos encontrar el viaje activo
        const today = new Date();
        const activeTrip = storedTrips.find((trip: any) => {
            return trip.startDate && new Date(trip.startDate) <= today;
        });

        if (activeTrip) setCurrentTrip(activeTrip);
    }, []);


    return { currentTrip, setCurrentTrip };
};

// 🔹 Hook para gestionar los gastos del viaje
export const useExpenses = () => {
    const [expenses, setExpenses] = useState<Expense[]>([]);

    useEffect(() => {
        const storedExpenses = JSON.parse(localStorage.getItem("tripExpenses") || "[]");
        setExpenses(storedExpenses);
    }, []);

    const addExpense = (expense: Expense) => {
        const updatedExpenses = [...expenses, expense];
        setExpenses(updatedExpenses);
        localStorage.setItem("tripExpenses", JSON.stringify(updatedExpenses));
    };

    return { expenses, setExpenses, addExpense };
};

// 🔹 Hook para obtener la información del clima
export const useWeather = (city: string) => {
    const [weather, setWeather] = useState<Weather | null>(null);

    useEffect(() => {
        if (city) {
            getWeather(city).then((data) => setWeather(data));
        }
    }, [city]);

    return weather;
};
