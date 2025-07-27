import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import { inventoryApi, type InventoryRow } from '@/lib/inventory-api';

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const supabase = createRouteHandlerClient({ cookies });
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    
    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    // Validate file type
    const allowedTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
    const allowedExtensions = ['.csv', '.xlsx', '.xls'];
    
    const isValidType = allowedTypes.includes(file.type) || 
                       allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!isValidType) {
      return NextResponse.json(
        { error: 'Invalid file type. Please upload a CSV or Excel file.' },
        { status: 400 }
      );
    }

    // Parse file content
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    let inventoryRows: InventoryRow[] = [];

    if (file.name.endsWith('.csv')) {
      // Parse CSV
      const csvContent = buffer.toString();
      const result = Papa.parse(csvContent, {
        header: true,
        skipEmptyLines: true
      });
      
      if (result.errors.length > 0) {
        return NextResponse.json(
          { error: 'Failed to parse CSV file' },
          { status: 400 }
        );
      }
      
      inventoryRows = mapColumns(result.data as any[]);
    } else {
      // Parse Excel
      try {
        const workbook = XLSX.read(buffer, { type: 'buffer' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet);
        inventoryRows = mapColumns(jsonData);
      } catch (error) {
        return NextResponse.json(
          { error: 'Failed to parse Excel file' },
          { status: 400 }
        );
      }
    }

    if (inventoryRows.length === 0) {
      return NextResponse.json(
        { error: 'No valid data found in file' },
        { status: 400 }
      );
    }

    // Upload to database
    const result = await inventoryApi.uploadInventory(inventoryRows);
    
    return NextResponse.json(result);
    
  } catch (error) {
    console.error('Inventory upload error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

function mapColumns(data: any[]): InventoryRow[] {
  return data.map(row => {
    // Try to map common column names
    const make = row.make || row.Make || row.MAKE || row['Make'] || '';
    const model = row.model || row.Model || row.MODEL || row['Model'] || '';
    const year = parseInt(row.year || row.Year || row.YEAR || row['Year'] || '0');
    const price = parseFloat(row.price || row.Price || row.PRICE || row['Price'] || '0');
    const mileage = row.mileage ? parseInt(row.mileage) : undefined;
    const description = row.description || row.Description || row.DESC || row['Description'] || '';
    const features = row.features || row.Features || row.FEATURES || row['Features'] || '';

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
} 