import { useState } from "react";
import { FaKey, FaTimes, FaEye, FaEyeSlash } from "react-icons/fa"; // 🔹 Importamos los iconos
import styles from "./change-password.module.scss";
import useAuth from "../../hooks/use-auth";

interface ChangePasswordModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function ChangePasswordModal({ isOpen, onClose }: ChangePasswordModalProps) {
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false); // ✅ Un solo estado para todas las contraseñas
    const { changePassword } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (newPassword !== confirmPassword) {
            alert("Las contraseñas no coinciden");
            return;
        }

        const result = await changePassword(currentPassword, newPassword);

        if (!result.success) {
            alert(result.error);
            return;
        }

        alert(result.message || "Contraseña cambiada con éxito.");
        onClose();
    };

    if (!isOpen) return null;
    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modal}>
                <button className={styles.closeButton} onClick={onClose}>
                    <FaTimes />
                </button>
                <h2 className={styles.title}><FaKey /></h2>
                <form className={styles.form} onSubmit={handleSubmit}>

                    {/* Contraseña actual */}
                    <label>Contraseña actual:</label>
                    <input
                        type={showPassword ? "text" : "password"}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                    />

                    {/* Nueva contraseña */}
                    <label>Nueva contraseña:</label>
                    <input
                        type={showPassword ? "text" : "password"}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                    />

                    {/* Confirmar contraseña */}
                    <label>Confirmar contraseña:</label>
                    <input
                        type={showPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                    />

                    {/* Contenedor clickeable del icono + texto */}
                    <div
                        className={styles.toggleContainer}
                        onClick={() => setShowPassword(!showPassword)}
                    >
                        <span className={styles.eyeIcon}>
                            {showPassword ? <FaEyeSlash /> : <FaEye />}
                        </span>
                        <p>{showPassword ? "Ocultar contraseñas" : "Mostrar contraseñas"}</p> {/* ✅ Cambia dinámicamente */}
                    </div>

                    <button type="submit">Guardar Cambios</button>
                </form>
            </div>
        </div>
    );
}
