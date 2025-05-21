import { useState } from 'react';
import Layout from '~/../src/components/common/layout/layout';
import TravelPage from './travel/travel-page';
import styles from './employee.module.scss';

import EmployeeTripsChart from './dashboard/employee-trips-chart/EmployeeTripsChart';
import EmployeeCitiesTable from './dashboard/employee-cities-table/EmployeeCitiesTable';
import NationalityPieChart from './dashboard/employee-pie-charts/NationalityPieChart';
import ExemptDaysPieChart from './dashboard/employee-pie-charts/ExemptDaysPieChart';
import EmployeeTravelSummary from './dashboard/employee-travel-summary/EmployeeTravelSummary';

function EmployeePage() {
  const [activeSection, setActiveSection] = useState('inicio');

  return (
    <Layout onSectionChange={setActiveSection}>
      <div className={styles.employeeContainer}>
        <div
          className={`${styles.workspace} ${
            activeSection === 'inicio' ? styles.dashboardScroll : ''
          }`}
        >
          {activeSection === 'inicio' && (
            <div className={styles.dashboardGrid}>
              {/* Parte superior: gráfica y tabla */}
              <div className={styles.chartSection}>
                <EmployeeTripsChart />
              </div>
              <div className={styles.tableSection}>
                <EmployeeCitiesTable />
              </div>

              {/* Gráficas pie */}
              <div className={styles.pieChartsRow}>
                <NationalityPieChart />
                <ExemptDaysPieChart />
              </div>

              {/* Resumen */}
              <div className={styles.fullWidthSection}>
                <EmployeeTravelSummary />
              </div>

              <div className={styles.contentEndSpacer}></div>
            </div>
          )}

          {activeSection === 'viajes' && <TravelPage />}

          {!['inicio', 'mensajes', 'viajes'].includes(activeSection) && (
            <p>Selecciona una opción del menú</p>
          )}
        </div>
      </div>
    </Layout>
  );
}

export default EmployeePage;
