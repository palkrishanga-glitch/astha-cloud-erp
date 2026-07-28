export interface Product {
  id: string;
  productCode: string;
  barcode?: string;
  sku: string;
  productName: string;
  categoryId: number;
  brandId: number;
  unitId: number;
  hsnCode: string;
  gstRate: number; // e.g. 18.00
  purchasePrice: number;
  sellingPrice: number;
  wholesalePrice?: number;
  retailPrice?: number;
  minimumStock: number;
  maximumStock: number;
  openingStock: number;
  openingStockValue: number;
  warehouseId: number;
  status: 'ACTIVE' | 'INACTIVE';
  createdAt: string;
  updatedAt: string;
}

export interface InventoryBatch {
  id: string;
  productId: string;
  warehouseId: number;
  batchNumber: string;
  expiryDate?: string;
  serialNumber?: string;
  quantity: number;
  purchaseRate: number;
  sellingRate: number;
}
