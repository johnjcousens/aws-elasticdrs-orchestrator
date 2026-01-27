/**
 * CloudScape Theme Configuration
 * 
 * Initializes AWS CloudScape Design System theme for the application.
 * Applies AWS-branded visual identity and design tokens.
 */

import { applyMode, Mode } from '@cloudscape-design/global-styles';

/**
 * Initialize CloudScape theme
 * 
 * Applies AWS branded theme based on saved preference or system default.
 * Call this once at application startup.
 */
export const initializeTheme = (theme?: 'light' | 'dark') => {
  if (theme === 'dark') {
    applyMode(Mode.Dark);
  } else if (theme === 'light') {
    applyMode(Mode.Light);
  } else {
    // Default to light mode
    applyMode(Mode.Light);
  }
};

/**
 * Switch theme dynamically
 * 
 * Changes the theme without page reload.
 * All CloudScape components automatically adapt.
 */
export const setTheme = (theme: 'light' | 'dark') => {
  applyMode(theme === 'dark' ? Mode.Dark : Mode.Light);
};

/**
 * Theme configuration
 * 
 * Custom theme tokens and overrides can be added here if needed.
 * CloudScape provides comprehensive design tokens out of the box.
 */
export const themeConfig = {
  // Custom theme tokens can be added here
  // Example: primaryColor: '#0073bb'
};

/**
 * Design tokens reference
 * 
 * CloudScape provides design tokens for:
 * - Colors (text, background, border, status)
 * - Spacing (xxxs to xxl)
 * - Typography (font sizes, weights, line heights)
 * - Shadows and borders
 * - Motion and animation
 * 
 * See: https://cloudscape.design/foundation/visual-foundation/design-tokens/
 */
