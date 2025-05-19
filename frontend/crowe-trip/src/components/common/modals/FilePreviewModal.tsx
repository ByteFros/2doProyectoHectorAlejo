// components/FilePreviewModal.tsx
import React from 'react';
import styles from './travel-trip-calendar.module.scss';

interface ExpenseInfo {
    concepto: string;
    monto: number;
    fecha?: string;
}

interface FilePreviewProps {
    file: {
        url: string;
        type: string;
        name?: string;
        expenseInfo?: ExpenseInfo;
    };
    isLoading: boolean;
    onClose: () => void;
    onDownload: () => void;
    getFileTypeIcon: (type: string) => string;
    formatDate: (dateString: string) => string;
}

const FilePreviewModal: React.FC<FilePreviewProps> = ({
    file,
    isLoading,
    onClose,
    onDownload,
    getFileTypeIcon,
    formatDate,
}) => {
    const getPreviewContent = () => {
        if (isLoading) {
            return <div className={styles.loadingIndicator}>Cargando archivo...</div>;
        }

        if (file.type.includes('pdf')) {
            return (
                <embed
                    src={file.url}
                    type="application/pdf"
                    className={styles.previewObject}
                    width="100%"
                    height="100%"
                />
            );
        }

        if (file.type.includes('image')) {
            return (
                <img
                    src={file.url}
                    alt="Justificante"
                    className={styles.previewImage}
                    onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.onerror = null;
                        target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24"><path fill="%23f87171" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>';
                    }}
                />
            );
        }

        return (
            <object
                data={file.url}
                type={file.type}
                className={styles.previewObject}
            >
                <div className={styles.fileError}>
                    <p>No se puede mostrar este tipo de archivo ({file.type}).</p>
                    <a href={file.url} target="_blank" rel="noopener noreferrer">
                        Abrir en nueva pestaña
                    </a>
                </div>
            </object>
        );
    };

    return (
        <div className={styles.filePreviewBackdrop} onClick={onClose}>
            <div
                className={`${styles.filePreviewModal} ${file.type.includes('pdf') ? styles.pdfPreview : styles.imagePreview}`}
                onClick={(e) => e.stopPropagation()}
            >
                <div className={styles.filePreviewHeader}>
                    <h3 className={styles.filePreviewTitle}>
                        <span className={`${styles.fileTypeIcon} ${file.type.includes('pdf') ? styles.pdfIcon : styles.imageIcon}`}>
                            {getFileTypeIcon(file.type)}
                        </span>
                        {file.expenseInfo?.concepto}
                        {file.expenseInfo?.fecha && (
                            <small style={{ marginLeft: '8px', color: '#6b7280', fontWeight: 'normal' }}>
                                ({formatDate(file.expenseInfo.fecha)})
                            </small>
                        )}
                    </h3>
                    <div className={styles.fileActions}>
                        
                        {/* Añadida la clase downloadButton para evitar superposición */}
                        <button className={`${styles.fileActionButton} ${styles.downloadButton}`} onClick={onDownload}>
                            Descargar
                        </button>
                    </div>
                    <button className={styles.closePreviewButton} onClick={onClose}>✖</button>
                </div>

                <div className={styles.filePreviewContent}>{getPreviewContent()}</div>
            </div>
        </div>
    );
};

export default FilePreviewModal;