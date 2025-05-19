import React, { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import 'chart.js/auto';
import styles from './employee-trips-chart.module.scss';
import useTripsChart from '../../../hooks/useTripsChart';

const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

function EmployeeTripsChart() {
  const [showSecondHalf, setShowSecondHalf] = useState(new Date().getMonth() >= 6);
  const { monthlyData, loading } = useTripsChart();

  const start = showSecondHalf ? 6 : 0;
  const end = showSecondHalf ? 12 : 6;

  const data = {
    labels: months.slice(start, end),
    datasets: [
      {
        label: 'Días viajados',
        data: monthlyData.slice(start, end),
        backgroundColor: '#4e73df',
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `Días Viajados (${showSecondHalf ? 'Jul - Dic' : 'Ene - Jun'})`,
      },
    },
  };

  if (loading) return <p className={styles.chartWrapper}>Cargando gráfico...</p>;

  return (
    <div className={styles.chartWrapper}>
      <div className={styles.toggleContainer}>
        <button onClick={() => setShowSecondHalf(!showSecondHalf)}>
          {showSecondHalf ? '← Ver Ene - Jun' : 'Ver Jul - Dic →'}
        </button>
      </div>
      <Bar data={data} options={options} />
    </div>
  );
}

export default EmployeeTripsChart;
