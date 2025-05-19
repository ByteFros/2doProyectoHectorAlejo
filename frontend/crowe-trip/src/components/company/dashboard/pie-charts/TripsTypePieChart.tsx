import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import styles from './pie-chart.module.scss';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartData {
  nacionales: number;
  internacionales: number;
}

const TripsTypePieChart = ({ data }: { data: PieChartData }) => {
  const { nacionales, internacionales } = data;

  const chartData = {
    labels: ['Viajes nacionales', 'Viajes internacionales'],
    datasets: [
      {
        data: [nacionales, internacionales],
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
