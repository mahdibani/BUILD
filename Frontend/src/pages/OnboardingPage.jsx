import { useNavigate } from "react-router-dom";
import MaterialIcon from "../components/MaterialIcon";
import PageTransition from "../components/PageTransition";
import { art, onboardingCharacters } from "../data/content";

export default function OnboardingPage() {
  const navigate = useNavigate();

  return (
    <PageTransition className="onboarding-page">
      <div className="full-bleed-bg">
        <img src={art.meadow} alt="Pastoral illustrated background" />
        <div className="bg-overlay" />
        <div className="sun-wash" />
      </div>

      <main className="onboarding-content">
        <header className="onboarding-header">
          <span className="eyebrow">Build-Slides</span>
          <h1 className="onboarding-title">Welcome to the Pitch Council</h1>
          <p className="onboarding-description">
            Step into the living sketchbook where research, design, and presentation coaching move as
            one cinematic flow.
          </p>
        </header>

        <section className="character-row">
          {onboardingCharacters.map((character) => (
            <article
              key={character.id}
              className={`character-card ${character.id === "leader" ? "is-featured" : ""}`.trim()}
              style={{
                "--card-rotate": character.rotate,
                "--card-shift": character.shift,
                "--character-accent": character.accent,
              }}
            >
              <div className="character-portrait">
                <img src={character.image} alt={character.name} />
              </div>
              <span className="character-name">{character.name}</span>
              <span className="character-role">{character.role}</span>
            </article>
          ))}
        </section>

        <div className="cta-cluster">
          <button className="wood-button" type="button" onClick={() => navigate("/workshop")}>
            <span>Start Your Journey</span>
            <MaterialIcon name="auto_awesome" className="button-icon large" />
          </button>

          <div className="info-pill">
            <MaterialIcon name="temp_preferences_custom" className="info-pill-icon" />
            <span>Join the council, build the deck, then rehearse the questions that follow.</span>
          </div>
        </div>
      </main>

      <div className="ambient-orb orb-a" />
      <div className="ambient-orb orb-b" />

      <aside className="memory-toast">
        <MaterialIcon name="ink_highlighter" className="memory-toast-icon" filled />
        <div>
          <strong>A fresh scroll awaits...</strong>
          <p>The Council is ready to hear your pitch.</p>
        </div>
      </aside>
    </PageTransition>
  );
}
