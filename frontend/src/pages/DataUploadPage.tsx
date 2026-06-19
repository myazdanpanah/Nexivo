import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react'

export default function DataUploadPage() {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
      if (!name) {
        setName(acceptedFiles[0].name.replace(/\.[^/.]+$/, ''))
      }
    }
  }, [name])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
  })

  const handleUpload = async () => {
    if (!file || !name) return

    setUploading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('name', name)
      formData.append('description', description)

      // Default allowed roles based on user role
      const allowedRoles = user?.role === 'ceo'
        ? ['finance', 'sales', 'ceo']
        : [user?.role || 'ceo']
      formData.append('allowed_roles', JSON.stringify(allowedRoles))

      await api.post('/datasets/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setSuccess(true)
      setTimeout(() => navigate('/dashboards'), 2000)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'خطا در بارگذاری فایل'
      setError(message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-lg font-bold text-gray-900">بارگذاری داده</h1>
          <p className="text-sm text-gray-500">فایل اکسل یا CSV خود را آپلود کنید</p>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        {success ? (
          <div className="text-center py-16">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              فایل با موفقیت بارگذاری شد
            </h3>
            <p className="text-gray-500">در حال انتقال به داشبوردها...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition ${
                isDragActive
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
              }`}
            >
              <input {...getInputProps()} />
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileSpreadsheet className="w-10 h-10 text-green-500" />
                  <div>
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">
                    فایل را اینجا رها کنید یا کلیک کنید
                  </p>
                  <p className="text-sm text-gray-400">
                    فرمت‌های پشتیبانی شده: .xlsx, .xls, .csv
                  </p>
                </>
              )}
            </div>

            {/* Form */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  نام مجموعه داده
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  placeholder="مثال: گزارش فروش فروردین"
                  dir="rtl"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  توضیحات (اختیاری)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
                  rows={3}
                  placeholder="توضیحاتی درباره این مجموعه داده"
                  dir="rtl"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {error}
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || !name || uploading}
                className="w-full py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'در حال بارگذاری...' : 'بارگذاری و پردازش'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
