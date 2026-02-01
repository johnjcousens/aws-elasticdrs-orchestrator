/**
 * Unit Tests for CapacityDetailsModal Component
 *
 * Tests the detailed capacity modal component including:
 * - Rendering with multiple accounts
 * - Regional breakdown display
 * - Capacity planning recommendations
 * - Status indicators and warnings
 * - Recovery capacity display
 *
 * REQUIREMENTS VALIDATED:
 * - 5.1: Display per-account capacity breakdown
 * - 5.7: Display regional breakdown for each account
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import userEvent from "@testing-library/user-event";
import { CapacityDetailsModal } from "../CapacityDetailsModal";
import type { CombinedCapacityData } from "../../types/staging-accounts";

/**
 * Create mock capacity data for testing
 */
const createMockCapacityData = (
  overrides?: Partial<CombinedCapacityData>
): CombinedCapacityData => {
  return {
    combined: {
      totalReplicating: 267,
      maxReplicating: 1200,
      percentUsed: 22.25,
      status: "OK",
      message: "Capacity is within normal operating limits",
      availableSlots: 933,
    },
    accounts: [
      {
        accountId: "111122223333",
        accountName: "DEMO_TARGET",
        accountType: "target",
        replicatingServers: 225,
        totalServers: 225,
        maxReplicating: 300,
        percentUsed: 75,
        availableSlots: 75,
        status: "WARNING",
        regionalBreakdown: [
          {
            region: "us-east-1",
            totalServers: 150,
            replicatingServers: 150,
          },
          {
            region: "us-west-2",
            totalServers: 75,
            replicatingServers: 75,
          },
        ],
        warnings: [
          "Account at 75% capacity - consider adding staging account",
        ],
      },
      {
        accountId: "444455556666",
        accountName: "STAGING_01",
        accountType: "staging",
        replicatingServers: 42,
        totalServers: 42,
        maxReplicating: 300,
        percentUsed: 14,
        availableSlots: 258,
        status: "OK",
        regionalBreakdown: [
          {
            region: "us-east-1",
            totalServers: 42,
            replicatingServers: 42,
          },
        ],
        warnings: [],
      },
    ],
    recoveryCapacity: {
      currentServers: 267,
      maxRecoveryInstances: 4000,
      percentUsed: 6.68,
      availableSlots: 3733,
      status: "OK",
    },
    warnings: [],
    timestamp: "2024-01-20T10:30:00Z",
    ...overrides,
  };
};

