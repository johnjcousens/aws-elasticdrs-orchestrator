/**
 * ServerLaunchConfigDialog Component
 * 
 * Modal dialog for configuring individual server launch template settings.
 * Features:
 * - Static private IP input with real-time validation
 * - Override toggles for each field
 * - "Use Group Defaults" checkbox
 * - Field-level validation
 * - Preview of effective configuration
 * - Shows which fields are custom vs default
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  FormField,
  Select,
  Checkbox,
  Header,
  Container,
  ColumnLayout,
  Alert,
  Spinner,
  type SelectProps,
} from '@cloudscape-design/components';
import { StaticIPInput } from './StaticIPInput';
import { ServerConfigBadge } from './ServerConfigBadge';
import apiClient from '../services/api';
import type {
  ResolvedServer,
  LaunchConfig,
  ServerLaunchConfig,
  SubnetOption,
  SecurityGroupOption,
  InstanceTypeOption,
} from '../types';

export interface ServerLaunchConfigDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Server to configure */
  server: ResolvedServer;
  /** Protection group defaults */
  groupDefaults: LaunchConfig;
  /** Current server configuration (if any) */
  serverConfig?: ServerLaunchConfig;
  /** AWS region */
  region: string;
  /** Protection group ID for API calls */
  groupId: string;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Callback when configuration is saved */
  onSave: (config: ServerLaunchConfig) => void;
  /** Whether save operation is in progress */
  saving?: boolean;
}

/**
 * ServerLaunchConfigDialog Component
 * 
 * Provides a modal dialog for configuring per-server launch template settings.
 * Supports both full override and partial override modes.
 */
