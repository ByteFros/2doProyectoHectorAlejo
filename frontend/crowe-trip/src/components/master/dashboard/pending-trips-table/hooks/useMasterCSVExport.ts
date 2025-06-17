// hooks/useCSVExport.ts
import useAuth from "~/components/hooks/use-auth";
import { apiFetch } from "~/utils/api";

export default function useCSVExport() {
  const { token, role } = useAuth();

  const exportCSV = async () => {
    if (!token || !role) {
      console.warn('🔴 No hay token o rol disponible');
      return;
    }

    const endpoint = role === 'MASTER'
      ? '/api/users/export/viajes/exportar/'
      : '/api/users/export/empresa/viajes/exportar/';

    const filename = role === 'MASTER'
      ? 'viajes_todas_empresas.csv'
      : 'viajes_empresa.csv';

    try {
      const response = await apiFetch(endpoint, {
        method: 'GET',
      }, true); // Indicamos que requiere autenticación

      if (!response.ok) {
        throw new Error(`No se pudo generar el CSV. Código ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Liberamos el objeto URL una vez descargado
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 100);
    } catch (error) {
      console.error('❌ Error al exportar CSV:', error);
      alert('Error al exportar el archivo. Inténtalo nuevamente.');
    }
  };

  return { exportCSV };
}