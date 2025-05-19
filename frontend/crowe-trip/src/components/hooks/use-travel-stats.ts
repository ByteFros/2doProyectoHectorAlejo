export type TravelStatsEntry = {
  month: string;
  daysTraveled: number;
};

export function useTravelStatsMock(): TravelStatsEntry[] {
  return [
    { month: "Enero", daysTraveled: 3 },
    { month: "Febrero", daysTraveled: 5 },
    { month: "Marzo", daysTraveled: 2 },
    { month: "Abril", daysTraveled: 4 },
    { month: "Mayo", daysTraveled: 0 },
    { month: "Junio", daysTraveled: 6 },
    { month: "Julio", daysTraveled: 2 },
    { month: "Agosto", daysTraveled: 1 },
    { month: "Septiembre", daysTraveled: 3 },
    { month: "Octubre", daysTraveled: 4 },
    { month: "Noviembre", daysTraveled: 2 },
    { month: "Diciembre", daysTraveled: 5 },
  ];
}