import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Spin,
  Empty,
  List,
  Avatar,
  Tooltip,
  Modal,
  Select,
  message,
  Tag,
  Descriptions,
  Tabs,
} from 'antd'
import {
  SendOutlined,
  LeftOutlined,
  BarChartOutlined,
  LineChartOutlined,
  ScatterChartOutlined,
  PieChartOutlined,
  TableOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { conversationApi, datasetApi, chartApi } from '../api/client'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography

interface Message {
  role: 'user' | 'assistant'
  content: string
  code_result?: any
}

interface Dataset {
  id: string
  name: string
  description: string | null
  file_type: string | null
  columns: any[]
  metadata: any
}

export default function Analysis() {
  const { id: datasetId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [charts, setCharts] = useState<{ id: string; type: string }[]>([])
  const [showChartModal, setShowChartModal] = useState(false)
  const [chartOption, setChartOption] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (datasetId) {
      fetchDataset()
      createNewConversation()
    }
  }, [datasetId])

  const fetchDataset = async () => {
    try {
      const response = await datasetApi.get(datasetId!)
      setDataset(response.data)
    } catch (error) {
      message.error('Failed to load dataset')
      navigate('/datasets')
    }
  }

  const createNewConversation = async () => {
    try {
      const response = await conversationApi.create({
        dataset_id: datasetId,
        title: `Analysis of ${datasetId}`,
      })
      setConversationId(response.data.id)
    } catch (error) {
      message.error('Failed to create conversation')
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!input.trim() || !conversationId) return

    const userMessage = input
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setSending(true)

    try {
      const response = await conversationApi.chat(conversationId, {
        message: userMessage,
        code_execution: true,
      })

      const assistantContent = response.data.message.content
      const codeResult = response.data.message.code_result

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: assistantContent, code_result: codeResult },
      ])

      // Extract chart info from code result
      if (codeResult?.charts) {
        const newCharts = codeResult.charts.map((c: any) => ({
          id: c.id,
          type: c.type,
        }))
        setCharts((prev) => [...prev, ...newCharts])
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to send message')
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ])
    } finally {
      setSending(false)
    }
  }

  const handleChartCommand = async (chartType: string) => {
    if (!datasetId || !dataset) return

    const prompt = `Generate a ${chartType} chart for this dataset.`
    setInput(prompt)
    handleSend()
  }

  const viewChart = (chartId: string) => {
    const chartUrl = chartApi.getUrl(chartId)
    setChartOption({
      title: { text: 'Chart' },
      graphic: {
        type: 'image',
        left: 'center',
        style: {
          image: chartUrl,
          width: 600,
        },
      },
    })
    setShowChartModal(true)
  }

  const renderMessageContent = (content: string) => {
    // Simple markdown-like rendering
    const parts = content.split(/(```[\s\S]*?```)/g)
    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3).trim()
        return (
          <pre
            key={index}
            style={{
              background: '#f5f5f5',
              padding: '12px',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '12px',
            }}
          >
            <code>{code}</code>
          </pre>
        )
      }
      return (
        <Paragraph key={index} style={{ whiteSpace: 'pre-wrap', margin: '8px 0' }}>
          {part}
        </Paragraph>
      )
    })
  }

  if (!dataset) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ height: 'calc(100vh - 120px)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
        <Button icon={<LeftOutlined />} onClick={() => navigate('/datasets')} style={{ marginRight: 16 }}>
          Back
        </Button>
        <div>
          <Title level={4} style={{ margin: 0 }}>{dataset.name}</Title>
          <Text type="secondary">
            {dataset.metadata?.row_count} rows x {dataset.columns?.length} columns
          </Text>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, height: 'calc(100% - 60px)' }}>
        {/* Dataset Info Panel */}
        <Card style={{ width: 280, overflow: 'auto' }} title="Dataset Info">
          <Descriptions size="small" column={1}>
            <Descriptions.Item label="Type">{dataset.file_type?.toUpperCase()}</Descriptions.Item>
            <Descriptions.Item label="Rows">{dataset.metadata?.row_count}</Descriptions.Item>
          </Descriptions>

          <Title level={5} style={{ marginTop: 16 }}>Columns</Title>
          <div style={{ maxHeight: 300, overflow: 'auto' }}>
            {dataset.columns?.map((col: any) => (
              <div key={col.id} style={{ marginBottom: 8 }}>
                <Tag>{col.data_type}</Tag>
                <Text>{col.name}</Text>
                {col.statistics?.null_rate > 0 && (
                  <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                    {col.statistics.null_rate.toFixed(1)}% missing
                  </Text>
                )}
              </div>
            ))}
          </div>

          <Title level={5} style={{ marginTop: 16 }}>Quick Charts</Title>
          <Space wrap>
            <Tooltip title="Bar Chart">
              <Button
                icon={<BarChartOutlined />}
                onClick={() => handleChartCommand('bar')}
              />
            </Tooltip>
            <Tooltip title="Line Chart">
              <Button
                icon={<LineChartOutlined />}
                onClick={() => handleChartCommand('line')}
              />
            </Tooltip>
            <Tooltip title="Scatter Plot">
              <Button
                icon={<ScatterChartOutlined />}
                onClick={() => handleChartCommand('scatter')}
              />
            </Tooltip>
            <Tooltip title="Histogram">
              <Button
                icon={<TableOutlined />}
                onClick={() => handleChartCommand('histogram')}
              />
            </Tooltip>
          </Space>

          {charts.length > 0 && (
            <>
              <Title level={5} style={{ marginTop: 16 }}>Generated Charts</Title>
              <List
                size="small"
                dataSource={charts}
                renderItem={(chart) => (
                  <List.Item>
                    <Button
                      type="link"
                      size="small"
                      onClick={() => viewChart(chart.id)}
                    >
                      {chart.type} #{chart.id.slice(0, 6)}
                    </Button>
                  </List.Item>
                )}
              />
            </>
          )}
        </Card>

        {/* Chat Panel */}
        <Card style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Messages */}
          <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
            {messages.length === 0 ? (
              <Empty
                description="Start asking questions about your data"
                style={{ marginTop: 80 }}
              >
                <Text type="secondary">
                  Try: "Show me the distribution of sales" or "What are the key correlations?"
                </Text>
              </Empty>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  style={{
                    marginBottom: 16,
                    padding: msg.role === 'user' ? '12px 16px' : '12px 16px',
                    background: msg.role === 'user' ? '#e6f7ff' : '#f6ffed',
                    borderRadius: 8,
                    marginLeft: msg.role === 'user' ? 40 : 0,
                    marginRight: msg.role === 'assistant' ? 40 : 0,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                    <Avatar
                      size="small"
                      style={{
                        backgroundColor: msg.role === 'user' ? '#1890ff' : '#52c41a',
                        marginRight: 8,
                      }}
                    >
                      {msg.role === 'user' ? 'U' : 'AI'}
                    </Avatar>
                    <Text strong>{msg.role === 'user' ? 'You' : 'AI Assistant'}</Text>
                  </div>
                  {renderMessageContent(msg.content)}
                </div>
              ))
            )}
            {sending && (
              <div style={{ padding: '12px 16px', background: '#f6ffed', borderRadius: 8 }}>
                <Spin size="small" /> AI is thinking...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{ marginTop: 16 }}>
            <Space.Compact style={{ width: '100%' }}>
              <TextArea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your data..."
                autoSize={{ minRows: 1, maxRows: 4 }}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                style={{ resize: 'none' }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={sending}
                style={{ height: 'auto' }}
              >
                Send
              </Button>
            </Space.Compact>
          </div>
        </Card>
      </div>

      {/* Chart Modal */}
      <Modal
        open={showChartModal}
        onCancel={() => setShowChartModal(false)}
        footer={null}
        width={800}
      >
        {chartOption && <ReactECharts option={chartOption} style={{ height: 500 }} />}
      </Modal>
    </div>
  )
}
