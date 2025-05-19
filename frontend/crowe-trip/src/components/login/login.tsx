import styles from './login.module.scss'
import LoginForm from '../login-form/login-form';
import logo from '../../assets/img/crowe-trip-logo/crowe-trip.png'

interface LoginProps {
  error?: string;
}

const Login: React.FC<LoginProps> = ({ error }) => {
    return (
        <div className={styles.container}>
            <div className={styles.loginBox}>
                
                <div className={styles.left}>
                    <img src={logo} alt="CroweTrip Logo" className={styles.logo} draggable={false} />
                </div>

                <div className={styles.right}>
                    <LoginForm />
                </div>

            </div>
        </div>
    );
}

export default Login;
