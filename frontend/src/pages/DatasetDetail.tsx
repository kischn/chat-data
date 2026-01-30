import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Table,
  Typography,
  Button,
  Tag,
  Space,
  Tabs,
  Spin,
  message,
  Row,
  Col,
  Statistic,
  Progress,
  Tooltip,
} from 'antd'
import {
  LeftOutlined,
  DownloadOutlined,
  EyeOutlined,
  ColumnWidthOutlined,
  CalculatorOutlined,
  PieChartOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { datasetApi } from '../api/client'
import type { Dataset, DatasetColumn } from '../types'

const { Title, Text } = Typography

export default function DatasetDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState('preview')

  useEffect(() => {
    if (id) {
      fetchDataset()
    }
  }, [id])

  const fetchDataset = async () => {
    try {
      const response = await datasetApi.get(id!)
      setDataset(response.data)
      // Load preview data (first 100 rows)
      setData(generateMockData(response.data.columns))
    } catch {
      message.error('Failed to load dataset')
      navigate('/datasets')
    } finally {
      setLoading(false)
    }
  }

  const generateMockData = (columns: DatasetColumn[]): any[] => {
    // Generate mock preview data
    const rows = []
    for (let i = 0; i < 20; i++) {
      const row: any = {}
      columns.forEach(col => {
        if (col.data_type === 'int64' || col.data_type === 'int32') {
          row[col.name] = Math.floor(Math.random() * 1000)
        } else if (col.data_type === 'float64') {
          row[col.name] = parseFloat((Math.random() * 100).toFixed(2))
        } else if (col.data_type === 'bool') {
          row[col.name] = Math.random() > 0.5
        } else {
          row[col.name] = `Value ${i + 1}`
        }
      })
      rows.push(row)
    }
    return rows
  }

  const getTypeIcon = (type: string | null) => {
    if (type?.includes('int') || type?.includes('float')) {
      return <CalculatorOutlined style={{ color: '#1677ff' }} />
    }
    if (type === 'object' || type === 'string') {
      return <ColumnWidthOutlined style={{ color: '#52c41a' }} />
    }
    return <PieChartOutlined style={{ color: '#722ed1' }} />
  }

  const getDistributionOption = (column: DatasetColumn) => {
    const stats = column.statistics
    return {
      title: { text: `${column.name} Distribution`, left: 'center' },
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: '60%',
        data: [
          { value: stats?.null_rate ? (1 - stats.null_rate) * 100 : 80, name: 'Valid' },
          { value: stats?.null_rate ? stats.null_rate * 100 : 20, name: 'Missing' },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      }],
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!dataset) {
    return null
  }

  const columns = dataset.columns.map(col => ({
    title: (
      <Space>
        {getTypeIcon(col.data_type)}
        {col.name}
        {col.nullable && (
          <Tooltip title="Nullable">
            <Text type="secondary" style={{ fontSize: 12 }}>*</Text>
          </Tooltip>
        )}
      </Space>
    ),
    dataIndex: col.name,
    key: col.name,
    render: (value: any) => {
      if (value === null || value === undefined) {
        return <Text type="secondary">null</Text>
      }
      if (typeof value === 'boolean') {
        return <Tag color={value ? 'green' : 'red'}>{value.toString()}</Tag>
      }
      if (typeof value === 'number') {
        return <Text>{value.toLocaleString()}</Text>
      }
      return <Text>{String(value)}</Text>
    },
  }))

  const tabItems = [
    {
      key: 'preview',
      label: <span><EyeOutlined /> Data Preview</span>,
      children: (
        <Table
          dataSource={data}
          columns={columns}
          rowKey={(_, index) => index?.toString() || '0'}
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: true }}
        />
      ),
    },
    {
      key: 'columns',
      label: 'Columns',
      children: (
        <Row gutter={[16, 16]}>
          {dataset.columns.map((col) => (
            <Col xs={24} sm={12} lg={8} key={col.id}>
              <Card size="small" title={col.name}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">Type: </Text>
                    <Tag>{col.data_type || 'unknown'}</Tag>
                  </div>
                  <div>
                    <Text type="secondary">Missing: </Text>
                    <Progress
                      percent={col.statistics?.null_rate ? col.statistics.null_rate * 100 : 0}
                      size="small"
                      status={col.statistics?.null_rate && col.statistics.null_rate > 0.1 ? 'exception' : 'normal'}
                    />
                  </div>
                  {col.statistics && (col.statistics.mean !== undefined || col.statistics.std !== undefined) && (
                    <div>
                      <Row gutter={8}>
                        {col.statistics.mean !== undefined && (
                          <Col span={12}>
                            <Statistic title="Mean" value={col.statistics.mean} precision={2} />
                          </Col>
                        )}
                        {col.statistics.std !== undefined && (
                          <Col span={12}>
                            <Statistic title="Std" value={col.statistics.std} precision={2} />
                          </Col>
                        )}
                      </Row>
                    </div>
                  )}
                  {col.sample_values && col.sample_values.length > 0 && (
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>Sample:</Text>
                      <div style={{ marginTop: 4 }}>
                        {col.sample_values.slice(0, 3).map((v, i) => (
                          <Tag key={i} style={{ marginBottom: 2 }}>{String(v)}</Tag>
                        ))}
                      </div>
                    </div>
                  )}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      ),
    },
    {
      key: 'statistics',
      label: 'Statistics',
      children: (
        <Row gutter={[16, 16]}>
          {dataset.columns.slice(0, 6).map((col) => (
            <Col xs={24} sm={12} lg={8} key={col.id}>
              <ReactECharts option={getDistributionOption(col)} style={{ height: 250 }} />
            </Col>
          ))}
        </Row>
      ),
    },
  ]

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
        <Button icon={<LeftOutlined />} onClick={() => navigate('/datasets')} style={{ marginRight: 16 }}>
          Back
        </Button>
        <div style={{ flex: 1 }}>
          <Title level={4} style={{ margin: 0 }}>{dataset.name}</Title>
          <Text type="secondary">
            {dataset.metadata?.row_count} rows x {dataset.columns.length} columns
          </Text>
        </div>
        <Space>
          <Button icon={<DownloadOutlined />}>Export</Button>
          <Button type="primary" onClick={() => navigate(`/datasets/${dataset.id}`)}>
            Open Analysis
          </Button>
        </Space>
      </div>

      {/* Info Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Rows" value={dataset.metadata?.row_count || 0} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Columns" value={dataset.columns.length} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="File Size" value={dataset.file_size ? (dataset.file_size / 1024).toFixed(1) : 0} suffix="KB" />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Missing Rate"
              value={(dataset.columns.reduce((acc, col) => acc + (col.statistics?.null_rate || 0), 0) / dataset.columns.length * 100).toFixed(1)}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      {/* Tabs */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  )
}
