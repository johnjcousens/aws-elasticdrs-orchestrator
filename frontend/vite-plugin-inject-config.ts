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
     * Transform index.html during build
     * Injects aws-config.js script tag before React bundle
     */
    transformIndexHtml(html: string) {
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
