// Slide content validation utilities

const VALIDATION_RULES = {
  TITLE_MAX_LENGTH: 60,
  BODY_MAX_LENGTH: 300,
  MIN_CONTRAST_RATIO: 4.5,
  MIN_CONTRAST_RATIO_LARGE: 3.0,
};

/**
 * Calculate relative luminance of a color
 * @param {number} r - Red value (0-255)
 * @param {number} g - Green value (0-255)
 * @param {number} b - Blue value (0-255)
 * @returns {number} Relative luminance
 */
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Calculate contrast ratio between two colors
 * @param {string} color1 - First color (hex or rgb)
 * @param {string} color2 - Second color (hex or rgb)
 * @returns {number} Contrast ratio
 */
export function getContrastRatio(color1, color2) {
  // Parse hex colors
  const parseHex = (hex) => {
    hex = hex.replace('#', '');
    if (hex.length === 3) {
      hex = hex.split('').map(c => c + c).join('');
    }
    return [
      parseInt(hex.substr(0, 2), 16),
      parseInt(hex.substr(2, 2), 16),
      parseInt(hex.substr(4, 2), 16),
    ];
  };

  const [r1, g1, b1] = parseHex(color1);
  const [r2, g2, b2] = parseHex(color2);

  const lum1 = getLuminance(r1, g1, b1);
  const lum2 = getLuminance(r2, g2, b2);

  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Validate a single slide for content issues
 * @param {Object} slide - Slide blueprint
 * @param {Array} sourceContext - Source context for evidence orbs
 * @returns {Object} Validation result with warnings
 */
export function validateSlide(slide, sourceContext = []) {
  const warnings = [];

  // Check for missing title
  if (!slide.title || slide.title.trim().length === 0) {
    warnings.push({
      type: 'missing_title',
      severity: 'error',
      message: 'Slide has no title',
      suggestion: 'Add a descriptive title to help your audience understand the slide content',
    });
  }

  // Check title length
  if (slide.title && slide.title.length > VALIDATION_RULES.TITLE_MAX_LENGTH) {
    warnings.push({
      type: 'title_too_long',
      severity: 'warning',
      message: `Title exceeds ${VALIDATION_RULES.TITLE_MAX_LENGTH} characters (${slide.title.length})`,
      suggestion: 'Shorten the title for better readability',
    });
  }

  // Check for missing key points
  if (!slide.key_points || slide.key_points.length === 0) {
    warnings.push({
      type: 'missing_key_points',
      severity: 'warning',
      message: 'Slide has no key points',
      suggestion: 'Add bullet points to support your message',
    });
  }

  // Check body text length (summary + key points)
  const bodyText = [
    slide.summary_paragraph || '',
    ...(slide.key_points || []),
  ].join(' ');
  
  if (bodyText.length > VALIDATION_RULES.BODY_MAX_LENGTH) {
    warnings.push({
      type: 'body_too_long',
      severity: 'warning',
      message: `Body text exceeds ${VALIDATION_RULES.BODY_MAX_LENGTH} characters (${bodyText.length})`,
      suggestion: 'Reduce text content for better audience engagement',
    });
  }

  // Check for missing speaker notes
  if (!slide.speaker_notes || slide.speaker_notes.trim().length === 0) {
    warnings.push({
      type: 'missing_speaker_notes',
      severity: 'info',
      message: 'Slide has no speaker notes',
      suggestion: 'Add speaker notes to help with presentation delivery',
    });
  }

  // Check for missing evidence orbs
  if (!slide.evidence_orbs || slide.evidence_orbs.length === 0) {
    warnings.push({
      type: 'missing_evidence',
      severity: 'info',
      message: 'Slide has no evidence orbs',
      suggestion: 'Link evidence to support your claims',
    });
  }

  // Check for invalid evidence orb references
  if (slide.evidence_orbs && sourceContext.length > 0) {
    const validOrbIds = new Set(sourceContext.map(ctx => ctx.id));
    const invalidOrbs = slide.evidence_orbs.filter(orb => !validOrbIds.has(orb));
    
    if (invalidOrbs.length > 0) {
      warnings.push({
        type: 'invalid_evidence',
        severity: 'error',
        message: `${invalidOrbs.length} evidence orb(s) not found in source context`,
        suggestion: 'Verify evidence orb references are correct',
      });
    }
  }

  // Check contrast ratio (simplified - assumes dark background)
  // In a real implementation, this would analyze actual rendered colors
  const backgroundColor = '#0c121c'; // Dark background from design system
  const textColor = '#f8fafc'; // Light text from design system
  const contrastRatio = getContrastRatio(textColor, backgroundColor);
  
  if (contrastRatio < VALIDATION_RULES.MIN_CONTRAST_RATIO) {
    warnings.push({
      type: 'low_contrast',
      severity: 'warning',
      message: `Text contrast ratio is ${contrastRatio.toFixed(2)}:1 (minimum: ${VALIDATION_RULES.MIN_CONTRAST_RATIO}:1)`,
      suggestion: 'Increase contrast between text and background for better accessibility',
    });
  }

  return {
    slideNumber: slide.slide_number,
    isValid: warnings.filter(w => w.severity === 'error').length === 0,
    warnings,
  };
}

/**
 * Validate all slides in a presentation
 * @param {Array} slides - Array of slide blueprints
 * @param {Array} sourceContext - Source context for evidence orbs
 * @returns {Object} Validation report
 */
export function validatePresentation(slides, sourceContext = []) {
  const slideValidations = slides.map(slide => validateSlide(slide, sourceContext));
  
  const totalWarnings = slideValidations.reduce((sum, v) => sum + v.warnings.length, 0);
  const totalErrors = slideValidations.reduce(
    (sum, v) => sum + v.warnings.filter(w => w.severity === 'error').length,
    0
  );
  const slidesWithIssues = slideValidations.filter(v => v.warnings.length > 0).length;

  return {
    isValid: totalErrors === 0,
    totalSlides: slides.length,
    slidesWithIssues,
    totalWarnings,
    totalErrors,
    slideValidations,
  };
}

/**
 * Get a summary of validation issues by type
 * @param {Object} validationReport - Validation report from validatePresentation
 * @returns {Object} Issue summary
 */
export function getIssueSummary(validationReport) {
  const summary = {};
  
  validationReport.slideValidations.forEach(validation => {
    validation.warnings.forEach(warning => {
      if (!summary[warning.type]) {
        summary[warning.type] = {
          count: 0,
          severity: warning.severity,
          message: warning.message,
          slides: [],
        };
      }
      summary[warning.type].count++;
      summary[warning.type].slides.push(validation.slideNumber);
    });
  });

  return summary;
}
