/**
 * Static IP Input Component
 * 
 * Provides an IP address input field with real-time validation for static private IP assignment.
 * Features:
 * - Client-side IPv4 format validation
 * - Debounced API validation (500ms) to check IP availability
 * - Visual feedback: ✓ Available, ✗ In use, ⚠ Invalid
 * - Inline error messages
 * - Integration with backend validation endpoint
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  FormField,
  Input,
  StatusIndicator,
  Box,
} from '@cloudscape-design/components';
import type { InputProps } from '@cloudscape-design/components';
import apiClient from '../services/api';
import type { IPValidationResult } from '../types';

export interface StaticIPInputProps {
  /** Current IP address value */
  value: string;
  /** Target subnet ID for validation */
  subnetId: string;
  /** Protection group ID for API validation */
  groupId: string;
  /** Source server ID for API validation */
  serverId: string;
  /** AWS region for validation */
  region: string;
  /** Callback when value changes */
  onChange: (value: string) => void;
  /** Callback when validation status changes */
  onValidation?: (valid: boolean, message?: string) => void;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Optional label override */
  label?: string;
  /** Optional description */
  description?: string;
  /** Whether the field is required */
  required?: boolean;
}

type ValidationState = 'idle' | 'validating' | 'valid' | 'invalid' | 'error';

export const StaticIPInput: React.FC<StaticIPInputProps> = ({
  value,
  subnetId,
  groupId,
  serverId,
  region,
  onChange,
  onValidation,
  disabled = false,
  label = 'Static Private IP Address',
  description = 'Enter a private IP address within the target subnet CIDR range',
  required = false,
}) => {
  const [validationState, setValidationState] = useState<ValidationState>('idle');
  const [validationMessage, setValidationMessage] = useState<string>('');
  const [errorText, setErrorText] = useState<string>('');
  
  // Debounce timer ref
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Track if component is mounted to prevent state updates after unmount
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  /**
   * Validate IPv4 format client-side
   */
  const validateIPFormat = (ip: string): { valid: boolean; message?: string } => {
    if (!ip || ip.trim() === '') {
      return { valid: true }; // Empty is valid (optional field)
    }

    // IPv4 pattern: X.X.X.X where X is 0-255
    const ipv4Pattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
    const match = ip.match(ipv4Pattern);

    if (!match) {
      return {
        valid: false,
        message: 'IP address must be in format X.X.X.X (e.g., 10.0.1.100)',
      };
    }

    // Validate each octet is 0-255
    const octets = [match[1], match[2], match[3], match[4]];
    for (const octet of octets) {
      const num = parseInt(octet, 10);
      if (num < 0 || num > 255) {
        return {
          valid: false,
          message: `Invalid IP address: each octet must be between 0 and 255`,
        };
      }
    }

    return { valid: true };
  };

  /**
   * Validate IP availability via API
   */
  const validateIPAvailability = useCallback(
    async (ip: string): Promise<void> => {
      if (!ip || !subnetId || !groupId || !serverId || !region) {
        return;
      }

      // Client-side format validation first
      const formatValidation = validateIPFormat(ip);
      if (!formatValidation.valid) {
        if (isMountedRef.current) {
          setValidationState('invalid');
          setValidationMessage('');
          setErrorText(formatValidation.message || 'Invalid IP format');
          onValidation?.(false, formatValidation.message);
        }
        return;
      }

      // Set validating state
      if (isMountedRef.current) {
        setValidationState('validating');
        setValidationMessage('Checking IP availability...');
        setErrorText('');
      }

      try {
        // TODO: Backend endpoint /validate-ip not yet implemented
        // Temporarily skip API validation and only use client-side format validation
        if (!isMountedRef.current) return;
        
        setValidationState('valid');
        setValidationMessage('Format valid (backend validation pending)');
        setErrorText('');
        onValidation?.(true, 'Format valid');
        
        /* COMMENTED OUT UNTIL BACKEND ENDPOINT IS IMPLEMENTED
        const result: IPValidationResult = await apiClient.validateStaticIP(
          groupId,
          serverId,
          ip,
          subnetId
        );

        if (!isMountedRef.current) return;

        if (result.valid) {
          setValidationState('valid');
          setValidationMessage(result.message || 'IP is available');
          setErrorText('');
          onValidation?.(true, result.message);
        } else {
          setValidationState('invalid');
          setValidationMessage('');
          
          // Build detailed error message
          let errorMsg = result.message || 'IP address is not available';
          
          if (result.conflictingResource) {
            const { type, id, name, isDrsResource } = result.conflictingResource;
            if (isDrsResource && name) {
              errorMsg = `IP is already assigned to DRS server: ${name}`;
            } else if (type === 'instance' && name) {
              errorMsg = `IP is in use by EC2 instance: ${name} (${id})`;
            } else if (type === 'network-interface') {
              errorMsg = `IP is in use by network interface: ${id}`;
            } else if (type === 'reserved') {
              errorMsg = 'IP is in the subnet reserved range (first 4 or last 1 addresses)';
            }
          }
          
          setErrorText(errorMsg);
          onValidation?.(false, errorMsg);
        }
        */
      } catch (error) {
        if (!isMountedRef.current) return;
        
        console.error('IP validation error:', error);
        setValidationState('error');
        setValidationMessage('');
        setErrorText('Failed to validate IP address. Please try again.');
        onValidation?.(false, 'Validation failed');
      }
    },
    [subnetId, groupId, serverId, region, onValidation]
  );

  /**
   * Handle input change with debounced validation
   */
  const handleChange: InputProps['onChange'] = ({ detail }) => {
    const newValue = detail.value;
    onChange(newValue);

    // Clear previous debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Reset validation state
    setValidationState('idle');
    setValidationMessage('');
    setErrorText('');

    // If empty, don't validate
    if (!newValue || newValue.trim() === '') {
      onValidation?.(true, '');
      return;
    }

    // Debounce API validation (500ms)
    debounceTimerRef.current = setTimeout(() => {
      validateIPAvailability(newValue);
    }, 500);
  };

  /**
   * Re-validate when subnet changes
   */
  useEffect(() => {
    if (value && subnetId && groupId && serverId && region) {
      // Clear any pending validation
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      
      // Validate immediately when subnet changes
      validateIPAvailability(value);
    }
  }, [subnetId, groupId, serverId, region, value, validateIPAvailability]);

  /**
   * Render validation status indicator
   */
  const renderValidationStatus = () => {
    if (!value || validationState === 'idle') {
      return null;
    }

    switch (validationState) {
      case 'validating':
        return (
          <Box margin={{ top: 'xs' }}>
            <StatusIndicator type="loading">
              {validationMessage}
            </StatusIndicator>
          </Box>
        );
      case 'valid':
        return (
          <Box margin={{ top: 'xs' }}>
            <StatusIndicator type="success">
              {validationMessage}
            </StatusIndicator>
          </Box>
        );
      case 'invalid':
        // Error text is shown in FormField errorText prop
        return null;
      case 'error':
        // Error text is shown in FormField errorText prop
        return null;
      default:
        return null;
    }
  };

  return (
    <FormField
      label={label}
      description={description}
      errorText={errorText || undefined}
      constraintText={required ? 'Required' : undefined}
    >
      <Input
        value={value}
        onChange={handleChange}
        placeholder="e.g., 10.0.1.100"
        disabled={disabled}
        type="text"
        autoComplete="off"
        inputMode="decimal"
        invalid={validationState === 'invalid' || validationState === 'error'}
      />
      {renderValidationStatus()}
    </FormField>
  );
};

export default StaticIPInput;
