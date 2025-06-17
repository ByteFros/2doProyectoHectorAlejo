// hooks/use-auth.ts
import { useEffect, useState } from "react";
import { useNavigate } from "@remix-run/react";
import { apiFetch } from "~/utils/api"; // Ajusta el path si es distinto

export type UserRole = "MASTER" | "EMPRESA" | "EMPLEADO" | null;

export default function useAuth() {
    const [role, setRole] = useState<UserRole>(null);
    const [username, setUsername] = useState<string | null>(null);
    const [userId, setUserId] = useState<number | null>(null);
    const [empresaId, setEmpresaId] = useState<number | null>(null);
    const [empleadoId, setEmpleadoId] = useState<number | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [mustChangePassword, setMustChangePassword] = useState(false);
    const [hasCheckedSession, setHasCheckedSession] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const savedToken = localStorage.getItem("token");
        if (!savedToken) {
            console.log("ℹ️ No hay token guardado, omitiendo verificación de sesión.");
            setHasCheckedSession(true);
            return;
        }

        const checkSession = async () => {
            try {
                const response = await apiFetch("/api/users/session/", {
                    method: "GET",
                }, true);

                if (response.ok) {
                    const data = await response.json();

                    setToken(data.token);
                    setUsername(data.username);
                    setRole(data.role);
                    setUserId(data.user_id);
                    setMustChangePassword(data.must_change_password || false);

                    localStorage.setItem("token", data.token);
                    localStorage.setItem("userId", data.user_id.toString());

                    if (data.empresa_id) {
                        setEmpresaId(data.empresa_id);
                        localStorage.setItem("empresaId", data.empresa_id.toString());
                    }

                    if (data.empleado_id) {
                        setEmpleadoId(data.empleado_id);
                        localStorage.setItem("empleadoId", data.empleado_id.toString());
                    }

                    console.log("✅ Sesión activa detectada:", data.username);
                } else {
                    console.log("ℹ️ Token inválido o expirado.");
                }
            } catch (err) {
                console.error("❌ Error al verificar sesión activa:", err);
            } finally {
                setHasCheckedSession(true);
            }
        };

        if (!hasCheckedSession) {
            checkSession();
        }
    }, [hasCheckedSession]);

    useEffect(() => {
        if (role && token) {
            const roleToPath: Record<string, string> = {
                MASTER: "/master",
                EMPRESA: "/company",
                EMPLEADO: "/employee",
            };

            const path = roleToPath[role];
            if (path && window.location.pathname !== path) {
                console.log("🔁 Redirigiendo automáticamente a:", path);
                navigate(path);
            }
        }
    }, [role, token, navigate]);

    const login = async (username: string, password: string) => {
        try {
            const response = await apiFetch("/api/users/login/", {
                method: "POST",
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) return false;

            const data = await response.json();

            if (data.token) {
                setToken(data.token);
                setUsername(username);
                setRole(data.role);
                setUserId(data.user_id);
                setMustChangePassword(!!data.must_change_password);

                localStorage.setItem("token", data.token);
                localStorage.setItem("userId", data.user_id.toString());

                if (data.role) {
                    document.cookie = `role=${data.role}; Path=/`;
                }

                if (data.empresa_id) {
                    setEmpresaId(data.empresa_id);
                    localStorage.setItem("empresaId", data.empresa_id.toString());
                }

                if (data.empleado_id) {
                    setEmpleadoId(data.empleado_id);
                    localStorage.setItem("empleadoId", data.empleado_id.toString());
                }

                return true;
            }

            return false;
        } catch (error) {
            console.error("❌ Error al hacer login:", error);
            return false;
        }
    };

    const logout = async () => {
        try {
            await apiFetch("/api/users/logout/", {
                method: "POST",
            }, true);
        } catch (error) {
            console.error("❌ Error al cerrar sesión:", error);
        } finally {
            document.cookie = "role=; Path=/; Max-Age=0";
            localStorage.removeItem("token");
            localStorage.removeItem("userId");
            localStorage.removeItem("empresaId");
            localStorage.removeItem("empleadoId");

            setToken(null);
            setRole(null);
            setUsername(null);
            setUserId(null);
            setEmpresaId(null);
            setEmpleadoId(null);
            setMustChangePassword(false);
            setHasCheckedSession(true);

            navigate("/");
        }
    };

    const changePassword = async (oldPassword: string, newPassword: string) => {
        if (!token) return { success: false, error: "No hay token." };

        try {
            const response = await apiFetch("/api/users/change-password/", {
                method: "PUT",
                body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
            }, true);

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