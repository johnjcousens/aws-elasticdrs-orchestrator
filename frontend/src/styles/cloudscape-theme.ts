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
 * Applies AWS branded light mode theme.
 * Call this once at application startup.
 */
export const initializeTheme = () => {
  // Apply AWS branded light mode theme
  applyMode(Mode.Light);
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
