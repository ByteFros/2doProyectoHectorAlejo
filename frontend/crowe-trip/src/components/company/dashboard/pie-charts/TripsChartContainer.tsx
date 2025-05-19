// TripsChartContainer.tsx
import React from 'react';
import TripsTypePieChart from './TripsTypePieChart';
import useTripsType from '~/components/hooks/trips/useTripsType';

const TripsChartContainer: React.FC = () => {
  const { data, loading } = useTripsType();
  
  if (loading) {
    return <div>Cargando datos de viajes...</div>;
  }
  
  // Adaptación de los datos del hook a la estructura esperada por el gráfico
  const chartData = {
    nacionales: data.national,
    internacionales: data.international
  };
  
  return <TripsTypePieChart data={chartData} />;
};

export default TripsChartContainer;