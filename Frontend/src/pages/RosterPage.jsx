import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import MaterialIcon from "../components/MaterialIcon";
import PageTransition from "../components/PageTransition";
import { art, councilAgents } from "../data/content";

export default function RosterPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedAgentId, setSelectedAgentId] = useState(location.state?.focus ?? "kuro");

  useEffect(() => {
    if (location.state?.focus) {
      setSelectedAgentId(location.state.focus);
    }
  }, [location.state]);

  const selectedAgent = useMemo(
    () => councilAgents.find((agent) => agent.id === selectedAgentId) ?? councilAgents[0],
    [selectedAgentId],
  );

  return (
    <AppShell>
      <PageTransition className="roster-page paper-texture" style={{ "--paper-texture": `url(${art.paper})` }}>
        <div className="roster-atmosphere orb-a" />
        <div className="roster-atmosphere orb-b" />

        <section className="roster-section">
          <header className="roster-header">
            <div>
              <span className="eyebrow">Council Roster</span>
              <h2>The Council of Spirits</h2>
              <p>
                Gathered from the edges of the digital aether, these specialists are ready to shape,
                critique, and elevate your next narrative.
              </p>
            </div>

            <div className="roster-actions">
              <button className="ghost-button" type="button" onClick={() => navigate("/")}>
                Back to journey
              </button>
              <button className="primary-button" type="button" onClick={() => navigate("/workshop")}>
                Return to workshop
              </button>
            </div>
          </header>

          <div className="roster-layout">
            <div className="roster-grid">
              {councilAgents.map((agent) => (
                <button
                  key={agent.id}
                  className={`agent-card ${selectedAgentId === agent.id ? "is-selected" : ""}`.trim()}
                  type="button"
                  onClick={() => setSelectedAgentId(agent.id)}
                >
                  <div className="agent-image-shell">
                    <img className="agent-image" src={agent.image} alt={agent.name} />
                    <span className={`agent-badge tone-${agent.badgeTone}`}>{agent.title}</span>
                  </div>

                  <div className="agent-summary">
                    <div className="agent-heading">
                      <h3>
                        {agent.name} <span>({agent.role})</span>
                      </h3>
                      <span className="agent-pill">{agent.aura}</span>
                    </div>

                    <div className="agent-stats">
                      {agent.stats.map((stat) => (
                        <div key={stat.label} className="stat-chip">
                          <MaterialIcon name={stat.icon} className="stat-icon" />
                          <span>{stat.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </button>
              ))}

              <button className="invite-card" type="button" onClick={() => navigate("/workshop")}>
                <span className="invite-plus">
                  <MaterialIcon name="add" className="invite-icon" />
                </span>
                <span>Invite a New Spirit</span>
              </button>
            </div>

            <aside className="agent-note-card">
              <span className="eyebrow">Selected spirit</span>
              <h3>{selectedAgent.title}</h3>
              <p className="agent-note-name">
                {selectedAgent.name} leads the {selectedAgent.role.toLowerCase()} lens.
              </p>
              <p className="agent-note-copy">{selectedAgent.note}</p>

              <div className="agent-note-actions">
                <button className="ghost-button" type="button" onClick={() => navigate("/")}>
                  Restart onboarding
                </button>
                <button className="primary-button" type="button" onClick={() => navigate("/workshop")}>
                  Bring to workshop
                </button>
              </div>
            </aside>
          </div>

          <footer className="footer-signature">
            <div>
              <p>"The ink is dry, but the world is yet unwritten."</p>
              <div className="footer-meta">
                <span className="dot" />
                <span>Studio AI Roster</span>
              </div>
            </div>
            <MaterialIcon name="auto_stories" className="footer-glyph" filled />
          </footer>
        </section>
      </PageTransition>
    </AppShell>
  );
}
