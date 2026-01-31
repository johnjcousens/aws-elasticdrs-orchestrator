/**
 * Capacity Gauge Component
 * 
 * Visual circular gauge showing capacity usage with color coding:
 * - Green: 0-60% (healthy)
 * - Yellow: 60-80% (warning)
 * - Orange: 80-90% (critical)
 * - Red: 90-100% (danger)
 */

import React from 'react';
import { Box } from '@cloudscape-design/components';

interface CapacityGaugeProps {
  used: number;
  total: number;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  label?: string;
}

export const CapacityGauge: React.FC<CapacityGaugeProps> = ({
  used,
  total,
  size = 'medium',
  showLabel = true,
  label,
}) => {
  const percentage = total > 0 ? (used / total) * 100 : 0;
  
  // Determine color based on percentage
  const getColor = (pct: number): string => {
    if (pct >= 90) return '#d13212'; // Red
    if (pct >= 80) return '#ff9900'; // Orange
    if (pct >= 60) return '#ffc107'; // Yellow
    return '#037f0c'; // Green
  };

  const color = getColor(percentage);
  
  // Size configurations
  const sizeConfig = {
    small: { radius: 30, strokeWidth: 5, fontSize: '12px' },
    medium: { radius: 50, strokeWidth: 7, fontSize: '16px' },
    large: { radius: 70, strokeWidth: 9, fontSize: '20px' },
  };

  const { radius, strokeWidth, fontSize } = sizeConfig[size];
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const svgSize = (radius + strokeWidth) * 2 + 4;

  return (
    <Box textAlign="center">
      <svg 
        width={svgSize} 
        height={svgSize} 
        style={{ display: 'block', margin: '0 auto' }}
      >
        {/* Background circle */}
        <circle
          cx={svgSize / 2}
          cy={svgSize / 2}
          r={radius}
          fill="none"
          stroke="#e9ebed"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={svgSize / 2}
          cy={svgSize / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ 
            transition: 'stroke-dashoffset 0.5s ease',
            transform: 'rotate(-90deg)',
            transformOrigin: 'center'
          }}
        />
        {/* Center text */}
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={fontSize}
          fontWeight="bold"
          fill={color}
        >
          {percentage.toFixed(1)}%
        </text>
      </svg>
      {showLabel && (
        <Box variant="small" color="text-body-secondary" padding={{ top: 'xs' }}>
          {label || `${used.toLocaleString()} / ${total.toLocaleString()}`}
        </Box>
      )}
    </Box>
  );
};
