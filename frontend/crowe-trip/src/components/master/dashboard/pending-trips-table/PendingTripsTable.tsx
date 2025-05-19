import { useState, useEffect } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import styles from './pending-trips-table.module.scss';

// Hooks para obtener datos del servidor
import usePendingCompanies from './hooks/usePendingCompanies';
import useEmployeesByCompany from './hooks/useEmployeesByCompany';
import usePendingTripsDetail from './hooks/usePendingTripsDetail';
import useFinalizeTripReview from './hooks/useFinalizeTripReview';
import useExemptDays from '~/components/hooks/trips/useExemptDays';
import useTripDays, { TripDay } from './hooks/useTripDays';
import useUpdateTripDay from './hooks/useUpdateTripDay';
import useMasterCSVExport from './hooks/useMasterCSVExport';
import { areSameDay } from './utils/dateUtils';

const PendingTripsTable = () => {
    // Estado para los datos obtenidos del servidor
    const { data: pendingCompanies = [], loading: loadingCompanies } = usePendingCompanies();
    const { data: exemptData, loading: loadingExempt } = useExemptDays();
    // Unificamos count + listado de viajes en revisión (sin filtro)
    const { count: totalPendingTrips, loading: loadingGlobalTrips } = usePendingTripsDetail();

    const { finalizeReview, loading: finalizingReview, error: finalizeError } = useFinalizeTripReview();

    const { exportCSV } = useMasterCSVExport();

    // Estado para la UI
    const [showCompanyNames, setShowCompanyNames] = useState(false);
    const [confirmedTrips, setConfirmedTrips] = useState<any[]>([]);
    const [selectedCompany, setSelectedCompany] = useState<any>(null);
    const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
    const [selectedTrip, setSelectedTrip] = useState<any>(null);
    const [calendarDate, setCalendarDate] = useState<Date>(new Date());
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);
    const [savingDays, setSavingDays] = useState(false);
    const [dayChangeSuccess, setDayChangeSuccess] = useState<string | null>(null);
    const [dayChangeError, setDayChangeError] = useState<string | null>(null);
    // Estado para el motivo de no exención
    const [nonExemptReason, setNonExemptReason] = useState('');
    const [showReasonError, setShowReasonError] = useState(false);

    // Estado para almacenar los días del viaje actual
    const [originalTripDays, setOriginalTripDays] = useState<TripDay[]>([]);
    // Estado para almacenar los cambios temporales antes de confirmar
    const [temporaryTripDays, setTemporaryTripDays] = useState<TripDay[]>([]);
    // Flag para indicar si hay cambios sin guardar
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    // Indicador de al menos un día revisado manualmente
    const [hasReviewedAny, setHasReviewedAny] = useState(false);

    // Obtener empleados de la empresa seleccionada
    const { data: employees = [], loading: loadingEmployees } =
        useEmployeesByCompany(selectedCompany?.id);

    // Cuando haya empleado seleccionado usamos el mismo hook con filtro
    const { trips: pendingTrips = [], loading: loadingEmployeeTrips } =
        usePendingTripsDetail(selectedEmployee?.id);

    // Obtener días de viaje cuando se selecciona un viaje
    const { data: tripDays = [], loading: loadingTripDays } =
        useTripDays(selectedTrip?.id);

    // Hook para actualizar estado de exención de un día
    const { updateDay, loading: updatingDay } = useUpdateTripDay();

    // Efecto para actualizar originalTripDays y temporaryTripDays cuando se cargan los días del viaje
    useEffect(() => {
        if (tripDays.length > 0 && selectedTrip) {
            // Crear copias profundas para evitar referencias mutables
            setOriginalTripDays([...tripDays]);
            setTemporaryTripDays([...tripDays]);

            // Establecer el calendario a la fecha de inicio del viaje
            if (tripDays.length > 0) {
                setCalendarDate(new Date(tripDays[0].fecha));
            }

            // Reiniciar flags
            setHasUnsavedChanges(false);
            setHasReviewedAny(false);
        }
    }, [tripDays, selectedTrip]);

    // Limpiar mensajes de éxito/error después de 3 segundos
    useEffect(() => {
        if (dayChangeSuccess || dayChangeError) {
            const timer = setTimeout(() => {
                setDayChangeSuccess(null);
                setDayChangeError(null);
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [dayChangeSuccess, dayChangeError]);

    // Manejadores de eventos
    const handleCompanyClick = (company: any) => {
        // Advertir si hay cambios sin guardar
        if (hasUnsavedChanges && !window.confirm("Hay cambios sin guardar. ¿Deseas descartarlos?")) {
            return;
        }

        setSelectedCompany(company);
        setSelectedEmployee(null);
        setSelectedTrip(null);
        setTemporaryTripDays([]);
        setOriginalTripDays([]);
        setHasUnsavedChanges(false);
        setHasReviewedAny(false);
        setNonExemptReason('');
    };

    const handleEmployeeClick = (employee: any) => {
        // Advertir si hay cambios sin guardar
        if (hasUnsavedChanges && !window.confirm("Hay cambios sin guardar. ¿Deseas descartarlos?")) {
            return;
        }

        setSelectedEmployee(employee);
        setSelectedTrip(null);
        setTemporaryTripDays([]);
        setOriginalTripDays([]);
        setHasUnsavedChanges(false);
        setHasReviewedAny(false);
        setNonExemptReason('');
    };

    const handleTripClick = (trip: any) => {
        // Advertir si hay cambios sin guardar
        if (hasUnsavedChanges && !window.confirm("Hay cambios sin guardar. ¿Deseas descartarlos?")) {
            return;
        }

        setSelectedTrip(trip);
        setTemporaryTripDays([]);
        setOriginalTripDays([]);

        // Establecer la fecha inicial del calendario
        if (trip.fecha_inicio) {
            setCalendarDate(new Date(trip.fecha_inicio));
        } else if (trip.tripDates && Array.isArray(trip.tripDates) && trip.tripDates.length > 0) {
            // Compatibilidad con el formato anterior
            setCalendarDate(new Date(trip.tripDates[0]));
        }

        // Limpiar mensajes de estado
        setDayChangeSuccess(null);
        setDayChangeError(null);
        setHasUnsavedChanges(false);
        setHasReviewedAny(false);
        setNonExemptReason('');
        setShowReasonError(false);
    };

    const handleDateClick = (date: Date) => {
        if (!selectedTrip) return;

        // Busca el día en temporaryTripDays
        const tripDayIndex = temporaryTripDays.findIndex(d =>
            areSameDay(date, new Date(d.fecha))
        );

        if (tripDayIndex === -1) {
            setDayChangeError("Este día no pertenece al viaje seleccionado");
            return;
        }

        // Crear una copia para modificar
        const updatedTripDays = [...temporaryTripDays];

        // Invertir el estado de exención (sin actualizar el servidor todavía)
        updatedTripDays[tripDayIndex] = {
            ...updatedTripDays[tripDayIndex],
            exento: !updatedTripDays[tripDayIndex].exento,
            // Marcamos como revisado
            revisado: true
        };

        // Actualizar el estado temporal
        setTemporaryTripDays(updatedTripDays);
        setHasUnsavedChanges(true);
        setHasReviewedAny(true);
    };

    // Función para guardar todos los cambios en el servidor
    const saveAllChanges = async () => {
        if (!selectedTrip || !selectedTrip.id) return;

        const diasParaEnviar = temporaryTripDays.map(day => ({
            id: day.id,
            exento: day.exento,
        }));

        const nonExemptDaysCount = diasParaEnviar.filter(day => !day.exento).length;

        // Validar motivo obligatorio si hay días no exentos
        if (nonExemptDaysCount > 0 && !nonExemptReason.trim()) {
            setShowReasonError(true);
            return;
        }

        setSavingDays(true);
        setDayChangeError(null);
        setDayChangeSuccess(null);

        try {
            const result = await finalizeReview(
                selectedTrip.id,
                diasParaEnviar,
                nonExemptReason.trim()
            );

            if (result.success) {
                const extraMessage = nonExemptDaysCount > 0 ? 'Se ha iniciado una conversacion' : '';
                // Añadir a lista confirmada
                setConfirmedTrips([
                    ...confirmedTrips,
                    {
                        employee: `${selectedEmployee.nombre} ${selectedEmployee.apellido}`,
                        destination: selectedTrip.destination || selectedTrip.destino,
                        exemptDays: diasParaEnviar.filter(day => day.exento).length,
                        nonExemptDays: diasParaEnviar.filter(day => !day.exento).length,
                        reason: nonExemptReason.trim(),
                    }
                ]);

                setDayChangeSuccess(result.message + extraMessage);
                // Limpiar estado
                setSelectedTrip(null);
                setTemporaryTripDays([]);
                setOriginalTripDays([]);
                setHasUnsavedChanges(false);
                setHasReviewedAny(false);
                setNonExemptReason('');
                setShowReasonError(false);
            } else {
                setDayChangeError(`Error al guardar: ${result.message}`);
            }
        } catch (err: any) {
            setDayChangeError(`Error inesperado: ${err.message}`);
        } finally {
            setSavingDays(false);
            setIsConfirmOpen(false);
        }
    };


    const handleAcceptConfirmed = () => {
        if (!selectedTrip || !selectedTrip.id) return;
        saveAllChanges();
    };

    const handleCancel = () => {
        // Descartar cambios temporales y volver a los originales
        if (hasUnsavedChanges) {
            if (window.confirm("¿Estás seguro de descartar los cambios realizados?")) {
                setTemporaryTripDays([...originalTripDays]);
                setHasUnsavedChanges(false);
                setHasReviewedAny(false);
                setDayChangeSuccess("Cambios descartados");
            }
        } else {
            // Si no hay cambios, simplemente cerrar la selección
            setSelectedTrip(null);
            setTemporaryTripDays([]);
            setOriginalTripDays([]);
            setNonExemptReason('');
        }
    };

    // Calculamos los días exentos y no exentos basándonos en temporaryTripDays
    const exemptDaysCount = temporaryTripDays.filter(day => day.exento).length;
    const nonExemptDaysCount = temporaryTripDays.filter(day => !day.exento).length;

    // Verificar cuántos días han cambiado respecto al original
    const changedDaysCount = temporaryTripDays.filter((tempDay, index) => {
        const origDay = originalTripDays[index];
        return origDay && tempDay.exento !== origDay.exento;
    }).length;

    const handleExportCSV = () => {
        exportCSV();
    };

    if (loadingCompanies) {
        return <p>Cargando datos...</p>;
    }

    return (
        <div className={styles.pendingTripsWrapper}>
            {/* Tabla Pendientes */}
            <table className={styles.pendingTripsTable}>
                <thead>
                    <tr>
                        <th>Nº Viajes por revisar</th>
                        <th>Días exentos</th>
                        <th>Días no exentos</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td
                            onClick={() => setShowCompanyNames(!showCompanyNames)}
                            className={styles.clickableCell}
                        >
                            {loadingGlobalTrips ? '…' : totalPendingTrips}
                        </td>
                        <td>{loadingExempt ? '…' : exemptData.exempt}</td>
                        <td>{loadingExempt ? '…' : exemptData.nonExempt}</td>
                    </tr>
                </tbody>
            </table>

            <div className={styles.exportButtonWrapper}>
                <button onClick={exportCSV} className={styles.exportButton}>
                    {' '}
                    Exportar CSV
                </button>
            </div>

            {showCompanyNames && pendingCompanies.length > 0 && (
                <div className={styles.companyDetailsContainer}>
                    <div className={styles.companiesList}>
                        {pendingCompanies.map((company) => (
                            <div
                                key={company.id}
                                className={`${styles.companyItem} ${selectedCompany?.id === company.id ? styles.activeItem : ''
                                    }`}
                                onClick={() => handleCompanyClick(company)}
                            >
                                {company.nombre_empresa}
                            </div>
                        ))}
                    </div>

                    {selectedCompany && (
                        <div className={styles.detailPanel}>
                            <h4>Empleados:</h4>
                            {loadingEmployees ? (
                                <p>Cargando empleados...</p>
                            ) : (
                                <div className={styles.employeesList}>
                                    {employees.map((employee: any) => (
                                        <div
                                            key={employee.id}
                                            className={`${styles.employeeItem} ${selectedEmployee?.id === employee.id
                                                ? styles.activeItem
                                                : ''
                                                }`}
                                            onClick={() => handleEmployeeClick(employee)}
                                        >
                                            {employee.nombre} {employee.apellido}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {selectedEmployee && (
                                <div className={styles.tripsList}>
                                    <h4>Viajes pendientes:</h4>
                                    {loadingEmployeeTrips ? (
                                        <p>Cargando viajes...</p>
                                    ) : pendingTrips.length === 0 ? (
                                        <p>No hay viajes pendientes de revisión.</p>
                                    ) : (
                                        pendingTrips.map((trip: any) => {
                                            // Adaptación para diferentes formatos de fecha
                                            const startDate = trip.fecha_inicio || (trip.tripDates && trip.tripDates[0]) || '';
                                            const endDate = trip.fecha_fin || (trip.tripDates && trip.tripDates[1]) || '';
                                            const destination = trip.destination || trip.destino || 'Destino no especificado';

                                            return (
                                                <div
                                                    key={trip.id}
                                                    className={`${styles.tripItem} ${selectedTrip?.id === trip.id ? styles.activeItem : ''}`}
                                                    onClick={() => handleTripClick(trip)}
                                                >
                                                    📅 {destination} ({startDate} - {endDate})
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            )}

                            {selectedTrip && (
                                <div className={styles.calendarPlaceholder}>
                                    <h5>Viaje de {selectedEmployee.nombre} {selectedEmployee.apellido}</h5>
                                    <p><strong>Destino:</strong> {selectedTrip.destination || selectedTrip.destino}</p>
                                    <p><strong>Información:</strong> {selectedTrip.info || selectedTrip.motivo}</p>
                                    <p><strong>Empresa visitada:</strong> {selectedTrip.companyVisited || selectedTrip.empresa_visitada || 'No especificada'}</p>
                                    {selectedTrip.es_internacional && <p><strong>Viaje internacional:</strong> {selectedTrip.pais}</p>}
                                    <p><strong>Notas:</strong> {selectedTrip.notes}</p>

                                    {/* Estado de carga y mensajes de éxito/error */}
                                    {loadingTripDays && <p className={styles.loadingMessage}>Cargando días del viaje...</p>}
                                    {dayChangeSuccess && <p className={styles.successMessage}>{dayChangeSuccess}</p>}
                                    {dayChangeError && <p className={styles.errorMessage}>{dayChangeError}</p>}
                                    {finalizingReview && <p className={styles.loadingMessage}>Guardando revisión de días...</p>}


                                    {/* Calendario */}
                                    <Calendar
                                        value={calendarDate}
                                        onClickDay={handleDateClick}
                                        tileDisabled={({ date, view }) => {
                                            if (view !== 'month') return false;
                                            // Solo habilita clic en días que estén en temporaryTripDays
                                            return !temporaryTripDays.some(d => areSameDay(date, new Date(d.fecha)));
                                        }}
                                        tileClassName={({ date, view }) => {
                                            if (view !== 'month') return null;
                                            // Buscar el día en temporaryTripDays
                                            const day = temporaryTripDays.find(d => areSameDay(date, new Date(d.fecha)));
                                            if (!day) return null;

                                            // Verificar si este día ha cambiado respecto al original
                                            const originalDay = originalTripDays.find(d => d.id === day.id);
                                            const hasChanged = originalDay && originalDay.exento !== day.exento;

                                            // Aplicar clase según exento y si ha cambiado
                                            let className = day.exento ? styles.exempted : styles.marked;
                                            if (hasChanged) {
                                                className += ' ' + styles.changed;
                                            }
                                            return className;
                                        }}
                                    />

                                    {/* Leyenda */}
                                    <div className={styles.legend}>
                                        <div className={styles.legendItem}>
                                            <span className={styles.marked}></span> Días no exentos: {nonExemptDaysCount}
                                        </div>
                                        <div className={styles.legendItem}>
                                            <span className={styles.exempted}></span> Días exentos: {exemptDaysCount}
                                        </div>
                                        {changedDaysCount > 0 && (
                                            <div className={styles.legendItem}>
                                                <span className={styles.changed}></span> Días modificados: {changedDaysCount}
                                            </div>
                                        )}
                                    </div>

                                    <p>Haz clic en un día exento(azul) para marcarlo como no exento(gris).</p>

                                    {/* Botones */}
                                    <div className={styles.buttonRow}>
                                        <button
                                            className={styles.acceptButton}
                                            disabled={!hasReviewedAny || finalizingReview}
                                            onClick={() => setIsConfirmOpen(true)}
                                        >
                                            Finalizar revisión
                                        </button>
                                        <button
                                            className={styles.cancelButton}
                                            onClick={handleCancel}
                                            disabled={finalizingReview}
                                        >
                                            {hasUnsavedChanges ? 'Descartar cambios' : 'Cancelar'}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {isConfirmOpen && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalContent}>
                        <p>
                            Vas a confirmar <strong>{nonExemptDaysCount}</strong> días como{' '}
                            <strong>no exentos</strong>
                        </p>
                        {nonExemptDaysCount > 0 && (
                            <>
                                <p>
                                    Por favor, indica el motivo para marcar estos días como no exentos:
                                </p>
                                <textarea
                                    className={`${styles.reasonInput} ${showReasonError ? styles.inputError : ''}`}
                                    placeholder="Escribe aquí el motivo..."
                                    value={nonExemptReason}
                                    onChange={(e) => {
                                        setNonExemptReason(e.target.value);
                                        if (e.target.value.trim()) setShowReasonError(false);
                                    }}
                                ></textarea>
                                {showReasonError && (
                                    <p
                                        style={{
                                            color: '#dc3545',
                                            marginTop: '4px',
                                            fontSize: '0.9rem',
                                        }}
                                    >
                                        El motivo es obligatorio.
                                    </p>
                                )}
                            </>
                        )}
                        <div className={styles.modalButtons}>
                            <button
                                className={styles.acceptButton}
                                onClick={handleAcceptConfirmed}
                                disabled={nonExemptDaysCount > 0 && !nonExemptReason.trim() || finalizingReview}
                            >
                                Confirmar
                            </button>
                            <button
                                className={styles.cancelButton}
                                onClick={() => setIsConfirmOpen(false)}
                                disabled={finalizingReview}
                            >
                                Cancelar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PendingTripsTable;