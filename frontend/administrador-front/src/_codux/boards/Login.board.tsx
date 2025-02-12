import { createBoard } from "@wixc3/react-board";
import Login from "../../components/Login";
import { BrowserRouter } from "react-router-dom"; // Importamos BrowserRouter


export default createBoard({
    name: "Login",
    Board: () => (
        <BrowserRouter> {/* Envolvemos Login en un Router */}
            <Login />
        </BrowserRouter>
    ),
});