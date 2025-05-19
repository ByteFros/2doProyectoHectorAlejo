import React, { useState } from 'react';
import styles from './company-table.module.scss';
import { Empresa } from '../manage-companies-page';
import ConfirmModal from '../../../common/confirm-modal/confirm-modal';

interface Props {
    companies: Empresa[];
    onDelete: (id: number) => void;
    onToggleAutogestion: (id: number) => void;
}

const CompanyTable: React.FC<Props> = ({ companies, onDelete, onToggleAutogestion }) => {
    const [selectedCompany, setSelectedCompany] = useState<Empresa | null>(null);
    const [localDeletedId, setLocalDeletedId] = useState<number | null>(null);

    const handleDeleteClick = (empresa: Empresa) => {
        setSelectedCompany(empresa);
    };

    const confirmDelete = () => {
        if (selectedCompany) {
            setLocalDeletedId(selectedCompany.id);
            setSelectedCompany(null); 

            setTimeout(() => {
                onDelete(selectedCompany.id);
                setLocalDeletedId(null);
            }, 400);
        }
    };

    const cancelDelete = () => {
        setSelectedCompany(null);
    };

    return (
        <div className={styles.tableWrapper}>
            <table className={styles.table}>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>NIF</th>
                        <th>Domicilio</th>
                        <th>Autogestión</th>
                        <th>Eliminar</th>
                    </tr>
                </thead>
                <tbody>
                    {companies.length === 0 ? (
                        <tr>
                            <td colSpan={5} className={styles.noData}>
                                No hay empresas registradas.
                            </td>
                        </tr>
                    ) : (
                        companies.map((empresa) => (
                            <tr
                                key={empresa.id}
                                className={empresa.id === localDeletedId ? styles.fadeOutRow : ''}
                            >
                                <td title={empresa.nombre}>{empresa.nombre}</td>
                                <td>{empresa.nif}</td>
                                <td title={empresa.domicilio}>{empresa.domicilio}</td>
                                <td className={styles.checkboxCell}>
                                    <input
                                        type="checkbox"
                                        checked={empresa.autogestion}
                                        onChange={() => onToggleAutogestion(empresa.id)}
                                    />
                                </td>
                                <td>
                                    <button
                                        className={styles.deleteBtn}
                                        onClick={() => handleDeleteClick(empresa)}
                                    >
                                        Eliminar
                                    </button>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>

            {selectedCompany && (
                <ConfirmModal
                    message={`¿Estás seguro que quieres eliminar la empresa "${selectedCompany.nombre}"?`}
                    onConfirm={confirmDelete}
                    onCancel={cancelDelete}
                />
            )}
        </div>
    );
};

export default CompanyTable;
