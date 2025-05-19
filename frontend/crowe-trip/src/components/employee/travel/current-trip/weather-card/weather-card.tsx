import styles from "./weather-card.module.scss";
import { Weather } from "../../../../hooks/types";

interface Props {
    weather: Weather;
}

export default function WeatherCard({ weather }: Props) {
    return (
        <div className={styles.weatherCard}>
            <h3 className={styles.city}>{weather.city}</h3>
            <img src={weather.icon} alt="Weather Icon" className={styles.weatherIcon} />
            <p className={styles.temperature}>{weather.temperature}</p>
            <p className={styles.feelsLike}>Sensación térmica: {weather.feelsLike}</p>
            <p className={styles.description}>{weather.description}</p>
        </div>
    );
}
