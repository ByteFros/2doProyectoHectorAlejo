import { useState } from "react";
import styles from "./force-change-password.module.scss";
import { FaLock, FaEye, FaEyeSlash } from "react-icons/fa";
import useAuth from "../../hooks/use-auth";

interface ForceChangePasswordProps {
    onPasswordChange: () => void;
}

const capitalizeFullName = (fullName: string) =>
    fullName
        .split(" ")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(" ");

export default function ForceChangePassword({ onPasswordChange }: ForceChangePasswordProps) {
    const { username, changePassword } = useAuth();
    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [passwordError, setPasswordError] = useState("");
    const [confirmError, setConfirmError] = useState("");
    const [passwordStrength, setPasswordStrength] = useState<"débil" | "media" | "segura" | "">("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const errors: string[] = [];

        if (newPassword.length < 8) errors.push("al menos 8 caracteres");
        if (!/[A-Z]/.test(newPassword)) errors.push("una letra mayúscula");
        if (!/[a-z]/.test(newPassword)) errors.push("una letra minúscula");
        if (!/\d/.test(newPassword)) errors.push("un número");
        if (!/[^a-zA-Z0-9]/.test(newPassword)) errors.push("un símbolo");

        if (errors.length > 0) {
            setPasswordError(
                `Hola ${capitalizeFullName(safeUsername)}, tu contraseña debe contener ${errors.join(", ")}.`
            );
        } else {
            setPasswordError("");
        }

        if (newPassword !== confirmPassword) {
            setConfirmError(`Hola ${capitalizeFullName(safeUsername)}, las contraseñas no coinciden.`);
        } else {
            setConfirmError("");
        }

        const result = await changePassword(oldPassword, newPassword);

        if (!result.success) {
            alert(result.error || "Error al cambiar la contraseña.");
        } else {
            alert("Contraseña actualizada correctamente.");
            onPasswordChange();
        }
    };

    return (
        <div className={styles.forceChangePasswordOverlay}>
            <div className={styles.forceChangePasswordModal}>
                <div className={styles.forceChangePasswordLockContainer}>
                    <FaLock className={styles.forceChangePasswordLockIcon} />
                </div>

                <h2 className={styles.forceChangePasswordTitle}>Cambio de contraseña obligatorio</h2>
                <p className={styles.forceChangePasswordMessage}>
                    Hola <strong>{capitalizeFullName(safeUsername)}</strong>, debes cambiar tu contraseña antes de usar tu perfil.
                </p>

                <form onSubmit={handleSubmit}>
                    <label>Contraseña actual:</label>
                    <input
                        className={styles.forceChangePasswordInput}
                        type={showPassword ? "text" : "password"}
                        value={oldPassword}
                        onChange={(e) => setOldPassword(e.target.value)}
                        required
                    />

                    <label>Nueva contraseña:</label>
                    <input
                        className={styles.forceChangePasswordInput}
                        type={showPassword ? "text" : "password"}
                        value={newPassword}
                        onChange={(e) => handlePasswordChange(e.target.value)}
                        required
                    />
                    {passwordStrength && (
                        <div className={styles.passwordStrengthContainer}>
                            <div className={`${styles.passwordStrengthBar} ${styles[`bar-${passwordStrength}`]}`} />
                            <span className={styles.passwordStrengthLabel}>
                                Seguridad: {passwordStrength.charAt(0).toUpperCase() + passwordStrength.slice(1)}
                            </span>
                        </div>
                    )}
                    {passwordError && <p className={styles.forceChangePasswordError}>{passwordError}</p>}

                    <label>Confirmar contraseña:</label>
                    <input
                        className={`${styles.forceChangePasswordInput} ${confirmError ? styles.errorInput : ""}`}
                        type={showPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                    />
                    {confirmError && <p className={styles.forceChangePasswordError}>{confirmError}</p>}

                    <div
                        className={styles.forceChangePasswordToggleContainer}
                        onClick={() => setShowPassword(!showPassword)}
                    >
                        <span className={styles.forceChangePasswordEyeIcon}>
                            {showPassword ? <FaEyeSlash /> : <FaEye />}
                        </span>
                        <span className={styles.forceChangePasswordToggleText}>
                            {showPassword ? "Ocultar contraseñas" : "Mostrar contraseñas"}
                        </span>
                    </div>

                    <button className={styles.forceChangePasswordButton} type="submit">
                        Actualizar contraseña
                    </button>
                </form>
            </div>
        </div>
    );
}
