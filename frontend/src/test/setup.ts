/**
 * Vitest Setup File
 * 
 * This file runs before all tests to set up the test environment.
 */

// Mock window.AWS_CONFIG for tests that import services depending on aws-config
Object.defineProperty(window, 'AWS_CONFIG', {
  value: undefined,
  writable: true,
});
