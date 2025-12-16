/**
 * Region Selector Component
 * 
 * Provides AWS region selection UI for DRS operations.
 * Shows all 28 commercial AWS regions where DRS is available.
 */

import React from 'react';
import { Select, type SelectProps } from '@cloudscape-design/components';

// All 28 commercial AWS regions where DRS is available (verified December 2025)
const DRS_REGIONS: SelectProps.Option[] = [
  // Americas (6)
  { value: 'us-east-1', label: 'us-east-1 (N. Virginia)' },
  { value: 'us-east-2', label: 'us-east-2 (Ohio)' },
  { value: 'us-west-1', label: 'us-west-1 (N. California)' },
  { value: 'us-west-2', label: 'us-west-2 (Oregon)' },
  { value: 'ca-central-1', label: 'ca-central-1 (Canada)' },
  { value: 'sa-east-1', label: 'sa-east-1 (São Paulo)' },
  // Europe (8)
  { value: 'eu-west-1', label: 'eu-west-1 (Ireland)' },
  { value: 'eu-west-2', label: 'eu-west-2 (London)' },
  { value: 'eu-west-3', label: 'eu-west-3 (Paris)' },
  { value: 'eu-central-1', label: 'eu-central-1 (Frankfurt)' },
  { value: 'eu-central-2', label: 'eu-central-2 (Zurich)' },
  { value: 'eu-north-1', label: 'eu-north-1 (Stockholm)' },
  { value: 'eu-south-1', label: 'eu-south-1 (Milan)' },
  { value: 'eu-south-2', label: 'eu-south-2 (Spain)' },
  // Asia Pacific (10)
  { value: 'ap-northeast-1', label: 'ap-northeast-1 (Tokyo)' },
  { value: 'ap-northeast-2', label: 'ap-northeast-2 (Seoul)' },
  { value: 'ap-northeast-3', label: 'ap-northeast-3 (Osaka)' },
  { value: 'ap-southeast-1', label: 'ap-southeast-1 (Singapore)' },
  { value: 'ap-southeast-2', label: 'ap-southeast-2 (Sydney)' },
  { value: 'ap-southeast-3', label: 'ap-southeast-3 (Jakarta)' },
  { value: 'ap-southeast-4', label: 'ap-southeast-4 (Melbourne)' },
  { value: 'ap-south-1', label: 'ap-south-1 (Mumbai)' },
  { value: 'ap-south-2', label: 'ap-south-2 (Hyderabad)' },
  { value: 'ap-east-1', label: 'ap-east-1 (Hong Kong)' },
  // Middle East & Africa (4)
  { value: 'me-south-1', label: 'me-south-1 (Bahrain)' },
  { value: 'me-central-1', label: 'me-central-1 (UAE)' },
  { value: 'af-south-1', label: 'af-south-1 (Cape Town)' },
  { value: 'il-central-1', label: 'il-central-1 (Tel Aviv)' },
];

interface RegionSelectorProps {
  // New interface (preferred)
  selectedRegion?: SelectProps.Option | null;
  onRegionChange?: (region: SelectProps.Option | null) => void;
  
  // Legacy interface (backward compatibility)
  value?: string;
  onChange?: (value: string) => void;
  error?: boolean;
  helperText?: string;
  
  placeholder?: string;
  disabled?: boolean;
}

export const RegionSelector: React.FC<RegionSelectorProps> = ({
  // New interface
  selectedRegion,
  onRegionChange,
  
  // Legacy interface
  value,
  onChange,
  error,
  helperText,
  
  placeholder = "Select region",
  disabled = false
}) => {
  // Determine which interface is being used
  const isLegacyInterface = value !== undefined || onChange !== undefined;
  
  if (isLegacyInterface) {
    // Legacy interface: value is string, onChange expects string
    const selectedOption = value ? DRS_REGIONS.find(r => r.value === value) || null : null;
    
    return (
      <Select
        selectedOption={selectedOption}
        onChange={({ detail }) => {
          if (onChange) {
            onChange(detail.selectedOption?.value || '');
          }
        }}
        options={DRS_REGIONS}
        placeholder={placeholder}
        disabled={disabled}
        invalid={error}
        expandToViewport
      />
    );
  } else {
    // New interface: selectedRegion is SelectProps.Option, onRegionChange expects SelectProps.Option
    return (
      <Select
        selectedOption={selectedRegion || null}
        onChange={({ detail }) => {
          if (onRegionChange) {
            onRegionChange(detail.selectedOption);
          }
        }}
        options={DRS_REGIONS}
        placeholder={placeholder}
        disabled={disabled}
        expandToViewport
      />
    );
  }
};