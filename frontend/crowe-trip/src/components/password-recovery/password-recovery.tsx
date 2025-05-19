import { useState } from "react";
import styles from "./password-recovery.module.scss";

interface PasswordRecoveryProps {
    onBack: () => void;
}

export default function PasswordRecovery({ onBack }: PasswordRecoveryProps) {
    const [email, setEmail] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage("");
        setError("");
        setLoading(true);

        try {
            const response = await fetch("http://localhost:8000/api/users/password-reset-request/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Error al enviar el correo de recuperación");
            }

            setMessage("📩 Se ha enviado un enlace de recuperación a tu correo.");
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <p className={styles.subtitle}>
                Introduce tu correo para restablecer tu contraseña.
            </p>

            {message ? (
                <p className={styles.successMessage}>{message}</p>
            ) : (
                <form className={styles.form} onSubmit={handleSubmit}>
                    <input
                        type="email"
                        placeholder="Correo Electrónico"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className={styles.input}
                        required
                    />
                    <button type="submit" className={styles.button} disabled={loading}>
                        {loading ? "Enviando..." : "Enviar Enlace"}
                    </button>
                    {error && <p className={styles.errorMessage}>{error}</p>}
                </form>
            )}

            <button className={styles.link} onClick={onBack}>
                ← Volver al inicio de sesión
            </button>
        </div>
    );
}