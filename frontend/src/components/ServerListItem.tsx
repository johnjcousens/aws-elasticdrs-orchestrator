import React from 'react';
import {
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Chip,
  Box,
  Typography
} from '@mui/material';
import {
  CheckCircle as ReadyIcon,
  Sync as SyncingIcon,
  Error as ErrorIcon,
  HelpOutline as UnknownIcon
} from '@mui/icons-material';

interface DRSServer {
  sourceServerID: string;
  hostname: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  assignedToProtectionGroup?: {
    protectionGroupId: string;
    protectionGroupName: string;
  };
  selectable: boolean;
}

interface ServerListItemProps {
  server: DRSServer;
  selected: boolean;
  onToggle: () => void;
}

const getStateColor = (state: string): 'success' | 'info' | 'error' | 'default' => {
  switch (state) {
    case 'READY_FOR_RECOVERY':
      return 'success';
    case 'SYNCING':
    case 'INITIATED':
      return 'info';
    case 'DISCONNECTED':
    case 'STOPPED':
      return 'error';
    default:
      return 'default';
  }
};

const getStateIcon = (state: string) => {
  switch (state) {
    case 'READY_FOR_RECOVERY':
      return <ReadyIcon fontSize="small" />;
    case 'SYNCING':
    case 'INITIATED':
      return <SyncingIcon fontSize="small" />;
    case 'DISCONNECTED':
    case 'STOPPED':
      return <ErrorIcon fontSize="small" />;
    default:
      return <UnknownIcon fontSize="small" />;
  }
};

export const ServerListItem: React.FC<ServerListItemProps> = ({
  server,
  selected,
  onToggle
}) => {
  const { sourceServerID, hostname, state, assignedToProtectionGroup, selectable } = server;
  
  return (
    <ListItem
      disablePadding
      sx={{
        opacity: selectable ? 1 : 0.6,
        backgroundColor: selectable ? 'inherit' : 'action.disabledBackground'
      }}
    >
      <ListItemButton onClick={onToggle} disabled={!selectable} dense>
        <ListItemIcon>
          <Checkbox
            edge="start"
            checked={selected}
            disabled={!selectable}
            tabIndex={-1}
            disableRipple
          />
        </ListItemIcon>
        <ListItemText
          primary={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body1">
                {hostname}
              </Typography>
              <Chip
                size="small"
                label={state}
                color={getStateColor(state)}
                icon={getStateIcon(state)}
              />
            </Box>
          }
          secondary={
            <Box>
              <Typography variant="body2" color="text.secondary">
                {sourceServerID}
              </Typography>
              {assignedToProtectionGroup && (
                <Typography variant="body2" color="warning.main">
                  Already assigned to: {assignedToProtectionGroup.protectionGroupName}
                </Typography>
              )}
              {selectable && (
                <Typography variant="body2" color="success.main">
                  Available
                </Typography>
              )}
            </Box>
          }
        />
      </ListItemButton>
    </ListItem>
  );
};
