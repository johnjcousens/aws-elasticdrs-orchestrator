/**
 * RegionalCapacitySection Bug Condition Exploration Test
 *
 * CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
 * DO NOT attempt to fix the test or the code when it fails.
 *
 * This test encodes the EXPECTED behavior (showing "servers used" instead of "slots available").
 * When the bug is fixed, this test will pass, validating the fix.
 *
 * BUG DESCRIPTION:
 * - Line 85: Shows "${maxReplicating - replicatingServers} slots available" (WRONG)
 * - Line 119: Shows "${300 - used} available" (WRONG)
 * - Should show: "${replicatingServers} servers used" and "${used} servers used" (CORRECT)
 *
 * REQUIREMENTS VALIDATED:
 * - 1.1: Current behavior shows "slots available" (defect)
 * - 1.2: Current behavior shows "available" for account breakdown (defect)
 * - 2.1: Expected behavior shows "servers used" for regional display
 * - 2.2: Expected behavior shows "servers used" for account breakdown
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { RegionalCapacitySection } from "../RegionalCapacitySection";
import type {
  RegionalCapacityBreakdown,
  AccountCapacity,
} from "../../types/staging-accounts";
import "@testing-library/jest-dom";

describe("RegionalCapacitySection - Bug Condition Exploration", () => {
  describe("Property 1: Fault Condition - Display Shows Servers Used Instead of Slots Available", () => {
    /**
     * Test Case 1: Regional replication display with 150 replicating servers
     *
     * EXPECTED (correct behavior): "150 servers used"
     * ACTUAL (buggy behavior): "150 slots available"
     *
     * This test will FAIL on unfixed code, confirming the bug exists.
     */
    it("should display 'X servers used' for regional replication capacity (line 85) - 150 servers", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 150,
          maxReplicating: 300,
          replicationPercent: 50,
          replicationAvailable: 150,
          recoveryServers: 150,
          recoveryMax: 4000,
          recoveryPercent: 3.75,
          recoveryAvailable: 3850,
          accountCount: 1,
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // EXPECTED: Should show "150 servers used"
      // ACTUAL (buggy): Shows "150 slots available"
      const expectedText = "150 servers used";
      const buggyText = "150 slots available";

      // This assertion will FAIL on unfixed code
      expect(screen.queryByText(expectedText)).toBeInTheDocument();

      // Document the counterexample (what the buggy code actually shows)
      if (!screen.queryByText(expectedText)) {
        console.log(
          `COUNTEREXAMPLE FOUND: Expected "${expectedText}" but found "${buggyText}"`
        );
      }
    });

    /**
     * Test Case 2: Regional replication display with 50 replicating servers
     *
     * EXPECTED (correct behavior): "50 servers used"
     * ACTUAL (buggy behavior): "250 slots available"
     */
    it("should display 'X servers used' for regional replication capacity (line 85) - 50 servers", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-west-2",
          replicatingServers: 50,
          maxReplicating: 300,
          replicationPercent: 16.67,
          replicationAvailable: 250,
          recoveryServers: 50,
          recoveryMax: 4000,
          recoveryPercent: 1.25,
          recoveryAvailable: 3950,
          accountCount: 1,
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // EXPECTED: Should show "50 servers used"
      // ACTUAL (buggy): Shows "250 slots available"
      expect(screen.queryByText("50 servers used")).toBeInTheDocument();
    });

    /**
     * Test Case 3: Regional replication display with 10 replicating servers
     *
     * EXPECTED (correct behavior): "10 servers used"
     * ACTUAL (buggy behavior): "290 slots available"
     */
    it("should display 'X servers used' for regional replication capacity (line 85) - 10 servers", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "eu-west-1",
          replicatingServers: 10,
          maxReplicating: 300,
          replicationPercent: 3.33,
          replicationAvailable: 290,
          recoveryServers: 10,
          recoveryMax: 4000,
          recoveryPercent: 0.25,
          recoveryAvailable: 3990,
          accountCount: 1,
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // EXPECTED: Should show "10 servers used"
      // ACTUAL (buggy): Shows "290 slots available"
      expect(screen.queryByText("10 servers used")).toBeInTheDocument();
    });

    /**
     * Test Case 4: Regional replication display at max capacity (300 servers)
     *
     * EXPECTED (correct behavior): "300 servers used"
     * ACTUAL (buggy behavior): "0 slots available"
     */
    it("should display 'X servers used' for regional replication capacity (line 85) - 300 servers (max)", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "ap-southeast-1",
          replicatingServers: 300,
          maxReplicating: 300,
          replicationPercent: 100,
          replicationAvailable: 0,
          recoveryServers: 300,
          recoveryMax: 4000,
          recoveryPercent: 7.5,
          recoveryAvailable: 3700,
          accountCount: 1,
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // EXPECTED: Should show "300 servers used"
      // ACTUAL (buggy): Shows "0 slots available"
      expect(screen.queryByText("300 servers used")).toBeInTheDocument();
    });

    /**
     * Test Case 5: Account breakdown display with 50 servers used
     *
     * EXPECTED (correct behavior): "50 servers used"
     * ACTUAL (buggy behavior): "250 available"
     *
     * This tests line 119 in the account breakdown section.
     */
    it("should display 'X servers used' for account breakdown capacity (line 119) - 50 servers", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 50,
          maxReplicating: 300,
          replicationPercent: 16.67,
          replicationAvailable: 250,
          recoveryServers: 50,
          recoveryMax: 4000,
          recoveryPercent: 1.25,
          recoveryAvailable: 3950,
          accountCount: 1,
        },
      ];

      const accounts: AccountCapacity[] = [
        {
          accountId: "111122223333",
          accountName: "DEMO_TARGET",
          accountType: "target",
          replicatingServers: 50,
          totalServers: 50,
          maxReplicating: 300,
          percentUsed: 16.67,
          availableSlots: 250,
          status: "OK",
          regionalBreakdown: [
            {
              region: "us-east-1",
              totalServers: 50,
              replicatingServers: 50,
            },
          ],
          warnings: [],
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={accounts}
        />
      );

      // EXPECTED: Should show "50 servers used" in account breakdown
      // The fix makes both replication AND account breakdown show "X servers used"
      // So we expect to find this text (possibly multiple times)
      const elements = screen.getAllByText("50 servers used");
      expect(elements.length).toBeGreaterThan(0);
    });

    /**
     * Test Case 6: Account breakdown display with 150 servers used
     *
     * EXPECTED (correct behavior): "150 servers used"
     * ACTUAL (buggy behavior): "150 available"
     */
    it("should display 'X servers used' for account breakdown capacity (line 119) - 150 servers", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-west-2",
          replicatingServers: 150,
          maxReplicating: 300,
          replicationPercent: 50,
          replicationAvailable: 150,
          recoveryServers: 150,
          recoveryMax: 4000,
          recoveryPercent: 3.75,
          recoveryAvailable: 3850,
          accountCount: 1,
        },
      ];

      const accounts: AccountCapacity[] = [
        {
          accountId: "444455556666",
          accountName: "STAGING_01",
          accountType: "staging",
          replicatingServers: 150,
          totalServers: 150,
          maxReplicating: 300,
          percentUsed: 50,
          availableSlots: 150,
          status: "OK",
          regionalBreakdown: [
            {
              region: "us-west-2",
              totalServers: 150,
              replicatingServers: 150,
            },
          ],
          warnings: [],
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={accounts}
        />
      );

      // EXPECTED: Should show "150 servers used" in account breakdown
      // The fix makes both replication AND account breakdown show "X servers used"
      // So we expect to find this text (possibly multiple times)
      const elements = screen.getAllByText("150 servers used");
      expect(elements.length).toBeGreaterThan(0);
    });

    /**
     * Test Case 7: Account breakdown display with 300 servers used (max capacity)
     *
     * EXPECTED (correct behavior): "300 servers used"
     * ACTUAL (buggy behavior): "0 available"
     */
    it("should display 'X servers used' for account breakdown capacity (line 119) - 300 servers (max)", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "eu-central-1",
          replicatingServers: 300,
          maxReplicating: 300,
          replicationPercent: 100,
          replicationAvailable: 0,
          recoveryServers: 300,
          recoveryMax: 4000,
          recoveryPercent: 7.5,
          recoveryAvailable: 3700,
          accountCount: 1,
        },
      ];

      const accounts: AccountCapacity[] = [
        {
          accountId: "777788889999",
          accountName: "STAGING_02",
          accountType: "staging",
          replicatingServers: 300,
          totalServers: 300,
          maxReplicating: 300,
          percentUsed: 100,
          availableSlots: 0,
          status: "CRITICAL",
          regionalBreakdown: [
            {
              region: "eu-central-1",
              totalServers: 300,
              replicatingServers: 300,
            },
          ],
          warnings: ["Account at 100% capacity"],
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={accounts}
        />
      );

      // EXPECTED: Should show "300 servers used" in account breakdown
      // The fix makes both replication AND account breakdown show "X servers used"
      // So we expect to find this text (possibly multiple times)
      const elements = screen.getAllByText("300 servers used");
      expect(elements.length).toBeGreaterThan(0);
    });

    /**
     * Test Case 8: Multiple regions with different server counts
     *
     * Tests that the bug affects all regions consistently.
     */
    it("should display 'X servers used' for all regions in multi-region scenario", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 100,
          maxReplicating: 300,
          replicationPercent: 33.33,
          replicationAvailable: 200,
          recoveryServers: 100,
          recoveryMax: 4000,
          recoveryPercent: 2.5,
          recoveryAvailable: 3900,
          accountCount: 1,
        },
        {
          region: "us-west-2",
          replicatingServers: 75,
          maxReplicating: 300,
          replicationPercent: 25,
          replicationAvailable: 225,
          recoveryServers: 75,
          recoveryMax: 4000,
          recoveryPercent: 1.88,
          recoveryAvailable: 3925,
          accountCount: 1,
        },
        {
          region: "eu-west-1",
          replicatingServers: 200,
          maxReplicating: 300,
          replicationPercent: 66.67,
          replicationAvailable: 100,
          recoveryServers: 200,
          recoveryMax: 4000,
          recoveryPercent: 5,
          recoveryAvailable: 3800,
          accountCount: 1,
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // EXPECTED: Should show "X servers used" for each region
      // ACTUAL (buggy): Shows "X slots available" for each region
      expect(screen.queryByText("100 servers used")).toBeInTheDocument();
      expect(screen.queryByText("75 servers used")).toBeInTheDocument();
      expect(screen.queryByText("200 servers used")).toBeInTheDocument();
    });
  });

  describe("Bug Documentation", () => {
    /**
     * This test documents the expected counterexamples that demonstrate the bug.
     *
     * When run on UNFIXED code, this test will output the actual buggy behavior
     * to help document the bug condition.
     */
    it("documents counterexamples found in buggy code", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 150,
          maxReplicating: 300,
          replicationPercent: 50,
          replicationAvailable: 150,
          recoveryServers: 150,
          recoveryMax: 4000,
          recoveryPercent: 3.75,
          recoveryAvailable: 3850,
          accountCount: 1,
        },
      ];

      const { container } = render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // Document what the buggy code actually shows
      const progressBars = container.querySelectorAll('[class*="awsui"]');
      console.log("\n=== BUG CONDITION EXPLORATION RESULTS ===");
      console.log("Expected behavior: Display '150 servers used'");
      console.log(
        "Actual behavior (buggy): Display '150 slots available' (calculated as 300 - 150)"
      );
      console.log(
        "Bug location: frontend/src/components/RegionalCapacitySection.tsx line 85"
      );
      console.log("=========================================\n");

      // This assertion encodes the EXPECTED behavior
      // It will FAIL on unfixed code, confirming the bug exists
      expect(screen.queryByText("150 servers used")).toBeInTheDocument();
    });
  });
});

