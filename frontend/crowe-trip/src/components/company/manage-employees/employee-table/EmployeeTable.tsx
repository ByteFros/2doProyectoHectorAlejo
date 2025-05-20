import { useState, useEffect } from "react";
import styles from "./employee-table.module.scss";
import useEmployees from "~/components/hooks/useEmployees";

export default function EmployeeTable() {
  const { employees, deleteEmployeeById, loading, error } = useEmployees(null);
  const [localDeletedId, setLocalDeletedId] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  // Añadimos un estado local para manejar la eliminación visual antes de la eliminación real
  const [localEmployees, setLocalEmployees] = useState<any[]>([]);
  
  // Sincronizamos los empleados del hook con nuestro estado local
  useEffect(() => {
    setLocalEmployees(employees);
  }, [employees]);

  const openModal = (id: number) => {
    setSelectedId(id);
    setShowModal(true);
  };

  const handleConfirmDelete = async () => {
    if (selectedId === null) return;
    setShowModal(false);
    setLocalDeletedId(selectedId);
    
    // Esperamos a que termine la animación antes de eliminar realmente
    setTimeout(async() => {
      // Solo llamamos a deleteEmployeeById una vez
      await deleteEmployeeById(selectedId);
      setLocalDeletedId(null);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }, 400); // 400ms es la duración de tu animación
  };

  const handleCancel = () => {
    setShowModal(false);
    setSelectedId(null);
  };

  if (loading) return <p>Cargando empleados...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <div className={styles.employeeTableWrapper}>
      {showSuccess && (
        <div className={styles.successMessage}>Empleado eliminado correctamente.</div>
      )}

      <table className={styles.employeeTable}>
        <thead>
          <tr>
            <th className={styles.employeeTableHeader}>Nombre</th>
            <th className={styles.employeeTableHeader}>Usuario</th>
            <th className={styles.employeeTableHeader}>DNI</th>
            <th className={styles.employeeTableHeader}>Email</th>
            <th className={styles.employeeTableHeader}>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((emp) => (
            <tr
              key={emp.id}
              className={emp.id === localDeletedId ? styles.fadeOutRow : ""}
            >
              <td className={styles.employeeTableCell}>{emp.nombre} {emp.apellido}</td>
              <td className={styles.employeeTableCell}>{emp.username}</td>
              <td className={styles.employeeTableCell}>{emp.dni}</td>
              <td className={styles.employeeTableCell}>{emp.email}</td>
              <td className={styles.employeeTableCell}>
                <button
                  className={styles.employeeTableDeleteBtn}
                  onClick={() => openModal(emp.id)}
                  disabled={localDeletedId !== null}
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h2 className={styles.modalTitle}>¿Estás seguro?</h2>
            <p className={styles.modalText}>
              Esta acción no se puede deshacer, toda la información vinculada será eliminada.
            </p>
            <div className={styles.modalActions}>
              <button className={styles.confirmBtn} onClick={handleConfirmDelete}>
                Sí, eliminar
              </button>
              <button className={styles.cancelBtn} onClick={handleCancel}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}