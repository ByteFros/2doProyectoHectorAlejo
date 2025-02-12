import "./Login.css";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./styles/Login.css"; // Importamos los estilos

const Login: React.FC = () => {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const response = await fetch("http://127.0.0.1:8000/api/users/login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const data: { token?: string; role?: string; error?: string } =
      await response.json();

    if (response.ok && data.token && data.role) {
      localStorage.setItem("token", data.token);
      localStorage.setItem("role", data.role);

      if (data.role === "MASTER") {
        navigate("/master");
      } else if (data.role === "EMPRESA") {
        navigate("/empresa");
      } else if (data.role === "EMPLEADO") {
        navigate("/empleado");
      }
    } else {
      setError(data.error || "Error en el login");
    }
  };

  return (
    <div className="login-container Login_div1 Login_div2">
      <h1 className="Login_header1">Login</h1>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="Login_input1"
        />
        <br />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="Login_input2"
        />
        <br />
        <button type="submit" className="Login_button1">
          Iniciar sesión
        </button>
      </form>

      {error && <p className="error">{error}</p>}
    </div>
  );
};



export default Login;
