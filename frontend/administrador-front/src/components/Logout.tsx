import { useNavigate } from "react-router-dom";

const LogoutButton: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate("/");
      return;
    }

    // Petición al backend para cerrar sesión
    await fetch("http://127.0.0.1:8000/api/users/logout/", {
      method: "POST",
      headers: {
        "Authorization": `Token ${token}`,
        "Content-Type": "application/json",
      },
    });

    // Eliminar token y rol del localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("role");

    // Redirigir al login
    navigate("/");
  };

  return <button onClick={handleLogout}>Cerrar Sesión</button>;
};

export default LogoutButton;
