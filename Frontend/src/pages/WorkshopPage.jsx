import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import MaterialIcon from "../components/MaterialIcon";
import PageTransition from "../components/PageTransition";
import { art, councilAgents, pitchCards } from "../data/content";

const stagePositions = {
  kaito: "member-kaito",
  mei: "member-mei",
  lumi: "member-lumi",
  hiro: "member-hiro",
};

export default function WorkshopPage() {
  const navigate = useNavigate();
  const [idea, setIdea] = useState("Build is a multimodal AI studio for high-stakes presentations.");
  const [selectedPitchId, setSelectedPitchId] = useState(pitchCards[0].id);
  const [showToast, setShowToast] = useState(false);

  const selectedPitch = useMemo(
    () => pitchCards.find((card) => card.id === selectedPitchId) ?? pitchCards[0],
    [selectedPitchId],
  );

  const stageAgents = councilAgents.filter((agent) => agent.id !== "kuro");
  const critic = councilAgents.find((agent) => agent.id === "kuro");

  const handleSend = () => {
    setShowToast(true);
    window.setTimeout(() => setShowToast(false), 2600);
  };

  return (
    <AppShell>
      <PageTransition className="workspace-page paper-texture" style={{ "--paper-texture": `url(${art.paper})` }}>
        <div className="workspace-backdrop">
          <img src={art.meadow} alt="Meadow backdrop" />
        </div>
        <div className="workspace-glow" />

        <div className="workspace-inner">
          <section className="idea-sheet">
            <div className="idea-sheet-frame">
              <div className="idea-sheet-inner">
                <input
                  className="idea-input"
                  type="text"
                  value={idea}
                  onChange={(event) => setIdea(event.target.value)}
                  placeholder="Unfurl your idea here..."
                />
                <div className="sheet-meta">
                  <div className="draft-meta">
                    <span className="dot" />
                    <span>Draft No. 427</span>
                  </div>
                  <div className="sheet-actions">
                    <button className="icon-button" type="button" aria-label="Edit draft">
                      <MaterialIcon name="stylus" />
                    </button>
                    <button className="icon-button" type="button" aria-label="Send to council" onClick={handleSend}>
                      <MaterialIcon name="send" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="workshop-grid">
            <div className="council-stage">
              <div className="table-glow" />
              <div className="table-surface" />

              {stageAgents.map((agent) => (
                <button
                  key={agent.id}
                  className={`council-member ${stagePositions[agent.id]}`.trim()}
                  type="button"
                  onClick={() => navigate("/roster", { state: { focus: agent.id } })}
                >
                  <div className="member-frame">
                    <img src={agent.image} alt={agent.name} />
                    <span className={`member-tag tone-${agent.badgeTone}`}>{agent.role}</span>
                  </div>
                  <span className="member-name">{agent.name}</span>
                </button>
              ))}

              <button
                className="critic-core"
                type="button"
                onClick={() => navigate("/roster", { state: { focus: critic?.id } })}
              >
                <div className="critic-portrait">
                  <img src={critic?.image} alt={critic?.name} />
                </div>
                <div className="critic-bubble">
                  <p>"{selectedPitch.quote}"</p>
                </div>
              </button>

              <button className="stage-cta" type="button" onClick={() => navigate("/roster")}>
                Meet the full council
              </button>
            </div>

            <aside className="pitch-panel">
              <div className="pitch-panel-header">
                <div>
                  <h2>Pitch Canvas</h2>
                  <p>Choose a storytelling lens and the council will tune its critique.</p>
                </div>
              </div>

              <div className="pitch-card-list">
                {pitchCards.map((card) => (
                  <button
                    key={card.id}
                    className={`pitch-card ${selectedPitchId === card.id ? "is-selected" : ""}`.trim()}
                    style={{ "--pitch-rotation": card.rotation, "--pitch-accent": card.accent }}
                    type="button"
                    onClick={() => setSelectedPitchId(card.id)}
                  >
                    <div className="pitch-card-media">
                      <img src={card.image} alt={card.title} />
                    </div>
                    <h3>{card.title}</h3>
                    <p>{card.description}</p>
                  </button>
                ))}
              </div>
            </aside>
          </section>

          <footer className="quote-footer">
            <p>"The ink is dry, but the world is yet unwritten."</p>
            <div className="footer-meta">
              <span className="dot" />
              <span>Studio AI Roster</span>
            </div>
          </footer>
        </div>

        {showToast ? (
          <div className="floating-toast">
            <MaterialIcon name="ink_highlighter" filled className="memory-toast-icon" />
            <div>
              <strong>Council aligned</strong>
              <p>Your idea was passed into the chamber for review.</p>
            </div>
          </div>
        ) : null}
      </PageTransition>
    </AppShell>
  );
}
