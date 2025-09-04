import { useState, useEffect } from "react";
import { useNavigate } from "@remix-run/react";
import useAuth from "../hooks/use-auth";
import { FaEye, FaEyeSlash } from 'react-icons/fa';
import PasswordRecovery from '../password-recovery/password-recovery';
import styles from './login-form.module.scss';

export default function LoginForm() {
    const [showRecovery, setShowRecovery] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login, role } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const isLoggedIn = await login(username, password);

        if (!isLoggedIn) {
            setError("⚠️ Nombre de usuario o contraseña incorrectos.");
        }
    };

    // 🔄 Limpieza de cookies antiguas al montar el componente
    useEffect(() => {
        document.cookie = "role=; Path=/; Max-Age=0";
        document.cookie = "token=; Path=/; Max-Age=0";
    }, []);


    // Redireccionamiento manejado por use-auth hook

    return showRecovery ? (
        <PasswordRecovery onBack={() => setShowRecovery(false)} />
    ) : (
        <div className={styles.formContainer}>
            {error && <p className={styles.error}>{error}</p>} {/* ✅ Mensaje de error */}
            <form className={styles.form} onSubmit={handleSubmit}>
                <input
                    type="text"
                    placeholder="Nombre de usuario"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className={styles.input}
                    required
                />

                <div className={styles.passwordContainer}>
                    <input
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Contraseña"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className={styles.input}
                        required
                    />
                    <button
                        type="button"
                        className={styles.iconButton}
                        onClick={() => setShowPassword(!showPassword)}
                    >
                        {showPassword ? <FaEyeSlash /> : <FaEye />}
                    </button>
                </div>

                <button type="submit" className={styles.button}>
                    Iniciar sesión
                </button>
            </form>
            <button className={styles.link} onClick={() => setShowRecovery(true)}>
                ¿Olvidaste tu contraseña?
            </button>
        </div>
    );
}