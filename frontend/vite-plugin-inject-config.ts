/**
 * Vite Plugin: Inject AWS Config Script
 * 
 * Automatically injects aws-config.js script tag into index.html
 * BEFORE the React bundle to ensure window.AWS_CONFIG is available
 * when the app initializes.
 * 
 * This plugin runs during the build process and survives all rebuilds.
 */

import type { Plugin } from 'vite';

export function injectConfigScript(): Plugin {
  return {
    name: 'inject-config-script',
    /**
     * Injects aws-config.js script tag before React bundle
     * ONLY in production builds (not dev mode)
     */
    transformIndexHtml(html: string) {
      // Skip injection in dev mode - aws-config.js only exists in CloudFormation S3
      if (process.env.NODE_ENV !== 'production') {
        return html;
      }

      // Find the first <script type="module"> tag (React bundle)
      // and inject our config script BEFORE it
      const transformed = html.replace(
        /(<script type="module" crossorigin src="[^"]*"><\/script>)/,
        '<script src="/assets/aws-config.js"></script>\n    $1'
      );

      // Build-time injection completed
      if (transformed !== html) {
        // Successfully injected
      } else {
        // Could not find injection point
      }

      return transformed;
    }
  };
}
