import { useState, useEffect } from "react";
import { useNavigate } from "@remix-run/react";
import { apiRequest } from "../../config/api";

export type UserRole = "MASTER" | "EMPRESA" | "EMPLEADO" | null;

interface SessionData {
    username: string;
    role: UserRole;
    token: string;
    user_id: number;
    empresa_id?: number;
    empleado_id?: number;
    must_change_password: boolean;
}

export default function useAuthUser() {
    const [user, setUser] = useState<SessionData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            setLoading(false);
            return;
        }

        const fetchUser = async () => {
            try {
                const response = await apiRequest("/users/session/", {
                    method: "GET",
                    headers: {
                        Authorization: `Token ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Sesión inválida");
                }

                const data = await response.json();
                setUser({
                    username: data.username,
                    role: data.role,
                    token: data.token,
                    user_id: data.user_id,
                    empresa_id: data.empresa_id,
                    empleado_id: data.empleado_id,
                    must_change_password: data.must_change_password || false,
                });

                localStorage.setItem("token", data.token);
                localStorage.setItem("userId", data.user_id.toString());
                if (data.empresa_id) localStorage.setItem("empresaId", data.empresa_id.toString());
                if (data.empleado_id) localStorage.setItem("empleadoId", data.empleado_id.toString());

            } catch (err) {
                console.error("❌ Error en sesión:", err);
                setError("Sesión inválida o expirada");
            } finally {
                setLoading(false);
            }
        };

        fetchUser();
    }, []);

    const login = async (username: string, password: string) => {
        try {
            const response = await apiRequest("/users/login/", {
                method: "POST",
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) return false;
            const data = await response.json();

            if (data.token) {
                setUser({
                    username,
                    role: data.role,
                    token: data.token,
                    user_id: data.user_id,
                    empresa_id: data.empresa_id,
                    empleado_id: data.empleado_id,
                    must_change_password: !!data.must_change_password,
                });

                localStorage.setItem("token", data.token);
                localStorage.setItem("userId", data.user_id.toString());
                if (data.empresa_id) localStorage.setItem("empresaId", data.empresa_id.toString());
                if (data.empleado_id) localStorage.setItem("empleadoId", data.empleado_id.toString());

                document.cookie = `role=${data.role}; Path=/`;
                return true;
            }

            return false;
        } catch (err) {
            console.error("❌ Error al hacer login:", err);
            return false;
        }
    };

    const logout = async () => {
        try {
            await apiRequest("/users/logout/", {
                method: "POST",
                headers: {
                    Authorization: `Token ${user?.token}`,
                },
            });
        } catch (err) {
            console.error("❌ Error al cerrar sesión:", err);
        } finally {
            document.cookie = "role=; Path=/; Max-Age=0";
            localStorage.clear();
            setUser(null);
            navigate("/");
        }
    };

    const changePassword = async (oldPassword: string, newPassword: string) => {
        if (!user?.token) return { success: false, error: "No hay token." };

        try {
            const response = await apiRequest("/users/change-password/", {
                method: "PUT",
                headers: {
                    Authorization: `Token ${user.token}`,
                },
                body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
            });

            const data = await response.json();
            if (!response.ok) return { success: false, error: data.error || "Error." };

            // Actualizamos el estado para reflejar que ya no debe cambiar la contraseña
            setUser(prev => prev ? { ...prev, must_change_password: false } : prev);

            return { success: true, message: data.message };
        } catch {
            return { success: false, error: "Error de red." };
        }
    };

    return {
        user,
        loading,
        error,
        login,
        logout,
        changePassword,
    };
}
