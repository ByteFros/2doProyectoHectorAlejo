import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./components/Login"; // Importa Login directamente
import LogoutButton from "./components/Logout";
import EmpresaDashboard from "./components/DashboardEmp";

const MasterHome: React.FC = () => (
  <div>
    <h1>Home de MASTER</h1>
    <LogoutButton />
  </div>
);

const EmpleadoHome: React.FC = () => (
  <div>
    <h1>Home de EMPLEADO</h1>
    <LogoutButton />
  </div>
);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/master" element={<MasterHome />} />
        <Route path="/empresa" element={<EmpresaDashboard />} />
        <Route path="/empleado" element={<EmpleadoHome />} />
        
      </Routes>
    </Router>
  </React.StrictMode>
);
