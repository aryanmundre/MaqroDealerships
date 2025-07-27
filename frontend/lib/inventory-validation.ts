import { type InventoryRow } from './inventory-api';

export type ValidationError = {
  row: number;
  error: string;
};

export type ValidationResult = {
  isValid: boolean;
  errors: ValidationError[];
  validRows: InventoryRow[];
};

export const inventoryValidation = {
  /**
   * Validate inventory rows and return validation result
   */
  validateInventoryRows(rows: InventoryRow[]): ValidationResult {
    const errors: ValidationError[] = [];
    const validRows: InventoryRow[] = [];

    rows.forEach((row, index) => {
      const rowNumber = index + 1; // 1-based row numbers for user display
      const rowErrors = this.validateRow(row, rowNumber);
      
      if (rowErrors.length > 0) {
        errors.push(...rowErrors);
      } else {
        validRows.push(row);
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      validRows
    };
  },

  /**
   * Validate a single inventory row
   */
  validateRow(row: InventoryRow, rowNumber: number): ValidationError[] {
    const errors: ValidationError[] = [];

    // Validate make
    if (!row.make || !row.make.trim()) {
      errors.push({ row: rowNumber, error: 'Missing make' });
    }

    // Validate model
    if (!row.model || !row.model.trim()) {
      errors.push({ row: rowNumber, error: 'Missing model' });
    }

    // Validate year
    if (!row.year || isNaN(row.year) || !this.isValidYear(row.year)) {
      errors.push({ row: rowNumber, error: 'Invalid year' });
    }

    // Validate price
    if (!row.price || isNaN(row.price) || row.price <= 0) {
      errors.push({ row: rowNumber, error: 'Invalid price' });
    }

    return errors;
  },

  /**
   * Check if year is within valid range
   */
  isValidYear(year: number): boolean {
    const currentYear = new Date().getFullYear();
    return year >= 1900 && year <= currentYear + 1;
  },

  /**
   * Get validation error message for display
   */
  getErrorMessage(error: ValidationError): string {
    return `Row ${error.row}: ${error.error}`;
  }
}; 