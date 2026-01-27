/**
 * Launch Config Section Component
 * 
 * Provides UI for configuring EC2 launch settings for Protection Groups.
 * Settings are applied to all servers in the group during recovery.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  SpaceBetween,
  FormField,
  Select,
  Multiselect,
  Checkbox,
  ColumnLayout,
  Spinner,
  Box,
  Alert,
  ExpandableSection,
} from '@cloudscape-design/components';
import type { SelectProps } from '@cloudscape-design/components';
import type {
  LaunchConfig,
  SubnetOption,
  SecurityGroupOption,
  InstanceProfileOption,
  InstanceTypeOption,
} from '../types';
import apiClient from '../services/api';

interface LaunchConfigSectionProps {
  region: string;
  launchConfig: LaunchConfig;
  onChange: (config: LaunchConfig) => void;
  onExpandChange?: (expanded: boolean) => void;
  disabled?: boolean;
}

export const LaunchConfigSection: React.FC<LaunchConfigSectionProps> = ({
  region,
  launchConfig,
  onChange,
  onExpandChange,
  disabled = false,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  // Notify parent when expanded state changes
  const handleExpandChange = (isExpanded: boolean) => {
    setExpanded(isExpanded);
    onExpandChange?.(isExpanded);
  };

  // Dropdown options
  const [subnets, setSubnets] = useState<SubnetOption[]>([]);
  const [securityGroups, setSecurityGroups] = useState<SecurityGroupOption[]>([]);
  const [instanceProfiles, setInstanceProfiles] = useState<InstanceProfileOption[]>([]);
  const [instanceTypes, setInstanceTypes] = useState<InstanceTypeOption[]>([]);

  // Load dropdown options when region changes or section expands
  const loadDropdownOptions = useCallback(async () => {
    if (!region) return;
    
    setLoading(true);
    setError(null);
    try {
      const [subs, sgs, profiles, types] = await Promise.all([
        apiClient.getEC2Subnets(region),
        apiClient.getEC2SecurityGroups(region),
        apiClient.getEC2InstanceProfiles(region),
        apiClient.getEC2InstanceTypes(region),
      ]);
      setSubnets(subs);
      setSecurityGroups(sgs);
      setInstanceProfiles(profiles);
      setInstanceTypes(types);
    } catch (err: unknown) {
      setError('Failed to load EC2 resources. Check IAM permissions.');
      console.error('Error loading dropdown options:', err);
    } finally {
      setLoading(false);
    }
  }, [region]);

  useEffect(() => {
    if (region && expanded) {
      loadDropdownOptions();
    }
  }, [region, expanded, loadDropdownOptions]);

  const updateConfig = (key: keyof LaunchConfig, value: unknown) => {
    onChange({ ...launchConfig, [key]: value });
  };

  // Convert to CloudScape options format
  const subnetOptions: SelectProps.Option[] = subnets.map(s => ({
    value: s.value,
    label: s.label,
  }));

  const sgOptions: SelectProps.Option[] = securityGroups.map(sg => ({
    value: sg.value,
    label: sg.label,
  }));

  const profileOptions: SelectProps.Option[] = instanceProfiles.map(p => ({
    value: p.value,
    label: p.label,
  }));

  const typeOptions: SelectProps.Option[] = instanceTypes.map(t => ({
    value: t.value,
    label: t.label,
  }));

  // Check if any launch config is set
  const hasConfig = launchConfig.subnetId || 
    (launchConfig.securityGroupIds && launchConfig.securityGroupIds.length > 0) ||
    launchConfig.instanceType ||
    launchConfig.instanceProfileName ||
    launchConfig.copyPrivateIp ||
    launchConfig.copyTags ||
    launchConfig.targetInstanceTypeRightSizingMethod ||
    launchConfig.launchDisposition ||
    launchConfig.licensing?.osByol !== undefined;

  // Build header text
  const headerText = hasConfig ? 'Launch Settings (All Servers in Protection Group)' : 'Launch Settings';

  return (
    <ExpandableSection
      variant="container"
      headerText={headerText}
      headerDescription="Configure EC2 settings applied to all servers during recovery"
      expanded={expanded}
      onChange={({ detail }) => handleExpandChange(detail.expanded)}
    >
      {loading ? (
        <Box textAlign="center" padding="l">
          <Spinner /> Loading EC2 resources...
        </Box>
      ) : error ? (
        <Alert type="error">{error}</Alert>
      ) : !region ? (
        <Alert type="info">Select a region first to configure launch settings.</Alert>
      ) : (
        <div data-form-type="other" data-lpignore="true" data-1p-ignore="true">
          <SpaceBetween direction="vertical" size="m">
            <ColumnLayout columns={2}>
              <FormField
                label="Target Subnet"
                description="VPC subnet for recovery instances"
              >
                <Select
                  selectedOption={subnetOptions.find(o => o.value === launchConfig.subnetId) || null}
                  onChange={({ detail }) => updateConfig('subnetId', detail.selectedOption?.value)}
                  options={subnetOptions}
                  placeholder="Select subnet"
                  filteringType="auto"
                  disabled={disabled}
                />
              </FormField>

              <FormField
                label="Instance Type"
                description="EC2 instance type for recovery"
              >
                <Select
                  selectedOption={typeOptions.find(o => o.value === launchConfig.instanceType) || null}
                  onChange={({ detail }) => updateConfig('instanceType', detail.selectedOption?.value)}
                  options={typeOptions}
                  placeholder="Select instance type"
                  filteringType="auto"
                  disabled={disabled}
                />
              </FormField>
            </ColumnLayout>

            <FormField
              label="Security Groups"
              description="Security groups for recovery instances"
            >
              <Multiselect
                selectedOptions={sgOptions.filter(o =>
                  launchConfig.securityGroupIds?.includes(o.value || '')
                )}
                onChange={({ detail }) =>
                  updateConfig('securityGroupIds', detail.selectedOptions.map(o => o.value))
                }
                options={sgOptions}
                placeholder="Select security groups"
                filteringType="auto"
                disabled={disabled}
              />
            </FormField>

            <FormField
              label="IAM Instance Profile"
              description="IAM role for recovery instances"
            >
              <Select
                selectedOption={profileOptions.find(o => o.value === launchConfig.instanceProfileName) || null}
                onChange={({ detail }) => updateConfig('instanceProfileName', detail.selectedOption?.value)}
                options={profileOptions}
                placeholder="Select instance profile"
                filteringType="auto"
                disabled={disabled}
              />
            </FormField>

            {/* DRS Automated Launch Settings */}
            <ColumnLayout columns={2}>
              <FormField
                label="Instance Type Right Sizing"
                description="How DRS selects instance type"
              >
                <Select
                  selectedOption={
                    launchConfig.targetInstanceTypeRightSizingMethod
                      ? {
                          value: launchConfig.targetInstanceTypeRightSizingMethod,
                          label: launchConfig.targetInstanceTypeRightSizingMethod === 'BASIC'
                            ? 'Active (basic) - DRS selects instance type'
                            : launchConfig.targetInstanceTypeRightSizingMethod === 'IN_AWS'
                            ? 'Active (in-aws) - Periodic updates from EC2'
                            : 'Inactive - Use EC2 launch template',
                        }
                      : null
                  }
                  onChange={({ detail }) =>
                    updateConfig('targetInstanceTypeRightSizingMethod', detail.selectedOption?.value)
                  }
                  options={[
                    { value: 'BASIC', label: 'Active (basic) - DRS selects instance type' },
                    { value: 'IN_AWS', label: 'Active (in-aws) - Periodic updates from EC2' },
                    { value: 'NONE', label: 'Inactive - Use EC2 launch template' },
                  ]}
                  placeholder="Select right sizing method"
                  disabled={disabled}
                />
              </FormField>

              <FormField
                label="Launch Disposition"
                description="Instance state after launch"
              >
                <Select
                  selectedOption={
                    launchConfig.launchDisposition
                      ? {
                          value: launchConfig.launchDisposition,
                          label: launchConfig.launchDisposition === 'STARTED' ? 'Started' : 'Stopped',
                        }
                      : { value: 'STARTED', label: 'Started' }
                  }
                  onChange={({ detail }) =>
                    updateConfig('launchDisposition', detail.selectedOption?.value)
                  }
                  options={[
                    { value: 'STARTED', label: 'Started - Instance starts automatically' },
                    { value: 'STOPPED', label: 'Stopped - Instance remains stopped' },
                  ]}
                  disabled={disabled}
                />
              </FormField>
            </ColumnLayout>

            <FormField
              label="OS Licensing"
              description="License type for Windows servers"
            >
              <Select
                selectedOption={
                  launchConfig.licensing?.osByol !== undefined
                    ? {
                        value: launchConfig.licensing.osByol ? 'BYOL' : 'AWS',
                        label: launchConfig.licensing.osByol
                          ? 'Bring your own license (BYOL)'
                          : 'Use AWS provided license',
                      }
                    : null
                }
                onChange={({ detail }) =>
                  updateConfig('licensing', { osByol: detail.selectedOption?.value === 'BYOL' })
                }
                options={[
                  { value: 'BYOL', label: 'Bring your own license (BYOL)' },
                  { value: 'AWS', label: 'Use AWS provided license' },
                ]}
                placeholder="Select licensing option"
                disabled={disabled}
              />
            </FormField>

            <ColumnLayout columns={2}>
              <Checkbox
                checked={launchConfig.copyPrivateIp || false}
                onChange={({ detail }) => updateConfig('copyPrivateIp', detail.checked)}
                disabled={disabled}
              >
                Copy Private IP
              </Checkbox>
              <Checkbox
                checked={launchConfig.copyTags || false}
                onChange={({ detail }) => updateConfig('copyTags', detail.checked)}
                disabled={disabled}
              >
                Transfer Server Tags
              </Checkbox>
            </ColumnLayout>
          </SpaceBetween>
        </div>
      )}
    </ExpandableSection>
  );
};

export default LaunchConfigSection;
