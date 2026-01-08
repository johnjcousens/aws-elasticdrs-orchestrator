/**
 * Minimal Execution Details Page for Testing Navigation
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Header, SpaceBetween } from '@cloudscape-design/components';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';

export const ExecutionDetailsPageMinimal: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button 
                  onClick={() => navigate('/executions')} 
                  iconName="arrow-left"
                >
                  Back to Executions
                </Button>
              </SpaceBetween>
            }
          >
            Execution Details (Minimal Test)
          </Header>
        }
      >
        <div>
          <p>Execution ID: {executionId}</p>
          <p>This is a minimal test page to check navigation.</p>
          <Button onClick={() => navigate('/executions')}>
            Navigate Back
          </Button>
        </div>
      </ContentLayout>
    </PageTransition>
  );
};