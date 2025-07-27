'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Search, Edit, Trash2, Car } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { inventoryApi } from '@/lib/inventory-api';
import { type Inventory } from '@/lib/supabase';
import { INVENTORY_STATUS, UI } from '@/lib/constants';
import { useToast } from '@/components/ui/use-toast';

export default function InventoryPage() {
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    loadInventory();
  }, []);

  const loadInventory = async () => {
    try {
      const data = await inventoryApi.getInventory();
      setInventory(data);
    } catch (error) {
      toast({
        title: "Error loading inventory",
        description: error instanceof Error ? error.message : "Failed to load inventory",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this vehicle?')) return;
    
    try {
      await inventoryApi.deleteInventory(id);
      setInventory(inventory.filter(item => item.id !== id));
      toast({
        title: "Vehicle deleted",
        description: "The vehicle has been removed from your inventory.",
      });
    } catch (error) {
      toast({
        title: "Error deleting vehicle",
        description: error instanceof Error ? error.message : "Failed to delete vehicle",
        variant: "destructive"
      });
    }
  };

  const filteredInventory = inventory.filter(item =>
    item.make.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.year.toString().includes(searchTerm)
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case INVENTORY_STATUS.ACTIVE:
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case INVENTORY_STATUS.SOLD:
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case INVENTORY_STATUS.PENDING:
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-center h-64">
          <div className={`animate-spin rounded-full border-b-2 border-blue-500 ${UI.LOADING_SPINNER_SIZE}`}></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-gray-900/50 to-gray-800/30 rounded-xl p-8 border border-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-100 mb-2">Inventory Management</h2>
            <p className="text-gray-400 text-lg">Manage your vehicle inventory for AI-powered responses</p>
          </div>
          <Button 
            onClick={() => router.push('/inventory/upload')} 
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Upload Inventory
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Car className="h-6 w-6 text-blue-500" />
              <div>
                <p className="text-sm text-gray-400">Total Vehicles</p>
                <p className="text-2xl font-bold text-gray-100">{inventory.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <div>
                <p className="text-sm text-gray-400">Active</p>
                <p className="text-2xl font-bold text-gray-100">
                  {inventory.filter(item => item.status === INVENTORY_STATUS.ACTIVE).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <div>
                <p className="text-sm text-gray-400">Sold</p>
                <p className="text-2xl font-bold text-gray-100">
                  {inventory.filter(item => item.status === INVENTORY_STATUS.SOLD).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div>
                <p className="text-sm text-gray-400">Pending</p>
                <p className="text-2xl font-bold text-gray-100">
                  {inventory.filter(item => item.status === INVENTORY_STATUS.PENDING).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Table */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-gray-100">Vehicle Inventory</CardTitle>
          <CardDescription className="text-gray-400">
            {filteredInventory.length} of {inventory.length} vehicles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Search by make, model, or year..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-gray-800 border-gray-700 text-gray-100 placeholder:text-gray-500"
              />
            </div>
          </div>

          {filteredInventory.length === 0 ? (
            <div className="text-center py-12">
              <Car className="mx-auto h-12 w-12 text-gray-500 mb-4" />
              <h4 className="text-lg font-semibold text-gray-300 mb-2">No vehicles found</h4>
              <p className="text-gray-400 mb-6">
                {searchTerm ? 'Try adjusting your search terms' : 'Upload your first inventory file to get started'}
              </p>
              {!searchTerm && (
                <Button 
                  onClick={() => router.push('/inventory/upload')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Upload Inventory
                </Button>
              )}
            </div>
          ) : (
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 bg-gray-800/50">
                    <TableHead className="text-gray-300 font-medium">Vehicle</TableHead>
                    <TableHead className="text-gray-300 font-medium">Year</TableHead>
                    <TableHead className="text-gray-300 font-medium">Price</TableHead>
                    <TableHead className="text-gray-300 font-medium">Mileage</TableHead>
                    <TableHead className="text-gray-300 font-medium">Status</TableHead>
                    <TableHead className="text-gray-300 font-medium">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredInventory.map((item, index) => (
                    <TableRow 
                      key={item.id} 
                      className="border-gray-800 hover:bg-gray-800/50 transition-all duration-200"
                      style={{ animationDelay: `${index * UI.ANIMATION_DELAY}ms` }}
                    >
                      <TableCell>
                        <div>
                          <p className="font-medium text-gray-100">{item.make} {item.model}</p>
                          {item.description && (
                            <p className="text-sm text-gray-400 truncate max-w-xs">
                              {item.description}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-gray-300">{item.year}</TableCell>
                      <TableCell className="text-gray-300">${item.price.toLocaleString()}</TableCell>
                      <TableCell className="text-gray-300">
                        {item.mileage ? item.mileage.toLocaleString() : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge className={`${getStatusColor(item.status)} border`}>
                          {item.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              // TODO: Implement edit functionality
                              toast({
                                title: "Edit feature",
                                description: "Edit functionality coming soon!",
                              });
                            }}
                            className="text-gray-400 hover:text-gray-300 hover:bg-gray-800"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(item.id)}
                            className="text-gray-400 hover:text-red-400 hover:bg-red-500/10"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 