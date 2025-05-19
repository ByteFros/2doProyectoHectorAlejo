import EmployeePage from "~/components/employee/employee";
import { json, redirect } from "@remix-run/node";

export const loader = async ({ request }: { request: Request }) => {
    const cookieHeader = request.headers.get("Cookie");

    if (!cookieHeader || !cookieHeader.includes("role=EMPLEADO")) {
        console.log("🔴 Usuario no autorizado para EMPLEADO, redirigiendo al login.");
        return redirect("/");
    }

    return json({ success: true });
};

export default function EmployeeRoute() {
    return <EmployeePage />;
}
