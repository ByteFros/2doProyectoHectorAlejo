import React, { useState, useRef, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import styles from '../travel.module.scss';
import './datepicker-custom.css';
import useTrips from '../../../hooks/useTrips'; // Importamos el hook de viajes
import useUser from "../../../hooks/useUser"; // Importamos el hook de usuario
import useCityAutocomplete from '~/components/hooks/userCityAutocomplete';

export default function ScheduleTrip() {
    // Obtenemos el usuario autenticado
    const { user, loading: userLoading } = useUser();

    // Obtenemos las funciones de viajes
    const { crearViaje } = useTrips();

    // Estado para almacenar mensajes de success/error
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [showMessage, setShowMessage] = useState(false);
    const [cityQuery, setCityQuery] = useState("");
    const citySuggestions = useCityAutocomplete(cityQuery);

    const [trip, setTrip] = useState<{
        startDate: Date | null;
        endDate: Date | null;
        days: string;
        city: string;
        country: string;
        company: string;
        reason: string;
    }>({
        startDate: new Date(),
        endDate: null,
        days: '1',
        city: '',
        country: '',
        company: '',
        reason: '',
    });

    // Referencia para el contenedor de sugerencias
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Efecto para manejar el clic fuera del área de sugerencias
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setCityQuery("");
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Efecto para el manejo de la animación del mensaje
    useEffect(() => {
        if (message) {
            setShowMessage(true);
            const timer = setTimeout(() => {
                setShowMessage(false);
                setTimeout(() => setMessage(null), 500); // Eliminar el mensaje después de que termine la animación
            }, 4000); // Mostrar el mensaje por 4 segundos
            return () => clearTimeout(timer);
        }
    }, [message]);

    // Manejar cambio de fechas en el rango
    const handleDateChange = (dates: [Date | null, Date | null]) => {
        const [start, end] = dates;
        setTrip({
            ...trip,
            startDate: start,
            endDate: end,
            days: end ? calculateDays(start!, end) : '1',
        });
    };

    // Calcular diferencia de días
    const calculateDays = (start: Date, end: Date) => {
        const diffTime = end.getTime() - start.getTime();
        return Math.max(Math.ceil(diffTime / (1000 * 60 * 60 * 24)), 1).toString();
    };

    // Manejar cambios en los inputs
    const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
    ) => {
        setTrip({ ...trip, [e.target.name]: e.target.value });
    };

    // Crear viaje utilizando el hook useViajes
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!trip.startDate || !trip.endDate) {
            setMessage({
                type: 'error',
                text: 'Por favor selecciona las fechas de inicio y fin del viaje'
            });
            return;
        }

        // Adaptar los datos al formato que espera la API
        const viajeData = {
            destino: `${trip.city}, ${trip.country}`,
            fecha_inicio: trip.startDate.toISOString().split('T')[0],
            fecha_fin: trip.endDate.toISOString().split('T')[0],
            empresa_visitada: trip.company,
            motivo: trip.reason
        };

        // Llamar a la función crearViaje del hook
        const result = await crearViaje(viajeData);

        if (result.success) {
            setMessage({
                type: 'success',
                text: result.success
            });

            // Resetear el formulario
            setTrip({
                startDate: new Date(),
                endDate: null,
                days: '1',
                city: '',
                country: '',
                company: '',
                reason: '',
            });
        } else if (result.error) {
            setMessage({
                type: 'error',
                text: result.error
            });
        }
    };

    // Mostrar cargando mientras obtenemos el usuario
    if (userLoading) {
        return <div>Cargando información del usuario...</div>;
    }

    return (
        <div className={styles.scheduleTrip}>
            {message && (
                <div className={`
                    ${styles.messageContainer} 
                    ${styles[message.type]} 
                    ${showMessage ? styles.show : styles.hide}
                `}>
                    <div className={styles.messageIcon}>
                        {message.type === 'success' ? '✓' : '⚠'}
                    </div>
                    <div className={styles.messageText}>
                        {message.text}
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit} className={styles.form}>
                {/* Primera fila: Fecha y Días */}
                <div className={styles.row}>
                    <div className={styles.inputGroup}>
                        <label>Selecciona la fecha</label>
                        <DatePicker
                            selected={trip.startDate}
                            onChange={handleDateChange}
                            startDate={trip.startDate}
                            endDate={trip.endDate}
                            selectsRange
                            dateFormat="dd/MM/yy"
                            className="custom-datepicker"
                            popperPlacement="bottom-start"
                            minDate={new Date()} // No permitir fechas pasadas
                        />
                    </div>
                    <div className={styles.inputGroup}>
                        <label>Número de días</label>
                        <input type="number" name="days" value={trip.days} readOnly disabled />
                    </div>
                </div>

                {/* Segunda fila: Ciudad y País */}
                <div className={styles.row}>
                    <div className={styles.inputGroup} ref={wrapperRef}>
                        <label>Ciudad de destino</label>
                        <input
                            type="text"
                            name="city"
                            value={trip.city}
                            onChange={(e) => {
                                handleChange(e);
                                setCityQuery(e.target.value);
                            }}
                            required
                        />
                        {cityQuery && citySuggestions.length > 0 && (
                            <ul className={styles.autocomplete}>
                                {citySuggestions.map(({ city, country }, idx) => (
                                    <li key={idx} onClick={() => {
                                        setTrip((prev) => ({
                                            ...prev,
                                            city,
                                            country
                                        }));
                                        setCityQuery(""); // ✅ cerrar sugerencias
                                    }}>
                                        {city}, {country}
                                    </li>
                                ))}
                            </ul>
                        )}

                    </div>
                    <div className={styles.inputGroup}>
                        <label>País</label>
                        <select
                            name="country"
                            value={trip.country}
                            onChange={handleChange}
                            required
                        >
                            <option value="">Seleccione un país</option>
                            {trip.country && (
                                <option value={trip.country}>{trip.country}</option>
                            )}
                        </select>
                    </div>
                </div>

                {/* Tercera fila: Empresa y Empleado */}
                <div className={styles.row}>
                    <div className={styles.inputGroup}>
                        <label>Empresa a la que se visita</label>
                        <input
                            type="text"
                            name="company"
                            value={trip.company}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className={styles.inputGroup}>
                        <label>Nombre del empleado</label>
                        <input
                            type="text"
                            value={user ? user.username : ''}
                            readOnly
                            disabled={!!cityQuery.length}
                        />
                    </div>
                </div>

                {/* Última fila: Motivo del viaje */}
                <div className={styles.inputGroup}>
                    <label>Motivo del viaje</label>
                    <textarea name="reason" value={trip.reason} onChange={handleChange} required />
                </div>

                <button type="submit">Programar</button>
            </form>
        </div>
    );
}