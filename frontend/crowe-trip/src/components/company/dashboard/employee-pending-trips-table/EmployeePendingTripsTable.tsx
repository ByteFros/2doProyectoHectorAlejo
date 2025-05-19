import { useState, useEffect } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import styles from './employee-pending-trips.module.scss';
import useAuth from '~/components/hooks/use-auth';
// Eliminar imports no utilizados y añadir los nuevos
// import usePendingEmployeesByCompany from '~/components/master/dashboard/pending-trips-table/hooks/useEmployeesByCompany';
// import usePendingTripsCount from '~/components/master/dashboard/pending-trips-table/hooks/usePendingTripscount';
import usePendingTripsDetail from '~/components/master/dashboard/pending-trips-table/hooks/usePendingTripsDetail'; // Añadido
import useFinalizeTripReview from '~/components/master/dashboard/pending-trips-table/hooks/useFinalizeTripReview'; // Añadido
import useExemptDays from '~/components/hooks/trips/useExemptDays';
// import usePendingTripsByEmployee from '~/components/master/dashboard/pending-trips-table/hooks/usePendingTripsByEmployee';
import useTripDays, { TripDay } from '~/components/master/dashboard/pending-trips-table/hooks/useTripDays'; 
// import useUpdateTripDay from '~/components/master/dashboard/pending-trips-table/hooks/useUpdateTripDay'; // Se reemplazará por useFinalizeTripReview
import { areSameDay } from '~/components/master/dashboard/pending-trips-table/utils/dateUtils';
import usePendingEmployeesByCompany from '~/components/master/dashboard/pending-trips-table/hooks/useEmployeesByCompany';

