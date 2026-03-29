import { BrowserRouter, Route, Routes } from "react-router-dom";
import OnboardingPage from "./pages/OnboardingPage";
import PresentationDeckPage from "./pages/PresentationDeckPage";
import RosterPage from "./pages/RosterPage";
import WorkshopPage from "./pages/WorkshopPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<OnboardingPage />} />
        <Route path="/workshop" element={<WorkshopPage />} />
        <Route path="/presentation" element={<PresentationDeckPage />} />
        <Route path="/roster" element={<RosterPage />} />
      </Routes>
    </BrowserRouter>
  );
}
