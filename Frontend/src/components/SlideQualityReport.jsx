import { useMemo, useState } from 'react';
import MaterialIcon from './MaterialIcon';
import { validatePresentation, getIssueSummary } from '../utils/slideValidation';

const SEVERITY_ICONS = {
  error: 'error',
  warning: 'warning',
  info: 'info',
};

const SEVERITY_COLORS = {
  error: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
};

export default function SlideQualityReport({ presentation, onClose, onNavigateToSlide }) {
  const [dismissedWarnings, setDismissedWarnings] = useState(new Set());

  const validationReport = useMemo(() => {
    if (!presentation) return null;
    return validatePresentation(
      presentation.deck.slides,
      presentation.source_context || []
    );
  }, [presentation]);

  const issueSummary = useMemo(() => {
    if (!validationReport) return {};
    return getIssueSummary(validationReport);
  }, [validationReport]);

  if (!validationReport) return null;

  const dismissWarning = (slideNumber, warningType) => {
    const key = `${slideNumber}-${warningType}`;
    setDismissedWarnings(prev => new Set([...prev, key]));
  };

  const isWarningDismissed = (slideNumber, warningType) => {
    const key = `${slideNumber}-${warningType}`;
    return dismissedWarnings.has(key);
  };

  const activeWarnings = validationReport.slideValidations.flatMap(validation =>
    validation.warnings
      .filter(w => !isWarningDismissed(validation.slideNumber, w.type))
      .map(w => ({ ...w, slideNumber: validation.slideNumber }))
  );

  const errorCount = activeWarnings.filter(w => w.severity === 'error').length;
  const warningCount = activeWarnings.filter(w => w.severity === 'warning').length;
  const infoCount = activeWarnings.filter(w => w.severity === 'info').length;

  return (
    <div className="quality-report-overlay" onClick={onClose}>
      <div className="quality-report-panel" onClick={(e) => e.stopPropagation()}>
        <div className="quality-report-header">
          <div>
            <h3>Slide Quality Report</h3>
            <p className="quality-report-subtitle">
              {validationReport.slidesWithIssues} of {validationReport.totalSlides} slides have issues
            </p>
          </div>
          <button
            className="presentation-icon-button-small"
            type="button"
            onClick={onClose}
            aria-label="Close quality report"
          >
            <MaterialIcon name="close" />
          </button>
        </div>

        <div className="quality-report-summary">
          <div className="quality-report-stat" style={{ borderColor: SEVERITY_COLORS.error }}>
            <MaterialIcon name={SEVERITY_ICONS.error} style={{ color: SEVERITY_COLORS.error }} />
            <div>
              <div className="quality-report-stat-value">{errorCount}</div>
              <div className="quality-report-stat-label">Errors</div>
            </div>
          </div>
          <div className="quality-report-stat" style={{ borderColor: SEVERITY_COLORS.warning }}>
            <MaterialIcon name={SEVERITY_ICONS.warning} style={{ color: SEVERITY_COLORS.warning }} />
            <div>
              <div className="quality-report-stat-value">{warningCount}</div>
              <div className="quality-report-stat-label">Warnings</div>
            </div>
          </div>
          <div className="quality-report-stat" style={{ borderColor: SEVERITY_COLORS.info }}>
            <MaterialIcon name={SEVERITY_ICONS.info} style={{ color: SEVERITY_COLORS.info }} />
            <div>
              <div className="quality-report-stat-value">{infoCount}</div>
              <div className="quality-report-stat-label">Info</div>
            </div>
          </div>
        </div>

        <div className="quality-report-content">
          {activeWarnings.length === 0 ? (
            <div className="quality-report-empty">
              <MaterialIcon name="check_circle" style={{ color: '#10b981' }} />
              <p>All issues have been reviewed or dismissed</p>
            </div>
          ) : (
            <div className="quality-report-issues">
              {activeWarnings.map((warning, idx) => (
                <div
                  key={`${warning.slideNumber}-${warning.type}-${idx}`}
                  className={`quality-report-issue quality-report-issue-${warning.severity}`}
                >
                  <div className="quality-report-issue-header">
                    <MaterialIcon
                      name={SEVERITY_ICONS[warning.severity]}
                      style={{ color: SEVERITY_COLORS[warning.severity] }}
                    />
                    <div className="quality-report-issue-title">
                      <strong>{warning.message}</strong>
                      <span className="quality-report-issue-slide">
                        Slide {warning.slideNumber}
                      </span>
                    </div>
                    <button
                      className="quality-report-dismiss"
                      type="button"
                      onClick={() => dismissWarning(warning.slideNumber, warning.type)}
                      aria-label="Dismiss warning"
                      title="Dismiss this warning"
                    >
                      <MaterialIcon name="close" />
                    </button>
                  </div>
                  <p className="quality-report-issue-suggestion">{warning.suggestion}</p>
                  <button
                    className="quality-report-goto"
                    type="button"
                    onClick={() => {
                      onNavigateToSlide(warning.slideNumber - 1);
                      onClose();
                    }}
                  >
                    Go to slide
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="quality-report-footer">
          <button
            className="presentation-ghost-button"
            type="button"
            onClick={() => setDismissedWarnings(new Set())}
            disabled={dismissedWarnings.size === 0}
          >
            Reset dismissed warnings
          </button>
          <button
            className="presentation-primary-button"
            type="button"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
