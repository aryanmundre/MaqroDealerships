// File upload constants
export const FILE_UPLOAD = {
  ACCEPTED_TYPES: ['.csv', '.xlsx', '.xls'],
  MAX_PREVIEW_ROWS: 10,
  SUPPORTED_COLUMNS: ['make', 'model', 'year', 'price', 'mileage', 'description', 'features']
} as const;

// Inventory status constants
export const INVENTORY_STATUS = {
  ACTIVE: 'active',
  SOLD: 'sold',
  PENDING: 'pending'
} as const;

// UI constants
export const UI = {
  ANIMATION_DELAY: 50, // ms
  LOADING_SPINNER_SIZE: 'h-8 w-8',
  TABLE_ROW_HEIGHT: 'h-96'
} as const;

// Validation constants
export const VALIDATION = {
  MIN_YEAR: 1900,
  MAX_YEAR_OFFSET: 1, // Allow current year + 1
  MIN_PRICE: 0
} as const; 