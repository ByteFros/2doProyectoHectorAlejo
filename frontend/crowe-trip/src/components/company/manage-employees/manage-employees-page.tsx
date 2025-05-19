import { useState, useRef, useEffect } from 'react';
import AddEmployee from './add-employee/AddEmployee';
import EmployeeTable from './employee-table/EmployeeTable';

import styles from './manage-employees-page.module.scss';

import { empleadosMock, type Empleado } from './mock/empleadosMock';

export default function ManageEmployeesPage() {
    const [activeTab, setActiveTab] = useState<'add' | 'manage' | 'trips'>('add');
    const [isSticky, setIsSticky] = useState(false);
    const [employees, setEmployees] = useState<Empleado[]>(empleadosMock);

    const buttonGroupRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const handleScroll = () => {
            if (buttonGroupRef.current) {
                const headerHeight = 60;
                const top = buttonGroupRef.current.getBoundingClientRect().top;
                setIsSticky(top <= headerHeight);
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handleAddEmployee = (empleado: Omit<Empleado, 'trips' | 'expenses'>) => {
        const empleadoConViajes: Empleado = {
            ...empleado,
            trips: [],
            expenses: [],
        };
        setEmployees((prev) => [...prev, empleadoConViajes]);
    };

    const handleDeleteEmployee = (id: number) => {
        setEmployees((prev) => prev.filter((emp) => emp.id !== id));
    };

    return (
        <div className={styles.container}>
            <div
                ref={buttonGroupRef}
                className={`${styles.buttonGroup} ${isSticky ? styles.sticky : ''}`}
            >
                <button
                    className={activeTab === 'add' ? styles.active : ''}
                    onClick={() => setActiveTab('add')}
                >
                    Agregar empleado
                </button>
                <button
                    className={activeTab === 'manage' ? styles.active : ''}
                    onClick={() => setActiveTab('manage')}
                >
                    Gestionar empleados
                </button>
            </div>

            <div className={styles.content}>
                {activeTab === 'add' && <AddEmployee/>}

                {activeTab === 'manage' && (
                    <EmployeeTable  />
                )}

                {activeTab === 'trips' && (
                    <TripManager
                        company={{ id: 1, nombre: 'Empresa Prueba' }}
                        employees={employees}
                        trips={employees.flatMap((e) => e.trips)}
                    />
                )}
            </div>
        </div>
    );
}
