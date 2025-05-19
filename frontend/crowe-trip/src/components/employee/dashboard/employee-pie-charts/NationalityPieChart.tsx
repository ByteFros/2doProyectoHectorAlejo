import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import useEmployeeTravelSummary from '~/components/hooks/useEmployeeTravelSummary';
import styles from './pie-chart.module.scss';

ChartJS.register(ArcElement, Tooltip, Legend);

const NationalityPieChart = () => {
  const { summary, loading } = useEmployeeTravelSummary();

  if (loading || !summary) return <p>Cargando gráfico de viajes...</p>;

  const data = {
    labels: ['Viajes nacionales', 'Viajes internacionales'],
    datasets: [
      {
        data: [summary.national, summary.international],
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
      <h4>Viajes nacionales vs Internacionales</h4>
      <Pie data={data} options={options} />
    </div>
  );
};

export default NationalityPieChart;
