// components/tables/company-trips-table.tsx
import React, { useState, Fragment } from 'react';
import styles from './company-trips-table.module.scss';
import useCompanyTripsSummary from '~/components/hooks/trips/useCompanyTripsSummary';
import useMasterEmployeesByCompany from '~/components/hooks/trips/useMasterEmployeesByCompany';

const CompanyTripsTable = () => {
  const { data: companyTrips, loading: loadingCompanies } = useCompanyTripsSummary();
  const { employees, loading: loadingEmployees, error: employeesError, fetchEmployeesByCompany } = useMasterEmployeesByCompany();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);

  if (loadingCompanies) return <div>Cargando datos de empresas...</div>;

  // Filtramos las empresas según el término de búsqueda
  const filteredTrips = companyTrips.filter((c) =>
    c.empresa.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Manejamos la selección de una empresa
  const handleSelectCompany = (company: { empresa: string; empresa_id: number }) => {
    // Si es la misma empresa que ya está seleccionada, la deseleccionamos
    if (selectedCompany === company.empresa) {
      setSelectedCompany(null);
      setSelectedCompanyId(null);
      return;
    }
    
    // Seleccionamos la empresa y cargamos sus empleados
    setSelectedCompany(company.empresa);
    setSelectedCompanyId(company.empresa_id.toString());
    
    // Usamos el empresa_id para hacer la consulta
    fetchEmployeesByCompany(company.empresa_id.toString());
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Buscar empresa..."
        className={styles.searchInput}
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          setSelectedCompany(null);
          setSelectedCompanyId(null);
        }}
      />

      <div className={styles.companyTableWrapper}>
        <table className={styles.companyTable}>
          <thead>
            <tr>
              <th className={styles.companyHeader}>Empresa</th>
              <th className={styles.companyHeader}>Viajes</th>
              <th className={styles.companyHeader}>Días</th>
              <th className={styles.companyHeader}>Días no exentos</th>
              <th className={styles.companyHeader}>Días exentos</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrips.map((company, i) => (
              <Fragment key={i}>
                <tr
                  className={styles.companyRow}
                  onClick={() => handleSelectCompany(company)}
                  style={{ cursor: 'pointer' }}
                >
                  <td className={styles.companyCell}>{company.empresa}</td>
                  <td className={styles.companyCell}>{company.trips}</td>
                  <td className={styles.companyCell}>{company.days}</td>
                  <td className={styles.companyCell}>{company.nonExemptDays}</td>
                  <td className={styles.companyCell}>
                    {company.days - company.nonExemptDays}
                  </td>
                </tr>
                {selectedCompany === company.empresa && (
                  <tr>
                    <td colSpan={5} className={styles.companyCell}>
                      <div className={styles.employeeScroll}>
                        {loadingEmployees ? (
                          <div className={styles.loadingEmployees}>
                            Cargando empleados...
                          </div>
                        ) : employeesError ? (
                          <div className={styles.errorMessage}>
                            {employeesError}
                          </div>
                        ) : (
                          <table className={styles.companyTable}>
                            <thead>
                              <tr>
                                <th className={styles.companyHeader}>Empleado</th>
                                <th className={styles.companyHeader}>Viajes</th>
                                <th className={styles.companyHeader}>Días totales</th>
                                <th className={styles.companyHeader}>Días exentos</th>
                                <th className={styles.companyHeader}>Días no exentos</th>
                              </tr>
                            </thead>
                            <tbody>
                              {employees.length > 0 ? (
                                employees.map((e, idx) => (
                                  <tr key={idx}>
                                    <td className={styles.companyCell}>{e.name}</td>
                                    <td className={styles.companyCell}>{e.trips}</td>
                                    <td className={styles.companyCell}>{e.travelDays}</td>
                                    <td className={styles.companyCell}>{e.exemptDays}</td>
                                    <td className={styles.companyCell}>{e.nonExemptDays}</td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan={5} className={styles.noEmployeesMessage}>
                                    No hay información de empleados disponible para esta empresa.
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {filteredTrips.length === 0 && (
              <tr>
                <td colSpan={5} className={styles.noResultsMessage}>
                  No se encontraron empresas que coincidan con la búsqueda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CompanyTripsTable;