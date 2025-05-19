export async function getWeather(city: string) {
    try {
        const apiKey = "bebf39095788f549215c731c2a041c58"; // Usa tu clave de OpenWeatherMap
        const response = await fetch(
            `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric&lang=es`
        );

        const data = await response.json();

        if (data.cod !== 200) throw new Error("Ciudad no encontrada");

        return {
            description: data.weather[0].description,  // 🌥 Estado del clima
            temperature: `${Math.round(data.main.temp)}°C`,  // 🌡 Temperatura
            feelsLike: `${Math.round(data.main.feels_like)}°C`,  // 🔥 Sensación térmica
            icon: `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`,  // ☁️ Ícono del clima
            city: data.name,  // 🏙 Nombre de la ciudad
        };
    } catch (error) {
        console.error("Error obteniendo clima:", error);
        return null; // 🔴 Devolvemos `null` si hay un error
    }
}
