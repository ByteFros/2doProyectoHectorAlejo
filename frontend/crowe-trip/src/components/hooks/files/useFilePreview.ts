// hooks/useFilePreview.ts
import { useState, useCallback, useEffect } from 'react';
import useAuth from '../use-auth';
import { apiFetch } from '~/utils/api';

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

// Helper: build the correct endpoint path according to category and ID
function buildFilePath(category: FileCategory, id: number): string {
  switch (category) {
    case 'mensaje':
      return `/api/users/mensajes/${id}/file/`;
    case 'justificante':
      return `/api/users/mensajes/justificante/${id}/file/`;
    case 'gasto':
      return `/api/users/gastos/${id}/file/`;
    default:
      throw new Error(`Categoría de archivo desconocida: ${category}`);
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
      if (!token) {
        console.error('❌ No hay token de autenticación');
        return;
      }

      setIsLoading(true);
      
      try {
        const endpoint = buildFilePath(category, id);
        
        const response = await apiFetch(endpoint, {
          method: 'GET',
        }, true);
        
        if (!response.ok) {
          throw new Error('Archivo no encontrado');
        }

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
        console.error('❌ Error al cargar el archivo:', error);
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