import React, { useState } from 'react';
import styles from './employee-cities-table.module.scss';
import useEmployeeCityStats from '~/components/hooks/useEmployeeCityStats';

function EmployeeCitiesTable() {
  const { cities, loading } = useEmployeeCityStats();
  const [sortKey, setSortKey] = useState<'city' | 'trips' | 'days' | 'nonExemptDays' | 'exemptDays'>('city');
  const [sortAsc, setSortAsc] = useState(true);

  const handleSort = (key: typeof sortKey) => {
    if (key === sortKey) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  const renderSortArrow = (key: typeof sortKey) => {
    if (sortKey !== key) return null;
    return sortAsc ? ' ▲' : ' ▼';
  };

  const sortedData = [...cities].sort((a, b) => {
    const valA = a[sortKey];
    const valB = b[sortKey];

    if (sortKey === 'city') {
      return sortAsc
        ? (valA as string).localeCompare(valB as string)
        : (valB as string).localeCompare(valA as string);
    } else {
      return sortAsc
        ? (valA as number) - (valB as number)
        : (valB as number) - (valA as number);
    }
  });

  if (loading) {
    return <p className={styles.loading}>Cargando destinos visitados...</p>;
  }

  if (cities.length === 0) {
    return <p className={styles.noResultsMessage}>No se han registrado viajes aún.</p>;
  }

  return (
    <div className={styles.companyTableWrapper}>
      <table className={styles.companyTable}>
        <thead>
          <tr>
            <th
              className={`${styles.companyHeader} ${sortKey === 'city' ? styles.active : ''}`}
              onClick={() => handleSort('city')}
            >
              Ciudad{renderSortArrow('city')}
            </th>
            <th
              className={`${styles.companyHeader} ${sortKey === 'trips' ? styles.active : ''}`}
              onClick={() => handleSort('trips')}
            >
              Viajes{renderSortArrow('trips')}
            </th>
            <th
              className={`${styles.companyHeader} ${sortKey === 'days' ? styles.active : ''}`}
              onClick={() => handleSort('days')}
            >
              Días{renderSortArrow('days')}
            </th>
            <th
              className={`${styles.companyHeader} ${sortKey === 'nonExemptDays' ? styles.active : ''}`}
              onClick={() => handleSort('nonExemptDays')}
            >
              Días no exentos{renderSortArrow('nonExemptDays')}
            </th>
            <th
              className={`${styles.companyHeader} ${sortKey === 'exemptDays' ? styles.active : ''}`}
              onClick={() => handleSort('exemptDays')}
            >
              Días exentos{renderSortArrow('exemptDays')}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((entry, idx) => (
            <tr key={idx}>
              <td className={styles.companyCell}>{entry.city}</td>
              <td className={styles.companyCell}>{entry.trips}</td>
              <td className={styles.companyCell}>{entry.days}</td>
              <td className={styles.companyCell}>{entry.nonExemptDays}</td>
              <td className={styles.companyCell}>{entry.exemptDays}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default EmployeeCitiesTable;
