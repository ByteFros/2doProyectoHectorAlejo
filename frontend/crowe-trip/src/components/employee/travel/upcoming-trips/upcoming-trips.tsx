import styles from "../travel.module.scss";
import useTrips from "../../../hooks/useTrips";

export default function UpcomingTrips() {
    const { viajes, loading, error, cancelarViaje } = useTrips();

    if (loading) return <p>Cargando viajes...</p>;
    if (error) return <p>Error: {error}</p>;

    const handleCancel = async (viajeId: number) => {
        const confirmCancel = window.confirm("¿Estás seguro de que deseas cancelar este viaje?");
        if (confirmCancel) {
            await cancelarViaje(viajeId);
        }
    };

    return (
        <div className={styles.upcomingTrips}>
            <h2 className={styles.title}>Próximos Viajes</h2>
            {viajes.length > 0 ? (
                <div className={styles.tripList}>
                    {viajes.map((trip, index) => (
                        <div key={index} className={styles.tripCard}>
                            <div className={styles.tripHeader}>
                                <h3>{trip.destino}</h3>
                                <span className={`${styles.status} ${styles[trip.estado.toLowerCase()]}`}>
                                    {trip.estado}
                                </span>
                            </div>
                            <p><strong>📅 Fechas:</strong> {trip.fecha_inicio} - {trip.fecha_fin}</p>
                            <p><strong>🏢 Empresa Visitada:</strong> {trip.empresa_visitada || 'No especificada'}</p>
                            <p><strong>✈️ Motivo:</strong> {trip.motivo}</p>
                            {trip.estado === "PENDIENTE" && (
                                <button className={styles.cancelButton} onClick={() => handleCancel(trip.id)}>
                                    Cancelar Viaje
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <p className={styles.noTrips}>No hay próximos viajes programados.</p>
            )}
        </div>
    );
}
