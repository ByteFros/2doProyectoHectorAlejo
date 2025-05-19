// 📁 company-page.tsx (Reescrito para usar useAuth global)

import { useState, useEffect } from "react";
import Layout from "~/../src/components/common/layout/layout";
import ForceChangePassword from "~/../src/components/common/force-change-password/force-change-password";
import styles from "./company.module.scss";
import useAuth from "../hooks/use-auth";

import useMockTripsStats from '../hooks/useMockTripsStats';
import EmployeeTripsChart from '~/components/company/dashboard/employee-trips-chart/EmployeeTripsChart';
import EmployeeTripsTable from '~/components/company/dashboard/employee-trips-table/EmployeeTripsTable';
import EmployeeTripsTypePieChart from './dashboard/pie-charts/TripsTypePieChart';
import EmployeeExemptDaysPieChart from './dashboard/pie-charts/ExemptDaysPieChart';
import ManageEmployeesPage from './manage-employees/manage-employees-page';
import EmployeeSummaryTable from '~/components/company/dashboard/employee-summary-table/EmployeeSummaryTable';
import EmployeePendingTripsTable from '~/components/company/dashboard/employee-pending-trips-table/EmployeePendingTripsTable';
import TripsChartContainer from "./dashboard/pie-charts/TripsChartContainer";
import TripsChartWrapper from "./dashboard/pie-charts/TripsChartWrapper";
import useGeneralInfo from "../hooks/trips/useGeneralInfo";

function CompanyPage() {
  const { mustChangePassword, updatePasswordStatus } = useAuth();
  const [activeSection, setActiveSection] = useState('inicio');
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const stats = useMockTripsStats();
  const { data, loading } = useGeneralInfo();

  useEffect(() => {
    if (mustChangePassword) {
      setIsPasswordModalOpen(true);
    }
  }, [mustChangePassword]);

  const handlePasswordChange = () => {
    updatePasswordStatus(true);
    setIsPasswordModalOpen(false);
  };

  return (
    <Layout onSectionChange={setActiveSection}>
      <div className={styles.companyContainer}>
        <div
          className={`${styles.workspace} ${
            activeSection === 'inicio' ? styles.dashboardScroll : ''
          }`}
        >
          {mustChangePassword ? (
            <p className={styles.blockedMessage}>
              🔒 Debes cambiar tu contraseña antes de acceder.
            </p>
          ) : (
            <>
              {activeSection === 'inicio' && (
                <div className={styles.dashboardGrid}>
                  {/* Gráfico de viajes por mes */}
                  <div className={styles.chartSection}>
                    <EmployeeTripsChart />
                  </div>

                  {/* Tabla de empleados */}
                  <div className={styles.tableSection}>
                    <EmployeeTripsTable />
                  </div>

                  {/* Gráficas pie */}
                  <div className={styles.pieChartsRow}>
                    <TripsChartContainer
                    />
                    <TripsChartWrapper
                    />
                  </div>

                  {/* Tabla de resumen total */}
                  <div className={styles.fullWidthSection}>
                    <EmployeeSummaryTable
                      totalEmpleados={data.employees}
                      viajesInternacionales={data.international_trips}
                      viajesNacionales={data.national_trips}
                    />
                  </div>

                  {/* Tabla de viajes pendientes por empleado */}
                  <div className={styles.fullWidthSection}>
                    <EmployeePendingTripsTable />
                  </div>

                  <div className={styles.contentEndSpacer}></div>
                </div>
              )}

              {activeSection === 'gestionar' && <ManageEmployeesPage />}
              {!['inicio', 'agregar', 'gestionar'].includes(activeSection) && (
                <p>Selecciona una opción del menú</p>
              )}
            </>
          )}
        </div>
      </div>

      {isPasswordModalOpen && (
        <ForceChangePassword onPasswordChange={handlePasswordChange} />
      )}
    </Layout>
  );
}

export default CompanyPage;