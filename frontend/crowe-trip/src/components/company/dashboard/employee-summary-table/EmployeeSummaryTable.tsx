// components/EmployeeSummaryTable.tsx
import React from 'react';
import styles from './employee-summary-table.module.scss';

interface EmployeeSummaryTableProps {
  totalEmpleados: number;
  viajesInternacionales: number;
  viajesNacionales: number;
}

const EmployeeSummaryTable: React.FC<EmployeeSummaryTableProps> = ({
  totalEmpleados,
  viajesInternacionales,
  viajesNacionales,
}) => (
  <div className={styles.tableWrapper}>
    <table className={styles.summaryTable}>
      <thead>
        <tr>
          <th>Total de empleados</th>
          <th>Viajes internacionales</th>
          <th>Viajes nacionales</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{totalEmpleados}</td>
          <td>{viajesInternacionales}</td>
          <td>{viajesNacionales}</td>
        </tr>
      </tbody>
    </table>
  </div>
);

export default EmployeeSummaryTable;
