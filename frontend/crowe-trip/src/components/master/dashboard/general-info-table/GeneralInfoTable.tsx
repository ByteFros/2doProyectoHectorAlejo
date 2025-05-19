// components/tables/GeneralInfoTable.tsx
import styles from './general-info-table.module.scss';
import useGeneralInfo from '~/components/hooks/trips/useGeneralInfo';

const GeneralInfoTable = () => {
  const { data, loading } = useGeneralInfo();
  if (loading) {
    return <p className={styles.infoTableWrapper}>Cargando datos…</p>;
  }

  return (
    <div className={styles.infoTableWrapper}>
      <table className={styles.infoTable}>
        <thead>
          <tr>
            <th>Total Empresas</th>
            <th>Total Empleados</th>
            <th>Viajes Internacionales</th>
            <th>Viajes Nacionales</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{data.companies}</td>
            <td>{data.employees}</td>
            <td>{data.international_trips}</td>
            <td>{data.national_trips}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default GeneralInfoTable;
