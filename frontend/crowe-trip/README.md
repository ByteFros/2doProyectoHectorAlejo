<div align="center">  
    <img height="50" src="./src/assets/svg/codux.svg">  
    <h1>Crowe Trip</h1>
</div>

# CROWE TRIP

## Descripción

CroweTrip es una aplicación web construida con React, TypeScript y Vite, diseñada para gestionar y optimizar la experiencia de viajes. Ofrece una interfaz dinámica y responsiva que puede ser desplegada fácilmente en Netlify.

## Características Principales

- **Interfaz Responsiva**: Adaptada para móviles y ordenadores.
- **Gestión de Itinerarios**: Herramientas intuitivas para planificar y gestionar viajes.
- **Despliegue Continuo**: Integración directa con Netlify para actualizaciones rápidas.

## Tecnologías
- **React**: Biblioteca para creación de interfaces.
- **TypeScript**: Proporciona tipos estáticos al código JavaScript.
- **Vite**: Entorno de desarrollo rápido y optimizado.
- **Netlify**: Plataforma de hosting con integración continua.

## Explicación detallada de Componentes

- **Autenticación:** Manejo de inicio de sesión, recuperación de contraseñas y cambios obligatorios.
  - **Login:** Donde se enseña el logotipo de CroweTrip y el formulario de inicio de sesión.
  - **Login-form:** Formulario de inicio de sesión. 
- **Componentes comunes:** Elementos reutilizables como mensajes, layout global y modales para confirmaciones.
  - **Layout:** Define la estructura visual común en toda la aplicación.
  - **Change-Password:** Se encuentra en el layout, donde el empleado como empresa podrán cambiar su contraseña en cualquier momento.
  - **Force-change-password:** Al iniciar sesión por primera vez, saldrá un PopUp advirtiendo del cambio de contraseña, el cual no permitirá usar la aplicación hasta que se haya cambiado. 
  - **Messages:** Manejo de notificaciones y mensajes de alerta para usuarios.
  - **Confirm-Modal:** Plantilla reutilizable para mensaje de confirmacón en PopUp.
- **Administración (Admin o Master):** Página específica para administradores donde pueden gestionar empresas (solo ellos pueden agregarlas), administrar permisos para que las empresas puedan autogestionarse (viajes de empleados), y visualizar estadísticas relacionadas.
- **Empresa (Company):** Página donde cada empresa podrá agregar y gestionar los empleados, aceptar o rechazar gastos de viaje, solicitar justificantes...
- **Empleado:** Página donde los empleados podrán programar sus viajes, subir justificantes, hacer notas... 
- **Hooks personalizados:** Lógica reutilizable para manejar estados específicos y efectos en la aplicación.

## Requisitos
- Node.js LTS o superior
- npm

## Autor
[Bronixia]