import api from './client'

// ─── Fiscal Years ──────────────────────────────────────────────
export const getFiscalYears = () => api.get('/finance/fiscal-years/')
export const createFiscalYear = (data: Record<string, unknown>) => api.post('/finance/fiscal-years/', data)
export const updateFiscalYear = (id: number, data: Record<string, unknown>) => api.put(`/finance/fiscal-years/${id}/`, data)
export const deleteFiscalYear = (id: number) => api.delete(`/finance/fiscal-years/${id}/`)

// ─── Chart of Accounts ─────────────────────────────────────────
export const getAccountGroups = () => api.get('/finance/accounts/groups/')
export const createAccountGroup = (data: Record<string, unknown>) => api.post('/finance/accounts/groups/', data)
export const getKolAccounts = (groupId?: number) =>
  api.get('/finance/accounts/kol/', { params: groupId ? { group: groupId } : {} })
export const getMoinAccounts = (kolId?: number) =>
  api.get('/finance/accounts/moin/', { params: kolId ? { kol: kolId } : {} })
export const getTafziliAccounts = (entityType?: string) =>
  api.get('/finance/accounts/tafzili/', { params: entityType ? { entity_type: entityType } : {} })
export const getChartOfAccountsTree = () => api.get('/finance/accounts/tree/')

// ─── Bank Accounts ─────────────────────────────────────────────
export const getBankAccounts = () => api.get('/finance/bank-accounts/')
export const createBankAccount = (data: Record<string, unknown>) => api.post('/finance/bank-accounts/', data)
export const updateBankAccount = (id: number, data: Record<string, unknown>) => api.put(`/finance/bank-accounts/${id}/`, data)
export const deleteBankAccount = (id: number) => api.delete(`/finance/bank-accounts/${id}/`)

// ─── Customers ─────────────────────────────────────────────────
export const getCustomers = (q?: string) =>
  api.get('/finance/customers/', { params: q ? { q } : {} })
export const createCustomer = (data: Record<string, unknown>) => api.post('/finance/customers/', data)
export const updateCustomer = (id: number, data: Record<string, unknown>) => api.put(`/finance/customers/${id}/`, data)
export const deleteCustomer = (id: number) => api.delete(`/finance/customers/${id}/`)
export const getCustomerBalances = () => api.get('/finance/customers/balances/')

// ─── Suppliers ─────────────────────────────────────────────────
export const getSuppliers = (q?: string) =>
  api.get('/finance/suppliers/', { params: q ? { q } : {} })
export const createSupplier = (data: Record<string, unknown>) => api.post('/finance/suppliers/', data)
export const updateSupplier = (id: number, data: Record<string, unknown>) => api.put(`/finance/suppliers/${id}/`, data)
export const deleteSupplier = (id: number) => api.delete(`/finance/suppliers/${id}/`)
export const getSupplierBalances = () => api.get('/finance/suppliers/balances/')

// ─── Journal Vouchers ──────────────────────────────────────────
export const getVouchers = (params?: Record<string, unknown>) =>
  api.get('/finance/vouchers/', { params })
export const getVoucher = (id: number) => api.get(`/finance/vouchers/${id}/`)
export const createVoucher = (data: Record<string, unknown>) => api.post('/finance/vouchers/', data)
export const updateVoucher = (id: number, data: Record<string, unknown>) => api.put(`/finance/vouchers/${id}/`, data)
export const deleteVoucher = (id: number) => api.delete(`/finance/vouchers/${id}/`)
export const confirmVoucher = (id: number) => api.post(`/finance/vouchers/${id}/confirm/`)

// ─── Invoices ──────────────────────────────────────────────────
export const getInvoices = (params?: Record<string, unknown>) =>
  api.get('/finance/invoices/', { params })
export const getInvoice = (id: number) => api.get(`/finance/invoices/${id}/`)
export const createInvoice = (data: Record<string, unknown>) => api.post('/finance/invoices/', data)
export const updateInvoice = (id: number, data: Record<string, unknown>) => api.put(`/finance/invoices/${id}/`, data)
export const deleteInvoice = (id: number) => api.delete(`/finance/invoices/${id}/`)
export const confirmInvoice = (id: number) => api.post(`/finance/invoices/${id}/confirm/`)

// ─── Receipts ──────────────────────────────────────────────────
export const getReceipts = () => api.get('/finance/receipts/')
export const createReceipt = (data: Record<string, unknown>) => api.post('/finance/receipts/', data)
export const updateReceipt = (id: number, data: Record<string, unknown>) => api.put(`/finance/receipts/${id}/`, data)
export const deleteReceipt = (id: number) => api.delete(`/finance/receipts/${id}/`)

// ─── Payments ──────────────────────────────────────────────────
export const getPayments = () => api.get('/finance/payments/')
export const createPayment = (data: Record<string, unknown>) => api.post('/finance/payments/', data)
export const updatePayment = (id: number, data: Record<string, unknown>) => api.put(`/finance/payments/${id}/`, data)
export const deletePayment = (id: number) => api.delete(`/finance/payments/${id}/`)

// ─── Cheques ───────────────────────────────────────────────────
export const getCheques = (params?: Record<string, unknown>) =>
  api.get('/finance/cheques/', { params })
export const createCheque = (data: Record<string, unknown>) => api.post('/finance/cheques/', data)
export const updateCheque = (id: number, data: Record<string, unknown>) => api.put(`/finance/cheques/${id}/`, data)
export const deleteCheque = (id: number) => api.delete(`/finance/cheques/${id}/`)

// ─── Reports / Summary ─────────────────────────────────────────
export const getFinanceSummary = () => api.get('/finance/summary/')
