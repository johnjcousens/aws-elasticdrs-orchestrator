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
        console.log('ℹ Skipping aws-config.js injection in dev mode (uses aws-config.json instead)');
        return html;
      }

      // Find the first <script type="module"> tag (React bundle)
      // and inject our config script BEFORE it
      const transformed = html.replace(
        /(<script type="module" crossorigin src="[^"]*"><\/script>)/,
        '<script src="/assets/aws-config.js"></script>\n    $1'
      );

      // Log for verification during build
      if (transformed !== html) {
        console.log('✓ Injected aws-config.js script tag into index.html');
      } else {
        console.warn('⚠ Could not find module script tag to inject aws-config.js');
      }

      return transformed;
    }
  };
}
