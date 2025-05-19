import { useState, useEffect, useRef } from "react";
import ScheduleTrip from "./schedule-trip/schedule-trip";
import CurrentTrip from "./current-trip/current-trip";
import UpcomingTrips from "./upcoming-trips/upcoming-trips";
import styles from "./travel.module.scss";

export default function TravelPage() {
    const [activeTab, setActiveTab] = useState("schedule");
    const [isSticky, setIsSticky] = useState(false);
    const buttonGroupRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const handleScroll = () => {
            if (buttonGroupRef.current) {
                const headerHeight = 60; // Ajusta esto al tamaño de tu header
                const buttonTop = buttonGroupRef.current.getBoundingClientRect().top;

                if (buttonTop <= headerHeight) {
                    setIsSticky(true);
                } else {
                    setIsSticky(false);
                }
            }
        };

        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    return (
        <div className={styles.travelContainer}>
            {/* Botones de selección con sticky */}
            <div
                ref={buttonGroupRef}
                className={`${styles.buttonGroup} ${isSticky ? styles.sticky : ""}`}
            >
                <button
                    className={activeTab === "schedule" ? styles.active : ""}
                    onClick={() => setActiveTab("schedule")}
                >
                    Programar viaje
                </button>
                <button
                    className={activeTab === "current" ? styles.active : ""}
                    onClick={() => setActiveTab("current")}
                >
                    Viaje en curso
                </button>
                <button
                    className={activeTab === "upcoming" ? styles.active : ""}
                    onClick={() => setActiveTab("upcoming")}
                >
                    Próximos viajes
                </button>
            </div>

            {/* Contenido dinámico */}
            <div className={styles.content}>
                {activeTab === "schedule" && <ScheduleTrip />}
                {activeTab === "current" && <CurrentTrip />}
                {activeTab === "upcoming" && <UpcomingTrips />}
            </div>
        </div>
    );
}
