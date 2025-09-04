import { useEffect, useState } from "react";
import { useNavigate } from "@remix-run/react";
import { apiRequest } from "../../config/api";

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

    // ✅ Verificar sesión activa si hay token en localStorage
    useEffect(() => {
        const savedToken = localStorage.getItem("token");
        if (!savedToken) {
            console.log("ℹ️ No hay token guardado, omitiendo verificación de sesión.");
            setHasCheckedSession(true);
            return;
        }

        const checkSession = async () => {
            try {
                const response = await apiRequest("/users/session/", {
                    method: "GET",
                    headers: {
                        Authorization: `Token ${savedToken}`,
                    },
                });

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
                setHasCheckedSession(true); // 💡 Muy importante
            }
        };

        if (!hasCheckedSession) {
            checkSession();
        }
    }, [hasCheckedSession]);

    // 🔁 Redirección automática según rol
    useEffect(() => {
        if (role && token && hasCheckedSession) {
            const roleToPath: Record<string, string> = {
                MASTER: "/master",
                EMPRESA: "/company",
                EMPLEADO: "/employee",
            };

            const path = roleToPath[role];
            const currentPath = window.location.pathname;
            
            // Solo redirigir si no estamos ya en la página correcta y no estamos en login
            if (path && currentPath !== path && (currentPath === "/" || currentPath === "/login")) {
                console.log("🔁 Redirigiendo automáticamente a:", path);
                navigate(path, { replace: true });
            }
        }
    }, [role, token, navigate, hasCheckedSession]);

    const login = async (username: string, password: string) => {
        try {
            const response = await apiRequest("/users/login/", {
                method: "POST",
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) return false;

            const data = await response.json();

            if (data.token) {
                // Actualizar todos los estados de una vez para evitar renders parciales
                setToken(data.token);
                setUsername(username);
                setRole(data.role);
                setUserId(data.user_id);
                setMustChangePassword(!!data.must_change_password);

                // Persistir datos inmediatamente
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

                console.log("✅ Login exitoso, datos establecidos:", { 
                    role: data.role, 
                    userId: data.user_id 
                });

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
            await apiRequest("/users/logout/", {
                method: "POST",
                headers: {
                    Authorization: `Token ${token}`,
                },
            });
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
            setHasCheckedSession(true); // ✅ Muy importante para evitar reinicio del ciclo

            navigate("/");
        }
    };

    const changePassword = async (oldPassword: string, newPassword: string) => {
        if (!token) return { success: false, error: "No hay token." };

        try {
            const response = await apiRequest("/users/change-password/", {
                method: "PUT",
                headers: {
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
