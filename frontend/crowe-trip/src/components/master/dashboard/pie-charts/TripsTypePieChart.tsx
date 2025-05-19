// components/charts/TripsTypePieChart.tsx
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import styles from './pie-chart.module.scss';
import useTripsType from '~/components/hooks/trips/useTripsType';

ChartJS.register(ArcElement, Tooltip, Legend);

const TripsTypePieChart = () => {
  const { data, loading } = useTripsType();

  if (loading) {
    return <p className={styles.pieChartContainer}>Cargando datos…</p>;
  }

  const chartData = {
    labels: ['Viajes nacionales', 'Viajes internacionales'],
    datasets: [
      {
        data: [data.national, data.international],
        backgroundColor: ['#36A2EB', '#FF6384'],
        hoverBackgroundColor: ['#36A2EB', '#FF6384'],
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
  };

  return (
    <div className={styles.pieChartContainer}>
      <h4>Distribución de viajes</h4>
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default TripsTypePieChart;
