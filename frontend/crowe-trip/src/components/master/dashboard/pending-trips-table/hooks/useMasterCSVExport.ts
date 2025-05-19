// hooks/useCSVExport.ts
import useAuth from "~/components/hooks/use-auth";

export default function useCSVExport() {
  const { token, role } = useAuth();

  const exportCSV = async () => {
    if (!token || !role) {
      console.warn('🔴 No hay token o rol disponible');
      return;
    }

    const endpoint = role === 'MASTER'
      ? 'http://127.0.0.1:8000/api/users/export/viajes/exportar/'
      : 'http://127.0.0.1:8000/api/users/export/empresa/viajes/exportar/';

    const filename = role === 'MASTER'
      ? 'viajes_todas_empresas.csv'
      : 'viajes_empresa.csv';

    try {
      const res = await fetch(endpoint, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`No se pudo generar el CSV. Código ${res.status}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('❌ Error al exportar CSV:', error);
      alert('Error al exportar el archivo. Inténtalo nuevamente.');
    }
  };

  return { exportCSV };
}
