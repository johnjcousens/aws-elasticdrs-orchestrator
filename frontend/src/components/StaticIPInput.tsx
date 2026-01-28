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
  /** Target subnet CIDR for range validation */
  subnetCidr?: string;
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
  subnetCidr,
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
   * Check if IP looks complete (has 4 octets)
   */
  const isCompleteIP = (ip: string): boolean => {
    const parts = ip.split('.');
    return parts.length === 4 && parts.every(p => p.length > 0);
  };

  /**
   * Validate IPv4 format and check if within subnet CIDR range
   */
  const validateIPFormat = (ip: string, cidr?: string): { valid: boolean; message?: string } => {
    if (!ip || ip.trim() === '') {
      return { valid: true }; // Empty is valid (optional field)
    }

    // Don't validate incomplete IPs (still typing)
    if (!isCompleteIP(ip)) {
      return { valid: true }; // Don't show error while typing
    }

    // IPv4 pattern: X.X.X.X where X is 0-255
    const ipv4Pattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
    const match = ip.match(ipv4Pattern);

    if (!match) {
      return {
        valid: false,
        message: 'Invalid IP format',
      };
    }

    // Validate each octet is 0-255
    const octets = [match[1], match[2], match[3], match[4]];
    for (const octet of octets) {
      const num = parseInt(octet, 10);
      if (num < 0 || num > 255) {
        return {
          valid: false,
          message: 'Invalid IP address',
        };
      }
    }

    // If CIDR provided, check if IP is within range
    if (cidr) {
      const isInRange = checkIPInCIDR(ip, cidr);
      if (!isInRange) {
        return {
          valid: false,
          message: `IP not in subnet range ${cidr}`,
        };
      }
    }

    return { valid: true };
  };

  /**
   * Check if IP address is within CIDR range
   */
  const checkIPInCIDR = (ip: string, cidr: string): boolean => {
    const [network, prefixStr] = cidr.split('/');
    const prefix = parseInt(prefixStr, 10);
    
    const ipToNumber = (ipStr: string): number => {
      return ipStr.split('.').reduce((acc, octet) => (acc << 8) + parseInt(octet, 10), 0) >>> 0;
    };
    
    const ipNum = ipToNumber(ip);
    const networkNum = ipToNumber(network);
    const mask = (0xFFFFFFFF << (32 - prefix)) >>> 0;
    
    const result = (ipNum & mask) === (networkNum & mask);
    console.log('[StaticIPInput] CIDR check:', {
      ip,
      cidr,
      ipNum,
      networkNum,
      mask,
      result
    });
    
    return result;
  };

  /**
   * Validate IP availability via API
   */
  const validateIPAvailability = useCallback(
    async (ip: string, subnetCidr?: string): Promise<void> => {
      if (!ip || !subnetId || !groupId || !serverId || !region) {
        return;
      }

      console.log('[StaticIPInput] Validating IP:', ip, 'against CIDR:', subnetCidr);

      // Client-side format and CIDR validation first
      const formatValidation = validateIPFormat(ip, subnetCidr);
      console.log('[StaticIPInput] Format validation result:', formatValidation);
      
      if (!formatValidation.valid) {
        if (isMountedRef.current) {
          setValidationState('invalid');
          setValidationMessage('');
          setErrorText(formatValidation.message || 'Invalid IP');
          console.log('[StaticIPInput] Calling onValidation(false) with message:', formatValidation.message);
          onValidation?.(false, formatValidation.message);
        }
        return;
      }

      // Set validating state
      if (isMountedRef.current) {
        setValidationState('validating');
        setValidationMessage('Checking availability...');
        setErrorText('');
      }

      try {
        // TODO: Backend endpoint /validate-ip not yet implemented
        // Temporarily skip API validation and only use client-side validation
        if (!isMountedRef.current) return;
        
        // If we got here, format and CIDR are valid
        setValidationState('valid');
        setValidationMessage('');
        setErrorText('');
        onValidation?.(true);
        
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
          setValidationMessage('');
          setErrorText('');
          onValidation?.(true);
        } else {
          setValidationState('invalid');
          setValidationMessage('');
          setErrorText(result.message || 'IP already in use');
          onValidation?.(false, result.message);
        }
        */
      } catch (error) {
        if (!isMountedRef.current) return;
        
        console.error('IP validation error:', error);
        setValidationState('error');
        setValidationMessage('');
        setErrorText('Validation failed');
        onValidation?.(false, 'Validation failed');
      }
    },
    [subnetId, subnetCidr, groupId, serverId, region, onValidation]
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
      onValidation?.(true);
      return;
    }

    // Only validate if IP looks complete (has 4 octets)
    if (!isCompleteIP(newValue)) {
      onValidation?.(true);
      return;
    }

    // Debounce API validation (500ms)
    debounceTimerRef.current = setTimeout(() => {
      validateIPAvailability(newValue, subnetCidr);
    }, 500);
  };

  /**
   * Handle blur - validate immediately
   */
  const handleBlur = () => {
    if (value && value.trim() !== '') {
      // Clear any pending debounce
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      // Validate immediately on blur
      validateIPAvailability(value, subnetCidr);
    }
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
      validateIPAvailability(value, subnetCidr);
    }
  }, [subnetId, subnetCidr, groupId, serverId, region, value, validateIPAvailability]);

  /**
   * Render validation status indicator
   */
  const renderValidationStatus = () => {
    if (!value || validationState === 'idle' || validationState === 'valid') {
      return null;
    }

    if (validationState === 'validating') {
      return (
        <Box margin={{ top: 'xs' }}>
          <StatusIndicator type="loading">
            {validationMessage}
          </StatusIndicator>
        </Box>
      );
    }

    return null;
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
        onBlur={handleBlur}
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
