import { useState, useEffect } from 'react'
import { Table, Button, Upload, message, Space, Tag } from 'antd'
import { UploadOutlined, EyeOutlined, DeleteOutlined, FileSearchOutlined } from '@ant-design/icons'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

interface Dataset {
  id: string
  name: string
  description: string | null
  file_type: string | null
  file_size: number | null
  created_at: string
  is_public: boolean
}

export default function DatasetList() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const fetchDatasets = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get('/api/v1/datasets', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setDatasets(response.data.items)
    } catch (error) {
      message.error('Failed to load datasets')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDatasets()
  }, [])

  const handleUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    const token = localStorage.getItem('token')
    try {
      await axios.post('/api/v1/datasets/upload', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      })
      message.success('Dataset uploaded successfully!')
      fetchDatasets()
    } catch (error) {
      message.error('Upload failed')
    }
    return false // Prevent default upload
  }

  const handleDelete = async (id: string) => {
    const token = localStorage.getItem('token')
    try {
      await axios.delete(`/api/v1/datasets/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      message.success('Dataset deleted')
      fetchDatasets()
    } catch (error) {
      message.error('Delete failed')
    }
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Type',
      dataIndex: 'file_type',
      key: 'type',
      render: (type: string) => <Tag>{type?.toUpperCase()}</Tag>,
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      key: 'size',
      render: (size: number) => size ? `${(size / 1024).toFixed(1)} KB` : '-',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Dataset) => (
        <Space>
          <Button
            icon={<FileSearchOutlined />}
            onClick={() => navigate(`/datasets/detail/${record.id}`)}
          >
            View
          </Button>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/datasets/${record.id}`)}
          >
            Analyze
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            Delete
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1>Datasets</h1>
        <Upload beforeUpload={handleUpload} accept=".csv,.xlsx,.xls,.json">
          <Button type="primary" icon={<UploadOutlined />}>
            Upload Dataset
          </Button>
        </Upload>
      </div>

      <Table
        dataSource={datasets}
        columns={columns}
        rowKey="id"
        loading={loading}
      />
    </div>
  )
}
