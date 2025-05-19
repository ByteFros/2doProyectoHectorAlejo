import { json, redirect, LoaderFunction, ActionFunction } from "@remix-run/node";
import { useActionData } from "@remix-run/react";
import Login from '../../../src/components/login/login';
import { authCookie } from "../logout/route";

export const loader: LoaderFunction = async ({ request }) => {
    const cookieHeader = request.headers.get("cookie");
    const token = await authCookie.parse(cookieHeader);

    if (!token) return null;

    const response = await fetch("http://127.0.0.1:8000/api/users/session/", {
        method: "GET",
        headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
        },
    });

    if (response.ok) {
        const data = await response.json();
        const roleToPath: Record<string, string> = {
            MASTER: "/master",
            EMPRESA: "/company",
            EMPLEADO: "/employee",
        };

        return redirect(roleToPath[data.role] || "/");
    }

    return null;
};

export const action: ActionFunction = async ({ request }) => {
    const formData = await request.formData();
    const username = formData.get("username");
    const password = formData.get("password");

    const response = await fetch("http://127.0.0.1:8000/api/users/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (!response.ok || !data.token || !data.role) {
        return json({ error: "Credenciales incorrectas" }, { status: 401 });
    }

    return redirect(`/${data.role.toLowerCase()}`, {
        headers: {
            "Set-Cookie": await authCookie.serialize(data.token),
        },
    });
};

export default function LoginPage() {
    const actionData = useActionData<{ error?: string }>();
    return <Login error={actionData?.error} />;
}
