import { Bar } from 'react-chartjs-2';
import { 
  Chart as ChartJS, 
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from 'chart.js';
import { useState } from 'react';
import styles from './trips-per-month-chart.module.scss';
import useTripsPerMonth from '~/components/hooks/trips/useTripsPerMonth';

// Register ChartJS components
ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const TripsPerMonthChart = () => {
  // Usar el hook real en lugar del mock
  const { data, loading } = useTripsPerMonth();

  if (loading) {
    return (
      <div className={styles.chartWrapper}>
        <p className={styles.loadingText}>Cargando gráfico...</p>
      </div>
    );
  }

  // Process data to match the format needed for the chart
  const monthLabels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  const totals = Array(12).fill(0);

  data.forEach(({ month, totalDays }) => {
    const m = parseInt(month.split('-')[1], 10) - 1;
    if (m >= 0 && m < 12) totals[m] = totalDays;
  });

  const chartData = {
    labels: monthLabels,
    datasets: [
      {
        label: 'Viajes por mes',
        data: totals,
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { 
        beginAtZero: true 
      },
    },
    barPercentage: 0.9,    // Controla el ancho de todas las barras como porcentaje del espacio disponible
    categoryPercentage: 0.9,  // Controla el espacio entre categorías (meses)
  };

  return (
    <div className={styles.chartWrapper}>
      <Bar data={chartData} options={options} height={250} />
    </div>
  );
};

export default TripsPerMonthChart;