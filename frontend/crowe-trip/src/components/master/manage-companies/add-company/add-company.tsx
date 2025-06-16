// components/manage-companies/add-company/add-company.tsx
import { useState } from "react";
import styles from "./add-company.module.scss";
import { FaBuilding, FaIdCard, FaMapMarkerAlt, FaCogs } from "react-icons/fa";
import useAuth from "~/components/hooks/use-auth";
import { apiRequest } from '@config/api';

export type Empresa = {
    id: number;
    nombre: string;
    nif: string;
    domicilio: string;
    autogestion: boolean;
};

type Props = {
    onAddCompany: (empresa: Empresa) => void;
};

export default function AddCompany({ onAddCompany }: Props) {
  const [form, setForm] = useState({
    nombre: "",
    nif: "",
    domicilio: "",
    correo: "",
    autogestion: false,
  });

  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { token } = useAuth();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    const isCheckbox = type === "checkbox";

    setForm({
      ...form,
      [name]: isCheckbox ? (e.target as HTMLInputElement).checked : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const res = await apiRequest("/users/empresas/new/", {
        method: "POST",
        headers: {
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify({
          nombre_empresa: form.nombre,
          nif: form.nif,
          address: form.domicilio,
          city: "",
          postal_code: "",
          correo_contacto: form.correo,
          permisos: form.autogestion,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || "Error al registrar la empresa");
      }

      const newEmpresa = await res.json();

      onAddCompany({
        id: newEmpresa.id,
        nombre: newEmpresa.nombre_empresa,
        nif: newEmpresa.nif,
        domicilio: newEmpresa.address,
        autogestion: newEmpresa.permisos,
      });

      setSubmitted(true);
      setForm({
        nombre: "",
        nif: "",
        domicilio: "",
        correo: "",
        autogestion: false,
      });

      setTimeout(() => setSubmitted(false), 3000);
    } catch (err: any) {
      setError(err.message);
    }
  };

    return (
        <div className={styles.formContainer}>
            <form onSubmit={handleSubmit} className={styles.form}>
                {submitted && (
                    <div className={styles.successMessage}>
                        Empresa registrada correctamente.
                    </div>
                )}
                <div className={styles.inputGroup}>
                    <label htmlFor="nombre">
                        <FaBuilding /> Nombre de la empresa
                    </label>
                    <input
                        type="text"
                        id="nombre"
                        name="nombre"
                        value={form.nombre}
                        onChange={handleChange}
                        placeholder="Ej. Crowe Trip SL"
                        required
                    />
                </div>

                <div className={styles.inputGroup}>
                    <label htmlFor="nif">
                        <FaIdCard /> NIF
                    </label>
                    <input
                        type="text"
                        id="nif"
                        name="nif"
                        value={form.nif}
                        onChange={handleChange}
                        placeholder="Ej. B12345678"
                        required
                    />
                </div>

        <div className={styles.inputGroup}>
          <label htmlFor="domicilio">
            <FaMapMarkerAlt /> Domicilio Social
          </label>
          <input
            type="text"
            id="domicilio"
            name="domicilio"
            value={form.domicilio}
            onChange={handleChange}
            placeholder="Ej. C/ Gran Vía, 123, Madrid"
            required
          />
        </div>

        <div className={styles.inputGroup}>
          <label htmlFor="correo">
            <FaIdCard /> Correo electrónico
          </label>
          <input
            type="email"
            id="correo"
            name="correo"
            value={form.correo}
            onChange={handleChange}
            placeholder="ejemplo@empresa.com"
            required
          />
        </div>

                <div className={styles.checkboxGroup}>
                    <label htmlFor="autogestion">
                        <input
                            type="checkbox"
                            id="autogestion"
                            name="autogestion"
                            checked={form.autogestion}
                            onChange={handleChange}
                        />
                        <FaCogs />
                        Permitir autogestión de viajesx
                    </label>
                </div>

        <button type="submit" className={styles.submitButton}>
          Registrar empresa
        </button>
      </form>

      {submitted && (
        <p className={styles.successMessage}>✅ Empresa registrada correctamente.</p>
      )}
      {error && <p className={styles.errorMessage}>❌ {error}</p>}
    </div>
  );
}
