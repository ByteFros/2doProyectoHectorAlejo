import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "@remix-run/react";
import styles from "./reset-password.module.scss";

export default function ResetPassword() {
    const location = useLocation();
    const navigate = useNavigate();
    const [newPassword, setNewPassword] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const token = new URLSearchParams(location.search).get("token");

    useEffect(() => {
        if (!token) {
            setError("Token no proporcionado. Asegúrate de usar el enlace del correo electrónico.");
        }
    }, [token]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setMessage("");

        try {
            const response = await fetch("http://localhost:8000/api/users/password-reset-confirm/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    token,
                    new_password: newPassword,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Error al restablecer contraseña");
            }

            setMessage("🔐 Tu contraseña ha sido restablecida con éxito.");
            setTimeout(() => navigate("/"), 3000);
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className={styles.pageContainer}>
            <div className={styles.container}>
                <h2 className={styles.title}>Restablecer Contraseña</h2>

                {message ? (
                    <p className={styles.successMessage}>{message}</p>
                ) : (
                    <form className={styles.form} onSubmit={handleSubmit}>
                        <input
                            type="password"
                            placeholder="Nueva Contraseña"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className={styles.input}
                            required
                        />
                        <button type="submit" className={styles.button} disabled={!token}>
                            Restablecer Contraseña
                        </button>
                        {error && <p className={styles.errorMessage}>{error}</p>}
                    </form>
                )}

                <button className={styles.link} onClick={() => navigate("/login")}>← Volver al inicio de sesión</button>
            </div>
        </div>
    );
}