import MasterPage from "~/components/master/master"; 
import { json, redirect } from "@remix-run/node";

export const loader = async ({ request }: { request: Request }) => {
    const cookieHeader = request.headers.get("Cookie");

    if (!cookieHeader || !cookieHeader.includes("role=MASTER")) {
        console.log("🔴 No se encontró la cookie de sesión, redirigiendo al login.");
        return redirect("/");
    }

    return json({ success: true });
};

export default function MasterRoute() {
    return <MasterPage />;
}
