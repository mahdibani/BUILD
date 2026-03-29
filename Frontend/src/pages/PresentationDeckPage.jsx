import { useEffect, useMemo, useState, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import MaterialIcon from "../components/MaterialIcon";
import PageTransition from "../components/PageTransition";
import backgroundImage from "../assets/presentation-background.jpeg";

const PRESENTATION_STORAGE_KEY = "build:last-presentation";
const SETTINGS_STORAGE_KEY = "build:presentation-settings";

// Image cache for preloading
const imageCache = new Map();

// Helper function to extract images from evidence orbs
function extractImagesFromContext(evidenceOrbs, sourceContext) {
  const images = [];
  const orbSet = new Set(evidenceOrbs);
  
  // Find matching context items and extract image URLs
  sourceContext.forEach(item => {
    if (orbSet.has(item.id) && item.metadata?.image_url) {
      images.push({
        url: item.metadata.image_url,
        source: item.source,
        id: item.id
      });
    }
  });
  
  return images;
}

// Preload images for smooth transitions
function preloadImage(url) {
  if (imageCache.has(url)) {
    return imageCache.get(url);
  }
  
  const promise = new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(url);
    img.onerror = reject;
    img.src = url;
  });
  
  imageCache.set(url, promise);
  return promise;
}

function readStoredPresentation() {
  try {
    const raw = window.sessionStorage.getItem(PRESENTATION_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function readStoredSettings() {
  try {
    const raw = window.localStorage.getItem(SETTINGS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSettings(settings) {
  try {
    window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Ignore storage errors
  }
}

const DEFAULT_SETTINGS = {
  transitionType: 'fade',
  transitionDuration: 300,
  animationsEnabled: true,
  theme: 'dark',
  fontSize: 'medium',
  showProgress: true,
  autoAdvanceEnabled: false,
  autoAdvanceDelay: 5,
};

// Visual Type Renderer Components
function TimelineRenderer({ slide, images }) {
  return (
    <div className="visual-type-timeline">
      <div className="timeline-line" />
      <div className="timeline-milestones">
        {slide.key_points.map((point, idx) => (
          <div key={idx} className="timeline-milestone" style={{ left: `${(idx / (slide.key_points.length - 1)) * 100}%` }}>
            <div className="timeline-marker" />
            <div className="timeline-content">
              <div className="timeline-label">Step {idx + 1}</div>
              <p>{point}</p>
            </div>
          </div>
        ))}
      </div>
      {images.length > 0 && (
        <div className="timeline-image">
          <img src={images[0].url} alt={slide.visual_brief} loading="lazy" />
        </div>
      )}
    </div>
  );
}

function ComparisonRenderer({ slide, images }) {
  const midpoint = Math.ceil(slide.key_points.length / 2);
  const leftPoints = slide.key_points.slice(0, midpoint);
  const rightPoints = slide.key_points.slice(midpoint);
  
  return (
    <div className="visual-type-comparison">
      <div className="comparison-column">
        <h4>Before / Option A</h4>
        {leftPoints.map((point, idx) => (
          <div key={idx} className="comparison-item">
            <span className="comparison-bullet" />
            <p>{point}</p>
          </div>
        ))}
      </div>
      <div className="comparison-divider" />
      <div className="comparison-column">
        <h4>After / Option B</h4>
        {rightPoints.map((point, idx) => (
          <div key={idx} className="comparison-item">
            <span className="comparison-bullet" />
            <p>{point}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProcessRenderer({ slide, images }) {
  return (
    <div className="visual-type-process">
      {slide.key_points.map((point, idx) => (
        <div key={idx} className="process-step">
          <div className="process-number">{idx + 1}</div>
          <div className="process-content">
            <p>{point}</p>
          </div>
          {idx < slide.key_points.length - 1 && (
            <div className="process-arrow">
              <MaterialIcon name="arrow_forward" />
            </div>
          )}
        </div>
      ))}
      {images.length > 0 && (
        <div className="process-image">
          <img src={images[0].url} alt={slide.visual_brief} loading="lazy" />
        </div>
      )}
    </div>
  );
}

function QuoteRenderer({ slide, images }) {
  return (
    <div className="visual-type-quote">
      <div className="quote-marks">"</div>
      <blockquote className="quote-text">
        {slide.summary_paragraph}
      </blockquote>
      <div className="quote-attribution">
        — {slide.title}
      </div>
      {images.length > 0 && (
        <div className="quote-image">
          <img src={images[0].url} alt={slide.visual_brief} loading="lazy" />
        </div>
      )}
    </div>
  );
}

function TitleRenderer({ slide, images }) {
  return (
    <div className="visual-type-title">
      <h1 className="title-heading">{slide.title}</h1>
      <p className="title-subtitle">{slide.summary_paragraph}</p>
      {images.length > 0 && (
        <div className="title-image">
          <img src={images[0].url} alt={slide.visual_brief} loading="lazy" />
        </div>
      )}
    </div>
  );
}

function ClosingRenderer({ slide, images }) {
  return (
    <div className="visual-type-closing">
      <h2 className="closing-heading">{slide.title}</h2>
      <div className="closing-summary">
        <p>{slide.summary_paragraph}</p>
      </div>
      <div className="closing-points">
        {slide.key_points.map((point, idx) => (
          <div key={idx} className="closing-point">
            <MaterialIcon name="check_circle" />
            <span>{point}</span>
          </div>
        ))}
      </div>
      {images.length > 0 && (
        <div className="closing-image">
          <img src={images[0].url} alt={slide.visual_brief} loading="lazy" />
        </div>
      )}
    </div>
  );
}

// Image display component with error handling
function SlideImages({ images, visualBrief, visualType }) {
  const [loadedImages, setLoadedImages] = useState([]);
  const [failedImages, setFailedImages] = useState(new Set());

  useEffect(() => {
    setLoadedImages([]);
    setFailedImages(new Set());
  }, [images]);

  const handleImageLoad = (url) => {
    setLoadedImages(prev => [...prev, url]);
  };

  const handleImageError = (url) => {
    setFailedImages(prev => new Set([...prev, url]));
  };

  if (images.length === 0) {
    return (
      <div className="slide-image-placeholder">
        <MaterialIcon name="image" />
        <p>{visualBrief}</p>
      </div>
    );
  }

  const validImages = images.filter(img => !failedImages.has(img.url));

  if (validImages.length === 0 && failedImages.size > 0) {
    return (
      <div className="slide-image-placeholder">
        <MaterialIcon name="broken_image" />
        <p>{visualBrief}</p>
      </div>
    );
  }

  return (
    <div className={`slide-images slide-images-${validImages.length > 1 ? 'grid' : 'single'}`}>
      {validImages.map((img, idx) => (
        <div key={img.id || idx} className="slide-image-container">
          <img
            src={img.url}
            alt={visualBrief}
            loading="lazy"
            onLoad={() => handleImageLoad(img.url)}
            onError={() => handleImageError(img.url)}
            className="slide-image"
          />
        </div>
      ))}
    </div>
  );
}

export default function PresentationDeckPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const incomingPresentation = location.state?.generationResult ?? null;
  const initialPresentation = useMemo(
    () => incomingPresentation ?? readStoredPresentation(),
    [incomingPresentation],
  );

  const [presentation, setPresentation] = useState(initialPresentation);
  const [activeIndex, setActiveIndex] = useState(0);
  const [showNotes, setShowNotes] = useState(false);
  const [numberBuffer, setNumberBuffer] = useState("");
  const [showThumbnails, setShowThumbnails] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState(() => ({
    ...DEFAULT_SETTINGS,
    ...readStoredSettings(),
  }));
  const [presenterMode, setPresenterMode] = useState({
    isActive: false,
    presenterWindow: null,
    channel: null,
    elapsedTime: 0,
    timerStarted: null,
  });

  const controlsTimeoutRef = useRef(null);
  const thumbnailContainerRef = useRef(null);
  const liveRegionRef = useRef(null);

  // Update settings and persist to localStorage
  const updateSettings = (newSettings) => {
    const updated = { ...settings, ...newSettings };
    setSettings(updated);
    saveSettings(updated);
  };

  // Fullscreen handlers
  const enterFullscreen = () => {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
      elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
      elem.msRequestFullscreen();
    }
  };

  const exitFullscreen = () => {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  };

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      enterFullscreen();
    } else {
      exitFullscreen();
    }
  };

  // Presenter mode handlers
  const openPresenterMode = () => {
    if (presenterMode.isActive) return;

    const presenterWindow = window.open(
      window.location.href,
      'presenter',
      'width=1024,height=768'
    );

    if (!presenterWindow) {
      alert('Failed to open presenter window. Please allow popups for this site.');
      return;
    }

    const channel = new BroadcastChannel('presentation-sync');
    
    setPresenterMode({
      isActive: true,
      presenterWindow,
      channel,
      elapsedTime: 0,
      timerStarted: new Date(),
    });

    // Send initial state to presenter window
    channel.postMessage({
      type: 'init',
      activeIndex,
      presentation,
      isPresenter: false,
    });
  };

  const closePresenterMode = () => {
    if (presenterMode.channel) {
      presenterMode.channel.close();
    }
    if (presenterMode.presenterWindow && !presenterMode.presenterWindow.closed) {
      presenterMode.presenterWindow.close();
    }
    setPresenterMode({
      isActive: false,
      presenterWindow: null,
      channel: null,
      elapsedTime: 0,
      timerStarted: null,
    });
  };

  const resetTimer = () => {
    setPresenterMode(prev => ({
      ...prev,
      elapsedTime: 0,
      timerStarted: new Date(),
    }));
  };

  useEffect(() => {
    if (!incomingPresentation) {
      return;
    }

    window.sessionStorage.setItem(
      PRESENTATION_STORAGE_KEY,
      JSON.stringify(incomingPresentation),
    );
    setPresentation(incomingPresentation);
  }, [incomingPresentation]);

  // Detect fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      const isNowFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.msFullscreenElement
      );
      setIsFullscreen(isNowFullscreen);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('msfullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('msfullscreenchange', handleFullscreenChange);
    };
  }, []);

  // Auto-hide controls in fullscreen
  useEffect(() => {
    if (!isFullscreen) {
      setShowControls(true);
      return;
    }

    const handleMouseMove = () => {
      setShowControls(true);
      
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }

      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false);
      }, 3000);
    };

    window.addEventListener('mousemove', handleMouseMove);
    handleMouseMove(); // Initial trigger

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, [isFullscreen]);

  // Presenter mode synchronization
  useEffect(() => {
    if (!presenterMode.channel) return;

    const handleMessage = (event) => {
      if (event.data.type === 'navigate') {
        setActiveIndex(event.data.activeIndex);
      }
    };

    presenterMode.channel.addEventListener('message', handleMessage);

    return () => {
      presenterMode.channel.removeEventListener('message', handleMessage);
    };
  }, [presenterMode.channel]);

  // Broadcast slide changes to presenter window
  useEffect(() => {
    if (presenterMode.channel && presenterMode.isActive) {
      presenterMode.channel.postMessage({
        type: 'navigate',
        activeIndex,
      });
    }
  }, [activeIndex, presenterMode.channel, presenterMode.isActive]);

  // Timer for presenter mode
  useEffect(() => {
    if (!presenterMode.isActive || !presenterMode.timerStarted) return;

    const interval = setInterval(() => {
      const elapsed = Math.floor((new Date() - presenterMode.timerStarted) / 1000);
      setPresenterMode(prev => ({ ...prev, elapsedTime: elapsed }));
    }, 1000);

    return () => clearInterval(interval);
  }, [presenterMode.isActive, presenterMode.timerStarted]);

  // Auto-scroll thumbnails to active slide
  useEffect(() => {
    if (!thumbnailContainerRef.current || !showThumbnails) return;

    const activeThumb = thumbnailContainerRef.current.querySelector('.presentation-thumbnail.is-active');
    if (activeThumb) {
      activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [activeIndex, showThumbnails]);

  // Preload images for current slide and next 2 slides
  useEffect(() => {
    if (!presentation) return;

    const slides = presentation.deck.slides;
    const sourceContext = presentation.source_context || [];
    
    // Preload images for current slide and next 2
    for (let i = activeIndex; i < Math.min(activeIndex + 3, slides.length); i++) {
      const slide = slides[i];
      const images = extractImagesFromContext(slide.evidence_orbs, sourceContext);
      images.forEach(img => {
        preloadImage(img.url).catch(() => {
          // Silently fail - will show placeholder
        });
      });
    }
  }, [activeIndex, presentation]);

  // Respect prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      updateSettings({ animationsEnabled: false, transitionType: 'none' });
    }
  }, []);

  // Announce slide changes to screen readers
  useEffect(() => {
    if (!presentation || !liveRegionRef.current) return;

    const slides = presentation.deck.slides;
    const currentSlide = slides[activeIndex];
    
    // Announce slide change
    const announcement = `Slide ${activeIndex + 1} of ${slides.length}. ${currentSlide.title}`;
    liveRegionRef.current.textContent = announcement;
  }, [activeIndex, presentation]);

  // Handle orientation changes
  useEffect(() => {
    const handleOrientationChange = () => {
      // Force re-layout on orientation change
      window.dispatchEvent(new Event('resize'));
    };

    window.addEventListener('orientationchange', handleOrientationChange);
    
    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
    };
  }, []);

  // Keyboard navigation handler
  useEffect(() => {
    if (!presentation) {
      return;
    }

    const handleKeyDown = (event) => {
      const totalSlides = presentation.deck.slides.length;

      // Handle settings panel
      if (event.key === 's' || event.key === 'S') {
        if (!event.ctrlKey && !event.metaKey) {
          event.preventDefault();
          setShowSettings(prev => !prev);
          return;
        }
      }

      // Handle thumbnail toggle
      if (event.key === 't' || event.key === 'T') {
        event.preventDefault();
        setShowThumbnails(prev => !prev);
        return;
      }

      // Handle fullscreen toggle
      if (event.key === 'f' || event.key === 'F') {
        if (!event.ctrlKey && !event.metaKey) {
          event.preventDefault();
          toggleFullscreen();
          return;
        }
      }

      // Handle presenter mode
      if (event.key === 'p' || event.key === 'P') {
        event.preventDefault();
        if (!presenterMode.isActive) {
          openPresenterMode();
        } else {
          closePresenterMode();
        }
        return;
      }

      // Handle ESC key
      if (event.key === 'Escape') {
        if (showSettings) {
          setShowSettings(false);
          return;
        }
        if (isFullscreen) {
          exitFullscreen();
          return;
        }
      }

      // Handle number input for direct slide jump
      if (event.key >= "0" && event.key <= "9") {
        event.preventDefault();
        setNumberBuffer((prev) => prev + event.key);
        return;
      }

      // Handle Enter key for slide jump
      if (event.key === "Enter" && numberBuffer) {
        event.preventDefault();
        const targetSlide = parseInt(numberBuffer, 10);
        if (targetSlide >= 1 && targetSlide <= totalSlides) {
          setActiveIndex(targetSlide - 1);
        }
        setNumberBuffer("");
        return;
      }

      // Clear number buffer on any other key
      if (numberBuffer && event.key !== "Enter") {
        setNumberBuffer("");
      }

      // Navigation keys
      switch (event.key) {
        case "ArrowRight":
        case " ": // Spacebar
          event.preventDefault();
          if (activeIndex < totalSlides - 1) {
            setActiveIndex((current) => current + 1);
          }
          break;

        case "ArrowLeft":
          event.preventDefault();
          if (activeIndex > 0) {
            setActiveIndex((current) => current - 1);
          }
          break;

        case "Home":
          event.preventDefault();
          setActiveIndex(0);
          break;

        case "End":
          event.preventDefault();
          setActiveIndex(totalSlides - 1);
          break;

        default:
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [presentation, activeIndex, numberBuffer, isFullscreen, showSettings, presenterMode.isActive]);

  if (!presentation) {
    return (
      <PageTransition className="presentation-page">
        <div
          className="presentation-page-backdrop"
          style={{ backgroundImage: `linear-gradient(rgba(12, 18, 28, 0.42), rgba(12, 18, 28, 0.6)), url(${backgroundImage})` }}
        />
        <div className="presentation-empty-state">
          <h1>No deck loaded yet</h1>
          <p>Generate a presentation from the workshop first, then open the React deck view.</p>
          <button className="presentation-ghost-button" type="button" onClick={() => navigate("/workshop")}>
            Back to workshop
          </button>
        </div>
      </PageTransition>
    );
  }

  const slides = presentation.deck.slides;
  const activeSlide = slides[activeIndex];
  const sourceContext = presentation.source_context || [];
  const slideImages = extractImagesFromContext(activeSlide.evidence_orbs, sourceContext);
  const canGoPrev = activeIndex > 0;
  const canGoNext = activeIndex < slides.length - 1;
  const progressPercentage = ((activeIndex + 1) / slides.length) * 100;

  // Determine if we should render a special visual type
  const shouldRenderSpecialVisual = ['timeline', 'comparison', 'process', 'quote', 'title', 'closing'].includes(activeSlide.visual_type);

  // Render visual type-specific layout
  const renderVisualType = () => {
    switch (activeSlide.visual_type) {
      case 'timeline':
        return <TimelineRenderer slide={activeSlide} images={slideImages} />;
      case 'comparison':
        return <ComparisonRenderer slide={activeSlide} images={slideImages} />;
      case 'process':
        return <ProcessRenderer slide={activeSlide} images={slideImages} />;
      case 'quote':
        return <QuoteRenderer slide={activeSlide} images={slideImages} />;
      case 'title':
        return <TitleRenderer slide={activeSlide} images={slideImages} />;
      case 'closing':
        return <ClosingRenderer slide={activeSlide} images={slideImages} />;
      default:
        return null;
    }
  };

  // Format elapsed time for presenter mode
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <PageTransition className={`presentation-page ${isFullscreen ? 'is-fullscreen' : ''} ${settings.theme === 'light' ? 'theme-light' : ''} font-size-${settings.fontSize}`}>
      {/* Screen reader live region for announcements */}
      <div 
        ref={liveRegionRef}
        className="sr-only" 
        role="status" 
        aria-live="polite" 
        aria-atomic="true"
      />

      <div
        className="presentation-page-backdrop"
        style={{ backgroundImage: `linear-gradient(rgba(12, 18, 28, 0.32), rgba(12, 18, 28, 0.58)), url(${backgroundImage})` }}
        aria-hidden="true"
      />

      {/* Fullscreen tooltip */}
      {isFullscreen && showControls && (
        <div className="presentation-fullscreen-tooltip" role="alert">
          Press ESC to exit fullscreen
        </div>
      )}

      {/* Header bar - hidden in fullscreen */}
      {(!isFullscreen || showControls) && (
        <header className="presentation-header-bar">
          <button 
            className="presentation-ghost-button" 
            type="button" 
            onClick={() => navigate("/workshop")}
            aria-label="Return to workshop"
          >
            <MaterialIcon name="arrow_back" aria-hidden="true" />
            <span>Workshop</span>
          </button>

          <div className="presentation-heading" role="banner">
            <span className="presentation-overline">{presentation.intent} council render</span>
            <h1>{presentation.deck.deck_title}</h1>
            <p>{presentation.deck.deck_subtitle}</p>
          </div>

          <nav className="presentation-header-actions" aria-label="Presentation controls">
            <button
              className="presentation-icon-button"
              type="button"
              onClick={() => setShowThumbnails(prev => !prev)}
              title="Toggle thumbnails (T)"
              aria-label={`${showThumbnails ? 'Hide' : 'Show'} thumbnails panel`}
              aria-pressed={showThumbnails}
            >
              <MaterialIcon name={showThumbnails ? "view_sidebar" : "view_sidebar"} aria-hidden="true" />
            </button>
            <button
              className="presentation-icon-button"
              type="button"
              onClick={toggleFullscreen}
              title="Toggle fullscreen (F)"
              aria-label={`${isFullscreen ? 'Exit' : 'Enter'} fullscreen mode`}
              aria-pressed={isFullscreen}
            >
              <MaterialIcon name={isFullscreen ? "fullscreen_exit" : "fullscreen"} aria-hidden="true" />
            </button>
            <button
              className="presentation-icon-button"
              type="button"
              onClick={() => presenterMode.isActive ? closePresenterMode() : openPresenterMode()}
              title="Presenter mode (P)"
              aria-label={`${presenterMode.isActive ? 'Close' : 'Open'} presenter mode`}
              aria-pressed={presenterMode.isActive}
            >
              <MaterialIcon name="present_to_all" aria-hidden="true" />
            </button>
            <button
              className="presentation-icon-button"
              type="button"
              onClick={() => setShowSettings(prev => !prev)}
              title="Settings (S)"
              aria-label="Open presentation settings"
              aria-expanded={showSettings}
            >
              <MaterialIcon name="settings" aria-hidden="true" />
            </button>
            <button
              className={`presentation-mode-button ${showNotes ? "" : "is-active"}`.trim()}
              type="button"
              onClick={() => setShowNotes(false)}
              aria-label="Show slides view"
              aria-pressed={!showNotes}
            >
              Slides
            </button>
            <button
              className={`presentation-mode-button ${showNotes ? "is-active" : ""}`.trim()}
              type="button"
              onClick={() => setShowNotes(true)}
              aria-label="Show speaker notes view"
              aria-pressed={showNotes}
            >
              Notes
            </button>
          </nav>
        </header>
      )}

      <div className="presentation-layout">
        {/* Thumbnail Panel */}
        {showThumbnails && (!isFullscreen || showControls) && (
          <aside 
            className="presentation-thumbnail-panel" 
            ref={thumbnailContainerRef}
            role="navigation"
            aria-label="Slide thumbnails"
          >
            <div className="presentation-thumbnail-header">
              <span className="presentation-overline">Slides</span>
              <button
                className="presentation-icon-button-small"
                type="button"
                onClick={() => setShowThumbnails(false)}
                title="Close (T)"
                aria-label="Close thumbnails panel"
              >
                <MaterialIcon name="close" aria-hidden="true" />
              </button>
            </div>
            <div className="presentation-thumbnail-list">
              {slides.map((slide, index) => (
                <button
                  key={slide.slide_number}
                  className={`presentation-thumbnail ${index === activeIndex ? "is-active" : ""}`.trim()}
                  type="button"
                  onClick={() => setActiveIndex(index)}
                  title={slide.title}
                  aria-label={`Go to slide ${slide.slide_number}: ${slide.title}`}
                  aria-current={index === activeIndex ? "page" : undefined}
                >
                  <div className="presentation-thumbnail-number" aria-hidden="true">{slide.slide_number}</div>
                  <div className="presentation-thumbnail-content">
                    <div className="presentation-thumbnail-title">{slide.title}</div>
                    <div className="presentation-thumbnail-type">{slide.visual_type.replaceAll("_", " ")}</div>
                  </div>
                </button>
              ))}
            </div>
          </aside>
        )}

        {/* Sidebar - hidden in fullscreen or when thumbnails are shown */}
        {!showThumbnails && (!isFullscreen || showControls) && (
          <aside className="presentation-sidebar" role="complementary" aria-label="Presentation information">
            <div className="presentation-sidebar-card">
              <span className="presentation-overline">Deck signal</span>
              <h2>{presentation.specialist.specialist_name}</h2>
              <p>{presentation.specialist.core_thesis}</p>
              <div className="presentation-badge-row">
                <span>{presentation.deck.slides.length} slides</span>
                <span>{presentation.challenger.length} Q&A prompts</span>
                <span>{presentation.background_image ?? "fixed background"}</span>
              </div>
            </div>

            <nav className="presentation-slide-list" aria-label="Slide navigation">
              {slides.map((slide, index) => (
                <button
                  key={slide.slide_number}
                  className={`presentation-slide-tab ${index === activeIndex ? "is-active" : ""}`.trim()}
                  type="button"
                  onClick={() => setActiveIndex(index)}
                  aria-label={`Go to slide ${slide.slide_number}: ${slide.title}`}
                  aria-current={index === activeIndex ? "page" : undefined}
                >
                  <span className="presentation-slide-tab-index" aria-hidden="true">{slide.slide_number}</span>
                  <div>
                    <strong>{slide.title}</strong>
                    <p>{slide.visual_type.replaceAll("_", " ")}</p>
                  </div>
                </button>
              ))}
            </nav>
          </aside>
        )}

        <main className="presentation-stage" role="main" aria-label="Slide content">
          {!showNotes ? (
            <article 
              className={`presentation-slide-card slide-transition-${settings.transitionType}`}
              style={{
                animationDuration: `${settings.transitionDuration}ms`
              }}
              key={activeIndex}
              role="article"
              aria-label={`Slide ${activeSlide.slide_number}: ${activeSlide.title}`}
            >
              <div className="presentation-slide-topline">
                <span>Slide {activeSlide.slide_number}</span>
                <span>{activeSlide.visual_type.replaceAll("_", " ")}</span>
              </div>

              {shouldRenderSpecialVisual ? (
                <div className="presentation-slide-visual-type">
                  {renderVisualType()}
                </div>
              ) : (
                <div className="presentation-slide-grid">
                  <section className="presentation-slide-copy">
                    <h2>{activeSlide.title}</h2>
                    <div className="presentation-objective-pill">{activeSlide.objective}</div>
                    <p className="presentation-summary">{activeSlide.summary_paragraph}</p>
                    <div className="presentation-bullets">
                      {activeSlide.key_points.map((point, idx) => (
                        <div 
                          key={point} 
                          className="presentation-bullet"
                          style={{
                            animationDelay: settings.animationsEnabled ? `${idx * 100}ms` : '0ms'
                          }}
                        >
                          <span />
                          <p>{point}</p>
                        </div>
                      ))}
                    </div>
                  </section>

                  <aside className="presentation-visual-panel">
                    {slideImages.length > 0 ? (
                      <SlideImages 
                        images={slideImages} 
                        visualBrief={activeSlide.visual_brief}
                        visualType={activeSlide.visual_type}
                      />
                    ) : (
                      <>
                        <div className="presentation-visual-card">
                          <span className="presentation-overline">Visual brief</span>
                          <h3>{activeSlide.visual_type.replaceAll("_", " ")}</h3>
                          <p>{activeSlide.visual_brief}</p>
                        </div>

                        <div className="presentation-evidence-card">
                          <span className="presentation-overline">Evidence</span>
                          <div className="presentation-badge-row">
                            {(activeSlide.evidence_orbs.length ? activeSlide.evidence_orbs : ["reasoned synthesis"]).map((orb) => (
                              <span key={orb}>{orb}</span>
                            ))}
                          </div>
                        </div>
                      </>
                    )}
                  </aside>
                </div>
              )}
            </article>
          ) : (
            <article className="presentation-notes-card">
              <div className="presentation-slide-topline">
                <span>Speaker notes</span>
                <span>Slide {activeSlide.slide_number}</span>
              </div>
              <h2>{activeSlide.title}</h2>
              <div className="presentation-notes-layout">
                <section className="presentation-notes-main">
                  <div className="presentation-notes-block">
                    <span className="presentation-overline">Talk track</span>
                    <p>{activeSlide.speaker_notes}</p>
                  </div>
                  <div className="presentation-notes-block">
                    <span className="presentation-overline">Slide summary</span>
                    <p>{activeSlide.summary_paragraph}</p>
                  </div>
                </section>

                <aside className="presentation-notes-side">
                  <div className="presentation-notes-block">
                    <span className="presentation-overline">Delivery cues</span>
                    <ul>
                      <li>Lead with the headline before the detail.</li>
                      <li>Use one proof point, then expand the consequence.</li>
                      <li>Pause after the closing line before moving on.</li>
                    </ul>
                  </div>
                  <div className="presentation-notes-block">
                    <span className="presentation-overline">Evidence orbs</span>
                    <div className="presentation-badge-row">
                      {(activeSlide.evidence_orbs.length ? activeSlide.evidence_orbs : ["reasoned synthesis"]).map((orb) => (
                        <span key={orb}>{orb}</span>
                      ))}
                    </div>
                  </div>
                </aside>
              </div>
            </article>
          )}

          <footer className="presentation-stage-footer">
            <nav className="presentation-nav-actions" aria-label="Slide navigation">
              <button
                className="presentation-ghost-button"
                type="button"
                onClick={() => canGoPrev && setActiveIndex((current) => current - 1)}
                disabled={!canGoPrev}
                aria-label="Go to previous slide"
              >
                <MaterialIcon name="west" aria-hidden="true" />
                <span>Previous</span>
              </button>
              <button
                className="presentation-primary-button"
                type="button"
                onClick={() => canGoNext && setActiveIndex((current) => current + 1)}
                disabled={!canGoNext}
                aria-label="Go to next slide"
              >
                <span>Next slide</span>
                <MaterialIcon name="east" aria-hidden="true" />
              </button>
            </nav>

            <div className="presentation-stage-meta">
              <span>{presentation.specialist.recommended_tone}</span>
              <span>{presentation.deck.design_direction}</span>
            </div>
          </footer>
        </main>

        {/* Progress Indicators */}
        {settings.showProgress && (
          <div 
            className="presentation-progress-container" 
            role="status" 
            aria-label={`Slide ${activeIndex + 1} of ${slides.length}`}
          >
            <div className="presentation-progress-bar" role="progressbar" aria-valuenow={progressPercentage} aria-valuemin="0" aria-valuemax="100">
              <div 
                className="presentation-progress-fill" 
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <div className="presentation-progress-counter" aria-hidden="true">
              {activeIndex + 1} / {slides.length}
            </div>
          </div>
        )}

        {/* Settings Panel */}
        {showSettings && (
          <div 
            className="presentation-settings-overlay" 
            onClick={() => setShowSettings(false)}
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
          >
            <div className="presentation-settings-panel" onClick={(e) => e.stopPropagation()}>
              <div className="presentation-settings-header">
                <h3 id="settings-title">Presentation Settings</h3>
                <button
                  className="presentation-icon-button-small"
                  type="button"
                  onClick={() => setShowSettings(false)}
                  aria-label="Close settings"
                >
                  <MaterialIcon name="close" aria-hidden="true" />
                </button>
              </div>

              <div className="presentation-settings-content">
                <div className="presentation-settings-group">
                  <label htmlFor="transition-type" className="presentation-settings-label">Transition Type</label>
                  <select
                    id="transition-type"
                    className="presentation-settings-select"
                    value={settings.transitionType}
                    onChange={(e) => updateSettings({ transitionType: e.target.value })}
                    aria-label="Select slide transition type"
                  >
                    <option value="fade">Fade</option>
                    <option value="slide">Slide</option>
                    <option value="zoom">Zoom</option>
                    <option value="none">None</option>
                  </select>
                </div>

                <div className="presentation-settings-group">
                  <label htmlFor="transition-duration" className="presentation-settings-label">
                    Transition Duration: {settings.transitionDuration}ms
                  </label>
                  <input
                    id="transition-duration"
                    type="range"
                    className="presentation-settings-slider"
                    min="100"
                    max="1000"
                    step="50"
                    value={settings.transitionDuration}
                    onChange={(e) => updateSettings({ transitionDuration: parseInt(e.target.value) })}
                    aria-label={`Transition duration: ${settings.transitionDuration} milliseconds`}
                  />
                </div>

                <div className="presentation-settings-group">
                  <label htmlFor="theme" className="presentation-settings-label">Theme</label>
                  <select
                    id="theme"
                    className="presentation-settings-select"
                    value={settings.theme}
                    onChange={(e) => updateSettings({ theme: e.target.value })}
                    aria-label="Select presentation theme"
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="high-contrast">High Contrast</option>
                  </select>
                </div>

                <div className="presentation-settings-group">
                  <label htmlFor="font-size" className="presentation-settings-label">Font Size</label>
                  <select
                    id="font-size"
                    className="presentation-settings-select"
                    value={settings.fontSize}
                    onChange={(e) => updateSettings({ fontSize: e.target.value })}
                    aria-label="Select font size"
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                  </select>
                </div>

                <div className="presentation-settings-group">
                  <label className="presentation-settings-checkbox">
                    <input
                      type="checkbox"
                      checked={settings.animationsEnabled}
                      onChange={(e) => updateSettings({ animationsEnabled: e.target.checked })}
                      aria-label="Enable or disable animations"
                    />
                    <span>Enable Animations</span>
                  </label>
                </div>

                <div className="presentation-settings-group">
                  <label className="presentation-settings-checkbox">
                    <input
                      type="checkbox"
                      checked={settings.showProgress}
                      onChange={(e) => updateSettings({ showProgress: e.target.checked })}
                      aria-label="Show or hide progress indicators"
                    />
                    <span>Show Progress Indicators</span>
                  </label>
                </div>

                <div className="presentation-settings-group">
                  <label className="presentation-settings-checkbox">
                    <input
                      type="checkbox"
                      checked={settings.autoAdvanceEnabled}
                      onChange={(e) => updateSettings({ autoAdvanceEnabled: e.target.checked })}
                      aria-label="Enable or disable auto-advance slides"
                    />
                    <span>Auto-Advance Slides</span>
                  </label>
                </div>

                {settings.autoAdvanceEnabled && (
                  <div className="presentation-settings-group">
                    <label htmlFor="auto-advance-delay" className="presentation-settings-label">
                      Auto-Advance Delay: {settings.autoAdvanceDelay}s
                    </label>
                    <input
                      id="auto-advance-delay"
                      type="range"
                      className="presentation-settings-slider"
                      min="3"
                      max="30"
                      step="1"
                      value={settings.autoAdvanceDelay}
                      onChange={(e) => updateSettings({ autoAdvanceDelay: parseInt(e.target.value) })}
                      aria-label={`Auto-advance delay: ${settings.autoAdvanceDelay} seconds`}
                    />
                  </div>
                )}

                <button
                  className="presentation-settings-reset"
                  type="button"
                  onClick={() => updateSettings(DEFAULT_SETTINGS)}
                  aria-label="Reset all settings to default values"
                >
                  Reset to Defaults
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Presenter Mode Info */}
        {presenterMode.isActive && (
          <div className="presentation-presenter-badge" role="status" aria-live="polite">
            <MaterialIcon name="present_to_all" aria-hidden="true" />
            <span>Presenter Mode Active</span>
            <span className="presentation-presenter-timer">{formatTime(presenterMode.elapsedTime)}</span>
            <button
              className="presentation-icon-button-small"
              type="button"
              onClick={resetTimer}
              title="Reset timer"
              aria-label="Reset presentation timer"
            >
              <MaterialIcon name="refresh" aria-hidden="true" />
            </button>
            <button
              className="presentation-icon-button-small"
              type="button"
              onClick={closePresenterMode}
              title="Close presenter mode"
              aria-label="Close presenter mode"
            >
              <MaterialIcon name="close" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </PageTransition>
  );
}
