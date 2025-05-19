// ✅ Componente AddEmployee corregido
import { useState } from 'react';
import styles from './add-employee.module.scss';
import useRegisterEmployees from '~/components/hooks/trips/useRegisterEmployees';

export default function AddEmployee() {
    // Estados para el formulario
    const [nombre, setNombre] = useState('');
    const [apellido, setApellido] = useState('');
    const [dni, setDni] = useState('');
    const [email, setEmail] = useState('');
    
    // Estados para la carga CSV
    const [useCSV, setUseCSV] = useState(false);
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [csvFileName, setCsvFileName] = useState('');
    const [csvFileLoaded, setCsvFileLoaded] = useState(false);
    const [isDragging, setIsDragging] = useState(false);

    // Hook para registro de empleados
    const {
        success,
        error,
        registerSingleEmployee,
        registerEmployeesFromCSV,
        clearMessages,
    } = useRegisterEmployees();

    // Manejo de envío de formulario individual
    const handleSingleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        registerSingleEmployee({ nombre, apellido, dni, email });
        setNombre('');
        setApellido('');
        setDni('');
        setEmail('');
    };

    // Manejo de carga de archivo CSV
    const handleCSVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0] || null;
        if (!file) return;
        
        setCsvFile(file);
        setCsvFileName(file.name);
        setCsvFileLoaded(true);
        clearMessages();
    };

    // Manejo de arrastrar y soltar para CSV
    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) {
            setCsvFile(file);
            setCsvFileName(file.name);
            setCsvFileLoaded(true);
            clearMessages();
        }
    };

    // Envío de archivo CSV para procesamiento
    const handleCSVSubmit = () => {
        if (!csvFile) return;
        registerEmployeesFromCSV(csvFile);
    };

    return (
        <div className={styles.addEmployeeWrapper}>
            {/* Mensajes de éxito y error */}
            {success && <div className={styles.successMessage}>{success}</div>}
            {error && <div className={styles.errorMessage}>{error}</div>}

            {/* Toggle para cambiar entre formulario individual y CSV */}
            <div className={styles.toggleWrapper}>
                <label className={styles.toggleSwitch}>
                    <input
                        type="checkbox"
                        checked={useCSV}
                        onChange={() => {
                            setUseCSV(!useCSV);
                            setCsvFile(null);
                            setCsvFileName('');
                            setCsvFileLoaded(false);
                            clearMessages();
                        }}
                    />
                    <span className={styles.slider}></span>
                </label>
                <span className={styles.toggleLabel}>Usar CSV</span>
            </div>

            {/* Formulario para registro individual */}
            {!useCSV ? (
                <form onSubmit={handleSingleSubmit} className={styles.form}>
                    <input
                        type="text"
                        placeholder="Nombre"
                        value={nombre}
                        onChange={(e) => setNombre(e.target.value)}
                        required
                    />
                    <input
                        type="text"
                        placeholder="Apellido"
                        value={apellido}
                        onChange={(e) => setApellido(e.target.value)}
                        required
                    />
                    <input
                        type="text"
                        placeholder="DNI"
                        value={dni}
                        onChange={(e) => setDni(e.target.value)}
                        required
                    />
                    <input
                        type="email"
                        placeholder="Correo electrónico"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                    <button type="submit">Registrar empleado</button>
                </form>
            ) : (
                /* Interfaz para carga de CSV */
                <div className={styles.csvUpload}>
                    <div
                        className={`${styles.dropZone} ${isDragging ? styles.dragOver : ''}`}
                        onClick={() => document.getElementById('csvInput')?.click()}
                        onDragOver={(e) => {
                            e.preventDefault();
                            setIsDragging(true);
                        }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleDrop}
                    >
                        <input
                            type="file"
                            id="csvInput"
                            accept=".csv"
                            onChange={handleCSVUpload}
                            hidden
                        />
                        <p className={styles.dropText}>
                            {csvFileLoaded
                                ? `Archivo cargado: ${csvFileName}`
                                : 'Haz clic o arrastra un archivo CSV aquí'}
                        </p>
                        {csvFileLoaded && (
                            <p className={styles.fileName}>
                                {csvFileName}
                            </p>
                        )}
                    </div>

                    <p className={styles.hint}>
                        Formato del archivo: <code>nombre,apellido,dni,email</code>
                    </p>
                    
                    {csvFile && (
                        <button onClick={handleCSVSubmit}>
                            Registrar desde CSV
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}