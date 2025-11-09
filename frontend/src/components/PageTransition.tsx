/**
 * PageTransition - Fade-in transition wrapper for page content
 * 
 * Provides smooth fade-in animation when page content loads.
 * Enhances perceived performance and creates polished UX.
 */

import type { ReactElement, ReactNode } from 'react';
import { Box, Fade } from '@mui/material';

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
 *   <Stack spacing={2}>
 *     {items.map(item => <Card key={item.id}>...</Card>)}
 *   </Stack>
 * </PageTransition>
 * ```
 */
export const PageTransition = ({
  children,
  in: inProp = true,
  timeout = 300,
}: PageTransitionProps): ReactElement => {
  return (
    <Fade in={inProp} timeout={timeout}>
      <Box>{children}</Box>
    </Fade>
  );
};
