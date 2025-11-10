import { Page } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * Protection Groups Page Object
 * 
 * Page object for the Protection Groups management page.
 * Provides methods for CRUD operations on protection groups.
 */
export class ProtectionGroupsPage extends BasePage {
  // Selectors
  private readonly selectors = {
    // Page elements
    createButton: 'button:has-text("Create Group"), button:has-text("Create New")',
    dataGrid: '[role="grid"], .MuiDataGrid-root',
    searchBox: 'input[placeholder*="Search"]',
    
    // Dialog elements
    dialog: '[role="dialog"]',
    dialogTitle: '[role="dialog"] h2',
    nameField: 'input[name="name"]',
    descriptionField: 'textarea[name="description"]',
    addFilterButton: 'button:has-text("Add Filter")',
    tagKeyInput: 'input[name="tagKey"]',
    tagValueInput: 'input[name="tagValue"]',
    submitButton: 'button:has-text("Create Group"), button:has-text("Save")',
    cancelButton: 'button:has-text("Cancel")',
    closeButton: '[aria-label="close"]',
    
    // Table/Grid elements
    rowByName: (name: string) => `[role="row"]:has-text("${name}")`,
    editButton: (name: string) => `[role="row"]:has-text("${name}") button[aria-label="Edit"]`,
    deleteButton: (name: string) => `[role="row"]:has-text("${name}") button[aria-label="Delete"]`,
    
    // Confirmation dialog
    confirmDialog: '[role="dialog"]:has-text("Are you sure")',
    confirmDeleteButton: '[role="dialog"] button:has-text("Delete")',
  };

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to Protection Groups page
   */
  async navigateToPage(): Promise<void> {
    await this.page.goto(`${this.baseUrl}/protection-groups`);
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to load completely
   */
  async waitForPageLoad(): Promise<void> {
    // Wait for either the data grid or empty state
    await Promise.race([
      this.page.waitForSelector(this.selectors.dataGrid, { timeout: 10000 }),
      this.page.waitForSelector('text="No protection groups"', { timeout: 10000 })
    ]);
    
    // Wait for create button
    await this.waitForElement(this.selectors.createButton);
    
    // Wait for any loading indicators to disappear
    await this.waitForLoadingComplete();
  }

  /**
   * Click the Create Group button
   * THIS IS THE KEY TEST - verifying button responsiveness
   */
  async clickCreateButton(): Promise<void> {
    console.log('Clicking Create Group button...');
    await this.page.click(this.selectors.createButton);
    
    // Wait for dialog to appear
    await this.waitForElement(this.selectors.dialog, 5000);
    console.log('Dialog opened successfully');
  }

  /**
   * Check if dialog is open
   */
  async isDialogOpen(): Promise<boolean> {
    return await this.elementExists(this.selectors.dialog);
  }

  /**
   * Get dialog title
   */
  async getDialogTitle(): Promise<string> {
    return await this.getElementText(this.selectors.dialogTitle);
  }

  /**
   * Close the dialog
   */
  async closeDialog(): Promise<void> {
    // Try close button first
    const hasCloseButton = await this.elementExists(this.selectors.closeButton);
    if (hasCloseButton) {
      await this.page.click(this.selectors.closeButton);
    } else {
      // Fallback to cancel button
      await this.page.click(this.selectors.cancelButton);
    }
    
    // Wait for dialog to disappear
    await this.waitForElementHidden(this.selectors.dialog);
  }

  /**
   * Fill protection group form
   * @param data Group form data
   */
  async fillGroupForm(data: {
    name: string;
    description: string;
    tagFilters?: Array<{ key: string; values: string[] }>;
  }): Promise<void> {
    // Fill name
    await this.fillWithRetry(this.selectors.nameField, data.name);
    
    // Fill description
    await this.fillWithRetry(this.selectors.descriptionField, data.description);
    
    // Add tag filters if provided
    if (data.tagFilters && data.tagFilters.length > 0) {
      for (const filter of data.tagFilters) {
        await this.addTagFilter(filter.key, filter.values);
      }
    }
  }

  /**
   * Add a tag filter
   */
  async addTagFilter(key: string, values: string[]): Promise<void> {
    // Click Add Filter button
    await this.page.click(this.selectors.addFilterButton);
    await this.page.waitForTimeout(500); // Wait for filter form to appear
    
    // Fill key
    await this.page.fill(this.selectors.tagKeyInput, key);
    
    // Add values
    for (const value of values) {
      await this.page.fill(this.selectors.tagValueInput, value);
      await this.page.press(this.selectors.tagValueInput, 'Enter');
      await this.page.waitForTimeout(300); // Wait for chip to appear
    }
  }

  /**
   * Submit the form
   */
  async submitForm(): Promise<void> {
    await this.page.click(this.selectors.submitButton);
    
    // Wait for toast notification
    await this.waitForToast('successfully', 8000);
    
    // Wait for dialog to close
    await this.waitForElementHidden(this.selectors.dialog, 5000);
  }

  /**
   * Create a protection group (full workflow)
   */
  async createProtectionGroup(data: {
    name: string;
    description: string;
    tagFilters?: Array<{ key: string; values: string[] }>;
  }): Promise<void> {
    await this.clickCreateButton();
    await this.fillGroupForm(data);
    await this.submitForm();
    
    // Verify group appears in list
    await this.page.waitForTimeout(1000); // Wait for refresh
    const exists = await this.verifyGroupInList(data.name);
    if (!exists) {
      throw new Error(`Protection group "${data.name}" was not found in the list after creation`);
    }
  }

  /**
   * Verify protection group exists in list
   */
  async verifyGroupInList(name: string): Promise<boolean> {
    await this.waitForPageLoad();
    return await this.elementExists(this.selectors.rowByName(name));
  }

  /**
   * Get protection group row element
   */
  async getGroupRow(name: string): Promise<string> {
    const row = await this.waitForElement(this.selectors.rowByName(name));
    const text = await row.textContent();
    return text || '';
  }

  /**
   * Click edit button for a group
   */
  async clickEditGroup(name: string): Promise<void> {
    await this.page.click(this.selectors.editButton(name));
    await this.waitForElement(this.selectors.dialog);
  }

  /**
   * Delete a protection group
   */
  async deleteGroup(name: string): Promise<void> {
    // Click delete button
    await this.page.click(this.selectors.deleteButton(name));
    
    // Wait for confirmation dialog
    await this.waitForElement(this.selectors.confirmDialog, 3000);
    
    // Confirm deletion
    await this.page.click(this.selectors.confirmDeleteButton);
    
    // Wait for toast notification
    await this.waitForToast('deleted successfully', 8000);
    
    // Wait for group to disappear from list
    await this.page.waitForTimeout(1000);
  }

  /**
   * Search for groups
   */
  async search(query: string): Promise<void> {
    const hasSearch = await this.elementExists(this.selectors.searchBox);
    if (hasSearch) {
      await this.page.fill(this.selectors.searchBox, query);
      await this.page.waitForTimeout(500); // Wait for search to filter
    }
  }

  /**
   * Get count of groups in list
   */
  async getGroupCount(): Promise<number> {
    const rows = await this.page.locator('[role="row"]').count();
    // Subtract 1 for header row
    return Math.max(0, rows - 1);
  }

  /**
   * Check if page is empty (no groups)
   */
  async isEmpty(): Promise<boolean> {
    return await this.elementExists('text="No protection groups"');
  }
}
