// components/charts/ExemptDaysPieChart.tsx

import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import styles from './pie-chart.module.scss';
import useExemptDays from '~/components/hooks/trips/useExemptDays';

ChartJS.register(ArcElement, Tooltip, Legend);

const ExemptDaysPieChart = () => {
  const { data, loading } = useExemptDays();

  if (loading) {
    return <p className={styles.pieChartContainer}>Cargando datos…</p>;
  }

  const chartData = {
    labels: ['Total días exentos', 'Total días no exentos'],
    datasets: [
      {
        data: [data.exempt, data.nonExempt],
        backgroundColor: ['#4BC0C0', '#FFCE56'],
        hoverBackgroundColor: ['#4BC0C0', '#FFCE56'],
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
  };

  return (
    <div className={styles.pieChartContainer}>
      <h4>Días exentos y no exentos</h4>
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default ExemptDaysPieChart;
