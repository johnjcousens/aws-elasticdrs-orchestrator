/**
 * Date Time Display Component
 * 
 * Displays formatted dates and times with consistent formatting.
 * Supports relative time display (e.g., "2 hours ago").
 */

import React from 'react';
import { Typography } from '@mui/material';
import type { TypographyProps } from '@mui/material';

export interface DateTimeDisplayProps extends Omit<TypographyProps, 'children'> {
  value: string | number | Date;
  format?: 'full' | 'date' | 'time' | 'relative';
  showSeconds?: boolean;
}

/**
 * Date Time Display Component
 * 
 * @param value - Date/time value (ISO string, timestamp, or Date object)
 * @param format - Display format (full, date, time, or relative)
 * @param showSeconds - Whether to show seconds (default: false)
 * @param props - Additional Typography props
 */
export const DateTimeDisplay: React.FC<DateTimeDisplayProps> = ({
  value,
  format = 'full',
  showSeconds = false,
  ...props
}) => {
  const formatDateTime = (value: string | number | Date): string => {
    // Handle null, undefined, or epoch 0 (uninitialized timestamp)
    if (!value || value === 0 || value === '0') {
      return '-';
    }
    
    // Convert Unix timestamp (seconds) to milliseconds
    // API returns timestamps in seconds, but JavaScript Date expects milliseconds
    let dateValue = value;
    if (typeof value === 'number' && value < 10000000000) {
      // If timestamp is less than 10 billion, it's in seconds (not milliseconds)
      // Multiply by 1000 to convert to milliseconds
      dateValue = value * 1000;
    }
    
    const date = dateValue instanceof Date ? dateValue : new Date(dateValue);
    
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }

    if (format === 'relative') {
      return formatRelativeTime(date);
    }

    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    };

    if (format === 'full' || format === 'time') {
      options.hour = '2-digit';
      options.minute = '2-digit';
      if (showSeconds) {
        options.second = '2-digit';
      }
    }

    if (format === 'time') {
      delete options.year;
      delete options.month;
      delete options.day;
    }

    return date.toLocaleString('en-US', options);
  };

  const formatRelativeTime = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) {
      return diffSec <= 1 ? 'just now' : `${diffSec} seconds ago`;
    } else if (diffMin < 60) {
      return diffMin === 1 ? '1 minute ago' : `${diffMin} minutes ago`;
    } else if (diffHour < 24) {
      return diffHour === 1 ? '1 hour ago' : `${diffHour} hours ago`;
    } else if (diffDay < 7) {
      return diffDay === 1 ? '1 day ago' : `${diffDay} days ago`;
    } else {
      // For dates older than 7 days, show the actual date
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
  };

  return (
    <Typography variant="body2" {...props}>
      {formatDateTime(value)}
    </Typography>
  );
};
