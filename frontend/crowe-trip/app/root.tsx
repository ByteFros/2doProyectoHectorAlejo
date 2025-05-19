import '~/styles/reset.scss';
import '~/styles/colors.scss';
import '~/styles/typography.scss';
import '~/styles/global.scss';
import '~/styles/utils.scss';

import {
    Links,
    Meta,
    Outlet,
    Scripts,
    ScrollRestoration,
    isRouteErrorResponse,
    useRouteError,
    useLocation,
} from '@remix-run/react';

import { ErrorComponent } from '~/components/error-component/error-component';
import Layout from '~/../src/components/common/layout/layout';

export default function App() {
    const location = useLocation();

    // ✅ Rutas públicas sin layout
    const publicRoutes = ['/', '/reset-password', '/registro'];
    const isPublicRoute = publicRoutes.some(path =>
        location.pathname.startsWith(path)
    );

    return (
        <html lang="es">
            <head>
                <meta charSet="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <Meta />
                <Links />
            </head>
            <body>
                {isPublicRoute ? (
                    <Outlet />
                ) : (
                    <Layout onSectionChange={() => {}}>
                        <Outlet />
                    </Layout>
                )}
                <ScrollRestoration />
                <Scripts />
            </body>
        </html>
    );
}

export function ErrorBoundary() {
    const error = useRouteError();
    const { title, message } = getErrorDetails(error);

    return <ErrorComponent title={title} message={message} />;
}

function getErrorDetails(error: unknown) {
    let title: string;
    let message: string | undefined;

    if (isRouteErrorResponse(error)) {
        if (error.status === 404) {
            title = 'Página no encontrada';
            message = 'La página que estás buscando no existe.';
        } else {
            title = `${error.status} - ${error.statusText}`;
            message = error.data?.message ?? '';
        }
    } else {
        title = 'Ha ocurrido un error inesperado';
    }

    return { title, message };
}
