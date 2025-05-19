import { useEffect, useState } from "react";
import { useNavigate } from "@remix-run/react";

export type UserRole = "MASTER" | "EMPRESA" | "EMPLEADO" | null;

export default function useAuth() {
    const [role, setRole] = useState<UserRole>(null);
    const [username, setUsername] = useState<string | null>(null);
    const [userId, setUserId] = useState<number | null>(null);
    const [empresaId, setEmpresaId] = useState<number | null>(null);
    const [empleadoId, setEmpleadoId] = useState<number | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [mustChangePassword, setMustChangePassword] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const savedToken = localStorage.getItem("token");
        if (savedToken) setToken(savedToken);

        const cookies = document.cookie.split("; ");
        const roleCookie = cookies.find((row) => row.startsWith("role="));
        const savedRole = roleCookie ? (roleCookie.split("=")[1] as UserRole) : null;

        if (savedRole) {
            console.log("🟢 Role cargado desde cookie:", savedRole);
            setRole(savedRole);
        }

        const savedEmpresaId = localStorage.getItem("empresaId");
        if (savedEmpresaId) setEmpresaId(Number(savedEmpresaId));
        const savedEmpleadoId = localStorage.getItem("empleadoId");
        if (savedEmpleadoId) setEmpleadoId(Number(savedEmpleadoId));
    }, []);

    // Redirección según rol
    useEffect(() => {
        if (role && token) {
            const roleToPath: Record<string, string> = {
                MASTER: "/master",
                EMPRESA: "/company",
                EMPLEADO: "/employee",
            };
            const path = roleToPath[role];
            if (path && window.location.pathname !== path) {
                navigate(path);
            }
        }
    }, [role, token, navigate]);

    const login = async (username: string, password: string) => {
        try {
            const response = await fetch(
                "http://127.0.0.1:8000/api/users/login/",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password }),
                    credentials: "include",
                }
            );
            if (!response.ok) return false;
            const data = await response.json();

            // guarda todo en estado y storage
            if (data.token) {
                localStorage.setItem("token", data.token);
                setToken(data.token);
                setUsername(username);

                if (data.role) {
                    document.cookie = `role=${data.role}; Path=/`;
                    setRole(data.role);
                }

                if (data.user_id) {
                    setUserId(data.user_id);
                    localStorage.setItem("userId", data.user_id.toString());
                }
                if (data.empresa_id) {
                    setEmpresaId(data.empresa_id);
                    localStorage.setItem("empresaId", data.empresa_id.toString());
                }
                if (data.empleado_id) {
                    setEmpleadoId(data.empleado_id);
                    localStorage.setItem("empleadoId", data.empleado_id.toString());
                }

                setMustChangePassword(!!data.must_change_password);
                return true;
            }
            return false;
        } catch (error) {
            console.error("Error al hacer login:", error);
            return false;
        }
    };

    const logout = async () => {
        try {
            await fetch("http://127.0.0.1:8000/api/users/logout/", {
                method: "POST",
                headers: {
                    Authorization: `Token ${token}`,
                    "Content-Type": "application/json",
                },
                credentials: "include",
            });
        } catch (error) {
            console.error("Error al cerrar sesión:", error);
        } finally {
            document.cookie = "role=; Path=/; Max-Age=0";
            localStorage.removeItem("token");
            setToken(null);
            setRole(null);
            setUsername(null);
            setMustChangePassword(false);
            navigate("/");
        }
    };

    const changePassword = async (oldPassword: string, newPassword: string) => {
        if (!token) return { success: false, error: "No hay token." };

        try {
            const response = await fetch("http://127.0.0.1:8000/api/users/change-password/", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
            });

            const data = await response.json();

            if (!response.ok)
                return { success: false, error: data.error || "Error." };

            setMustChangePassword(!!data.must_change_password);
            return { success: true, message: data.message };
        } catch {
            return { success: false, error: "Error de red." };
        }
    };

    const updatePasswordStatus = (newStatus: boolean) => setMustChangePassword(newStatus);

    return {
        role,
        username,
        token,
        mustChangePassword,
        empresaId,
        empleadoId,
        login,
        logout,
        changePassword,
        updatePasswordStatus,
    };
}