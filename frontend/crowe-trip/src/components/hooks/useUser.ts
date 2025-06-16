import { useEffect, useState } from "react";
import { apiRequest } from "@config/api";

interface User {
    username: string;
    role: "MASTER" | "EMPRESA" | "EMPLEADO";
    empresa_id?: number;
    must_change_password?: boolean;
    nombre?: string;
    apellido?: string;
}

export default function useUser() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                // 🔥 Obtener el token desde localStorage
                const token = localStorage.getItem("token");

                if (!token) {
                    throw new Error("No se encontró el token de autenticación");
                }

                const response = await apiRequest("/users/profile/", {
                    method: "GET",
                    headers: {
                        "Authorization": `Token ${token}`,
                    },
                });

                if (!response.ok) throw new Error("No se pudo obtener la información del usuario");

                const data = await response.json();
                setUser(data);
            } catch (err) {
                setError((err as Error).message);
            } finally {
                setLoading(false);
            }
        };

        fetchUserData();
    }, []);

    return { user, loading, error };
}
