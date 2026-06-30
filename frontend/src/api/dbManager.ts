import api from './client'

// Database Management
export const getDatabases = () => api.get('/db-manager/databases/')
export const createDatabase = (data: Record<string, unknown>) => api.post('/db-manager/databases/', data)
export const getDatabase = (id: number) => api.get(`/db-manager/databases/${id}/`)
export const updateDatabase = (id: number, data: Record<string, unknown>) => api.put(`/db-manager/databases/${id}/`, data)
export const deleteDatabase = (id: number) => api.delete(`/db-manager/databases/${id}/`)
export const testDatabase = (id: number) => api.post(`/db-manager/databases/${id}/test/`)

// Table Operations
export const listTables = (source: string) => api.get(`/db-manager/databases/${source}/tables/`)
export const getTableSchema = (source: string, table: string) => api.get(`/db-manager/tables/${source}/${table}/schema/`)
export const getTableData = (source: string, table: string, params?: Record<string, unknown>) =>
  api.get(`/db-manager/tables/${source}/${table}/data/`, { params })
export const getTableCount = (source: string, table: string) => api.get(`/db-manager/tables/${source}/${table}/count/`)

// Cell Editing
export const updateCell = (source: string, table: string, data: Record<string, unknown>) =>
  api.patch(`/db-manager/tables/${source}/${table}/cell/`, data)
export const batchUpdateCells = (source: string, table: string, updates: Array<Record<string, unknown>>) =>
  api.patch(`/db-manager/tables/${source}/${table}/batch/`, { updates })
export const insertRow = (source: string, table: string, data: Record<string, unknown>) =>
  api.post(`/db-manager/tables/${source}/${table}/rows/`, data)
export const deleteRows = (source: string, table: string, pkColumn: string, pkValues: unknown[]) =>
  api.delete(`/db-manager/tables/${source}/${table}/rows/delete/`, { data: { pk_column: pkColumn, pk_values: pkValues } })

// Schema Editing
export const addColumn = (source: string, table: string, data: Record<string, unknown>) =>
  api.post(`/db-manager/tables/${source}/${table}/columns/`, data)
export const updateColumn = (source: string, table: string, columnName: string, data: Record<string, unknown>) =>
  api.patch(`/db-manager/tables/${source}/${table}/columns/${columnName}/`, data)
export const dropColumn = (source: string, table: string, columnName: string) =>
  api.delete(`/db-manager/tables/${source}/${table}/columns/${columnName}/drop/`)

// File Import
export const importFile = (source: string, table: string, formData: FormData) =>
  api.post(`/db-manager/tables/${source}/${table}/import/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const importToNewTable = (formData: FormData) =>
  api.post('/db-manager/import/new/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

// SQL Editor
export const executeSql = (source: string, sql: string, allowMulti = false) =>
  api.post('/db-manager/sql/', { source, sql, allow_multi: allowMulti })

// Google Sheets Sync
export const getSyncs = () => api.get('/db-manager/syncs/')
export const createSync = (data: Record<string, unknown>) => api.post('/db-manager/syncs/', data)
export const getSync = (id: number) => api.get(`/db-manager/syncs/${id}/`)
export const updateSync = (id: number, data: Record<string, unknown>) => api.put(`/db-manager/syncs/${id}/`, data)
export const deleteSync = (id: number) => api.delete(`/db-manager/syncs/${id}/`)
export const runSync = (id: number) => api.post(`/db-manager/syncs/${id}/run/`)

// Permissions
export const getPermissions = () => api.get('/db-manager/permissions/')
export const createPermission = (data: Record<string, unknown>) => api.post('/db-manager/permissions/', data)
export const deletePermission = (id: number) => api.delete(`/db-manager/permissions/${id}/`)
