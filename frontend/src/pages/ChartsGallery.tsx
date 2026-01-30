import { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Row,
  Col,
  Button,
  Space,
  Tag,
  Empty,
  Modal,
  Spin,
  message,
  Dropdown,
} from 'antd'
import {
  DownloadOutlined,
  DeleteOutlined,
  MoreOutlined,
  ExpandOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

interface Chart {
  id: string
  type: string
  dataset_id: string
  dataset_name: string
  created_at: string
}

const { Title, Text } = Typography

// Mock data for demonstration
const mockCharts: Chart[] = [
  {
    id: 'chart-1',
    type: 'bar',
    dataset_id: 'ds-1',
    dataset_name: 'Sales Data 2024',
    created_at: new Date().toISOString(),
  },
  {
    id: 'chart-2',
    type: 'line',
    dataset_id: 'ds-1',
    dataset_name: 'Sales Data 2024',
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 'chart-3',
    type: 'scatter',
    dataset_id: 'ds-2',
    dataset_name: 'Customer Analytics',
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: 'chart-4',
    type: 'pie',
    dataset_id: 'ds-3',
    dataset_name: 'Market Share',
    created_at: new Date(Date.now() - 259200000).toISOString(),
  },
]

const chartTypeConfig: Record<string, { label: string; color: string; icon: string }> = {
  bar: { label: 'Bar Chart', color: '#1677ff', icon: '📊' },
  line: { label: 'Line Chart', color: '#52c41a', icon: '📈' },
  scatter: { label: 'Scatter Plot', color: '#722ed1', icon: '🔵' },
  histogram: { label: 'Histogram', color: '#fa8c16', icon: '📉' },
  pie: { label: 'Pie Chart', color: '#eb2f96', icon: '🥧' },
  heatmap: { label: 'Heatmap', color: '#13c2c2', icon: '🔥' },
}

export default function ChartsGallery() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [charts, setCharts] = useState<Chart[]>([])
  const [selectedChart, setSelectedChart] = useState<Chart | null>(null)
  const [previewVisible, setPreviewVisible] = useState(false)

  useEffect(() => {
    fetchCharts()
  }, [])

  const fetchCharts = async () => {
    setLoading(true)
    try {
      // Simulate API call - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 500))
      setCharts(mockCharts)
    } catch {
      message.error('Failed to load charts')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = (chartId: string) => {
    Modal.confirm({
      title: 'Delete Chart',
      content: 'Are you sure you want to delete this chart?',
      okText: 'Delete',
      okType: 'danger',
      onOk: () => {
        setCharts(charts.filter(c => c.id !== chartId))
        message.success('Chart deleted')
      },
    })
  }

  const getChartUrl = (chartId: string) => `/api/v1/charts/${chartId}`

  const getChartImage = (type: string) => {
    const configs = chartTypeConfig[type] || chartTypeConfig.bar
    return `data:image/svg+xml,${encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
        <rect fill="#fafafa" width="400" height="300" rx="8"/>
        <text x="200" y="150" text-anchor="middle" font-family="sans-serif" font-size="24" fill="${configs.color}">
          ${configs.icon} ${configs.label}
        </text>
        <text x="200" y="180" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#999">
          Click to view full size
        </text>
      </svg>
    `)}`
  }

  const getMenuItems = (chart: Chart) => ({
    items: [
      {
        key: 'view',
        icon: <ExpandOutlined />,
        label: 'View Full Size',
        onClick: () => {
          setSelectedChart(chart)
          setPreviewVisible(true)
        },
      },
      {
        key: 'copy',
        icon: <CopyOutlined />,
        label: 'Copy Image URL',
        onClick: () => {
          navigator.clipboard.writeText(getChartUrl(chart.id))
          message.success('URL copied to clipboard')
        },
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'delete',
        icon: <DeleteOutlined />,
        label: 'Delete',
        danger: true,
        onClick: () => handleDelete(chart.id),
      },
    ],
  })

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>Charts Gallery</Title>
        <Space>
          <Button onClick={() => navigate('/datasets')}>Browse Datasets</Button>
        </Space>
      </div>

      {charts.length === 0 ? (
        <Card>
          <Empty
            description="No charts generated yet"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => navigate('/datasets')}>
              Generate Your First Chart
            </Button>
          </Empty>
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {charts.map((chart) => {
            const config = chartTypeConfig[chart.type] || chartTypeConfig.bar
            return (
              <Col xs={24} sm={12} lg={8} xl={6} key={chart.id}>
                <Card
                  hoverable
                  cover={
                    <div style={{ padding: 16, background: '#fafafa', textAlign: 'center' }}>
                      <img
                        src={getChartImage(chart.type)}
                        alt={config.label}
                        style={{ width: '100%', height: 180, objectFit: 'cover', borderRadius: 4 }}
                      />
                    </div>
                  }
                  actions={[
                    <Button
                      type="text"
                      icon={<ExpandOutlined />}
                      onClick={() => {
                        setSelectedChart(chart)
                        setPreviewVisible(true)
                      }}
                    >
                      View
                    </Button>,
                    <Button
                      type="text"
                      icon={<DownloadOutlined />}
                      href={getChartUrl(chart.id)}
                      target="_blank"
                      download
                    >
                      Download
                    </Button>,
                    <Dropdown menu={getMenuItems(chart)} trigger={['click']}>
                      <Button type="text" icon={<MoreOutlined />}>More</Button>
                    </Dropdown>,
                  ]}
                >
                  <Card.Meta
                    title={
                      <Space>
                        <span>{config.icon}</span>
                        <span>{config.label}</span>
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary">{chart.dataset_name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {new Date(chart.created_at).toLocaleDateString()}
                        </Text>
                      </div>
                    }
                  />
                </Card>
              </Col>
            )
          })}
        </Row>
      )}

      {/* Preview Modal */}
      <Modal
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button
            key="copy"
            icon={<CopyOutlined />}
            onClick={() => {
              if (selectedChart) {
                navigator.clipboard.writeText(getChartUrl(selectedChart.id))
                message.success('URL copied')
              }
            }}
          >
            Copy URL
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            href={selectedChart ? getChartUrl(selectedChart.id) : '#'}
            target="_blank"
            download
          >
            Download
          </Button>,
        ]}
        width={900}
      >
        {selectedChart && (
          <div style={{ textAlign: 'center' }}>
            <img
              src={getChartImage(selectedChart.type)}
              alt={selectedChart.type}
              style={{ maxWidth: '100%', maxHeight: 500 }}
            />
            <div style={{ marginTop: 16 }}>
              <Tag color={chartTypeConfig[selectedChart.type]?.color}>{chartTypeConfig[selectedChart.type]?.label}</Tag>
              <Text type="secondary"> • {selectedChart.dataset_name}</Text>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
