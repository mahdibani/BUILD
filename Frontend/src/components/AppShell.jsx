import { Link, NavLink } from "react-router-dom";
import MaterialIcon from "./MaterialIcon";

const sideItems = [
  { label: "Drafts", icon: "edit_note", disabled: true },
  { label: "The Great Library", icon: "auto_stories", disabled: true },
  { label: "Scrolls", icon: "history_edu", disabled: true },
  { label: "Workshop", icon: "stylus_note", to: "/workshop" },
  { label: "Council Chamber", icon: "groups", to: "/roster" },
  { label: "Inkwell", icon: "ink_highlighter", disabled: true },
];

const topItems = [
  { label: "Journey", to: "/" },
  { label: "Workshop", to: "/workshop" },
  { label: "Council", to: "/roster" },
];

function ShellLink({ item, compact = false }) {
  if (item.disabled) {
    return (
      <div className={`sidebar-link is-disabled ${compact ? "is-compact" : ""}`}>
        <MaterialIcon name={item.icon} className="sidebar-icon" />
        <span>{item.label}</span>
      </div>
    );
  }

  return (
    <NavLink
      end
      to={item.to}
      className={({ isActive }) =>
        `sidebar-link ${compact ? "is-compact" : ""} ${isActive ? "is-active" : ""}`.trim()
      }
    >
      {({ isActive }) => (
        <>
          <MaterialIcon
            name={item.icon}
            className="sidebar-icon"
            filled={isActive && item.icon === "groups"}
          />
          <span>{item.label}</span>
        </>
      )}
    </NavLink>
  );
}

export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-panel">
          <div className="brand-mark">
            <MaterialIcon name="auto_awesome" className="brand-mark-icon" />
          </div>
          <div>
            <h1 className="brand-title">Pitch Council</h1>
            <p className="brand-caption">Crafting new worlds</p>
          </div>
        </div>

        <button className="new-pitch-button" type="button">
          <MaterialIcon name="add" className="button-icon" />
          <span>New Pitch</span>
        </button>

        <nav className="sidebar-nav">
          {sideItems.map((item) => (
            <ShellLink key={item.label} item={item} />
          ))}
        </nav>
      </aside>

      <div className="shell-main">
        <header className="topbar">
          <Link className="topbar-logo" to="/">
            Build
          </Link>

          <nav className="topnav">
            {topItems.map((item) => (
              <NavLink
                key={item.label}
                end
                to={item.to}
                className={({ isActive }) => `topnav-link ${isActive ? "is-active" : ""}`.trim()}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="topbar-tools">
            <label className="search-pill">
              <MaterialIcon name="search" className="search-icon" />
              <input placeholder="Search the scrolls..." type="text" />
            </label>
            <button className="icon-button subtle" type="button" aria-label="Profile">
              <MaterialIcon name="account_circle" />
            </button>
            <button className="icon-button subtle" type="button" aria-label="Settings">
              <MaterialIcon name="settings" />
            </button>
          </div>
        </header>

        {children}
      </div>

      <nav className="mobile-nav">
        <NavLink end to="/" className={({ isActive }) => `mobile-link ${isActive ? "is-active" : ""}`.trim()}>
          <MaterialIcon name="travel_explore" filled />
          <span>Journey</span>
        </NavLink>
        <NavLink
          end
          to="/workshop"
          className={({ isActive }) => `mobile-link ${isActive ? "is-active" : ""}`.trim()}
        >
          <MaterialIcon name="stylus_note" />
          <span>Workshop</span>
        </NavLink>
        <NavLink
          end
          to="/roster"
          className={({ isActive }) => `mobile-link ${isActive ? "is-active" : ""}`.trim()}
        >
          <MaterialIcon name="groups" filled />
          <span>Council</span>
        </NavLink>
      </nav>
    </div>
  );
}
