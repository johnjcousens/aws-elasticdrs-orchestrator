/**
 * Reusable Confirmation Dialog Component
 * 
 * Generic confirmation dialog with customizable title, message, and action buttons.
 * Used for delete confirmations and other destructive actions.
 */

import React, { type ReactNode } from 'react';
import { Modal, Box, SpaceBetween, Button } from '@cloudscape-design/components';

export interface ConfirmDialogProps {
  open?: boolean; // Material-UI style
  visible?: boolean; // CloudScape style
  title: string;
  message: string | ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmColor?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  onConfirm: () => void;
  onCancel?: () => void;
  onDismiss?: () => void; // CloudScape style
  loading?: boolean; // Disable buttons while action is in progress
}

/**
 * ConfirmDialog Component
 * 
 * @param open - Whether the dialog is open
 * @param title - Dialog title
 * @param message - Confirmation message (string or ReactNode)
 * @param confirmLabel - Label for confirm button (default: "Confirm")
 * @param cancelLabel - Label for cancel button (default: "Cancel")
 * @param confirmColor - Color of confirm button (default: "primary") - Note: CloudScape uses variant instead
 * @param onConfirm - Callback when user confirms
 * @param onCancel - Callback when user cancels
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  visible,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  confirmColor = 'primary',
  onConfirm,
  onCancel,
  onDismiss,
  loading = false,
}) => {
  // Support both 'open' and 'visible' props for backwards compatibility
  const isVisible = visible !== undefined ? visible : (open !== undefined ? open : false);
  const handleDismiss = onDismiss || onCancel || (() => {});
  
  // Map Material-UI colors to CloudScape button variants
  const getButtonVariant = (color: string): 'primary' | 'normal' | 'link' | 'icon' => {
    if (color === 'error') return 'primary'; // CloudScape doesn't have error variant, use primary for destructive actions
    return 'primary';
  };

  return (
    <Modal
      visible={isVisible}
      onDismiss={handleDismiss}
      header={title}
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={handleDismiss} disabled={loading}>
              {cancelLabel}
            </Button>
            <Button 
              variant={getButtonVariant(confirmColor)} 
              onClick={onConfirm}
              disabled={loading}
              loading={loading}
            >
              {confirmLabel}
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      {typeof message === 'string' ? (
        <Box variant="p">{message}</Box>
      ) : (
        message
      )}
    </Modal>
  );
};
