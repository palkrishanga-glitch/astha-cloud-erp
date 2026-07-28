/**
  * Calculate Party Outstanding Balance dynamically from ledger components.
  * Formula: Outstanding = Opening Balance + Sales Invoices + Debit Notes - Receipts - Credit Notes - Returns
  */
export function calculatePartyOutstanding(
  openingBalance: number,
  openingBalanceType: 'DEBIT' | 'CREDIT',
  totalSalesInvoices: number,
  totalDebitNotes: number,
  totalReceipts: number,
  totalCreditNotes: number,
  totalSalesReturns: number
): number {
  const initial = openingBalanceType === 'DEBIT' ? openingBalance : -openingBalance;
  return (
    initial +
    totalSalesInvoices +
    totalDebitNotes -
    totalReceipts -
    totalCreditNotes -
    totalSalesReturns
  );
}

export interface TaxCalculationResult {
  taxableAmount: number;
  cgstRate: number;
  cgstAmount: number;
  sgstRate: number;
  sgstAmount: number;
  igstRate: number;
  igstAmount: number;
  totalTax: number;
  finalAmount: number;
}

/**
 * Calculate Line-Item GST taxes according to Indian Tax Rules.
 */
export function calculateItemGST(
  qty: number,
  rate: number,
  discountAmount: number,
  gstRate: number, // e.g. 18 for 18%
  isInterstate: boolean
): TaxCalculationResult {
  const taxableAmount = Math.max(0, qty * rate - discountAmount);
  
  if (isInterstate) {
    const igstAmount = (taxableAmount * gstRate) / 100;
    return {
      taxableAmount,
      cgstRate: 0,
      cgstAmount: 0,
      sgstRate: 0,
      sgstAmount: 0,
      igstRate: gstRate,
      igstAmount,
      totalTax: igstAmount,
      finalAmount: taxableAmount + igstAmount,
    };
  } else {
    const halfRate = gstRate / 2;
    const cgstAmount = (taxableAmount * halfRate) / 100;
    const sgstAmount = (taxableAmount * halfRate) / 100;
    return {
      taxableAmount,
      cgstRate: halfRate,
      cgstAmount,
      sgstRate: halfRate,
      sgstAmount,
      igstRate: 0,
      igstAmount: 0,
      totalTax: cgstAmount + sgstAmount,
      finalAmount: taxableAmount + cgstAmount + sgstAmount,
    };
  }
}
