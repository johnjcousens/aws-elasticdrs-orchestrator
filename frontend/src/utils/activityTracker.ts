// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

/**
 * Global Activity Tracker
 * 
 * Provides a global way to record user activity without circular dependencies.
 * The AuthContext will register its recordActivity function here.
 */

let globalActivityRecorder: (() => void) | null = null;

/**
 * Register the activity recording function from AuthContext
 */
export const registerActivityRecorder = (recorder: () => void): void => {
  globalActivityRecorder = recorder;
};

/**
 * Record user activity (safe to call even if no recorder is registered)
 */
export const recordActivity = (): void => {
  if (globalActivityRecorder) {
    globalActivityRecorder();
  }
};

/**
 * Unregister the activity recorder (cleanup)
 */
export const unregisterActivityRecorder = (): void => {
  globalActivityRecorder = null;
};