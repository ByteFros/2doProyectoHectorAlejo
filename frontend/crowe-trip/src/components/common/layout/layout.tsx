import { ReactNode, useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from '@remix-run/react';
import useAuth from '../../hooks/use-auth';
import useUser from '../../hooks/useUser';
import '~/styles/layout.scss';
import logo from '~/assets/img/crowe-trip-logo/crowe-trip.png';

import Messages from '../messages/messages';
import { FaSignOutAlt, FaKey, FaClock, FaCalendarAlt, FaCog } from 'react-icons/fa';
import ChangePasswordModal from '../change-password/change-password';
import ForceChangePassword from '../force-change-password/force-change-password';

interface LayoutProps {
    children: ReactNode;
    onSectionChange: (section: string) => void;
}

export default function Layout({ children, onSectionChange }: LayoutProps) {
    const { logout } = useAuth();
    const { user, loading, error } = useUser();
    const location = useLocation();
    const navigate = useNavigate();
    const currentPage = location.pathname.replace('/', '');

    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
    const [dateTime, setDateTime] = useState(new Date());
    const [hasNewMessages, setHasNewMessages] = useState(true);
    const [activeSection, setActiveSection] = useState('inicio');

    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const interval = setInterval(() => {
            setDateTime(new Date());
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    // Redirigir si el empleado debe cambiar contraseña
    useEffect(() => {
        if (user && user.must_change_password === true && user.role === "EMPLEADO") {
            setIsPasswordModalOpen(true);
        }
    }, [user]);

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsSettingsOpen(false);
            }
        };

        if (isSettingsOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isSettingsOpen]);

    const formattedDate = dateTime.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    });
    const formattedTime = dateTime.toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });

    const sidebarMenus: Record<string, { id: string; label: string }[]> = {
        MASTER: [
            { id: 'inicio', label: 'Inicio' },
            { id: 'mensajes', label: 'Mensajes' },
            { id: 'gestionar', label: 'Gestionar' },
        ],
        EMPRESA: [
            { id: 'inicio', label: 'Inicio' },
            { id: 'mensajes', label: 'Mensajes' },
            { id: 'gestionar', label: 'Gestionar' },
        ],
        EMPLEADO: [
            { id: 'inicio', label: 'Inicio' },
            { id: 'mensajes', label: 'Mensajes' },
            { id: 'viajes', label: 'Viajes' },
        ],
    };

    const buttons = user?.role ? sidebarMenus[user.role] || [] : [];

    if (loading) return <p>Cargando usuario...</p>;
    if (error) return <p>Error: {error}</p>;
    if (!user) return <p>No se pudo cargar la información del usuario.</p>;

    return (
        <div className="layout">
            <header className="header">
                <img src={logo} alt="Crowe Logo" className="logo" draggable={false} />
            </header>

            <div className="container">
                <aside className="sidebar">
                    <div className="datetime-container">
                        <div className="datetime-container">
                            <p className="datetime">
                                <FaCalendarAlt /> {formattedDate}
                            </p>
                            <p className="datetime">
                                <FaClock /> {formattedTime}
                            </p>
                        </div>
                    </div>
                    <hr className="divider" />

                    <nav>
                        <ul>
                            {buttons.map(({ id, label }) => (
                                <li key={id}>
                                    <button
                                        className={activeSection === id ? 'active' : ''}
                                        onClick={() => {
                                            setActiveSection(id);
                                            onSectionChange(id);
                                            if (id === 'mensajes') setHasNewMessages(false);
                                        }}
                                    >
                                        <span>{label}</span>
                                        {id === 'mensajes' && hasNewMessages && (
                                            <span className="notification-dot" />
                                        )}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </nav>

                    <div className="user-footer">
                        <button
                            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                            className={`user-button ${isSettingsOpen ? 'open' : ''}`}
                        >
                            <div>
                                <p className="username">
                                    {user.role === 'EMPLEADO'
                                        ? `${user.nombre} ${user.apellido}`
                                        : user.username}
                                </p>
                                <p className="user-role">
                                    {user.role.charAt(0).toUpperCase() + user.role.slice(1).toLowerCase()}
                                </p>
                            </div>
                            <FaCog />
                        </button>

                        {isSettingsOpen && (
                            <div className="user-dropdown" ref={dropdownRef}>
                                <button
                                    className="dropdown-item"
                                    onClick={() => {
                                        setIsPasswordModalOpen(true);
                                        setIsSettingsOpen(false);
                                    }}
                                >
                                    <FaKey /> Cambiar contraseña
                                </button>
                                <button className="dropdown-item logout" onClick={handleLogout}>
                                    <FaSignOutAlt /> Cerrar sesión
                                </button>
                            </div>
                        )}
                    </div>

                </aside>

                {/* ✅ Usamos workspace directamente */}
                <main className={`workspace ${activeSection === 'mensajes' ? 'messagesPage' : ''}`}>
                    {activeSection === 'mensajes' ? <Messages /> : children}
                </main>
            </div>

            {isPasswordModalOpen && (
                <ForceChangePassword
                    onPasswordChange={() => {
                        // If you have a way to update the user context, do it here.
                        // For now, just close the modal.
                        setIsPasswordModalOpen(false);
                    }}
                />
            )}

        </div>
    );
}