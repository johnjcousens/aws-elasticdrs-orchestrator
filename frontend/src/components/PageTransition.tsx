/**
 * PageTransition - Fade-in transition wrapper for page content
 * 
 * Provides smooth fade-in animation when page content loads.
 * Enhances perceived performance and creates polished UX.
 * 
 * Note: CloudScape doesn't have built-in transitions like Material-UI's Fade.
 * This component now uses CSS transitions for similar effect.
 */

import type { ReactElement, ReactNode } from 'react';
import { Box } from '@cloudscape-design/components';

interface PageTransitionProps {
  /** Content to animate */
  children: ReactNode;
  /** Whether content is ready to show */
  in?: boolean;
  /** Transition duration in milliseconds */
  timeout?: number;
}

/**
 * PageTransition Component
 * 
 * Wraps page content with a fade-in animation for smooth loading transitions.
 * Use this to wrap main content that should fade in after data loads.
 * 
 * @param children - Content to animate
 * @param in - Whether to show content (triggers fade-in when true)
 * @param timeout - Animation duration in ms (default: 300)
 * 
 * @example
 * ```tsx
 * <PageTransition in={!loading && !error}>
 *   <SpaceBetween size="l">
 *     {items.map(item => <Container key={item.id}>...</Container>)}
 *   </SpaceBetween>
 * </PageTransition>
 * ```
 */
export const PageTransition = ({
  children,
  in: inProp = true,
  timeout = 300,
}: PageTransitionProps): ReactElement => {
  return (
    <Box>
      <div
        style={{
          opacity: inProp ? 1 : 0,
          transition: `opacity ${timeout}ms ease-in-out`,
        }}
      >
        {children}
      </div>
    </Box>
  );
};
