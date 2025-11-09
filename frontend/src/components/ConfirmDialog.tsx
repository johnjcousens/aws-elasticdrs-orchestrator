/**
 * Reusable Confirmation Dialog Component
 * 
 * Generic confirmation dialog with customizable title, message, and action buttons.
 * Used for delete confirmations and other destructive actions.
 */

import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from '@mui/material';
import type { ReactNode } from 'react';

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
 * @param confirmColor - Color of confirm button (default: "primary")
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
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <DialogTitle id="confirm-dialog-title">{title}</DialogTitle>
      <DialogContent>
        {typeof message === 'string' ? (
          <DialogContentText id="confirm-dialog-description">{message}</DialogContentText>
        ) : (
          message
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} color="inherit">
          {cancelLabel}
        </Button>
        <Button onClick={onConfirm} color={confirmColor} variant="contained" autoFocus>
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