export const ServerLaunchConfigDialog: React.FC<ServerLaunchConfigDialogProps> = ({
  open,
  server,
  groupDefaults,
  serverConfig,
  region,
  groupId,
  onClose,
  onSave,
  saving = false,
}) => {
  // Dropdown options state
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [subnets, setSubnets] = useState<SubnetOption[]>([]);
  const [securityGroups, setSecurityGroups] = useState<SecurityGroupOption[]>([]);
  const [instanceTypes, setInstanceTypes] = useState<InstanceTypeOption[]>([]);

  // Load dropdown options when dialog opens
  const loadDropdownOptions = useCallback(async () => {
    if (!region) return;
    
    setLoading(true);
    setLoadError(null);
    try {
      const [subs, sgs, types] = await Promise.all([
        apiClient.getEC2Subnets(region),
        apiClient.getEC2SecurityGroups(region),
        apiClient.getEC2InstanceTypes(region),
      ]);
      setSubnets(subs);
      setSecurityGroups(sgs);
      setInstanceTypes(types);
    } catch (err: unknown) {
      setLoadError('Failed to load EC2 resources. Check IAM permissions.');
      console.error('Error loading dropdown options:', err);
    } finally {
      setLoading(false);
    }
  }, [region]);

  useEffect(() => {
    if (open && region) {
      loadDropdownOptions();
    }
  }, [open, region, loadDropdownOptions]);

  // Form state
  const [useGroupDefaults, setUseGroupDefaults] = useState(
    serverConfig?.useGroupDefaults ?? true
  );
  const [staticPrivateIp, setStaticPrivateIp] = useState(
    serverConfig?.launchTemplate?.staticPrivateIp || ''
  );
  const [subnetId, setSubnetId] = useState(
    serverConfig?.launchTemplate?.subnetId || groupDefaults.subnetId || ''
  );
  const [selectedSecurityGroups, setSelectedSecurityGroups] = useState<SelectProps.Option[]>(
    []
  );
  const [instanceType, setInstanceType] = useState(
    serverConfig?.launchTemplate?.instanceType || groupDefaults.instanceType || ''
  );
  
  // Validation state
  const [ipValid, setIpValid] = useState(true);
  const [ipValidationMessage, setIpValidationMessage] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize form when dialog opens or server config changes
  useEffect(() => {
    if (open) {
      setUseGroupDefaults(serverConfig?.useGroupDefaults ?? true);
      setStaticPrivateIp(serverConfig?.launchTemplate?.staticPrivateIp || '');
      setSubnetId(serverConfig?.launchTemplate?.subnetId || groupDefaults.subnetId || '');
      setInstanceType(serverConfig?.launchTemplate?.instanceType || groupDefaults.instanceType || '');
      
      // Initialize security groups
      const configSgs = serverConfig?.launchTemplate?.securityGroupIds || groupDefaults.securityGroupIds || [];
      const sgOptions = configSgs.map(sgId => {
        const sg = securityGroups.find(s => s.value === sgId);
        return {
          label: sg?.label || sgId,
          value: sgId,
        };
      });
      setSelectedSecurityGroups(sgOptions);
      
      setIpValid(true);
      setIpValidationMessage('');
      setHasChanges(false);
    }
  }, [open, server, serverConfig, groupDefaults, securityGroups]);

  // Track changes
  useEffect(() => {
    const originalConfig = serverConfig?.launchTemplate || {};
    const originalUseDefaults = serverConfig?.useGroupDefaults ?? true;
    
    const changed =
      useGroupDefaults !== originalUseDefaults ||
      staticPrivateIp !== (originalConfig.staticPrivateIp || '') ||
      subnetId !== (originalConfig.subnetId || groupDefaults.subnetId || '') ||
      instanceType !== (originalConfig.instanceType || groupDefaults.instanceType || '');
    
    setHasChanges(changed);
  }, [useGroupDefaults, staticPrivateIp, subnetId, instanceType, serverConfig, groupDefaults]);

  /**
   * Handle IP validation callback
   */
  const handleIpValidation = (valid: boolean, message?: string) => {
    console.log('[ServerLaunchConfigDialog] IP validation callback:', { valid, message });
    setIpValid(valid);
    setIpValidationMessage(message || '');
  };

  /**
   * Handle save button click
   */
  const handleSave = () => {
    // Final validation check before saving
    if (staticPrivateIp && staticPrivateIp.trim() !== '') {
      if (!ipValid) {
        console.error('[ServerLaunchConfigDialog] Cannot save: IP validation failed');
        return;
      }
    }

    // Build configuration object
    const config: ServerLaunchConfig = {
      sourceServerId: server.sourceServerID,
      instanceId: server.sourceInstanceId,
      instanceName: server.hostname || server.nameTag,
      tags: server.tags,
      useGroupDefaults,
      launchTemplate: {},
    };

    // Add fields that differ from defaults
    if (staticPrivateIp && staticPrivateIp.trim() !== '') {
      config.launchTemplate.staticPrivateIp = staticPrivateIp.trim();
    }
    
    if (!useGroupDefaults) {
      // Full override mode - include all fields
      if (subnetId) config.launchTemplate.subnetId = subnetId;
      if (instanceType) config.launchTemplate.instanceType = instanceType;
      if (selectedSecurityGroups.length > 0) {
        config.launchTemplate.securityGroupIds = selectedSecurityGroups.map(sg => sg.value || '');
      }
    } else {
      // Partial override mode - only include explicitly set fields
      if (subnetId && subnetId !== groupDefaults.subnetId) {
        config.launchTemplate.subnetId = subnetId;
      }
      if (instanceType && instanceType !== groupDefaults.instanceType) {
        config.launchTemplate.instanceType = instanceType;
      }
      const defaultSgs = groupDefaults.securityGroupIds || [];
      const currentSgs = selectedSecurityGroups.map(sg => sg.value || '');
      if (JSON.stringify(currentSgs) !== JSON.stringify(defaultSgs)) {
        config.launchTemplate.securityGroupIds = currentSgs;
      }
    }

    onSave(config);
  };

  /**
   * Handle cancel button click
   */
  const handleCancel = () => {
    onClose();
  };

  /**
   * Get effective subnet ID and CIDR (server override or group default)
   */
  const getEffectiveSubnet = (): { id: string; cidr?: string } => {
    const effectiveSubnetId = (!useGroupDefaults && subnetId) 
      ? subnetId 
      : (useGroupDefaults && serverConfig?.launchTemplate?.subnetId)
        ? serverConfig.launchTemplate.subnetId
        : groupDefaults.subnetId || '';
    
    const subnet = subnets.find(s => s.value === effectiveSubnetId);
    const result = {
      id: effectiveSubnetId,
      cidr: subnet?.cidr,
    };
    console.log('[ServerLaunchConfigDialog] getEffectiveSubnet:', result);
    return result;
  };

  /**
   * Check if a field is using custom value
   */
  const isFieldCustom = (fieldName: string): boolean => {
    if (!serverConfig || useGroupDefaults) return false;
    return serverConfig.launchTemplate[fieldName as keyof LaunchConfig] !== undefined;
  };

  /**
   * Get field indicator badge
   */
  const getFieldIndicator = (fieldName: string) => {
    const isCustom = isFieldCustom(fieldName);
    return (
      <Box display="inline" margin={{ left: 'xs' }}>
        <ServerConfigBadge
          hasCustomConfig={isCustom}
          customFields={isCustom ? [fieldName] : []}
        />
      </Box>
    );
  };

  // Prepare dropdown options
  const subnetOptions: SelectProps.Option[] = subnets.map(subnet => ({
    label: `${subnet.label} (${subnet.cidr})`,
    value: subnet.value,
    description: `VPC: ${subnet.vpcId} | AZ: ${subnet.az}`,
  }));

  const securityGroupOptions: SelectProps.Option[] = securityGroups.map(sg => ({
    label: sg.label,
    value: sg.value,
    description: sg.description || `VPC: ${sg.vpcId}`,
  }));

  const instanceTypeOptions: SelectProps.Option[] = instanceTypes.map(it => ({
    label: `${it.label} (${it.vcpus} vCPUs, ${it.memoryGb} GB RAM)`,
    value: it.value,
  }));

  // Find selected options for dropdowns
  const selectedSubnet = subnetOptions.find(opt => opt.value === subnetId) || null;
  const selectedInstanceType = instanceTypeOptions.find(opt => opt.value === instanceType) || null;

  // Determine if save button should be enabled
  const canSave = hasChanges && (staticPrivateIp === '' || ipValid);
  console.log('[ServerLaunchConfigDialog] Save button state:', {
    hasChanges,
    staticPrivateIp,
    ipValid,
    canSave
  });

  return (
    <Modal
      visible={open}
      onDismiss={handleCancel}
      size="large"
      header={
        <Header
          variant="h2"
          description={`Server: ${server.sourceServerID} | Instance: ${server.sourceInstanceId || 'N/A'}`}
        >
          Configure Launch Settings: {server.hostname || server.nameTag || 'Unknown'}
        </Header>
      }
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={handleCancel} disabled={saving}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={!canSave || saving}
              loading={saving}
            >
              Save Configuration
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      <SpaceBetween size="l">
        {/* Loading State */}
        {loading && (
          <Box textAlign="center" padding="l">
            <Spinner /> Loading EC2 resources...
          </Box>
        )}

        {/* Error State */}
        {loadError && (
          <Alert type="error">{loadError}</Alert>
        )}

        {/* Form Content */}
        {!loading && !loadError && (
          <>
            {/* Use Group Defaults Checkbox */}
            <Container>
              <Checkbox
                checked={useGroupDefaults}
                onChange={({ detail }) => setUseGroupDefaults(detail.checked)}
                description="When enabled, only explicitly set fields will override group defaults. When disabled, all fields must be configured."
              >
                Use Protection Group Defaults
              </Checkbox>
            </Container>

            {/* Configuration Form */}
            <Container header={<Header variant="h3">Launch Template Settings</Header>}>
              <SpaceBetween size="l">
            {/* Static Private IP */}
            <FormField
              label={
                <span>
                  Static Private IP Address (Optional)
                  {getFieldIndicator('staticPrivateIp')}
                </span>
              }
              description="Leave empty to use DHCP-assigned IP address"
            >
              <StaticIPInput
                value={staticPrivateIp}
                subnetId={getEffectiveSubnet().id}
                subnetCidr={getEffectiveSubnet().cidr}
                groupId={groupId}
                serverId={server.sourceServerID}
                region={region}
                onChange={setStaticPrivateIp}
                onValidation={handleIpValidation}
              />
            </FormField>

            {/* Subnet */}
            <FormField
              label={
                <span>
                  Target Subnet
                  {getFieldIndicator('subnetId')}
                </span>
              }
              description={
                useGroupDefaults && groupDefaults.subnetId
                  ? `Group default: ${groupDefaults.subnetId}`
                  : undefined
              }
            >
              <Select
                selectedOption={selectedSubnet}
                onChange={({ detail }) => setSubnetId(detail.selectedOption.value || '')}
                options={subnetOptions}
                placeholder="Select subnet"
                disabled={!useGroupDefaults && !subnetId}
                filteringType="auto"
              />
            </FormField>

            {/* Security Groups */}
            <FormField
              label={
                <span>
                  Security Groups
                  {getFieldIndicator('securityGroupIds')}
                </span>
              }
              description={
                useGroupDefaults && groupDefaults.securityGroupIds
                  ? `Group default: ${groupDefaults.securityGroupIds.join(', ')}`
                  : undefined
              }
            >
              <Select
                selectedOption={selectedSecurityGroups.length > 0 ? selectedSecurityGroups[0] : null}
                onChange={({ detail }) => {
                  if (detail.selectedOption) {
                    setSelectedSecurityGroups([detail.selectedOption]);
                  }
                }}
                options={securityGroupOptions}
                placeholder="Select security group"
                filteringType="auto"
              />
            </FormField>

            {/* Instance Type */}
            <FormField
              label={
                <span>
                  Instance Type
                  {getFieldIndicator('instanceType')}
                </span>
              }
              description={
                useGroupDefaults && groupDefaults.instanceType
                  ? `Group default: ${groupDefaults.instanceType}`
                  : undefined
              }
            >
              <Select
                selectedOption={selectedInstanceType}
                onChange={({ detail }) => setInstanceType(detail.selectedOption.value || '')}
                options={instanceTypeOptions}
                placeholder="Select instance type"
                filteringType="auto"
              />
            </FormField>
          </SpaceBetween>
        </Container>

        {/* Validation Messages */}
        {!ipValid && ipValidationMessage && (
          <Alert type="error" header="IP Validation Error">
            {ipValidationMessage}
          </Alert>
        )}

        {/* Info Alert */}
        {useGroupDefaults && (
          <Alert type="info" header="Using Group Defaults">
            Only fields you explicitly configure will override the protection group defaults.
            All other settings will inherit from the group configuration.
          </Alert>
        )}
          </>
        )}
      </SpaceBetween>
    </Modal>
  );
};

export default ServerLaunchConfigDialog;
