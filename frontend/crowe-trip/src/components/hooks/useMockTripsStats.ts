import { useMemo } from "react";

const useMockTripsStats = () => {
    // 🔹 Datos mock de viajes
    const trips = useMemo(() => [
        { tipo: "nacional", exento: true, empleado: "Carlos" },
        { tipo: "internacional", exento: false, empleado: "Ana" },
        { tipo: "nacional", exento: true, empleado: "Carlos" },
        { tipo: "nacional", exento: false, empleado: "Juan" },
        { tipo: "internacional", exento: false, empleado: "Ana" },
        { tipo: "nacional", exento: true, empleado: "Lucía" },
        { tipo: "internacional", exento: true, empleado: "Pedro" },
        { tipo: "nacional", exento: false, empleado: "Carlos" },
        { tipo: "internacional", exento: true, empleado: "Lucía" },
    ], []);

    const stats = useMemo(() => {
        const nacionales = trips.filter(t => t.tipo === "nacional").length;
        const internacionales = trips.filter(t => t.tipo === "internacional").length;
        const exentos = trips.filter(t => t.exento).length;
        const noExentos = trips.filter(t => !t.exento).length;

        // 🔹 Obtener empleados únicos
        const empleadosUnicos = new Set(trips.map(t => t.empleado));
        const totalEmpleados = empleadosUnicos.size;

        return {
            nacionales,
            internacionales,
            exentos,
            noExentos,
            totalEmpleados, // ✅ ahora sí
        };
    }, [trips]);

    return stats;
};

export default useMockTripsStats;
