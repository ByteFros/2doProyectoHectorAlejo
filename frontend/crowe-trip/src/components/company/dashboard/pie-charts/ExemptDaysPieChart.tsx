import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import styles from './pie-chart.module.scss';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartData {
  exentos: number;
  noExentos: number;
}

const ExemptDaysPieChart = ({ data }: { data: PieChartData }) => {
  const { exentos, noExentos } = data;

  const chartData = {
    labels: ['Total días exentos', 'Total días no exentos'],
    datasets: [
      {
        data: [exentos, noExentos],
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
      <h4>Días exentos y No exentos</h4>
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default ExemptDaysPieChart;
