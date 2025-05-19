import { useEffect, useState } from "react";
import styles from "./current-trip.module.scss";
import ExpenseModal from "./expense-modal/expense-modal";
import ExpensesTable from "./expenses-table/expenses-table";
import NotesSection from "./notes-section/notes-section";
import WeatherCard from "./weather-card/weather-card";
import ConfirmModal from "../../../common/confirm-modal/confirm-modal";
import useTrips from "../../../hooks/useTrips";
import useSpends from "../../../hooks/useSpends";
import useAuth from "../../../hooks/use-auth";
import { useWeather } from "../../../hooks/useCurrentTrip";
import { Expense } from "~/components/hooks/types";

export default function CurrentTrip() {
    const { token } = useAuth();
    const {
        currentTrip,
        setCurrentTrip,
        getViajeEnCurso,
        finalizarViaje,
    } = useTrips();

    const [isLoading, setIsLoading] = useState(true);
    const [showExpenseModal, setShowExpenseModal] = useState(false);
    const [showConfirmModal, setShowConfirmModal] = useState(false);

    // Hook de clima
    const weather = useWeather(currentTrip?.city || "");

    // Hook de gastos actualizado
    const {
        gastosViajeActual,
        loading: loadingGastos,
        error: gastosError,
        crearGasto,
        fetchGastos
    } = useSpends(currentTrip?.id);

    // Cargar viaje actual
    useEffect(() => {
        const loadCurrentTrip = async () => {
            if (token) {
                setIsLoading(true);
                await getViajeEnCurso();
                setIsLoading(false);
            }
        };
        loadCurrentTrip();
    }, [token]);

    // Finalizar viaje
    const handleEndTrip = async () => {
        if (currentTrip?.id) {
            const result = await finalizarViaje(currentTrip.id);
            if (result.success) {
                setCurrentTrip(null);
            } else {
                alert(`Error al finalizar el viaje: ${result.error}`);
            }
        }
    };

    // Guardar nuevo gasto - adaptado al hook actualizado
    const handleSaveExpense = async (expense: {
        concept: string;
        amount: number;
        receipt?: File;
    }) => {
        if (!currentTrip?.id) {
            alert("No hay un viaje activo");
            return;
        }

        const result = await crearGasto({
            ...expense,
            viaje_id: currentTrip.id, // 👈 fuerza explícitamente
        });

        if (result.success) {
            await fetchGastos();
            setShowExpenseModal(false);
        } else {
            alert(`Error al guardar el gasto: ${result.error}`);
        }
    };


    // Estados de carga y error
    if (isLoading) return <p className={styles.noTrip}>Cargando viaje...</p>;
    if (!currentTrip) return <p className={styles.noTrip}>No hay un viaje activo actualmente.</p>;
    if (loadingGastos) return <p className={styles.noTrip}>Cargando gastos...</p>;
    if (gastosError) return <p className={styles.error}>Error al cargar gastos: {gastosError}</p>;

    return (
        <div className={styles.currentTrip}>
            <div className={styles.tripDetails}>
                <div className={styles.tripInfo}>
                    <p><strong>Destino:</strong> {currentTrip.city}, {currentTrip.country}</p>
                    <p><strong>Duración:</strong> {currentTrip.days} días</p>
                    <p><strong>Motivo:</strong> {currentTrip.reason}</p>
                </div>

                <div className={styles.tripButtons}>
                    <button
                        className={styles.expenseButton}
                        onClick={() => setShowExpenseModal(true)}
                    >
                        Cargar gasto
                    </button>
                </div>

                <div className={styles.endTripContainer}>
                    <button
                        className={styles.endTripButton}
                        onClick={() => setShowConfirmModal(true)} // Mostrar modal
                    >
                        Finalizar viaje
                    </button>
                </div>
            </div>

            <div className={styles.tripSections}>
                <NotesSection tripId= {currentTrip.id} />
                {weather && <WeatherCard weather={weather} />}
            </div>

            {/* Actualizado para usar la nueva interfaz del modal */}
            {showExpenseModal && (
                <ExpenseModal
                    onClose={() => setShowExpenseModal(false)}
                    onSave={handleSaveExpense}
                />
            )}

            {/* Mostramos los gastos desde el hook actualizado */}
            <ExpensesTable expenses={gastosViajeActual} />

            {showConfirmModal && (
                <ConfirmModal
                    message="¿Deseás finalizar este viaje? Se guardarán todos los gastos cargados y no podrás hacer más cambios."
                    onConfirm={() => {
                        handleEndTrip();
                        setShowConfirmModal(false);
                    }}
                    onCancel={() => setShowConfirmModal(false)}
                />
            )}
        </div>
    );
}