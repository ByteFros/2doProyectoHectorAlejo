import React from 'react';
import styles from './employee-travel-summary.module.scss';
import useEmployeeTravelSummary from '~/components/hooks/useEmployeeTravelSummary';

function EmployeeTravelSummary() {
  const { summary, loading } = useEmployeeTravelSummary();

  if (loading) {
    return <p className={styles.loading}>Cargando resumen de viajes...</p>;
  }

  if (!summary) {
    return <p className={styles.errorMessage}>No se pudo cargar el resumen.</p>;
  }

  return (
    <div className={styles.summaryTable}>
      <table>
        <thead>
          <tr>
            <th>Total de viajes</th>
            <th>Días totales de viaje</th>
            <th>Total viajes nacionales</th>
            <th>Total viajes internacionales</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{summary.total}</td>
            <td>{summary.total_days}</td>
            <td>{summary.national}</td>
            <td>{summary.international}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
  
}

export default EmployeeTravelSummary;
