/**
 * AddStagingAccountModal Component Tests (Simplified)
 *
 * Tests for the simplified AddStagingAccountModal component covering:
 * - Form validation (account ID format only)
 * - Auto-generation of role ARN and external ID
 * - Validation flow with success
 * - Add button disabled until validation succeeds
 * - Add flow with success
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AddStagingAccountModal } from "../AddStagingAccountModal";
import type { StagingAccount } from "../../types/staging-accounts";
import * as stagingAccountsApi from "../../services/staging-accounts-api";
import "@testing-library/jest-dom";

// Mock the API module
vi.mock("../../services/staging-accounts-api", () => ({
  validateStagingAccount: vi.fn(),
  addStagingAccount: vi.fn(),
}));

describe("AddStagingAccountModal", () => {
  const mockOnDismiss = vi.fn();
  const mockOnAdd = vi.fn();
  const targetAccountId = "111122223333";

  const defaultProps = {
    visible: true,
    onDismiss: mockOnDismiss,
    onAdd: mockOnAdd,
    targetAccountId,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock responses
    vi.mocked(stagingAccountsApi.validateStagingAccount).mockResolvedValue({
      valid: true,
      roleAccessible: true,
      drsInitialized: true,
      currentServers: 42,
      replicatingServers: 42,
      totalAfter: 309,
    });
    
    vi.mocked(stagingAccountsApi.addStagingAccount).mockResolvedValue({
      success: true,
      message: "Staging account added successfully",
      stagingAccounts: [],
    });
  });

  describe("Form rendering", () => {
    it("renders modal when visible", () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      expect(screen.getByText("Add Staging Account")).toBeInTheDocument();
    });

    it("renders simplified form fields", () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      expect(screen.getByLabelText("Account ID")).toBeInTheDocument();
      expect(screen.getByLabelText(/Account Name \(Optional\)/i)).toBeInTheDocument();
    });

    it("renders action buttons", () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      expect(screen.getByText("Cancel")).toBeInTheDocument();
      expect(screen.getByText("Validate Access")).toBeInTheDocument();
      expect(screen.getByText("Add Account")).toBeInTheDocument();
    });

    it("renders info alert about simplified setup", () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      expect(screen.getByText(/Simplified Setup/i)).toBeInTheDocument();
      expect(screen.getByText(/Enter the AWS account ID/i)).toBeInTheDocument();
    });
  });

  describe("Form validation - Account ID", () => {
    it("shows error for empty account ID", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText("Account ID is required")).toBeInTheDocument();
      });
    });

    it("shows error for invalid account ID format", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      const accountIdInput = screen.getByLabelText("Account ID");
      fireEvent.change(accountIdInput, { target: { value: "12345" } });

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText("Account ID must be exactly 12 digits")).toBeInTheDocument();
      });
    });

    it("accepts valid 12-digit account ID", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      const accountIdInput = screen.getByLabelText("Account ID");
      fireEvent.change(accountIdInput, { target: { value: "444455556666" } });

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.queryByText("Account ID must be exactly 12 digits")).not.toBeInTheDocument();
      });
    });
  });

  describe("Auto-generated configuration", () => {
    it("displays auto-generated role ARN and external ID after validation starts", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("Account ID"), {
        target: { value: "444455556666" },
      });

      // Role ARN and External ID should be auto-filled
      await waitFor(() => {
        expect(screen.getByLabelText("Role ARN")).toHaveValue("arn:aws:iam::444455556666:role/DRSOrchestrationRole");
        expect(screen.getByLabelText("External ID")).toHaveValue("drs-orchestration-cross-account");
      });
    });
  });

  describe("Validation flow - Success", () => {
    it("displays validation results after successful validation", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("Account ID"), {
        target: { value: "444455556666" },
      });

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText("Validation Results")).toBeInTheDocument();
      });

      expect(screen.getByText("Role Accessible")).toBeInTheDocument();
      expect(screen.getByText("DRS Initialized")).toBeInTheDocument();
    });

    it("displays success alert after successful validation", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("Account ID"), {
        target: { value: "444455556666" },
      });

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText("Validation Successful")).toBeInTheDocument();
      });
    });
  });

  describe("Add button state", () => {
    it("disables Add button initially", () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      const addButton = screen.getByRole("button", { name: /Add Account/i });
      expect(addButton).toBeDisabled();
    });

    it("enables Add button after successful validation", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("Account ID"), {
        target: { value: "444455556666" },
      });

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText("Validation Successful")).toBeInTheDocument();
      });

      const addButton = screen.getByText("Add Account");
      expect(addButton).not.toBeDisabled();
    });
  });

  describe("Add staging account flow", () => {
    it("calls onAdd callback with staging account data", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("Account ID"), {
        target: { value: "444455556666" },
      });

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText("Validation Successful")).toBeInTheDocument();
      });

      const addButton = screen.getByText("Add Account");
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockOnAdd).toHaveBeenCalledTimes(1);
      });

      const stagingAccount: StagingAccount = mockOnAdd.mock.calls[0][0];
      expect(stagingAccount.accountId).toBe("444455556666");
      expect(stagingAccount.roleArn).toBe("arn:aws:iam::444455556666:role/DRSOrchestrationRole");
      expect(stagingAccount.externalId).toBe("drs-orchestration-cross-account");
    });

    it("calls onDismiss after successful add", async () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("Account ID"), {
        target: { value: "444455556666" },
      });

      const validateButton = screen.getByText("Validate Access");
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText("Validation Successful")).toBeInTheDocument();
      });

      const addButton = screen.getByText("Add Account");
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockOnDismiss).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("Cancel button", () => {
    it("calls onDismiss when Cancel button is clicked", () => {
      render(<AddStagingAccountModal {...defaultProps} />);

      const cancelButton = screen.getByText("Cancel");
      fireEvent.click(cancelButton);

      expect(mockOnDismiss).toHaveBeenCalledTimes(1);
    });
  });
});
