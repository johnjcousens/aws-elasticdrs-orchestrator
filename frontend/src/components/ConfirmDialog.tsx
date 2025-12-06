/**
 * Reusable Confirmation Dialog Component
 * 
 * Generic confirmation dialog with customizable title, message, and action buttons.
 * Used for delete confirmations and other destructive actions.
 */

import React, { type ReactNode } from 'react';
import { Modal, Box, SpaceBetween, Button } from '@cloudscape-design/components';

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string | ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmColor?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  onConfirm: () => void;
  onCancel: () => void;
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
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  confirmColor = 'primary',
  onConfirm,
  onCancel,
}) => {
  // Map Material-UI colors to CloudScape button variants
  const getButtonVariant = (color: string): 'primary' | 'normal' | 'link' | 'icon' => {
    if (color === 'error') return 'primary'; // CloudScape doesn't have error variant, use primary for destructive actions
    return 'primary';
  };

  return (
    <Modal
      visible={open}
      onDismiss={onCancel}
      header={title}
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={onCancel}>
              {cancelLabel}
            </Button>
            <Button 
              variant={getButtonVariant(confirmColor)} 
              onClick={onConfirm}
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
