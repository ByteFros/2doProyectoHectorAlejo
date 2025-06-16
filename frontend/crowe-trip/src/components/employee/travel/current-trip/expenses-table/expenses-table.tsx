// expenses-table/expenses-table.tsx
import { useState } from "react";
import styles from "./expenses-table.module.scss";
import { apiRequest, buildApiUrl } from '@config/api';

interface Gasto {
  id: number;
  concepto: string;
  monto: number;
  estado: string;
  fecha_gasto: string;
  comprobante?: string;
}

interface Props {
  expenses: Gasto[];
}

export default function ExpensesTable({ expenses }: Props) {
  const [selectedExpenses, setSelectedExpenses] = useState<number[]>([]);
  const [previewFile, setPreviewFile] = useState<{ url: string; type: string } | null>(null);

  const handleCheckboxChange = (expenseId: number) => {
    setSelectedExpenses(prev =>
      prev.includes(expenseId) ? prev.filter(id => id !== expenseId) : [...prev, expenseId]
    );
  };

  const handleDeleteSelected = async () => {
    for (const id of selectedExpenses) {
      try {
        await apiRequest(`/users/gastos/edit/${id}/`, {
          method: "DELETE",
          headers: {
            Authorization: `Token ${localStorage.getItem("token")}`,
          },
        });
      } catch (error) {
        console.error("Error al eliminar gasto", id);
      }
    }
    window.location.reload();
  };

  const handlePreviewFile = async (expenseId: number) => {
    const token = localStorage.getItem("token");

    try {
      // Para respuestas de archivos, usar fetch con buildApiUrl
      const response = await fetch(buildApiUrl(`/users/gastos/${expenseId}/file/`), {
        method: "GET",
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("No se pudo cargar el archivo");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPreviewFile({ url, type: blob.type });
    } catch (error) {
      console.error("Error al previsualizar archivo:", error);
    }
  };

  const closePreview = () => setPreviewFile(null);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-ES");
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
    }).format(amount);
  };

  return (
    <div className={styles.expensesContainer}>
      <h3>Gastos del viaje</h3>
      {expenses.length > 0 ? (
        <>
          <div className={styles.expensesTableWrapper}>
            <table className={styles.expensesTable}>
              <thead>
                <tr>
                  <th>Borrar</th>
                  <th>Fecha</th>
                  <th>Concepto</th>
                  <th>Monto</th>
                  <th>Archivo</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <tr key={expense.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedExpenses.includes(expense.id)}
                        onChange={() => handleCheckboxChange(expense.id)}
                      />
                    </td>
                    <td>{formatDate(expense.fecha_gasto)}</td>
                    <td>{expense.concepto}</td>
                    <td>{formatCurrency(expense.monto)}</td>
                    <td>
                      {expense.comprobante ? (
                        <button
                          className={styles.viewFileButton}
                          onClick={() => handlePreviewFile(expense.id)}
                        >
                          📄 Ver archivo
                        </button>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selectedExpenses.length > 0 && (
            <button className={styles.deleteButton} onClick={handleDeleteSelected}>
              Eliminar seleccionados ({selectedExpenses.length})
            </button>
          )}
        </>
      ) : (
        <p>No hay gastos registrados.</p>
      )}

      {previewFile && (
        <div className={styles.filePreviewBackdrop} onClick={closePreview}>
          <div className={styles.filePreviewModal} onClick={(e) => e.stopPropagation()}>
            <button className={styles.closePreviewButton} onClick={closePreview}>
              ✖
            </button>
            {previewFile.type === "application/pdf" ? (
              <iframe src={previewFile.url} className={styles.previewIframe}></iframe>
            ) : (
              <img src={previewFile.url} alt="Archivo adjunto" className={styles.previewImage} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}