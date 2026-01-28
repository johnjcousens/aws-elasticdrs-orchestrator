/**
 * Security utilities for frontend application
 * Provides XSS prevention and input sanitization
 */

/**
 * Sanitize string to prevent XSS attacks
 * @param input - String to sanitize
 * @returns Sanitized string safe for display
 */
export const sanitizeForDisplay = (input: string): string => {
  if (typeof input !== 'string') {
    return String(input);
  }

  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
    .replace(/[\r\n]/g, '');
};

/**
 * Sanitize error messages for safe logging and display
 * @param error - Error object or string
 * @returns Sanitized error message
 */
export const sanitizeErrorMessage = (error: unknown): string => {
  let message: string;
  
  if (error instanceof Error) {
    message = error.message;
  } else if (typeof error === 'string') {
    message = error;
  } else if (error && typeof error === 'object') {
    message = JSON.stringify(error);
  } else {
    message = String(error);
  }

  return sanitizeForDisplay(message);
};

/**
 * Sanitize object for safe logging (removes sensitive fields)
 * @param obj - Object to sanitize
 * @returns Sanitized object safe for logging
 */
export const sanitizeForLogging = (obj: Record<string, unknown>): Record<string, unknown> => {
  const sensitiveFields = [
    'password', 'token', 'authorization', 'auth', 'secret', 'key',
    'credential', 'session', 'cookie', 'jwt', 'bearer'
  ];

  const sanitized: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(obj)) {
    const keyLower = key.toLowerCase();
    const isSensitive = sensitiveFields.some(field => keyLower.includes(field));

    if (isSensitive && typeof value === 'string' && value.length > 4) {
      sanitized[key] = value.substring(0, 4) + '*'.repeat(value.length - 4);
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeForLogging(value as Record<string, unknown>);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
};

/**
 * Validate and sanitize URL to prevent open redirect attacks
 * @param url - URL to validate
 * @returns Safe URL or null if invalid
 */
export const sanitizeUrl = (url: string): string | null => {
  try {
    const parsed = new URL(url, window.location.origin);
    
    // Only allow same origin URLs
    if (parsed.origin !== window.location.origin) {
      return null;
    }
    
    return parsed.pathname + parsed.search + parsed.hash;
  } catch {
    return null;
  }
};