const EmployeePendingTrips = () => {
  const { empresaId } = useAuth(); // user puede ser necesario para filtrar por empleado si es el mismo que está logueado
  const companyId = empresaId ?? undefined;
  
  // Estado para los datos obtenidos del servidor
  const { data: pendingEmployees = [], loading: loadingEmployees } = usePendingEmployeesByCompany(companyId);
  // Usar usePendingTripsDetail para el conteo global y para viajes por empleado
  const { count: totalPendingTrips, loading: loadingGlobalTrips } = usePendingTripsDetail(); // Para el conteo global de la empresa
  const { data: exemptData, loading: loadingExempt } = useExemptDays();
  const { finalizeReview, loading: finalizingReview, error: finalizeError } = useFinalizeTripReview(); // Añadido

  // Estado para la UI
  const [showEmployees, setShowEmployees] = useState(false);
  const [confirmedTrips, setConfirmedTrips] = useState<any[]>([]);
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

  // Datos filtrados por empleado cuando se selecciona uno
  // const { data: pendingTrips = [], loading: loadingTrips } = usePendingTripsByEmployee(selectedEmployee?.id);
  const { trips: pendingTrips = [], loading: loadingTrips } = usePendingTripsDetail(selectedEmployee?.id); // Modificado
  
  // Datos de los días de viaje cuando se selecciona un viaje
  const { data: tripDays = [], loading: loadingTripDays } = useTripDays(selectedTrip?.id);
  // Hook para actualizar el estado de exención de un día - Se elimina, se usa finalizeReview
  // const { updateDay } = useUpdateTripDay();

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
      setNonExemptReason('');
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
    setShowReasonError(false);
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
    
    // Notificar al usuario del cambio temporal
    setDayChangeSuccess(
      `Día ${updatedTripDays[tripDayIndex].fecha} marcado temporalmente como ${
        updatedTripDays[tripDayIndex].exento ? "exento" : "no exento"
      }`
    );
  };

  // Función para guardar todos los cambios en el servidor
  const saveAllChanges = async () => {
    if (!selectedTrip || !selectedTrip.id) return;
    
    const diasParaEnviar = temporaryTripDays.map(day => ({
      id: day.id,
      exento: day.exento,
    }));

    const nonExemptDaysCount = diasParaEnviar.filter(day => !day.exento).length;
    
    // Validar que haya un motivo si hay días no exentos
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
        const extraMessage = nonExemptDaysCount > 0 ? 'Se ha iniciado una conversación con el empleado.' : '';
        // Añadir a confirmedTrips para la UI
        setConfirmedTrips([
          ...confirmedTrips,
          {
            employee: `${selectedEmployee.nombre} ${selectedEmployee.apellido}`,
            destination: selectedTrip.destination || selectedTrip.destino,
            exemptDays: diasParaEnviar.filter(day => day.exento).length,
            nonExemptDays: nonExemptDaysCount,
            reason: nonExemptDaysCount > 0 ? nonExemptReason.trim() : ''
          }
        ]);
      
        setDayChangeSuccess(result.message + ' ' + extraMessage);
      
        // Limpiar selección actual
        setSelectedTrip(null);
        setTemporaryTripDays([]);
        setOriginalTripDays([]);
        setHasUnsavedChanges(false);
        setHasReviewedAny(false);
        setNonExemptReason('');
        setShowReasonError(false);
      } else {
        setDayChangeError(`Error al guardar: ${result.message || 'Error desconocido.'}`);
      }
    } catch (error: any) {
      setDayChangeError(`Error al guardar los cambios: ${error.message}`);
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

  if (loadingEmployees) {
    return <p>Cargando empleados...</p>;
  }
  
  return (
    <div className={styles.pendingTripsWrapper}>
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
              onClick={() => setShowEmployees(!showEmployees)}
              className={styles.clickableCell}
            >
              {loadingGlobalTrips ? '…' : totalPendingTrips} {/* Modificado loadingPendings a loadingGlobalTrips */}
            </td>
            <td>{loadingExempt ? '…' : exemptData.exempt}</td>
            <td>{loadingExempt ? '…' : exemptData.nonExempt}</td>
          </tr>
        </tbody>
      </table>

      {showEmployees && (
        <div className={styles.companyDetailsContainer}>
          <div className={styles.companiesList}>
            {pendingEmployees.length > 0 ? (
              pendingEmployees.map((emp) => (
                <div
                  key={emp.id}
                  className={`${styles.companyItem} ${
                    selectedEmployee?.id === emp.id ? styles.activeItem : ''
                  }`}
                  onClick={() => handleEmployeeClick(emp)}
                >
                  {emp.nombre} {emp.apellido}
                </div>
              ))
            ) : (
              <div className={styles.noEmployeesMessage}>
                No se encontraron empleados con viajes pendientes de revisión.
              </div>
            )}
          </div>

          {selectedEmployee && (
            <div className={styles.detailPanel}>
              <h4>Viajes pendientes de {selectedEmployee.nombre} {selectedEmployee.apellido}:</h4>
              {loadingTrips ? (
                <p>Cargando viajes...</p>
              ) : pendingTrips.length === 0 ? (
                <p>No hay viajes pendientes de revisión.</p>
              ) : (
                pendingTrips.map((trip) => {
                  // Adaptación para diferentes formatos de fecha
                  const startDate = trip.tripDates || (trip.tripDates && trip.tripDates[0]) || '';
                  const endDate = trip.tripDates || (trip.tripDates && trip.tripDates[1]) || '';
                  const destination = trip.destination || 'Destino no especificado';

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

              {selectedTrip && (
                <div className={styles.calendarPlaceholder}>
                  <h5>Viaje de {selectedEmployee.nombre} {selectedEmployee.apellido}</h5>
                  <p><strong>Destino:</strong> {selectedTrip.destination || selectedTrip.destino}</p>
                  <p><strong>Información:</strong> {selectedTrip.info || selectedTrip.motivo}</p>
                  {selectedTrip.companyVisited && <p><strong>Empresa visitada:</strong> {selectedTrip.companyVisited}</p>}
                  {selectedTrip.empresa_visitada && <p><strong>Empresa visitada:</strong> {selectedTrip.empresa_visitada}</p>}
                  {selectedTrip.es_internacional && <p><strong>Viaje internacional:</strong> {selectedTrip.pais}</p>}

                  {/* Estado de carga y mensajes */}
                  {loadingTripDays && <p className={styles.loadingMessage}>Cargando días del viaje...</p>}
                  {dayChangeSuccess && <p className={styles.successMessage}>{dayChangeSuccess}</p>}
                  {dayChangeError && <p className={styles.errorMessage}>{dayChangeError || finalizeError}</p>} {/* Añadido finalizeError */}
                  {(savingDays || finalizingReview) && <p className={styles.loadingMessage}>Guardando cambios...</p>} {/* Añadido finalizingReview */}
                  {hasUnsavedChanges && (
                    <p className={styles.warningMessage}>
                      Tienes cambios sin guardar. Presiona "Finalizar revisión" para guardarlos o "Cancelar" para descartarlos.
                    </p>
                  )}

                  {/* Calendario */}
                  <Calendar
                    value={calendarDate}
                    onClickDay={handleDateClick}
                    tileDisabled={({ date, view }) => {
                      if (view !== 'month') return false;
                      return !temporaryTripDays.some(d => areSameDay(date, new Date(d.fecha)));
                    }}
                    tileClassName={({ date, view }) => {
                      if (view !== 'month') return null;
                      const day = temporaryTripDays.find(d => areSameDay(date, new Date(d.fecha)));
                      if (!day) return null;
                      const originalDay = originalTripDays.find(d => d.id === day.id);
                      const hasChanged = originalDay && originalDay.exento !== day.exento;
                      let cls = day.exento ? styles.exempted : styles.marked;
                      if (hasChanged) cls += ` ${styles.changed}`;
                      return cls;
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

                  <p>Haz clic en un día para cambiar entre exento y no exento. Los cambios se guardarán al finalizar la revisión.</p>

                  {/* Contadores y progreso */}
                  <div className={styles.progressRow}>
                    <span>Días del viaje: {temporaryTripDays.length}</span>
                    <span>Días modificados: {changedDaysCount}</span>
                  </div>

                  {/* Botones */}
                  <div className={styles.buttonRow}>
                    <button
                      className={styles.acceptButton}
                      disabled={!hasReviewedAny || savingDays || finalizingReview} /* Añadido finalizingReview */
                      onClick={() => setIsConfirmOpen(true)}
                    >
                      Finalizar revisión
                    </button>
                    <button
                      className={styles.cancelButton}
                      onClick={handleCancel}
                      disabled={savingDays || finalizingReview} /* Añadido finalizingReview */
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
            <h4>Confirmación de revisión</h4>
            <p>Has revisado el viaje y estos son los cambios:</p>
            <ul>
              <li><strong>Días no exentos:</strong> {nonExemptDaysCount}</li>
              <li><strong>Días exentos:</strong> {exemptDaysCount}</li>
              <li><strong>Total:</strong> {temporaryTripDays.length}</li>
              <li><strong>Días modificados:</strong> {changedDaysCount}</li>
            </ul>
            
            {/* Campo para el motivo de no exención */}
            {nonExemptDaysCount > 0 && (
              <div className={styles.reasonContainer}>
                <label htmlFor="nonExemptReason">
                  <strong>Motivo para días no exentos:</strong>
                </label>
                <textarea
                  id="nonExemptReason"
                  value={nonExemptReason}
                  onChange={(e) => {
                    setNonExemptReason(e.target.value);
                    if (e.target.value.trim()) setShowReasonError(false);
                  }}
                  className={`${styles.reasonTextarea} ${showReasonError ? styles.errorTextarea : ''}`}
                  placeholder="Introduce el motivo por el que estos días no están exentos..."
                  rows={3}
                />
                {showReasonError && (
                  <p className={styles.errorMessage}>
                    Debes indicar un motivo para los días no exentos
                  </p>
                )}
              </div>
            )}
            
            <p>Una vez confirmado, el viaje cambiará su estado a "FINALIZADO".</p>
            <div className={styles.modalButtons}>
              <button
                className={styles.acceptButton}
                onClick={handleAcceptConfirmed}
                disabled={savingDays || finalizingReview} /* Añadido finalizingReview */
              >
                Confirmar
              </button>
              <button
                className={styles.cancelButton}
                onClick={() => setIsConfirmOpen(false)}
                disabled={savingDays || finalizingReview} /* Añadido finalizingReview */
              >
                Volver a revisar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmployeePendingTrips;