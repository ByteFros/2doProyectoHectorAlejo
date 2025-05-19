
import type { MetaFunction } from "@remix-run/node";
import ResetPassword from "~/components/password-recovery/resetPassword/resetPassword";

export const meta: MetaFunction = () => {
    return [
        { title: "Restablecer Contraseña" },
        { name: "description", content: "Formulario para restablecer la contraseña con un token válido" },
    ];
};

export default function ResetPasswordRoute() {
    return <ResetPassword />;
}
