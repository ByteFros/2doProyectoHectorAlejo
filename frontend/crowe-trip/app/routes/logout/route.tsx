import { redirect } from "@remix-run/node";
import { createCookie } from "@remix-run/node";

// 🔥 Definir una cookie segura para la autenticación
export const authCookie = createCookie("session", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
});

export const action = async ({ request }: { request: Request }) => {
    // Enviar la petición de logout al backend Django
    try {
        await fetch("http://127.0.0.1:8000/api/logout/", {
            method: "POST",
            credentials: "include", // Permite enviar cookies al backend
        });
    } catch (error) {
        console.error("Error en el logout del backend:", error);
    }

    // 🔥 Eliminar la cookie de sesión en el frontend
    return redirect("/", {
        headers: {
            "Set-Cookie": await authCookie.serialize("", { maxAge: 0 }), // Invalida la cookie
        },
    });
};
