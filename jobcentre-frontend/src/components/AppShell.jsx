import {
  Bell,
  BriefcaseBusiness,
  CalendarClock,
  FileCheck2,
  Heart,
  Home,
  LogOut,
  Menu,
  MessageSquareText,
  PlusCircle,
  Settings,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import SiteFooter from "./SiteFooter";
import UserAvatar from "./UserAvatar";

const linkClass = ({ isActive }) =>
  `nav-link ${isActive ? "active" : ""}`;

export default function AppShell() {
  const { user, logout, avatarRevision } = useAuth();
  const [mobileMoreOpen, setMobileMoreOpen] = useState(false);

  return (
    <>
      <header className="topbar">
        <NavLink to="/" className="brand">
          <img
            className="brand-logo"
            src="/images/logo.png"
            alt="UmsebenziWethu Job Market"
          />

          <span className="brand-name">
            UmsebenziWethu
            <b>Job Market</b>
          </span>
        </NavLink>

        <div className="top-actions">
          {user ? (
            <>
              <NavLink
                to="/profile"
                className="user-chip"
                aria-label="Open your profile"
              >
                <UserAvatar
                  user={user}
                  className="nav-avatar"
                  cacheKey={avatarRevision}
                />

                <span className="user-name">
                  {user.first_name || user.username}
                </span>
              </NavLink>

              <button
                type="button"
                className="icon-button"
                onClick={logout}
                aria-label="Log out"
              >
                <LogOut size={20} />
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="button ghost">
                Log in
              </NavLink>

              <NavLink to="/register" className="button primary">
                Join
              </NavLink>
            </>
          )}
        </div>
      </header>

      <div className="page-grid">
        <aside className="sidebar left-sidebar">
          <nav aria-label="Main navigation">
            <NavLink className={linkClass} to="/">
              <Home />
              Home
            </NavLink>

            {user?.role === "job_seeker" && (
              <>
                <NavLink className={linkClass} to="/saved">
                  <Heart />
                  Saved jobs
                </NavLink>

                <NavLink className={linkClass} to="/applications">
                  <FileCheck2 />
                  Applications
                </NavLink>
              </>
            )}

            {user?.role === "employer" && (
              <>
                <NavLink className={linkClass} to="/employer">
                  <BriefcaseBusiness />
                  My jobs
                </NavLink>

                <NavLink className={linkClass} to="/applicants">
                  <UsersRound />
                  Applicants
                </NavLink>

                <NavLink className={linkClass} to="/post-job">
                  <PlusCircle />
                  Post a job
                </NavLink>
              </>
            )}

            {user && (
              <>
                <NavLink className={linkClass} to="/interviews">
                  <CalendarClock />
                  Interview Hub
                </NavLink>

                <NavLink className={linkClass} to="/notifications">
                  <Bell />
                  Notifications
                </NavLink>

                <NavLink className={linkClass} to="/profile">
                  <UserRound />
                  Profile
                </NavLink>

                <NavLink className={linkClass} to="/settings">
                  <Settings />
                  Settings
                </NavLink>
              </>
            )}

            <NavLink className={linkClass} to="/feedback">
              <MessageSquareText />
              Feedback
            </NavLink>
          </nav>

          <div className="safety-note">
            <b>Stay safe</b>
            <p>
              A legitimate employer should never charge you to apply.
            </p>
          </div>
        </aside>

        <main className="main-content">
          <Outlet />
        </main>

        <aside className="sidebar right-sidebar">
          <section className="side-card">
            <h3>Popular categories</h3>

            {[
              "Driving",
              "Retail",
              "Warehousing",
              "Administration",
              "Hospitality",
            ].map((category) => (
              <NavLink
                key={category}
                to={`/?search=${category}`}
              >
                {category}
              </NavLink>
            ))}
          </section>

          <section className="side-card">
            <h3>Job Centre promise</h3>
            <p>
              Fresh opportunities, clear closing dates and safer
              employer communication.
            </p>
          </section>
        </aside>
      </div>

      <SiteFooter />

      {user?.role === "employer" ? (
        <>
          <nav
            className="bottom-nav employer-bottom-nav"
            aria-label="Employer mobile navigation"
          >
            <NavLink className={linkClass} to="/employer">
              <BriefcaseBusiness />
              <span>My jobs</span>
            </NavLink>

            <NavLink className={linkClass} to="/applicants">
              <UsersRound />
              <span>Applicants</span>
            </NavLink>

            <NavLink className={linkClass} to="/post-job">
              <PlusCircle />
              <span>Post</span>
            </NavLink>

            <NavLink className={linkClass} to="/interviews">
              <CalendarClock />
              <span>Interviews</span>
            </NavLink>

            <button
              type="button"
              className={`nav-link ${
                mobileMoreOpen ? "active" : ""
              }`}
              onClick={() => setMobileMoreOpen(true)}
              aria-expanded={mobileMoreOpen}
              aria-controls="employer-mobile-more"
            >
              <Menu />
              <span>More</span>
            </button>
          </nav>

          {mobileMoreOpen && (
            <>
              <button
                type="button"
                className="mobile-more-backdrop"
                aria-label="Close employer menu"
                onClick={() => setMobileMoreOpen(false)}
              />

              <section
                id="employer-mobile-more"
                className="mobile-more-panel"
                role="dialog"
                aria-modal="true"
                aria-label="More employer navigation"
              >
                <header>
                  <div>
                    <strong>Employer menu</strong>
                    <small>Account, updates and support</small>
                  </div>

                  <button
                    type="button"
                    className="icon-button"
                    onClick={() => setMobileMoreOpen(false)}
                    aria-label="Close menu"
                  >
                    <X />
                  </button>
                </header>

                <nav>
                  <NavLink
                    className={linkClass}
                    to="/notifications"
                    onClick={() => setMobileMoreOpen(false)}
                  >
                    <Bell />
                    <span>Notifications</span>
                  </NavLink>

                  <NavLink
                    className={linkClass}
                    to="/profile"
                    onClick={() => setMobileMoreOpen(false)}
                  >
                    <UserRound />
                    <span>Profile</span>
                  </NavLink>

                  <NavLink
                    className={linkClass}
                    to="/settings"
                    onClick={() => setMobileMoreOpen(false)}
                  >
                    <Settings />
                    <span>Settings</span>
                  </NavLink>

                  <NavLink
                    className={linkClass}
                    to="/feedback"
                    onClick={() => setMobileMoreOpen(false)}
                  >
                    <MessageSquareText />
                    <span>Feedback</span>
                  </NavLink>
                </nav>
              </section>
            </>
          )}
        </>
      ) : user?.role === "job_seeker" ? (
        <nav
          className="bottom-nav interview-bottom-nav"
          aria-label="Job-seeker mobile navigation"
        >
          <NavLink className={linkClass} to="/">
            <Home />
            <span>Home</span>
          </NavLink>

          <NavLink className={linkClass} to="/applications">
            <FileCheck2 />
            <span>Applied</span>
          </NavLink>

          <NavLink className={linkClass} to="/interviews">
            <CalendarClock />
            <span>Interviews</span>
          </NavLink>

          <NavLink className={linkClass} to="/saved">
            <Heart />
            <span>Saved</span>
          </NavLink>
        </nav>
      ) : (
        <nav
          className="bottom-nav guest-bottom-nav"
          aria-label="Guest mobile navigation"
        >
          <NavLink className={linkClass} to="/">
            <Home />
            <span>Home</span>
          </NavLink>

          <NavLink className={linkClass} to="/feedback">
            <MessageSquareText />
            <span>Feedback</span>
          </NavLink>

          <NavLink className={linkClass} to="/login">
            <UserRound />
            <span>Log in</span>
          </NavLink>
        </nav>
      )}
    </>
  );
}