import { Link } from 'react-router-dom';
import './NavBar.css';
import FullscreenToggle from './FullscreenToggle';

export default function NavBar() {
    return (
        <nav className="top-nav">
            <div className="nav-left">Dashboard</div>
            <div className="nav-links">
                <Link to="/dashboard/food" className="nav-link">Essen</Link>
                <Link to="/dashboard/drinks" className="nav-link">Getränke</Link>
                <Link to="/summary" className="nav-link">Summary</Link>
            </div>
            <FullscreenToggle />
        </nav>
    );
}
