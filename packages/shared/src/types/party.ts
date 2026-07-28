export type PartyType = 'CUSTOMER' | 'SUPPLIER' | 'BOTH';
export type OpeningBalanceType = 'DEBIT' | 'CREDIT';
export type PartyStatus = 'ACTIVE' | 'INACTIVE';

export interface Party {
  id: string;
  partyCode: string;
  businessName: string;
  contactPerson?: string;
  partyType: PartyType;
  gstin?: string;
  pan?: string;
  mobile: string;
  email?: string;
  address: string;
  state: string;
  district?: string;
  city: string;
  pincode: string;
  creditLimit: number;
  creditDays: number;
  openingBalance: number;
  openingBalanceType: OpeningBalanceType;
  openingBalanceDate: string;
  status: PartyStatus;
  createdAt: string;
  updatedAt: string;
}

export interface PartyLedgerEntry {
  id: string;
  partyId: string;
  date: string;
  voucherNumber: string;
  voucherType: 'OPENING_BALANCE' | 'SALES_INVOICE' | 'PURCHASE_INVOICE' | 'RECEIPT' | 'PAYMENT' | 'SALES_RETURN' | 'PURCHASE_RETURN' | 'CREDIT_NOTE' | 'DEBIT_NOTE' | 'JOURNAL';
  description: string;
  debit: number;
  credit: number;
  runningBalance: number;
  createdBy: string;
  timestamp: string;
}
