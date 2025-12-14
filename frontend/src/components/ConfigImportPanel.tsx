/**
 * Configuration Import Panel
 * 
 * Handles importing Protection Groups and Recovery Plans from JSON file.
 */

import React, { useState, useRef } from 'react';
import {
  SpaceBetween,
  Button,
  Alert,
  Box,
  TextContent,
  Container,
  Header,
  ColumnLayout,
  Toggle,
} from '@cloudscape-design/components';
import { useApi } from '../contexts/ApiContext';
import { ImportResultsDialog } from './ImportResultsDialog';
import toast from 'react-hot-toast';

interface ImportPreview {
  protectionGroups: number;
  recoveryPlans: number;
  schemaVersion: string;
  exportedAt: string;
  sourceRegion: string;
}

interface ImportResults {
  success: boolean;
  dryRun: boolean;
  correlationId: string;
  summary: {
    protectionGroups: { created: number; skipped: number; failed: number };
    recoveryPlans: { created: number; skipped: number; failed: number };
  };
  created: Array<{ type: string; name: string; details?: Record<string, unknown> }>;
  skipped: Array<{ type: string; name: string; reason: string; details?: Record<string, unknown> }>;
  failed: Array<{ type: string; name: string; reason: string; details?: Record<string, unknown> }>;
}

interface ConfigImportPanelProps {
  onImportComplete?: () => void;
}

export const ConfigImportPanel: React.FC<ConfigImportPanelProps> = ({
  onImportComplete,
}) => {
  const { importConfiguration } = useApi();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [configData, setConfigData] = useState<Record<string, unknown> | null>(null);
  const [dryRun, setDryRun] = useState(false);
  const [results, setResults] = useState<ImportResults | null>(null);
  const [showResults, setShowResults] = useState(false);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError(null);
    setSelectedFile(file);
    setPreview(null);
    setConfigData(null);

    try {
      const text = await file.text();
      const data = JSON.parse(text);

      // Validate basic structure
      if (!data.metadata?.schemaVersion) {
        throw new Error('Invalid configuration file: missing schemaVersion');
      }

      setConfigData(data);
      setPreview({
        protectionGroups: data.protectionGroups?.length || 0,
        recoveryPlans: data.recoveryPlans?.length || 0,
        schemaVersion: data.metadata.schemaVersion,
        exportedAt: data.metadata.exportedAt || 'Unknown',
        sourceRegion: data.metadata.sourceRegion || 'Unknown',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to parse configuration file';
      setError(message);
      setSelectedFile(null);
    }
  };

  const handleImport = async () => {
    if (!configData) return;

    setLoading(true);
    setError(null);

    try {
      const result = await importConfiguration(configData, dryRun);
      setResults(result as ImportResults);
      setShowResults(true);

      if (result.success && !dryRun) {
        toast.success('Configuration imported successfully');
      } else if (dryRun) {
        toast.success('Dry run completed - no changes made');
      } else {
        toast.error('Import completed with errors');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to import configuration';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreview(null);
    setConfigData(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleResultsClose = () => {
    setShowResults(false);
    if (results?.success && !results.dryRun) {
      onImportComplete?.();
    }
  };

  return (
    <>
      <SpaceBetween size="l">
        <TextContent>
          <p>
            Import Protection Groups and Recovery Plans from a previously exported JSON file.
            This operation is non-destructive - existing resources will be skipped.
          </p>
        </TextContent>

        {error && (
          <Alert type="error" dismissible onDismiss={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={() => fileInputRef.current?.click()}>
              Select File
            </Button>
            {selectedFile && (
              <Button variant="link" onClick={handleClear}>
                Clear
              </Button>
            )}
          </SpaceBetween>
          {selectedFile && (
            <Box padding={{ top: 'xs' }} color="text-body-secondary">
              Selected: {selectedFile.name}
            </Box>
          )}
        </Box>

        {preview && (
          <Container header={<Header variant="h3">Import Preview</Header>}>
            <ColumnLayout columns={2} variant="text-grid">
              <div>
                <Box variant="awsui-key-label">Protection Groups</Box>
                <Box variant="awsui-value-large">{preview.protectionGroups}</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">Recovery Plans</Box>
                <Box variant="awsui-value-large">{preview.recoveryPlans}</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">Schema Version</Box>
                <Box>{preview.schemaVersion}</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">Source Region</Box>
                <Box>{preview.sourceRegion}</Box>
              </div>
              <div>
                <Box variant="awsui-key-label">Exported At</Box>
                <Box>{new Date(preview.exportedAt).toLocaleString()}</Box>
              </div>
            </ColumnLayout>
          </Container>
        )}

        {preview && (
          <SpaceBetween size="m">
            <Toggle
              checked={dryRun}
              onChange={({ detail }) => setDryRun(detail.checked)}
            >
              Dry run (validate without making changes)
            </Toggle>

            <Button
              variant="primary"
              loading={loading}
              onClick={handleImport}
              disabled={!configData}
              iconName="upload"
            >
              {dryRun ? 'Validate Configuration' : 'Import Configuration'}
            </Button>
          </SpaceBetween>
        )}
      </SpaceBetween>

      {results && (
        <ImportResultsDialog
          visible={showResults}
          onDismiss={handleResultsClose}
          results={results}
        />
      )}
    </>
  );
};
