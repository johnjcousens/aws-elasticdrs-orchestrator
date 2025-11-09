/**
 * Dashboard Page Component
 * 
 * Main dashboard showing overview of DRS orchestration status.
 * Displays protection groups, recovery plans, and recent executions.
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { PageTransition } from '../components/PageTransition';
import SecurityIcon from '@mui/icons-material/Security';
import MapIcon from '@mui/icons-material/Map';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';

/**
 * Dashboard Page
 * 
 * Landing page after authentication showing system overview.
 */
export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <Box>
        <Typography variant="h4" gutterBottom fontWeight={600}>
          Dashboard
        </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        AWS Disaster Recovery Service Orchestration Platform
      </Typography>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={{ xs: 2, md: 3 }} sx={{ mt: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Card
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              cursor: 'pointer',
              '&:hover': {
                boxShadow: 6,
                transform: 'translateY(-4px)',
                transition: 'all 0.3s ease-in-out',
              },
            }}
            onClick={() => navigate('/protection-groups')}
          >
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon sx={{ fontSize: { xs: 32, sm: 40 }, color: 'primary.main', mr: 2 }} />
                <Typography variant="h5" component="div">
                  Protection Groups
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Manage and configure protection groups for disaster recovery.
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                fullWidth
                onClick={(e) => {
                  e.stopPropagation();
                  navigate('/protection-groups/new');
                }}
              >
                Create New
              </Button>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: 1 }}>
          <Card
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              cursor: 'pointer',
              '&:hover': {
                boxShadow: 6,
                transform: 'translateY(-4px)',
                transition: 'all 0.3s ease-in-out',
              },
            }}
            onClick={() => navigate('/recovery-plans')}
          >
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MapIcon sx={{ fontSize: { xs: 32, sm: 40 }, color: 'primary.main', mr: 2 }} />
                <Typography variant="h5" component="div">
                  Recovery Plans
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Design and manage multi-wave recovery orchestration plans.
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                fullWidth
                onClick={(e) => {
                  e.stopPropagation();
                  navigate('/recovery-plans/new');
                }}
              >
                Create New
              </Button>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: 1 }}>
          <Card
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              cursor: 'pointer',
              '&:hover': {
                boxShadow: 6,
                transform: 'translateY(-4px)',
                transition: 'all 0.3s ease-in-out',
              },
            }}
            onClick={() => navigate('/executions')}
          >
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PlayArrowIcon sx={{ fontSize: { xs: 32, sm: 40 }, color: 'primary.main', mr: 2 }} />
                <Typography variant="h5" component="div">
                  Executions
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Monitor and manage active and historical recovery executions.
              </Typography>
              <Button
                variant="outlined"
                fullWidth
                onClick={(e) => {
                  e.stopPropagation();
                  navigate('/executions');
                }}
              >
                View All
              </Button>
            </CardContent>
          </Card>
        </Box>
      </Stack>

      <Box sx={{ mt: { xs: 3, md: 4 } }}>
        <Typography variant="h5" gutterBottom>
          Quick Start Guide
        </Typography>
        <Card>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="body1" paragraph>
              <strong>Step 1:</strong> Create a Protection Group to define which servers to protect
            </Typography>
            <Typography variant="body1" paragraph>
              <strong>Step 2:</strong> Design a Recovery Plan with orchestrated waves
            </Typography>
            <Typography variant="body1" paragraph>
              <strong>Step 3:</strong> Execute the Recovery Plan when needed
            </Typography>
          </CardContent>
        </Card>
      </Box>
      </Box>
    </PageTransition>
  );
};