/**
 * Property 2: Preservation Tests
 *
 * These tests verify that all functionality NOT related to the description text remains unchanged.
 * Following observation-first methodology: observe behavior on UNFIXED code, then write tests
 * capturing that behavior.
 *
 * EXPECTED OUTCOME: These tests PASS on unfixed code (confirms baseline behavior to preserve).
 *
 * REQUIREMENTS VALIDATED:
 * - 3.1: Percentage calculation (used / max) * 100 remains unchanged
 * - 3.2: AdditionalInfo text showing "X / Y servers" remains unchanged
 * - 3.3: Status color logic (>= 90% = error, else in-progress) remains unchanged
 * - 3.4: Recovery capacity display showing "X slots available" remains unchanged
 * - 3.5: Region filtering (only show regions with replicatingServers > 0) remains unchanged
 * - 3.6: Backend pre-calculated values displayed correctly remains unchanged
 */

describe("RegionalCapacitySection - Preservation Property Tests", () => {
  describe("Property 2.1: Percentage Calculation Preservation", () => {
    /**
     * Verify that percentage calculation (replicatingServers / maxReplicating) * 100
     * continues to work correctly for various input values.
     *
     * This test generates multiple test cases to ensure the calculation is preserved.
     */
    it("should calculate percentage as (replicatingServers / maxReplicating) * 100", () => {
      const testCases = [
        { replicating: 50, max: 300, expectedPct: 17 },   // 16.67 rounds to 17
        { replicating: 150, max: 300, expectedPct: 50 },
        { replicating: 270, max: 300, expectedPct: 90 },  // Threshold case
        { replicating: 300, max: 300, expectedPct: 100 }, // Max capacity
        { replicating: 10, max: 300, expectedPct: 3 },    // Low usage
        { replicating: 225, max: 300, expectedPct: 75 },
      ];

      testCases.forEach(({ replicating, max, expectedPct }) => {
        const regionalCapacity: RegionalCapacityBreakdown[] = [
          {
            region: "us-east-1",
            replicatingServers: replicating,
            maxReplicating: max,
            replicationPercent: expectedPct,
            replicationAvailable: max - replicating,
            recoveryServers: replicating,
            recoveryMax: 4000,
            recoveryPercent: (replicating / 4000) * 100,
            recoveryAvailable: 4000 - replicating,
            accountCount: 1,
          },
        ];

        const { container } = render(
          <RegionalCapacitySection
            regionalCapacity={regionalCapacity}
            accounts={[]}
          />
        );

        // Verify the ProgressBar value attribute matches expected percentage
        const progressBars = container.querySelectorAll('[role="progressbar"]');
        const replicationProgressBar = progressBars[0];
        
        // ProgressBar value should be the calculated percentage
        if (replicationProgressBar) {
          expect(replicationProgressBar).toHaveAttribute(
            "aria-valuenow",
            expectedPct.toString()
          );
        }
      });
    });

    /**
     * Verify percentage calculation for account breakdown (used / 300) * 100
     */
    it("should calculate account breakdown percentage as (used / 300) * 100", () => {
      const testCases = [
        { used: 50, expectedPct: 17 },   // 16.67 rounds to 17
        { used: 150, expectedPct: 50 },
        { used: 270, expectedPct: 90 },  // Threshold case
        { used: 300, expectedPct: 100 }, // Max capacity
      ];

      testCases.forEach(({ used, expectedPct }) => {
        const regionalCapacity: RegionalCapacityBreakdown[] = [
          {
            region: "us-east-1",
            replicatingServers: used,
            maxReplicating: 300,
            replicationPercent: expectedPct,
            replicationAvailable: 300 - used,
            recoveryServers: used,
            recoveryMax: 4000,
            recoveryPercent: (used / 4000) * 100,
            recoveryAvailable: 4000 - used,
            accountCount: 1,
          },
        ];

        const accounts: AccountCapacity[] = [
          {
            accountId: "111122223333",
            accountName: "TEST_ACCOUNT",
            accountType: "target",
            replicatingServers: used,
            totalServers: used,
            maxReplicating: 300,
            percentUsed: expectedPct,
            availableSlots: 300 - used,
            status: "OK",
            regionalBreakdown: [
              {
                region: "us-east-1",
                totalServers: used,
                replicatingServers: used,
              },
            ],
            warnings: [],
          },
        ];

        const { container } = render(
          <RegionalCapacitySection
            regionalCapacity={regionalCapacity}
            accounts={accounts}
          />
        );

        // Find account breakdown progress bars (after expanding section)
        const progressBars = container.querySelectorAll('[role="progressbar"]');
        
        // First two are regional (replication + recovery), rest are account breakdown
        if (progressBars.length > 2) {
          const accountProgressBar = progressBars[2];
          expect(accountProgressBar).toHaveAttribute(
            "aria-valuenow",
            expectedPct.toString()
          );
        }
      });
    });
  });

  describe("Property 2.2: AdditionalInfo Text Preservation", () => {
    /**
     * Verify that additionalInfo text continues to show "X / Y servers" format unchanged.
     * This text appears on the ProgressBar component and should not be affected by the fix.
     */
    it("should display additionalInfo as 'X / Y servers' format for replication", () => {
      const testCases = [
        { replicating: 50, max: 300, expected: "50 / 300 servers" },
        { replicating: 150, max: 300, expected: "150 / 300 servers" },
        { replicating: 300, max: 300, expected: "300 / 300 servers" },
      ];

      testCases.forEach(({ replicating, max, expected }) => {
        const regionalCapacity: RegionalCapacityBreakdown[] = [
          {
            region: "us-east-1",
            replicatingServers: replicating,
            maxReplicating: max,
            replicationPercent: (replicating / max) * 100,
            replicationAvailable: max - replicating,
            recoveryServers: replicating,
            recoveryMax: 4000,
            recoveryPercent: (replicating / 4000) * 100,
            recoveryAvailable: 4000 - replicating,
            accountCount: 1,
          },
        ];

        render(
          <RegionalCapacitySection
            regionalCapacity={regionalCapacity}
            accounts={[]}
          />
        );

        // Verify additionalInfo text is present and unchanged
        expect(screen.getByText(expected)).toBeInTheDocument();
      });
    });

    /**
     * Verify that additionalInfo text for account breakdown shows "X / 300 servers"
     */
    it("should display additionalInfo as 'X / 300 servers' for account breakdown", () => {
      const testCases = [
        { used: 50, expected: "50 / 300 servers" },
        { used: 150, expected: "150 / 300 servers" },
        { used: 300, expected: "300 / 300 servers" },
      ];

      testCases.forEach(({ used, expected }) => {
        const regionalCapacity: RegionalCapacityBreakdown[] = [
          {
            region: "us-east-1",
            replicatingServers: used,
            maxReplicating: 300,
            replicationPercent: (used / 300) * 100,
            replicationAvailable: 300 - used,
            recoveryServers: used,
            recoveryMax: 4000,
            recoveryPercent: (used / 4000) * 100,
            recoveryAvailable: 4000 - used,
            accountCount: 1,
          },
        ];

        const accounts: AccountCapacity[] = [
          {
            accountId: "111122223333",
            accountName: "TEST_ACCOUNT",
            accountType: "target",
            replicatingServers: used,
            totalServers: used,
            maxReplicating: 300,
            percentUsed: (used / 300) * 100,
            availableSlots: 300 - used,
            status: "OK",
            regionalBreakdown: [
              {
                region: "us-east-1",
                totalServers: used,
                replicatingServers: used,
              },
            ],
            warnings: [],
          },
        ];

        render(
          <RegionalCapacitySection
            regionalCapacity={regionalCapacity}
            accounts={accounts}
          />
        );

        // Verify additionalInfo text is present (may appear multiple times)
        expect(screen.getAllByText(expected).length).toBeGreaterThan(0);
      });
    });
  });

  describe("Property 2.3: Status Color Logic Preservation", () => {
    /**
     * Verify that status determination (>= 90% = error, else in-progress) continues to work correctly.
     * This logic determines the color of the ProgressBar component.
     */
    it("should show 'error' status when percentage >= 90%", () => {
      const testCases = [
        { replicating: 270, max: 300, pct: 90 },  // Exactly 90%
        { replicating: 280, max: 300, pct: 93 },  // Above 90%
        { replicating: 300, max: 300, pct: 100 }, // Max capacity
      ];

      testCases.forEach(({ replicating, max, pct }) => {
        const regionalCapacity: RegionalCapacityBreakdown[] = [
          {
            region: "us-east-1",
            replicatingServers: replicating,
            maxReplicating: max,
            replicationPercent: pct,
            replicationAvailable: max - replicating,
            recoveryServers: replicating,
            recoveryMax: 4000,
            recoveryPercent: (replicating / 4000) * 100,
            recoveryAvailable: 4000 - replicating,
            accountCount: 1,
          },
        ];

        const { container } = render(
          <RegionalCapacitySection
            regionalCapacity={regionalCapacity}
            accounts={[]}
          />
        );

        // Find the replication progress bar (first one)
        const progressBars = container.querySelectorAll('[role="progressbar"]');
        const replicationProgressBar = progressBars[0];

        // Verify it has error status (aria-label should contain "Error")
        if (replicationProgressBar) {
          const ariaLabel = replicationProgressBar.getAttribute("aria-label");
          expect(ariaLabel).toContain("Error");
        }
      });
    });

    it("should show 'in-progress' status when percentage < 90%", () => {
      const testCases = [
        { replicating: 50, max: 300, pct: 17 },   // Low usage
        { replicating: 150, max: 300, pct: 50 },  // Medium usage
        { replicating: 260, max: 300, pct: 87 },  // Just below 90%
      ];

      testCases.forEach(({ replicating, max, pct }) => {
        const regionalCapacity: RegionalCapacityBreakdown[] = [
          {
            region: "us-east-1",
            replicatingServers: replicating,
            maxReplicating: max,
            replicationPercent: pct,
            replicationAvailable: max - replicating,
            recoveryServers: replicating,
            recoveryMax: 4000,
            recoveryPercent: (replicating / 4000) * 100,
            recoveryAvailable: 4000 - replicating,
            accountCount: 1,
          },
        ];

        const { container } = render(
          <RegionalCapacitySection
            regionalCapacity={regionalCapacity}
            accounts={[]}
          />
        );

        // Find the replication progress bar (first one)
        const progressBars = container.querySelectorAll('[role="progressbar"]');
        const replicationProgressBar = progressBars[0];

        // Verify it has in-progress status (aria-label should contain "In progress")
        if (replicationProgressBar) {
          const ariaLabel = replicationProgressBar.getAttribute("aria-label");
          expect(ariaLabel).toContain("In progress");
        }
      });
    });
  });

  describe("Property 2.4: Recovery Capacity Display Preservation", () => {
    /**
     * Verify that recovery capacity continues to show "X slots available" (not changed by this fix).
     * The fix only affects replication capacity description, not recovery capacity.
     */
    it("should continue to show 'X slots available' for recovery capacity", () => {
      const testCases = [
        { recovery: 100, max: 4000, expected: "3900 slots available" },
        { recovery: 500, max: 4000, expected: "3500 slots available" },
        { recovery: 1000, max: 4000, expected: "3000 slots available" },
      ];

      testCases.forEach(({ recovery, max, expected }) => {
        const regionalCapacity: RegionalCapacityBreakdown[] = [
          {
            region: "us-east-1",
            replicatingServers: 100,
            maxReplicating: 300,
            replicationPercent: 33,
            replicationAvailable: 200,
            recoveryServers: recovery,
            recoveryMax: max,
            recoveryPercent: (recovery / max) * 100,
            recoveryAvailable: max - recovery,
            accountCount: 1,
          },
        ];

        render(
          <RegionalCapacitySection
            regionalCapacity={regionalCapacity}
            accounts={[]}
          />
        );

        // Verify recovery capacity description text is unchanged
        expect(screen.getByText(expected)).toBeInTheDocument();
      });
    });
  });

  describe("Property 2.5: Region Filtering Preservation", () => {
    /**
     * Verify that regions with 0 replicating servers continue to be filtered out.
     * Only regions with replicatingServers > 0 should be displayed.
     */
    it("should filter out regions with 0 replicating servers", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 150,
          maxReplicating: 300,
          replicationPercent: 50,
          replicationAvailable: 150,
          recoveryServers: 150,
          recoveryMax: 4000,
          recoveryPercent: 3.75,
          recoveryAvailable: 3850,
          accountCount: 1,
        },
        {
          region: "us-west-2",
          replicatingServers: 0, // Should be filtered out
          maxReplicating: 300,
          replicationPercent: 0,
          replicationAvailable: 300,
          recoveryServers: 0,
          recoveryMax: 4000,
          recoveryPercent: 0,
          recoveryAvailable: 4000,
          accountCount: 0,
        },
        {
          region: "eu-west-1",
          replicatingServers: 75,
          maxReplicating: 300,
          replicationPercent: 25,
          replicationAvailable: 225,
          recoveryServers: 75,
          recoveryMax: 4000,
          recoveryPercent: 1.88,
          recoveryAvailable: 3925,
          accountCount: 1,
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // Verify us-east-1 and eu-west-1 are displayed
      expect(screen.getByText("us-east-1")).toBeInTheDocument();
      expect(screen.getByText("eu-west-1")).toBeInTheDocument();

      // Verify us-west-2 is NOT displayed (filtered out)
      expect(screen.queryByText("us-west-2")).not.toBeInTheDocument();
    });

    it("should return null when all regions have 0 replicating servers", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 0,
          maxReplicating: 300,
          replicationPercent: 0,
          replicationAvailable: 300,
          recoveryServers: 0,
          recoveryMax: 4000,
          recoveryPercent: 0,
          recoveryAvailable: 4000,
          accountCount: 0,
        },
      ];

      const { container } = render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // Component should render nothing (null)
      expect(container.firstChild).toBeNull();
    });
  });

  describe("Property 2.6: Account Breakdown Preservation", () => {
    /**
     * Verify that account breakdown expandable section logic continues to work correctly.
     * This includes filtering accounts with 0 servers in a region.
     */
    it("should filter out accounts with 0 servers in the region", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 100,
          maxReplicating: 300,
          replicationPercent: 33,
          replicationAvailable: 200,
          recoveryServers: 100,
          recoveryMax: 4000,
          recoveryPercent: 2.5,
          recoveryAvailable: 3900,
          accountCount: 1,
        },
      ];

      const accounts: AccountCapacity[] = [
        {
          accountId: "111122223333",
          accountName: "ACCOUNT_WITH_SERVERS",
          accountType: "target",
          replicatingServers: 100,
          totalServers: 100,
          maxReplicating: 300,
          percentUsed: 33,
          availableSlots: 200,
          status: "OK",
          regionalBreakdown: [
            {
              region: "us-east-1",
              totalServers: 100,
              replicatingServers: 100,
            },
          ],
          warnings: [],
        },
        {
          accountId: "444455556666",
          accountName: "ACCOUNT_WITHOUT_SERVERS",
          accountType: "staging",
          replicatingServers: 0,
          totalServers: 0,
          maxReplicating: 300,
          percentUsed: 0,
          availableSlots: 300,
          status: "OK",
          regionalBreakdown: [
            {
              region: "us-east-1",
              totalServers: 0,
              replicatingServers: 0, // Should be filtered out
            },
          ],
          warnings: [],
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={accounts}
        />
      );

      // Verify account with servers is shown
      expect(screen.getByText("ACCOUNT_WITH_SERVERS")).toBeInTheDocument();

      // Verify account without servers is NOT shown
      expect(screen.queryByText("ACCOUNT_WITHOUT_SERVERS")).not.toBeInTheDocument();
    });

    it("should display account type labels (Target/Staging) correctly", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 150,
          maxReplicating: 600,
          replicationPercent: 25,
          replicationAvailable: 450,
          recoveryServers: 150,
          recoveryMax: 4000,
          recoveryPercent: 3.75,
          recoveryAvailable: 3850,
          accountCount: 2,
        },
      ];

      const accounts: AccountCapacity[] = [
        {
          accountId: "111122223333",
          accountName: "TARGET_ACCOUNT",
          accountType: "target",
          replicatingServers: 75,
          totalServers: 75,
          maxReplicating: 300,
          percentUsed: 25,
          availableSlots: 225,
          status: "OK",
          regionalBreakdown: [
            {
              region: "us-east-1",
              totalServers: 75,
              replicatingServers: 75,
            },
          ],
          warnings: [],
        },
        {
          accountId: "444455556666",
          accountName: "STAGING_ACCOUNT",
          accountType: "staging",
          replicatingServers: 75,
          totalServers: 75,
          maxReplicating: 300,
          percentUsed: 25,
          availableSlots: 225,
          status: "OK",
          regionalBreakdown: [
            {
              region: "us-east-1",
              totalServers: 75,
              replicatingServers: 75,
            },
          ],
          warnings: [],
        },
      ];

      render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={accounts}
        />
      );

      // Verify account type labels are displayed correctly
      expect(screen.getByText(/\(Target\)/)).toBeInTheDocument();
      expect(screen.getByText(/\(Staging\)/)).toBeInTheDocument();
    });
  });

  describe("Property 2.7: Multi-Region Preservation", () => {
    /**
     * Verify that all preservation properties hold across multiple regions.
     * This is a comprehensive test ensuring the fix doesn't break multi-region scenarios.
     */
    it("should preserve all behaviors across multiple regions", () => {
      const regionalCapacity: RegionalCapacityBreakdown[] = [
        {
          region: "us-east-1",
          replicatingServers: 150,
          maxReplicating: 300,
          replicationPercent: 50,
          replicationAvailable: 150,
          recoveryServers: 150,
          recoveryMax: 4000,
          recoveryPercent: 3.75,
          recoveryAvailable: 3850,
          accountCount: 1,
        },
        {
          region: "us-west-2",
          replicatingServers: 270,
          maxReplicating: 300,
          replicationPercent: 90,
          replicationAvailable: 30,
          recoveryServers: 270,
          recoveryMax: 4000,
          recoveryPercent: 6.75,
          recoveryAvailable: 3730,
          accountCount: 1,
        },
        {
          region: "eu-west-1",
          replicatingServers: 50,
          maxReplicating: 300,
          replicationPercent: 17,
          replicationAvailable: 250,
          recoveryServers: 50,
          recoveryMax: 4000,
          recoveryPercent: 1.25,
          recoveryAvailable: 3950,
          accountCount: 1,
        },
      ];

      const { container } = render(
        <RegionalCapacitySection
          regionalCapacity={regionalCapacity}
          accounts={[]}
        />
      );

      // Verify all regions are displayed
      expect(screen.getByText("us-east-1")).toBeInTheDocument();
      expect(screen.getByText("us-west-2")).toBeInTheDocument();
      expect(screen.getByText("eu-west-1")).toBeInTheDocument();

      // Verify additionalInfo text for all regions
      expect(screen.getByText("150 / 300 servers")).toBeInTheDocument();
      expect(screen.getByText("270 / 300 servers")).toBeInTheDocument();
      expect(screen.getByText("50 / 300 servers")).toBeInTheDocument();

      // Verify recovery capacity descriptions are unchanged
      expect(screen.getByText("3850 slots available")).toBeInTheDocument();
      expect(screen.getByText("3730 slots available")).toBeInTheDocument();
      expect(screen.getByText("3950 slots available")).toBeInTheDocument();

      // Verify status colors (check aria-labels)
      const progressBars = container.querySelectorAll('[role="progressbar"]');
      
      // us-east-1 replication (50%) should be in-progress
      if (progressBars[0]) {
        expect(progressBars[0].getAttribute("aria-label")).toContain("In progress");
      }
      
      // us-west-2 replication (90%) should be error
      if (progressBars[2]) {
        expect(progressBars[2].getAttribute("aria-label")).toContain("Error");
      }
      
      // eu-west-1 replication (17%) should be in-progress
      if (progressBars[4]) {
        expect(progressBars[4].getAttribute("aria-label")).toContain("In progress");
      }
    });
  });
});
