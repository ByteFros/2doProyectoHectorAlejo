// components/manage-companies/manage-companies-page.tsx
import { useState, useRef, useEffect } from "react";
import AddCompany from "./add-company/add-company";
import CompanyTable from "./company-table/company-table";
import styles from "./manage-companies-page.module.scss";
import useCompanies from "~/components/hooks/useCompanies";

export interface Empresa {
  id: number;
  nombre: string;
  nif: string;
  domicilio: string;
  autogestion: boolean;
}

export default function ManageCompaniesPage() {
  const [activeTab, setActiveTab] = useState("add");
  const [isSticky, setIsSticky] = useState(false);

  const {
    companies,
    loading,
    error,
    deleteCompany,
    toggleAutogestion,
    refetch,
  } = useCompanies();

  const buttonGroupRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (buttonGroupRef.current) {
        const headerHeight = 60;
        const top = buttonGroupRef.current.getBoundingClientRect().top;
        setIsSticky(top <= headerHeight);
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleAddCompany = () => {
    refetch(); // recargar empresas desde backend después de agregar
  };

  const handleDeleteCompany = (id: number) => {
    deleteCompany(id);
  };

  const handleToggleAutogestion = (id: number) => {
    const empresa = companies.find((e) => e.id === id);
    if (empresa) toggleAutogestion(id, empresa.autogestion);
  };

  return (
    <div className={styles.container}>
      <div
        ref={buttonGroupRef}
        className={`${styles.buttonGroup} ${isSticky ? styles.sticky : ""}`}
      >
        <button
          className={activeTab === "add" ? styles.active : ""}
          onClick={() => setActiveTab("add")}
        >
          Agregar empresa
        </button>
        <button
          className={activeTab === "manage" ? styles.active : ""}
          onClick={() => setActiveTab("manage")}
        >
          Gestionar empresas
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === "add" && <AddCompany onAddCompany={handleAddCompany} />}
        {activeTab === "manage" && (
          <CompanyTable
            companies={companies}
            onDelete={handleDeleteCompany}
            onToggleAutogestion={handleToggleAutogestion}
          />
        )}
      </div>
    </div>
  );
}
