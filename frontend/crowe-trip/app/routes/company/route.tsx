import CompanyPage from "~/components/company/company";
import { json, redirect } from "@remix-run/node";



export default function CompanyRoute() {
    return <CompanyPage />;
}
