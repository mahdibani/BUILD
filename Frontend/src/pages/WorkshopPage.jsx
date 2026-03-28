import { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import MaterialIcon from "../components/MaterialIcon";
import PageTransition from "../components/PageTransition";
import { art, councilAgents, pitchCards } from "../data/content";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const stagePositions = {
  kaito: "member-kaito",
  mei: "member-mei",
  lumi: "member-lumi",
  hiro: "member-hiro",
};

export default function WorkshopPage() {
  const navigate = useNavigate();
  const fileInputsRef = useRef({});
  const [idea, setIdea] = useState("");
  const [selectedPitchId, setSelectedPitchId] = useState(pitchCards[0].id);
  const [showToast, setShowToast] = useState(false);
  const [showLinkInput, setShowLinkInput] = useState(false);
  const [linkDraft, setLinkDraft] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [allowWebSearch, setAllowWebSearch] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [intakeResult, setIntakeResult] = useState(null);

  const selectedPitch = useMemo(
    () => pitchCards.find((card) => card.id === selectedPitchId) ?? pitchCards[0],
    [selectedPitchId],
  );

  const stageAgents = councilAgents.filter((agent) => agent.id !== "kuro");
  const critic = councilAgents.find((agent) => agent.id === "kuro");

  const uploadOptions = [
    { key: "image", label: "Image", icon: "image", accept: "image/*" },
    { key: "video", label: "Video", icon: "movie", accept: "video/*" },
    { key: "pdf", label: "PDF", icon: "picture_as_pdf", accept: ".pdf,application/pdf" },
    { key: "audio", label: "Audio", icon: "graphic_eq", accept: "audio/*" },
  ];

  const handleFilePick = (type, files) => {
    const pickedFiles = Array.from(files ?? []);
    if (!pickedFiles.length) {
      return;
    }

    setAttachments((current) => [
      ...current,
      ...pickedFiles.map((file) => ({
        id: `${type}-${file.name}-${file.lastModified}`,
        type,
        label: file.name,
        file,
      })),
    ]);
  };

  const handleAddLink = () => {
    const normalized = linkDraft.trim();
    if (!normalized) {
      return;
    }

    setAttachments((current) => [
      ...current,
      {
        id: `link-${normalized}`,
        type: "link",
        label: normalized,
        url: normalized,
      },
    ]);
    setLinkDraft("");
    setShowLinkInput(false);
  };

  const handleRemoveAttachment = (id) => {
    setAttachments((current) => current.filter((item) => item.id !== id));
  };

  const handleSend = async () => {
    if (!idea.trim()) {
      setSubmitError("Add a topic before sending the pitch to the backend.");
      return;
    }

    setIsSubmitting(true);
    setSubmitError("");
    setIntakeResult(null);

    try {
      const formData = new FormData();
      formData.append("topic", idea.trim());
      formData.append("allow_web_search", String(allowWebSearch));

      attachments.forEach((attachment) => {
        if (attachment.type === "link" && attachment.url) {
          formData.append("resource_urls", attachment.url);
        } else if (attachment.file) {
          formData.append("files", attachment.file, attachment.file.name);
        }
      });

      const response = await fetch(`${API_BASE_URL}/api/presentations/intake`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const details = await response.text();
        throw new Error(details || "The backend request failed.");
      }

      const result = await response.json();
      setIntakeResult(result);
      setShowToast(true);
      window.setTimeout(() => setShowToast(false), 2600);
    } catch (error) {
      setSubmitError(error.message || "Something went wrong while calling the backend.");
    } finally {
      setIsSubmitting(false);
    }
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
                <div className="upload-toolbar">
                  {uploadOptions.map((option) => (
                    <div key={option.key}>
                      <input
                        ref={(node) => {
                          fileInputsRef.current[option.key] = node;
                        }}
                        className="sr-only-input"
                        type="file"
                        accept={option.accept}
                        onChange={(event) => {
                          handleFilePick(option.key, event.target.files);
                          event.target.value = "";
                        }}
                      />
                      <button
                        className="upload-chip"
                        type="button"
                        onClick={() => fileInputsRef.current[option.key]?.click()}
                      >
                        <MaterialIcon name={option.icon} className="upload-chip-icon" />
                        <span>{option.label}</span>
                      </button>
                    </div>
                  ))}

                  <button
                    className={`upload-chip ${showLinkInput ? "is-active" : ""}`.trim()}
                    type="button"
                    onClick={() => setShowLinkInput((current) => !current)}
                  >
                    <MaterialIcon name="link" className="upload-chip-icon" />
                    <span>Website</span>
                  </button>

                  <button
                    className={`upload-chip ${allowWebSearch ? "is-active" : ""}`.trim()}
                    type="button"
                    onClick={() => setAllowWebSearch((current) => !current)}
                  >
                    <MaterialIcon name="travel_explore" className="upload-chip-icon" />
                    <span>{allowWebSearch ? "Web Search On" : "Web Search Off"}</span>
                  </button>
                </div>

                {showLinkInput ? (
                  <div className="link-entry-row">
                    <input
                      className="link-entry-input"
                      type="url"
                      value={linkDraft}
                      onChange={(event) => setLinkDraft(event.target.value)}
                      placeholder="Paste a website link..."
                    />
                    <button className="link-add-button" type="button" onClick={handleAddLink}>
                      Add link
                    </button>
                  </div>
                ) : null}

                {attachments.length ? (
                  <div className="attachment-list">
                    {attachments.map((attachment) => (
                      <div key={attachment.id} className="attachment-pill">
                        <span className="attachment-type">{attachment.type}</span>
                        <span className="attachment-label">{attachment.label}</span>
                        <button
                          className="attachment-remove"
                          type="button"
                          aria-label={`Remove ${attachment.label}`}
                          onClick={() => handleRemoveAttachment(attachment.id)}
                        >
                          <MaterialIcon name="close" />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : null}
                {submitError ? <div className="submission-banner is-error">{submitError}</div> : null}
                {intakeResult ? (
                  <div className="submission-banner is-success">
                    <strong>
                      Stored {intakeResult.stored_points} memory orbs under the {intakeResult.intent.intent} intent.
                    </strong>
                    <span>
                      Scenario: {intakeResult.scenario.replaceAll("_", " ")} | Sources:{" "}
                      {Object.entries(intakeResult.source_breakdown)
                        .map(([source, count]) => `${source} (${count})`)
                        .join(", ")}
                    </span>
                  </div>
                ) : null}
                <div className="sheet-meta">
                  <div className="draft-meta">
                    <span className="dot" />
                    <span>Draft No. 427</span>
                  </div>
                  <div className="sheet-actions">
                    <button className="icon-button" type="button" aria-label="Edit draft">
                      <MaterialIcon name="stylus" />
                    </button>
                    <button
                      className="icon-button"
                      type="button"
                      aria-label="Send to council"
                      onClick={handleSend}
                      disabled={isSubmitting}
                    >
                      <MaterialIcon name={isSubmitting ? "progress_activity" : "send"} />
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
                  <p>
                    Choose a storytelling lens and the council will tune its critique.
                    {intakeResult ? ` Latest intent: ${intakeResult.intent.intent}.` : ""}
                  </p>
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
