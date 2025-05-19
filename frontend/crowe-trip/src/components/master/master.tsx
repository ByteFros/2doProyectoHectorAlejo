import { useState } from 'react';
import Layout from '~/../src/components/common/layout/layout';
import styles from './master.module.scss';

import TripsPerMonthChart from './dashboard/trips-per-month-chart/TripsPerMonthChart';
import CompanyTripsTable from './dashboard/company-trips-table/CompanyTripsTable';
import PendingTripsTable from './dashboard/pending-trips-table/PendingTripsTable';
import GeneralInfoTable from './dashboard/general-info-table/GeneralInfoTable';

import TripsTypePieChart from './dashboard/pie-charts/TripsTypePieChart';
import ExemptDaysPieChart from './dashboard/pie-charts/ExemptDaysPieChart';

import ManageCompaniesPage from './manage-companies/manage-companies-page';

function MasterPage() {
    const [activeSection, setActiveSection] = useState('inicio');

    return (
        <Layout onSectionChange={setActiveSection}>
            <div className={styles.masterContainer}>
                <div
                    className={`${styles.workspace} ${
                        activeSection === 'inicio' ? styles.dashboardScroll : ''
                    }`}
                >
                    {activeSection === 'inicio' && (
                        <div className={styles.dashboardGrid}>
                            {/* 🔹 Parte Superior */}
                            <div className={styles.chartSection}>
                                <TripsPerMonthChart />
                            </div>

                            <div className={styles.tableSection}>
                                <CompanyTripsTable />
                            </div>

                            {/* 🔹 Gráficas de Disco */}
                            <div className={styles.pieChartsRow}>
                                <TripsTypePieChart />
                                <ExemptDaysPieChart />
                            </div>

                            {/* 🔹 Tabla General Info */}
                            <div className={styles.tableSection}>
                                <GeneralInfoTable />
                            </div>

                            {/* 🔹 Tabla Pendientes AL FINAL y EN LÍNEA COMPLETA */}
                            <div className={styles.fullWidthSection}>
                                <PendingTripsTable />
                            </div>

                            {/* 🔹 Espaciador Visual */}
                            <div className={styles.contentEndSpacer}></div>
                        </div>
                    )}
                    {activeSection === 'gestionar' && <ManageCompaniesPage />}
                </div>
            </div>
        </Layout>
    );
}

export default MasterPage;
