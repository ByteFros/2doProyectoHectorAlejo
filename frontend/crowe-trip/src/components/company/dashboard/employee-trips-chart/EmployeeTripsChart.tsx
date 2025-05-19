import { useEffect, useRef } from 'react';
import { Chart as ChartJS, BarController, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js';
import styles from './employee-trips-chart.module.scss';
import useCompanyTripsChart from '~/components/hooks/trips/useComanyTripsChart';

ChartJS.register(BarController, CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function EmployeeTripsChart() {
    const chartRef = useRef<HTMLCanvasElement>(null);
    const chartInstance = useRef<ChartJS | null>(null);
    const { data, loading } = useCompanyTripsChart();

    useEffect(() => {
        if (!chartRef.current || loading) return;

        if (chartInstance.current) {
            chartInstance.current.destroy(); // 🔁 Evita conflicto por canvas duplicado
        }

        chartInstance.current = new ChartJS(chartRef.current, {
            type: 'bar',
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }, [data, loading]);

    return (
        <div className={styles.employeeChartWrapper}>
            <canvas ref={chartRef} />
        </div>
    );
}
