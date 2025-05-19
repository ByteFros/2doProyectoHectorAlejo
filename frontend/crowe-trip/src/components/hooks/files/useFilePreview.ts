import { useState, useCallback, useEffect } from 'react';
import useAuth from '../use-auth';

// Define the allowed file categories/endpoints
export type FileCategory = 'mensaje' | 'justificante' | 'gasto';

// Optional extra info when previewing an expense-related file
export interface ExpenseInfo {
  concepto: string;
  monto: number;
  fecha?: string;
}

// Structure for the previewed file
export interface PreviewFile {
  url: string;
  type: string;
  name: string;
  expenseInfo?: ExpenseInfo;
}

const API_BASE = 'http://127.0.0.1:8000/api/users';

// Helper: build the correct URL according to category and ID
function buildFileUrl(category: FileCategory, id: number): string {
  switch (category) {
    case 'mensaje':
      return `${API_BASE}/mensajes/${id}/file/`;
    case 'justificante':
      return `${API_BASE}/mensajes/justificante/${id}/file/`;
    case 'gasto':
      return `${API_BASE}/gastos/${id}/file/`;
    default:
      throw new Error(`Unknown file category: ${category}`);
  }
}

// Helper: parse filename from Content-Disposition header
function parseFilename(disposition: string | null, fallback: string): string {
  if (!disposition) return fallback;
  const match = disposition.match(/filename\*=UTF-8''(.+)$|filename="?([^";]+)"?/);
  return match ? decodeURIComponent(match[1] || match[2]) : fallback;
}

export default function useFilePreview() {
  const [previewFile, setPreviewFile] = useState<PreviewFile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuth();

  // Cleanup object URL on unmount or when previewFile changes
  useEffect(() => {
    return () => {
      if (previewFile) {
        URL.revokeObjectURL(previewFile.url);
      }
    };
  }, [previewFile]);

  const openPreview = useCallback(
    async (
      id: number,
      category: FileCategory,
      expenseInfo?: ExpenseInfo
    ) => {
      setIsLoading(true);
      try {
        const url = buildFileUrl(category, id);
        const response = await fetch(url, {
          method: 'GET',
          headers: { Authorization: `Token ${token}` },
        });
        if (!response.ok) throw new Error('Archivo no encontrado');

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const disposition = response.headers.get('Content-Disposition');
        const filename = parseFilename(disposition, `file-${id}`);

        setPreviewFile({
          url: objectUrl,
          type: blob.type,
          name: filename,
          expenseInfo,
        });
      } catch (error) {
        console.error(error);
        alert('No se pudo cargar el archivo');
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  const closePreview = useCallback(() => {
    if (previewFile) {
      URL.revokeObjectURL(previewFile.url);
      setPreviewFile(null);
    }
  }, [previewFile]);

  const downloadFile = useCallback(() => {
    if (!previewFile) return;
    const link = document.createElement('a');
    link.href = previewFile.url;
    link.download = previewFile.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [previewFile]);

  return {
    previewFile,
    isLoading,
    openPreview,
    closePreview,
    downloadFile,
  };
}
