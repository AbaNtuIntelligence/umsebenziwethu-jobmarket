import { Link } from "react-router-dom";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-signature">
          <img
            className="footer-logo"
            src="/images/logo.png"
            alt="AbaNtu Intelligence"
          />

          <div>
            <strong>AbaNtu Intelligence</strong>
            <small>Connecting people to meaningful opportunities.</small>
          </div>
        </div>

        <nav className="footer-links" aria-label="Footer navigation">
          <Link to="/">Opportunities</Link>
          <Link to="/privacy">Privacy &amp; terms</Link>
          <Link to="/safety">Safety Centre</Link>
          <Link to="/feedback">Feedback</Link>
        </nav>

        <p className="footer-note">
          Never pay anyone merely to apply for a job through Umsebenz'wethu Job Market.
        </p>

        <p className="footer-copyright">
          &copy; {new Date().getFullYear()} AbaNtu Intelligence. Pilot platform.
        </p>
      </div>
    </footer>
  );
}
