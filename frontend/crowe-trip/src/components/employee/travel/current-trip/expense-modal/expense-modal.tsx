import { useState, ReactElement } from "react";
import styles from "./expense-modal.module.scss";
import useSpends from "../../../../hooks/useSpends";
import { Expense } from "../../../../hooks/types";

/**
 * Esta versión del modal es un adaptador que mantiene la interfaz original
 * pero utiliza internamente la nueva implementación del hook useSpends
 */
interface Props {
    onClose: () => void;
    onSave: (expense: Omit<Expense, 'id' | 'date'>) => void;
    tripId?: number; // Nuevo parámetro para el ID del viaje
    onSuccess?: () => void; // Callback opcional después de guardar con éxito
}

export default function ExpenseModal({ onClose, onSave, tripId, onSuccess }: Props): ReactElement {
    const predefinedConcepts = ["Billete de avión", "Comida", "Taxi", "Otro..."];
    const [conceptSelection, setConceptSelection] = useState<string>(""); // valor del <select>
    const [customConcept, setCustomConcept] = useState<string>("");        // valor si selecciona "Otro..."
    const [amount, setAmount] = useState<string>("");
    const [receipt, setReceipt] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    
    // Usar el hook useSpends cuando tenemos un tripId
    const { crearGasto, loading } = useSpends(tripId);

    const handleSave = async () => {
        // Validación básica
        const finalConcept = conceptSelection === "Otro..." ? customConcept : conceptSelection;

        if (!finalConcept || !amount) {
            setError("Por favor, completa todos los campos obligatorios");
            return;
        }

        const parsedAmount = parseFloat(amount);
        if (isNaN(parsedAmount) || parsedAmount <= 0) {
            setError("El monto debe ser un número positivo");
            return;
        }

        const expenseData = {
            concept: finalConcept,
            amount: parsedAmount,
            receipt: receipt || undefined,
            viaje_id: tripId as number
        };

        try {
            // Si tenemos onSave (interfaz legacy), la usamos
            if (onSave) {
                onSave(expenseData);
                if (onSuccess) onSuccess();
                onClose();
            }
            // Si tenemos tripId, usamos el nuevo hook directamente
            else if (tripId) {
                const result = await crearGasto(expenseData);
                
                if (result.success) {
                    if (onSuccess) onSuccess();
                    onClose();
                } else {
                    setError(result.error || "Error al guardar el gasto");
                }
            } else {
                setError("No se puede guardar: no hay viaje seleccionado ni función de guardado");
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Error desconocido";
            setError(errorMessage);
        }
    };

    return (
        <div className={styles.modalBackdrop}>
            <div className={styles.modalContent}>
                <h3>Nuevo Gasto</h3>
                
                {error && <p className={styles.errorMessage}>{error}</p>}

                <select
                    name="conceptSelection"
                    value={conceptSelection}
                    onChange={(e) => {
                        setConceptSelection(e.target.value);
                        setError(null); // Limpiar error al modificar campos
                    }}
                    disabled={loading}
                >
                    <option value="">-- Selecciona un concepto --</option>
                    {predefinedConcepts.map((concept) => (
                        <option key={concept} value={concept}>
                            {concept}
                        </option>
                    ))}
                </select>

                {conceptSelection === "Otro..." && (
                    <input
                        type="text"
                        name="customConcept"
                        placeholder="Escribe el concepto"
                        value={customConcept}
                        onChange={(e) => {
                            setCustomConcept(e.target.value);
                            setError(null);
                        }}
                        disabled={loading}
                    />
                )}

                <input
                    type="number"
                    name="amount"
                    placeholder="Monto"
                    value={amount}
                    onChange={(e) => {
                        setAmount(e.target.value);
                        setError(null);
                    }}
                    disabled={loading}
                />

                <label className={styles.fileUpload}>
                    <input 
                        type="file" 
                        accept=".jpg,.png,.pdf" 
                        onChange={(e) => {
                            setReceipt(e.target.files?.[0] || null);
                            setError(null);
                        }} 
                        disabled={loading}
                    />
                    {receipt ? receipt.name : "Adjuntar justificante"}
                </label>

                <div className={styles.buttonGroup}>
                    <button 
                        className={styles.saveButton} 
                        onClick={handleSave}
                        disabled={loading}
                    >
                        {loading ? "Guardando..." : "Guardar gasto"}
                    </button>
                    
                    <button 
                        className={styles.closeButton} 
                        onClick={onClose}
                        disabled={loading}
                    >
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
    );
}