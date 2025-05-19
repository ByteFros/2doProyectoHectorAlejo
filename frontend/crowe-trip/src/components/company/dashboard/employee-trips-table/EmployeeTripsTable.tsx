import { useState } from 'react';
import styles from './employee-trips-table.module.scss';
import useEmployeeTripsTable from '~/components/hooks/trips/useEmployeTripsTable';

const EmployeeTripsTable = () => {
    // Estados para búsqueda y ordenamiento
    const [searchTerm, setSearchTerm] = useState('');
    const [sortAsc, setSortAsc] = useState(true);
    
    // Obtener datos de los empleados mediante el hook
    const { employees, loading } = useEmployeeTripsTable();
    
    if (loading) return <p className={styles.loading}>Cargando tabla...</p>;
    
    // Funciones de utilidad para filtrado y ordenamiento
    // Elimina tildes/acentos de un string
    const normalize = (str: string) =>
        str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    
    // Extrae el apellido (última palabra)
    const getLastName = (fullName: string) => {
        const parts = fullName.trim().toLowerCase().split(' ');
        return parts[parts.length - 1];
    };
    
    // Filtrar y ordenar empleados
    const filteredEmployees = employees
        .filter(e => {
            const normalizedFullName = normalize(e.name);
            const terms = normalize(searchTerm).split(' ').filter(Boolean);
            return terms.length === 0 || terms.every(term => normalizedFullName.includes(term));
        })
        .sort((a, b) => {
            const lastNameA = getLastName(a.name);
            const lastNameB = getLastName(b.name);
            return sortAsc
                ? lastNameA.localeCompare(lastNameB)
                : lastNameB.localeCompare(lastNameA);
        });
    
    const toggleSort = () => {
        setSortAsc(prev => !prev);
    };
    
    return (
        <div className={styles.employeeTableWrapper}>
            <div className={styles.searchBar}>
                <input
                    type="text"
                    placeholder="Buscar por nombre o apellido..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>
            <table className={styles.employeeTable}>
                <thead>
                    <tr>
                        <th
                            className={styles.employeeHeader}
                            onClick={toggleSort}
                            style={{ cursor: 'pointer' }}
                            title="Se ordena por apellido"
                        >   
                            Empleado{sortAsc ? '▲' : '▼'}
                        </th>
                        <th className={styles.employeeHeader}>Viajes</th>
                        <th className={styles.employeeHeader}>Días de viaje</th>
                        <th className={styles.employeeHeader}>Días exentos</th>
                        <th className={styles.employeeHeader}>Días no exentos</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredEmployees.map((e, i) => (
                        <tr key={i}>
                            <td className={styles.employeeCell}>{e.name}</td>
                            <td className={styles.employeeCell}>{e.trips}</td>
                            <td className={styles.employeeCell}>{e.travelDays || 0}</td>
                            <td className={styles.employeeCell}>{e.exemptDays || 0}</td>
                            <td className={styles.employeeCell}>{e.nonExemptDays || 0}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default EmployeeTripsTable;