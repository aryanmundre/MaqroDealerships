'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { inventoryApi, type InventoryRow, type InventoryUploadResult } from '@/lib/inventory-api';
import { fileParser } from '@/lib/file-parser';
import { FILE_UPLOAD } from '@/lib/constants';
import { useToast } from '@/components/ui/use-toast';

export default function InventoryUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<InventoryRow[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<InventoryUploadResult | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const { toast } = useToast();
  const router = useRouter();

  const parseFile = useCallback(async (file: File) => {
    const result = await fileParser.parseFile(file);
    
    if (result.success && result.data) {
      setPreviewData(result.data);
    } else {
      toast({
        title: "Error parsing file",
        description: result.error || "Failed to parse file",
        variant: "destructive"
      });
    }
  }, [toast]);

  const handleFileSelect = (selectedFile: File) => {
    const isValidType = FILE_UPLOAD.ACCEPTED_TYPES.some(ext => 
      selectedFile.name.toLowerCase().endsWith(ext)
    );
    
    if (isValidType) {
      setFile(selectedFile);
      parseFile(selectedFile);
      setUploadResult(null);
    } else {
      toast({
        title: "Invalid file type",
        description: "Please select a CSV or Excel file.",
        variant: "destructive"
      });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) { // Changed from previewData.length
      toast({
        title: "No file to upload",
        description: "Please select an inventory file.",
        variant: "destructive"
      });
      return;
    }

    setIsUploading(true);
    try {
      const result = await inventoryApi.uploadInventory(file); // Pass the file object
      setUploadResult(result);
      
      if (result.successCount > 0) {
        toast({
          title: "Upload successful", 
          description: `${result.successCount} vehicles uploaded and ${result.embeddingsGenerated || 0} embeddings generated for AI search.`,
        });
      }
      
      if (result.errorCount > 0) {
        toast({
          title: "Upload completed with errors",
          description: `${result.errorCount} rows failed to upload.`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "An error occurred during upload.",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setPreviewData([]);
    setUploadResult(null);
  };

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-gray-900/50 to-gray-800/30 rounded-xl p-8 border border-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-100 mb-2">Upload Inventory</h2>
            <p className="text-gray-400 text-lg">Upload your vehicle inventory to personalize AI responses</p>
          </div>
          <Button 
            variant="outline" 
            onClick={() => router.push('/inventory')}
            className="border-gray-700 text-gray-300 hover:bg-gray-800"
          >
            Back to Inventory
          </Button>
        </div>
      </div>

      {/* File Upload Section */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-gray-100">Upload Inventory File</CardTitle>
          <CardDescription className="text-gray-400">
            Upload a CSV or Excel file with your vehicle inventory. 
            Supported columns: make, model, year, price, mileage, description, features
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragOver 
                ? 'border-blue-500 bg-blue-500/10' 
                : 'border-gray-700 hover:border-gray-600'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="mx-auto h-12 w-12 text-gray-500 mb-4" />
            <p className="text-lg font-medium text-gray-100 mb-2">
              {file ? file.name : 'Drag and drop your file here'}
            </p>
            <p className="text-sm text-gray-400 mb-4">
              or click to browse
            </p>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => {
                const selectedFile = e.target.files?.[0];
                if (selectedFile) handleFileSelect(selectedFile);
              }}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button asChild className="bg-blue-600 hover:bg-blue-700">
                <span>Choose File</span>
              </Button>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Upload Actions - Always show when file is selected */}
      {file && (
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="text-gray-100">Ready to Upload</CardTitle>
            <CardDescription className="text-gray-400">
              File selected: {file.name} 
              {previewData.length > 0 && ` (${previewData.length} vehicles detected)`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button 
                onClick={handleUpload} 
                disabled={isUploading}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
              >
                {isUploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Upload Inventory
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={resetUpload} className="border-gray-700 text-gray-300 hover:bg-gray-800">
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview Section - Optional */}
      {previewData.length > 0 && (
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-100">
              <FileText className="h-5 w-5" />
              Preview ({previewData.length} vehicles)
            </CardTitle>
            <CardDescription className="text-gray-400">
              Review your data before uploading
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800">
                    <TableHead className="text-gray-300">Make</TableHead>
                    <TableHead className="text-gray-300">Model</TableHead>
                    <TableHead className="text-gray-300">Year</TableHead>
                    <TableHead className="text-gray-300">Price</TableHead>
                    <TableHead className="text-gray-300">Mileage</TableHead>
                    <TableHead className="text-gray-300">Description</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {previewData.slice(0, FILE_UPLOAD.MAX_PREVIEW_ROWS).map((row, index) => (
                    <TableRow key={index} className="border-gray-800 hover:bg-gray-800/50">
                      <TableCell className="font-medium text-gray-100">{row.make}</TableCell>
                      <TableCell className="text-gray-300">{row.model}</TableCell>
                      <TableCell className="text-gray-300">{row.year}</TableCell>
                      <TableCell className="text-gray-300">
                        {typeof row.price === 'string' ? row.price : `$${row.price.toLocaleString()}`}
                      </TableCell>
                      <TableCell className="text-gray-300">{row.mileage ? row.mileage.toLocaleString() : '-'}</TableCell>
                      <TableCell className="max-w-xs truncate text-gray-300">
                        {row.description || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {previewData.length > FILE_UPLOAD.MAX_PREVIEW_ROWS && (
                <p className="text-sm text-gray-400 mt-2">
                  Showing first {FILE_UPLOAD.MAX_PREVIEW_ROWS} rows of {previewData.length} total
                </p>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Upload Results */}
      {uploadResult && (
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-100">
              {uploadResult.errorCount === 0 ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <AlertCircle className="h-5 w-5 text-yellow-500" />
              )}
              Upload Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-4 flex-wrap">
                <Badge variant="default" className="bg-green-500">
                  {uploadResult.successCount} vehicles uploaded
                </Badge>
                {uploadResult.embeddingsGenerated !== undefined && (
                  <Badge variant="secondary" className="bg-blue-500">
                    {uploadResult.embeddingsGenerated} AI embeddings generated
                  </Badge>
                )}
                {uploadResult.errorCount > 0 && (
                  <Badge variant="destructive">
                    {uploadResult.errorCount} rows failed
                  </Badge>
                )}
              </div>

              {uploadResult.embeddingsError && (
                <Alert className="border-yellow-500/30 bg-yellow-500/10">
                  <AlertCircle className="h-4 w-4 text-yellow-400" />
                  <AlertDescription className="text-gray-300">
                    <p className="font-medium text-gray-100">Embedding Warning:</p>
                    <p className="text-sm">{uploadResult.embeddingsError}</p>
                    <p className="text-sm mt-1">Your inventory was uploaded successfully, but AI search may not include these items immediately.</p>
                  </AlertDescription>
                </Alert>
              )}

              {uploadResult.errors.length > 0 && (
                <Alert className="border-red-500/30 bg-red-500/10">
                  <AlertCircle className="h-4 w-4 text-red-400" />
                  <AlertDescription className="text-gray-300">
                    <div className="space-y-2">
                      <p className="font-medium text-gray-100">Errors found:</p>
                      <div className="space-y-1">
                        {uploadResult.errors.map((error, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm">
                            <X className="h-3 w-3 text-red-400" />
                            Row {error.row}: {error.error}
                          </div>
                        ))}
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 