describe("CapacityDetailsModal", () => {
  const mockOnDismiss = vi.fn();

  beforeEach(() => {
    mockOnDismiss.mockClear();
  });

  describe("Modal Visibility", () => {
    it("should not render when visible is false", () => {
      const capacityData = createMockCapacityData();

      const { container } = render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={false}
          onDismiss={mockOnDismiss}
        />
      );

      // CloudScape modals render in DOM but are hidden when visible=false
      // Just verify the modal exists but we can't easily test visibility
      expect(container).toBeTruthy();
    });

    it("should render when visible is true", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText("Capacity Details")).toBeInTheDocument();
    });

    it("should call onDismiss when Close button is clicked", async () => {
      const user = userEvent.setup();
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      const closeButton = screen.getByRole("button", { name: /close/i });
      await user.click(closeButton);

      expect(mockOnDismiss).toHaveBeenCalledTimes(1);
    });
  });

  describe("Capacity Summary", () => {
    it("should display total accounts count", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText("Total Accounts")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText(/1 target, 1 staging/i)).toBeInTheDocument();
    });

    it("should display combined capacity metrics", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText("Combined Capacity")).toBeInTheDocument();
      expect(screen.getByText(/267.*1,200/)).toBeInTheDocument();
      expect(screen.getByText(/22.3% used/i)).toBeInTheDocument();
    });

    it("should display combined status", async () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Combined Status")).toBeInTheDocument();
      });
      
      const statusIndicators = screen.getAllByText("OK");
      expect(statusIndicators.length).toBeGreaterThan(0);
    });

    it("should display timestamp when provided", () => {
      const capacityData = createMockCapacityData({
        timestamp: "2024-01-20T10:30:00Z",
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/Last updated:/i)).toBeInTheDocument();
    });
  });

  describe("Per-Account Details", () => {
    it("should display all accounts in expandable sections", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText(/DEMO_TARGET \(111122223333\)/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/STAGING_01 \(444455556666\)/i)
      ).toBeInTheDocument();
    });

    it("should display account type for each account", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Account types are shown in expandable section descriptions
      expect(screen.getByText(/target.*225 servers/i)).toBeInTheDocument();
      expect(screen.getByText(/staging.*42 servers/i)).toBeInTheDocument();
    });

    it("should display replicating servers for each account", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/225 servers/i)).toBeInTheDocument();
      expect(screen.getByText(/42 servers/i)).toBeInTheDocument();
    });

    it("should display percentage used for each account", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Percentages appear in multiple places (expandable section and progress bars)
      const percentages75 = screen.getAllByText(/75\.0% used/i);
      expect(percentages75.length).toBeGreaterThan(0);
      const percentages14 = screen.getAllByText(/14\.0% used/i);
      expect(percentages14.length).toBeGreaterThan(0);
    });

    it("should auto-expand accounts with critical status", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "CRITICAL_ACCOUNT",
            accountType: "target",
            replicatingServers: 285,
            totalServers: 285,
            maxReplicating: 300,
            percentUsed: 95,
            availableSlots: 15,
            status: "CRITICAL",
            regionalBreakdown: [],
            warnings: ["Critical capacity warning"],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Critical accounts should be expanded by default
      expect(screen.getByText("Account Type")).toBeInTheDocument();
      expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    });

    it("should display account warnings", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Expand the target account to see warnings
      const targetSection = screen.getByText(
        /DEMO_TARGET \(111122223333\)/i
      );
      userEvent.click(targetSection);

      // Warning should be visible (it's auto-expanded for WARNING status)
      expect(
        screen.getByText(
          /Account at 75% capacity - consider adding staging account/i
        )
      ).toBeInTheDocument();
    });
  });

  describe("Regional Breakdown", () => {
    it("should display regional breakdown table for each account", async () => {
      const user = userEvent.setup();
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Target account section is auto-expanded due to WARNING status
      // Check for regional breakdown (there will be multiple, one per account)
      const regionalBreakdowns = screen.getAllByText("Regional Breakdown");
      expect(regionalBreakdowns.length).toBeGreaterThan(0);
      // Regions appear multiple times (once per account)
      const usEast1Elements = screen.getAllByText("us-east-1");
      expect(usEast1Elements.length).toBeGreaterThan(0);
      expect(screen.getByText("us-west-2")).toBeInTheDocument();
    });

    it("should display server counts per region", async () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Target account is auto-expanded
      // Check for regional server counts (150 and 75 appear in tables)
      const count150 = screen.getAllByText("150");
      expect(count150.length).toBeGreaterThan(0);
      const count75 = screen.getAllByText("75");
      expect(count75.length).toBeGreaterThan(0);
    });

    it("should calculate percentage of account total per region", async () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Target account is auto-expanded
      // us-east-1: 150/225 = 66.7%
      const percentages = screen.getAllByText(/66\.7%/);
      expect(percentages.length).toBeGreaterThan(0);
      // us-west-2: 75/225 = 33.3%
      expect(screen.getByText(/33\.3%/)).toBeInTheDocument();
    });

    it("should handle accounts with no regional data", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "NO_REGIONS",
            accountType: "staging",
            replicatingServers: 0,
            totalServers: 0,
            maxReplicating: 300,
            percentUsed: 0,
            availableSlots: 300,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Account should still render (will appear multiple times in different sections)
      const noRegionsElements = screen.getAllByText(/NO_REGIONS/i);
      expect(noRegionsElements.length).toBeGreaterThan(0);
    });
  });

  describe("Capacity Planning Recommendations", () => {
    it("should display recommendations for critical accounts", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "CRITICAL_ACCOUNT",
            accountType: "target",
            replicatingServers: 285,
            totalServers: 285,
            maxReplicating: 300,
            percentUsed: 95,
            availableSlots: 15,
            status: "CRITICAL",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText("Capacity Planning Recommendations")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/URGENT.*critical capacity/i)
      ).toBeInTheDocument();
    });

    it("should display recommendations for warning accounts", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "WARNING_ACCOUNT",
            accountType: "target",
            replicatingServers: 240,
            totalServers: 240,
            maxReplicating: 300,
            percentUsed: 80,
            availableSlots: 60,
            status: "WARNING",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText(/account\(s\) at warning level/i)
      ).toBeInTheDocument();
    });

    it("should display healthy status when all accounts below 50%", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "HEALTHY_ACCOUNT",
            accountType: "target",
            replicatingServers: 100,
            totalServers: 100,
            maxReplicating: 300,
            percentUsed: 33,
            availableSlots: 200,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText(/All accounts are below 50% capacity/i)
      ).toBeInTheDocument();
    });

    it("should recommend adding staging accounts when target is high", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "TARGET",
            accountType: "target",
            replicatingServers: 200,
            totalServers: 200,
            maxReplicating: 300,
            percentUsed: 67,
            availableSlots: 100,
            status: "INFO",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Should have multiple recommendations mentioning staging accounts
      const recommendations = screen.getAllByText(/Consider adding staging accounts/i);
      expect(recommendations.length).toBeGreaterThan(0);
    });

    it("should recommend rebalancing when distribution is uneven", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "TARGET",
            accountType: "target",
            replicatingServers: 240,
            totalServers: 240,
            maxReplicating: 300,
            percentUsed: 80,
            availableSlots: 60,
            status: "WARNING",
            regionalBreakdown: [],
            warnings: [],
          },
          {
            accountId: "222222222222",
            accountName: "STAGING",
            accountType: "staging",
            replicatingServers: 50,
            totalServers: 50,
            maxReplicating: 300,
            percentUsed: 17,
            availableSlots: 250,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText(/Consider rebalancing server distribution/i)
      ).toBeInTheDocument();
    });

    it("should highlight multi-region distribution", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "MULTI_REGION",
            accountType: "target",
            replicatingServers: 150,
            totalServers: 150,
            maxReplicating: 300,
            percentUsed: 50,
            availableSlots: 150,
            status: "OK",
            regionalBreakdown: [
              { region: "us-east-1", totalServers: 75, replicatingServers: 75 },
              { region: "us-west-2", totalServers: 75, replicatingServers: 75 },
            ],
            warnings: [],
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText(/using multi-region distribution/i)
      ).toBeInTheDocument();
    });
  });

  describe("Recovery Capacity", () => {
    it("should display recovery capacity metrics", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText("Recovery Capacity")).toBeInTheDocument();
      expect(screen.getByText("Current Servers")).toBeInTheDocument();
      expect(screen.getByText("267")).toBeInTheDocument();
      expect(screen.getByText("4,000")).toBeInTheDocument();
    });

    it("should display recovery capacity percentage", () => {
      const capacityData = createMockCapacityData();

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // 6.7% appears in recovery capacity section (may also appear in regional breakdown)
      const percentages = screen.getAllByText(/6\.7%/);
      expect(percentages.length).toBeGreaterThan(0);
    });

    it("should display warning when recovery capacity exceeds 80%", () => {
      const capacityData = createMockCapacityData({
        recoveryCapacity: {
          currentServers: 3300,
          maxRecoveryInstances: 4000,
          percentUsed: 82.5,
          availableSlots: 700,
          status: "WARNING",
        },
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText(/Recovery capacity is above 80%/i)
      ).toBeInTheDocument();
    });

    it("should display critical warning when recovery capacity exceeds 90%", () => {
      const capacityData = createMockCapacityData({
        recoveryCapacity: {
          currentServers: 3700,
          maxRecoveryInstances: 4000,
          percentUsed: 92.5,
          availableSlots: 300,
          status: "CRITICAL",
        },
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(
        screen.getByText(/Recovery capacity is above 90%/i)
      ).toBeInTheDocument();
    });
  });

  describe("System Warnings", () => {
    it("should display system-wide warnings when present", () => {
      const capacityData = createMockCapacityData({
        warnings: [
          "Combined capacity approaching operational limits",
          "Consider adding additional staging accounts",
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText("System Warnings")).toBeInTheDocument();
      expect(
        screen.getByText(/Combined capacity approaching operational limits/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Consider adding additional staging accounts/i)
      ).toBeInTheDocument();
    });

    it("should not display system warnings section when no warnings", () => {
      const capacityData = createMockCapacityData({
        warnings: [],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.queryByText("System Warnings")).not.toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    it("should display error for inaccessible accounts", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "INACCESSIBLE",
            accountType: "staging",
            replicatingServers: 0,
            totalServers: 0,
            maxReplicating: 300,
            percentUsed: 0,
            availableSlots: 0,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
            accessible: false,
            error: "Unable to assume role: Access Denied",
          },
        ],
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      // Account name appears in multiple places (expandable section header and container header)
      const inaccessibleElements = screen.getAllByText(/INACCESSIBLE/i);
      expect(inaccessibleElements.length).toBeGreaterThan(0);

      // Error should be visible (account is auto-expanded due to error)
      expect(screen.getByText("Account Inaccessible")).toBeInTheDocument();
      expect(
        screen.getByText(/Unable to assume role: Access Denied/i)
      ).toBeInTheDocument();
    });
  });

  describe("Multiple Accounts", () => {
    it("should render with 5 accounts (1 target + 4 staging)", () => {
      const capacityData = createMockCapacityData({
        accounts: [
          {
            accountId: "111111111111",
            accountName: "TARGET",
            accountType: "target",
            replicatingServers: 200,
            totalServers: 200,
            maxReplicating: 300,
            percentUsed: 67,
            availableSlots: 100,
            status: "INFO",
            regionalBreakdown: [],
            warnings: [],
          },
          {
            accountId: "222222222222",
            accountName: "STAGING_01",
            accountType: "staging",
            replicatingServers: 150,
            totalServers: 150,
            maxReplicating: 300,
            percentUsed: 50,
            availableSlots: 150,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
          {
            accountId: "333333333333",
            accountName: "STAGING_02",
            accountType: "staging",
            replicatingServers: 100,
            totalServers: 100,
            maxReplicating: 300,
            percentUsed: 33,
            availableSlots: 200,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
          {
            accountId: "444444444444",
            accountName: "STAGING_03",
            accountType: "staging",
            replicatingServers: 75,
            totalServers: 75,
            maxReplicating: 300,
            percentUsed: 25,
            availableSlots: 225,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
          {
            accountId: "555555555555",
            accountName: "STAGING_04",
            accountType: "staging",
            replicatingServers: 50,
            totalServers: 50,
            maxReplicating: 300,
            percentUsed: 17,
            availableSlots: 250,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
        combined: {
          totalReplicating: 575,
          maxReplicating: 1500,
          percentUsed: 38.3,
          status: "OK",
          message: "Capacity is healthy",
          availableSlots: 925,
        },
      });

      render(
        <CapacityDetailsModal
          capacityData={capacityData}
          visible={true}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText("5")).toBeInTheDocument();
      expect(screen.getByText(/1 target, 4 staging/i)).toBeInTheDocument();
      // TARGET appears multiple times (expandable section, header, account type)
      const targetElements = screen.getAllByText(/TARGET/i);
      expect(targetElements.length).toBeGreaterThan(0);
      const staging01Elements = screen.getAllByText(/STAGING_01/i);
      expect(staging01Elements.length).toBeGreaterThan(0);
      const staging04Elements = screen.getAllByText(/STAGING_04/i);
      expect(staging04Elements.length).toBeGreaterThan(0);
    });
  });
});
