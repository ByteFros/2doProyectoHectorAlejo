import React from 'react';
import useExemptDays from '~/components/hooks/trips/useExemptDays';
import ExemptDaysPieChart from './ExemptDaysPieChart';

const ExemptDaysPieChartWrapper = () => {
  const { data, loading } = useExemptDays();

  if (loading) {
    return <p>Cargando gráfico de días exentos...</p>;
  }

  return (
    <ExemptDaysPieChart
      data={{
        exentos: data.exempt,
        noExentos: data.nonExempt,
      }}
    />
  );
};

export default ExemptDaysPieChartWrapper;
