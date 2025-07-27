import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import { type InventoryRow } from './inventory-api';

export type FileParseResult = {
  success: boolean;
  data?: InventoryRow[];
  error?: string;
};

export const fileParser = {
  /**
   * Parse CSV or Excel file and return mapped inventory data
   */
  async parseFile(file: File): Promise<FileParseResult> {
    try {
      const content = await this.readFileContent(file);
      
      if (file.name.endsWith('.csv')) {
        return this.parseCSV(content);
      } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        return this.parseExcel(content);
      } else {
        return {
          success: false,
          error: 'Unsupported file type. Please upload a CSV or Excel file.'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to parse file'
      };
    }
  },

  /**
   * Read file content as binary string
   */
  async readFileContent(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsBinaryString(file);
    });
  },

  /**
   * Parse CSV content
   */
  parseCSV(content: string): FileParseResult {
    try {
      const result = Papa.parse(content as any, {
        header: true,
        skipEmptyLines: true
      });

      if (result.errors.length > 0) {
        return {
          success: false,
          error: 'Failed to parse CSV file. Please check the file format.'
        };
      }

      const mappedData = this.mapColumns(result.data as any[]);
      return {
        success: true,
        data: mappedData
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to parse CSV file'
      };
    }
  },

  /**
   * Parse Excel content
   */
  parseExcel(content: string): FileParseResult {
    try {
      const workbook = XLSX.read(content, { type: 'binary' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      const mappedData = this.mapColumns(jsonData);
      
      return {
        success: true,
        data: mappedData
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to parse Excel file. Please check the file format.'
      };
    }
  },

  /**
   * Map raw data to InventoryRow format
   */
  mapColumns(data: any[]): InventoryRow[] {
    return data.map(row => {
      const make = this.getColumnValue(row, ['make', 'Make', 'MAKE', 'Make']);
      const model = this.getColumnValue(row, ['model', 'Model', 'MODEL', 'Model']);
      const year = this.getNumericValue(row, ['year', 'Year', 'YEAR', 'Year']);
      const price = this.getNumericValue(row, ['price', 'Price', 'PRICE', 'Price']);
      const mileage = this.getOptionalNumericValue(row, ['mileage', 'Mileage', 'MILEAGE']);
      const description = this.getColumnValue(row, ['description', 'Description', 'DESC', 'Description']);
      const features = this.getColumnValue(row, ['features', 'Features', 'FEATURES', 'Features']);

      return {
        make: make.toString(),
        model: model.toString(),
        year,
        price,
        mileage,
        description: description.toString(),
        features: features.toString()
      };
    });
  },

  /**
   * Get column value with fallback options
   */
  getColumnValue(row: any, columnNames: string[]): string {
    for (const columnName of columnNames) {
      if (row[columnName] !== undefined && row[columnName] !== null) {
        return row[columnName];
      }
    }
    return '';
  },

  /**
   * Get numeric value with fallback options
   */
  getNumericValue(row: any, columnNames: string[]): number {
    const value = this.getColumnValue(row, columnNames);
    return parseInt(value) || 0;
  },

  /**
   * Get optional numeric value with fallback options
   */
  getOptionalNumericValue(row: any, columnNames: string[]): number | undefined {
    const value = this.getColumnValue(row, columnNames);
    return value ? parseInt(value) : undefined;
  }
}; 