import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import useEmployeeCityStats from '~/components/hooks/useEmployeeCityStats';
import styles from './pie-chart.module.scss';

ChartJS.register(ArcElement, Tooltip, Legend);

const ExemptDaysPieChart = () => {
  const { cities, loading } = useEmployeeCityStats();

  if (loading) return <p>Cargando gráfico de días...</p>;

  const totalExemptDays = cities.reduce((acc, c) => acc + c.exemptDays, 0);
  const totalNonExemptDays = cities.reduce((acc, c) => acc + c.nonExemptDays, 0);

  const data = {
    labels: ['Días exentos', 'Días no exentos'],
    datasets: [
      {
        data: [totalExemptDays, totalNonExemptDays],
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
      <h4>Exentos vs No exentos</h4>
      <Pie data={data} options={options} />
    </div>
  );
};

export default ExemptDaysPieChart;
