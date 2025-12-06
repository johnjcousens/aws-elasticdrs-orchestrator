/**
 * Wave Configuration Editor Component
 * 
 * Allows creation and editing of recovery waves with server selection,
 * execution type, dependencies, and configuration options.
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  Input,
  FormField,
  Select,
  SpaceBetween,
  Badge,
  ExpandableSection,
  Alert,
  Header,
  Container,
  Multiselect,
  Textarea,
} from '@cloudscape-design/components';
import { ServerSelector } from './ServerSelector';
import type { Wave, ProtectionGroup } from '../types';

interface WaveConfigEditorProps {
  waves: Wave[];
  protectionGroupId: string;  // Keep for backward compatibility, use as default
  protectionGroupIds?: string[];  // Array of available PG IDs
  protectionGroups?: ProtectionGroup[];  // Full ProtectionGroup objects with sourceServerIds
  onChange: (waves: Wave[]) => void;
  readonly?: boolean;
}

/**
 * Wave Configuration Editor Component
 * 
 * Provides UI for configuring multiple recovery waves with dependencies.
 */
export const WaveConfigEditor: React.FC<WaveConfigEditorProps> = ({
  waves,
  protectionGroups,
  onChange,
  readonly = false,
}) => {
  // Defensive: ensure waves is never undefined AND migrate old format to new
  const safeWaves = (waves || []).map(wave => ({
    ...wave,
    // Ensure protectionGroupIds array exists (migrate from old single protectionGroupId format)
    protectionGroupIds: wave.protectionGroupIds && wave.protectionGroupIds.length > 0
      ? wave.protectionGroupIds
      : wave.protectionGroupId 
        ? [wave.protectionGroupId]
        : []
  }));
  
  const [expandedWave, setExpandedWave] = useState<number | null>(safeWaves.length > 0 ? 0 : null);

  /**
   * Calculate which Protection Groups are available for a specific wave
   * A PG is unavailable if ALL its servers are already assigned to OTHER waves
   */
  const getAvailableProtectionGroups = (currentWaveNumber: number) => {
    if (!protectionGroups || protectionGroups.length === 0) return [];

    return protectionGroups.map(pg => {
      // Get all servers from other waves using this PG
      // Check BOTH old protectionGroupId field AND new protectionGroupIds array for backward compatibility
      const otherWavesWithThisPg = safeWaves.filter(w => {
        if (w.waveNumber === currentWaveNumber) return false;
        
        // Check new array format first
        if (w.protectionGroupIds && w.protectionGroupIds.includes(pg.protectionGroupId)) {
          return true;
        }
        
        // Fallback to old single field format
        if (w.protectionGroupId === pg.protectionGroupId) {
          return true;
        }
        
        return false;
      });

      // Get all server IDs assigned to other waves for this PG
      const assignedServerIds = new Set(
        otherWavesWithThisPg.flatMap(w => w.serverIds || [])
      );

      // Calculate available servers (all servers in PG minus assigned ones)
      // Support both sourceServerIds (camelCase) and SourceServerIds (PascalCase from Lambda)
      const serverIds = pg.sourceServerIds || (pg as any).SourceServerIds || [];
      const totalServers = serverIds.length;
      const availableServerCount = totalServers - assignedServerIds.size;

      return {
        ...pg,
        availableServerCount,
        isAvailable: availableServerCount > 0
      };
    });
  };

  const handleAddWave = () => {
    const newWave: Wave = {
      waveNumber: safeWaves.length,
      name: `Wave ${safeWaves.length + 1}`,
      description: '',
      serverIds: [],
      // executionType removed - all within-wave execution is parallel with delays
      dependsOnWaves: [],
      protectionGroupIds: [],  // Empty - user must select PG
      protectionGroupId: '',  // Empty - no default
    };
    onChange([...safeWaves, newWave]);
    setExpandedWave(safeWaves.length);
  };

  const handleRemoveWave = (waveNumber: number) => {
    const updatedWaves = safeWaves
      .filter(w => w.waveNumber !== waveNumber)
      .map((w, index) => ({
        ...w,
        waveNumber: index,
        // Update dependencies to reflect removed wave
        dependsOnWaves: (w.dependsOnWaves || [])
          .filter(dep => dep !== waveNumber)
          .map(dep => dep > waveNumber ? dep - 1 : dep),
      }));
    onChange(updatedWaves);
    setExpandedWave(null);
  };

  const handleMoveWave = (waveNumber: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && waveNumber === 0) ||
      (direction === 'down' && waveNumber === safeWaves.length - 1)
    ) {
      return;
    }

    const newIndex = direction === 'up' ? waveNumber - 1 : waveNumber + 1;
    const updatedWaves = [...safeWaves];
    [updatedWaves[waveNumber], updatedWaves[newIndex]] = [updatedWaves[newIndex], updatedWaves[waveNumber]];
    
    // Renumber waves and update dependencies
    const renumberedWaves = updatedWaves.map((w, index) => ({
      ...w,
      waveNumber: index,
      dependsOnWaves: (w.dependsOnWaves || []).map(dep => {
        if (dep === waveNumber) return newIndex;
        if (dep === newIndex) return waveNumber;
        return dep;
      }),
    }));

    onChange(renumberedWaves);
    setExpandedWave(newIndex);
  };

  const handleUpdateWave = (waveNumber: number, field: keyof Wave, value: any) => {
    const updatedWaves = safeWaves.map(w =>
      w.waveNumber === waveNumber ? { ...w, [field]: value } : w
    );
    onChange(updatedWaves);
  };

  const getAvailableDependencies = (currentWaveNumber: number): number[] => {
    // Waves can only depend on previous waves to prevent circular dependencies
    return Array.from({ length: currentWaveNumber }, (_, i) => i);
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <Header variant="h3">Wave Configuration</Header>
        {!readonly && (
          <Button
            variant="primary"
            iconName="add-plus"
            onClick={handleAddWave}
          >
            Add Wave
          </Button>
        )}
      </div>

      {/* Waves list */}
      {safeWaves.length === 0 ? (
        <Alert type="info">
          No waves configured. Add at least one wave to define the recovery sequence.
        </Alert>
      ) : (
        <SpaceBetween size="m">
          {safeWaves.map((wave) => (
            <ExpandableSection
              key={wave.waveNumber}
              expanded={expandedWave === wave.waveNumber}
              onChange={({ detail }) => setExpandedWave(detail.expanded ? wave.waveNumber : null)}
              headerText={
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%' }}>
                  <span style={{ fontWeight: 600, minWidth: '100px' }}>
                    {wave.name}
                  </span>
                  <Badge color="blue">
                    {(wave.protectionGroupIds || []).length} PG{(wave.protectionGroupIds || []).length !== 1 ? 's' : ''}
                  </Badge>
                  <Badge>
                    {(wave.serverIds || []).length} server{(wave.serverIds || []).length !== 1 ? 's' : ''}
                  </Badge>
                  {!readonly && (
                    <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
                      <Button
                        variant="icon"
                        iconName="angle-up"
                        onClick={() => handleMoveWave(wave.waveNumber, 'up')}
                        disabled={wave.waveNumber === 0}
                      />
                      <Button
                        variant="icon"
                        iconName="angle-down"
                        onClick={() => handleMoveWave(wave.waveNumber, 'down')}
                        disabled={wave.waveNumber === safeWaves.length - 1}
                      />
                      <Button
                        variant="icon"
                        iconName="remove"
                        onClick={() => handleRemoveWave(wave.waveNumber)}
                      />
                    </div>
                  )}
                </div>
              }
            >
              <SpaceBetween size="l">
                {/* Basic Information */}
                <Container header={<Header variant="h3">Basic Information</Header>}>
                  <SpaceBetween size="m">
                    <FormField label="Wave Name" constraintText="Required">
                      <Input
                        value={wave.name}
                        onChange={({ detail }) => handleUpdateWave(wave.waveNumber, 'name', detail.value)}
                        disabled={readonly}
                      />
                    </FormField>
                    <FormField label="Description">
                      <Textarea
                        value={wave.description || ''}
                        onChange={({ detail }) => handleUpdateWave(wave.waveNumber, 'description', detail.value)}
                        disabled={readonly}
                        rows={2}
                      />
                    </FormField>
                  </SpaceBetween>
                </Container>

                {/* Execution Configuration */}
                <Container header={<Header variant="h3">Execution Configuration</Header>}>
                  <SpaceBetween size="m">
                    <Alert type="info">
                      All servers within a wave launch in parallel with DRS-safe delays (15s between servers).
                      Use wave dependencies for sequential operations.
                    </Alert>

                    {getAvailableDependencies(wave.waveNumber).length > 0 && (
                      <FormField label="Depends On Waves">
                        <Multiselect
                          selectedOptions={
                            (wave.dependsOnWaves || []).map(waveNum => ({
                              label: `Wave ${waveNum + 1} - ${safeWaves[waveNum].name}`,
                              value: String(waveNum)
                            }))
                          }
                          onChange={({ detail }) =>
                            handleUpdateWave(
                              wave.waveNumber,
                              'dependsOnWaves',
                              detail.selectedOptions.map(opt => Number(opt.value))
                            )
                          }
                          options={
                            getAvailableDependencies(wave.waveNumber).map(waveNum => ({
                              label: `Wave ${waveNum + 1} - ${safeWaves[waveNum].name}`,
                              value: String(waveNum)
                            }))
                          }
                          disabled={readonly}
                          placeholder="Select waves this wave depends on"
                        />
                      </FormField>
                    )}
                  </SpaceBetween>
                </Container>

                {/* Protection Group Selection - Multi-Select Support */}
                <Container header={<Header variant="h3">Protection Groups</Header>}>
                  <SpaceBetween size="m">
                    <FormField
                      label="Protection Groups"
                      constraintText="Required - Multiple Protection Groups can be selected per wave"
                    >
                      <Multiselect
                        selectedOptions={
                          (protectionGroups || [])
                            .filter(pg => (wave.protectionGroupIds || []).includes(pg.protectionGroupId))
                            .map(pg => {
                              const availablePgs = getAvailableProtectionGroups(wave.waveNumber);
                              const availableInfo = availablePgs.find(apg => apg.protectionGroupId === pg.protectionGroupId);
                              const availableCount = availableInfo?.availableServerCount || 0;
                              const totalCount = pg.sourceServerIds?.length || 0;
                              return {
                                label: `${pg.name} (${availableCount}/${totalCount} available)`,
                                value: pg.protectionGroupId,
                                tags: availableCount > 0 ? ['available'] : ['unavailable']
                              };
                            })
                        }
                        onChange={({ detail }) => {
                          const pgIds = detail.selectedOptions.map(opt => opt.value || '');
                          const updatedWaves = safeWaves.map(w =>
                            w.waveNumber === wave.waveNumber 
                              ? { ...w, protectionGroupIds: pgIds, protectionGroupId: pgIds[0] || '', serverIds: [] } 
                              : w
                          );
                          onChange(updatedWaves);
                        }}
                        options={
                          (protectionGroups || []).map(pg => {
                            const availablePgs = getAvailableProtectionGroups(wave.waveNumber);
                            const availableInfo = availablePgs.find(apg => apg.protectionGroupId === pg.protectionGroupId);
                            const availableCount = availableInfo?.availableServerCount || 0;
                            const totalCount = pg.sourceServerIds?.length || 0;
                            return {
                              label: `${pg.name} (${availableCount}/${totalCount} available)`,
                              value: pg.protectionGroupId,
                              tags: availableCount > 0 ? ['available'] : ['unavailable']
                            };
                          })
                        }
                        disabled={readonly}
                        placeholder="Select one or more Protection Groups"
                      />
                    </FormField>
                    {(wave.protectionGroupIds || []).length === 0 && (
                      <Alert type="warning">
                        Please select at least one Protection Group for this wave
                      </Alert>
                    )}
                    {(wave.protectionGroupIds || []).length > 1 && (
                      <Alert type="info">
                        Multiple Protection Groups selected. Servers from all selected Protection Groups will be available for this wave.
                      </Alert>
                    )}
                  </SpaceBetween>
                </Container>

                {/* Server Selection */}
                <Container header={<Header variant="h3">Server Selection</Header>}>
                  {(wave.protectionGroupIds || []).length > 0 ? (
                    <ServerSelector
                      key={(wave.protectionGroupIds || []).join(',')}
                      protectionGroupIds={wave.protectionGroupIds || []}
                      protectionGroupId={wave.protectionGroupId || wave.protectionGroupIds?.[0] || ''}
                      selectedServerIds={wave.serverIds}
                      onChange={(serverIds) => handleUpdateWave(wave.waveNumber, 'serverIds', serverIds)}
                      readonly={readonly}
                    />
                  ) : (
                    <Alert type="info">
                      Select one or more Protection Groups above to choose servers for this wave
                    </Alert>
                  )}
                </Container>
              </SpaceBetween>
            </ExpandableSection>
          ))}
        </SpaceBetween>
      )}

      {/* Validation Messages */}
      {safeWaves.length > 0 && safeWaves.some(w => (w.serverIds || []).length === 0) && (
        <Alert type="warning" dismissible>
          Some waves have no servers selected. Each wave must include at least one server.
        </Alert>
      )}
    </div>
  );
};
