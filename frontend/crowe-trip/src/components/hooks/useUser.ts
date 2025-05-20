import { useEffect, useState } from "react";

interface User {
    username: string;
    role: "MASTER" | "EMPRESA" | "EMPLEADO";
    empresa_id?: number;
    must_change_password?: boolean;
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

                const response = await fetch("http://127.0.0.1:8000/api/users/profile/", {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Token ${token}`, // 🔥 Enviar el token en la cabecera
                    },
                    credentials: "include",
                    
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
