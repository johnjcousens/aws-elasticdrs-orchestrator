import React from 'react';
import { FormControl, InputLabel, Select, MenuItem, FormHelperText } from '@mui/material';

interface RegionSelectorProps {
  value: string;
  onChange: (region: string) => void;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
}

const AWS_REGIONS = [
  { value: 'us-east-1', label: 'US East (N. Virginia)' },
  { value: 'us-east-2', label: 'US East (Ohio)' },
  { value: 'us-west-1', label: 'US West (N. California)' },
  { value: 'us-west-2', label: 'US West (Oregon)' },
  { value: 'eu-west-1', label: 'EU (Ireland)' },
  { value: 'eu-west-2', label: 'EU (London)' },
  { value: 'eu-central-1', label: 'EU (Frankfurt)' },
  { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
  { value: 'ap-southeast-2', label: 'Asia Pacific (Sydney)' },
  { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)' },
  { value: 'ap-south-1', label: 'Asia Pacific (Mumbai)' },
  { value: 'sa-east-1', label: 'South America (São Paulo)' },
  { value: 'ca-central-1', label: 'Canada (Central)' },
];

export const RegionSelector: React.FC<RegionSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  error = false,
  helperText
}) => {
  return (
    <FormControl fullWidth error={error} disabled={disabled}>
      <InputLabel id="region-select-label">AWS Region *</InputLabel>
      <Select
        labelId="region-select-label"
        id="region-select"
        value={value}
        label="AWS Region *"
        onChange={(e) => onChange(e.target.value)}
      >
        {AWS_REGIONS.map((region) => (
          <MenuItem key={region.value} value={region.value}>
            {region.label}
          </MenuItem>
        ))}
      </Select>
      {helperText && (
        <FormHelperText>{helperText}</FormHelperText>
      )}
    </FormControl>
  );
};
