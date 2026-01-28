/**
 * Wave Configuration Editor Component
 * 
 * Allows creation and editing of recovery waves with server selection,
 * execution type, dependencies, and configuration options.
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Input,
  FormField,
  SpaceBetween,
  Badge,
  ExpandableSection,
  Alert,
  Header,
  Container,
  Multiselect,
  Textarea,
  Checkbox,
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

  const handleAddWave = useCallback(() => {
    const newWave: Wave = {
      waveNumber: safeWaves.length,
      waveName: `Wave ${safeWaves.length + 1}`,
      waveDescription: '',
      serverIds: [],
      // executionType removed - all within-wave execution is parallel with delays
      dependsOnWaves: [],
      protectionGroupIds: [],  // Empty - user must select PG
      protectionGroupId: '',  // Empty - no default
    };
    
    const updatedWaves = [...safeWaves, newWave];
    
    // Use setTimeout to ensure state update happens after current render cycle
    setTimeout(() => {
      onChange(updatedWaves);
      setExpandedWave(safeWaves.length);
    }, 0);
  }, [safeWaves, onChange]);

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

  const handleUpdateWave = (waveNumber: number, field: keyof Wave, value: string | boolean | string[] | number | number[]) => {
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
      {/* Header with Add Wave button */}
      <Box float="right" margin={{ bottom: 's' }}>
        {!readonly && (
          <Button 
            iconName="add-plus" 
            onClick={handleAddWave}
            variant="normal"
          >
            Add Wave
          </Button>
        )}
      </Box>

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
                    {wave.waveName}
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
                        value={wave.waveName}
                        onChange={({ detail }: { detail: { value: string } }) => handleUpdateWave(wave.waveNumber, 'waveName', detail.value)}
                        disabled={readonly}
                      />
                    </FormField>
                    <FormField label="Description">
                      <Textarea
                        value={wave.waveDescription || ''}
                        onChange={({ detail }: { detail: { value: string } }) => handleUpdateWave(wave.waveNumber, 'waveDescription', detail.value)}
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
                        <div onClick={(e) => e.stopPropagation()} onMouseDown={(e) => e.stopPropagation()}>
                          <Multiselect
                            selectedOptions={
                              (wave.dependsOnWaves || []).map(waveNum => ({
                                label: `Wave ${waveNum + 1} - ${safeWaves[waveNum].waveName}`,
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
                                label: `Wave ${waveNum + 1} - ${safeWaves[waveNum].waveName}`,
                                value: String(waveNum)
                              }))
                            }
                            disabled={readonly}
                            placeholder="Select waves this wave depends on"
                          />
                        </div>
                      </FormField>
                    )}

                    {/* Pause Before Wave Checkbox - only show for waves after the first */}
                    {wave.waveNumber > 0 && (
                      <FormField
                        label="Pause Before Wave"
                        description="When enabled, execution will pause before starting this wave and require manual resume"
                      >
                        <Checkbox
                          checked={wave.pauseBeforeWave || false}
                          onChange={({ detail }) =>
                            handleUpdateWave(wave.waveNumber, 'pauseBeforeWave', detail.checked)
                          }
                          disabled={readonly}
                        >
                          Pause execution before starting this wave
                        </Checkbox>
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
                      <div onClick={(e) => e.stopPropagation()} onMouseDown={(e) => e.stopPropagation()}>
                        <Multiselect
                          selectedOptions={
                            (protectionGroups || [])
                              .filter(pg => (wave.protectionGroupIds || []).includes(pg.protectionGroupId))
                              .map(pg => {
                                const tagCount = Object.keys(pg.serverSelectionTags || {}).length;
                                const serverCount = (pg.sourceServerIds || []).length;
                                const selectionMode = tagCount > 0 ? 'tag-based' : serverCount > 0 ? 'server-based' : 'unconfigured';
                                const label = tagCount > 0 
                                  ? `${pg.groupName} (${tagCount} tag${tagCount !== 1 ? 's' : ''})`
                                  : `${pg.groupName} (${serverCount} server${serverCount !== 1 ? 's' : ''})`;
                                return {
                                  label,
                                  value: pg.protectionGroupId,
                                  tags: [selectionMode]
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
                              const tagCount = Object.keys(pg.serverSelectionTags || {}).length;
                              const serverCount = (pg.sourceServerIds || []).length;
                              const selectionMode = tagCount > 0 ? 'tag-based' : serverCount > 0 ? 'server-based' : 'unconfigured';
                              const label = tagCount > 0 
                                ? `${pg.groupName} (${tagCount} tag${tagCount !== 1 ? 's' : ''})`
                                : `${pg.groupName} (${serverCount} server${serverCount !== 1 ? 's' : ''})`;
                              return {
                                label,
                                value: pg.protectionGroupId,
                                tags: [selectionMode]
                              };
                            })
                          }
                          disabled={readonly}
                          placeholder="Select one or more Protection Groups"
                        />
                      </div>
                    </FormField>
                    {(wave.protectionGroupIds || []).length === 0 && (
                      <Alert type="warning">
                        Please select at least one Protection Group for this wave
                      </Alert>
                    )}
                    {(wave.protectionGroupIds || []).length > 1 && (
                      <Alert type="info">
                        Multiple Protection Groups selected. Servers from all selected Protection Groups will be included.
                      </Alert>
                    )}
                  </SpaceBetween>
                </Container>

                {/* Server Selection */}
                <Container header={<Header variant="h3">Server Selection</Header>}>
                  {(wave.protectionGroupIds || []).length > 0 ? (
                    (() => {
                      const selectedPGs = (protectionGroups || []).filter(pg => 
                        (wave.protectionGroupIds || []).includes(pg.protectionGroupId)
                      );
                      const allTagBased = selectedPGs.length > 0 && selectedPGs.every(pg => 
                        pg.serverSelectionTags && Object.keys(pg.serverSelectionTags).length > 0
                      );
                      const hasServerBasedPGs = selectedPGs.some(pg => 
                        pg.sourceServerIds && pg.sourceServerIds.length > 0
                      );
                      
                      if (allTagBased) {
                        return (
                          <Alert type="info">
                            <strong>Tag-based Protection Groups selected.</strong><br />
                            Servers will be automatically resolved at execution time based on Protection Group tags.
                            No manual server selection is needed.
                          </Alert>
                        );
                      }
                      
                      if (hasServerBasedPGs) {
                        return (
                          <ServerSelector
                            key={(wave.protectionGroupIds || []).join(',')}
                            protectionGroupIds={wave.protectionGroupIds || []}
                            protectionGroupId={wave.protectionGroupId || wave.protectionGroupIds?.[0] || ''}
                            selectedServerIds={wave.serverIds}
                            onChange={(serverIds) => handleUpdateWave(wave.waveNumber, 'serverIds', serverIds)}
                            readonly={readonly}
                            protectionGroups={protectionGroups}
                          />
                        );
                      }
                      
                      return (
                        <Alert type="warning">
                          Selected Protection Groups have no servers configured. 
                          Please edit the Protection Groups to add servers or configure tags.
                        </Alert>
                      );
                    })()
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

      {/* Validation Messages - only show for non-tag-based PGs */}
      {safeWaves.length > 0 && safeWaves.some(w => {
        // Check if wave uses tag-based PGs
        const selectedPGs = (protectionGroups || []).filter(pg => 
          (w.protectionGroupIds || []).includes(pg.protectionGroupId)
        );
        const isTagBased = selectedPGs.length > 0 && selectedPGs.every(pg => 
          pg.serverSelectionTags && Object.keys(pg.serverSelectionTags).length > 0
        );
        // Only warn if NOT tag-based and no servers selected
        return !isTagBased && (w.serverIds || []).length === 0;
      }) && (
        <Alert type="warning" dismissible>
          Some waves have no servers selected. Each wave must include at least one server.
        </Alert>
      )}
    </div>
  );
};
