import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Input, Button, Empty, Spin, Typography, Space } from 'antd'
import ReactECharts from 'echarts-for-react'
import axios from 'axios'

const { TextArea } = Input
const { Title, Text } = Typography

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Analysis() {
  const { id } = useParams<{ id: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [chartOption, setChartOption] = useState<any>(null)

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = input
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `/api/v1/conversations`,
        { dataset_id: id },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      const conversationId = response.data.id

      const chatResponse = await axios.post(
        `/api/v1/conversations/${conversationId}/chat`,
        { message: userMessage, code_execution: true },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      const assistantContent = chatResponse.data.message.content
      setMessages(prev => [...prev, { role: 'assistant', content: assistantContent }])

      // TODO: Parse chart data from response
      // For now, show a placeholder chart
      setChartOption({
        title: { text: 'Sample Analysis' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'] },
        yAxis: { type: 'value' },
        series: [{ data: [120, 200, 150, 80, 70], type: 'bar' }],
      })
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 120px)', gap: 16 }}>
      {/* Chat Panel */}
      <Card style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Title level={4}>AI Assistant</Title>
        <div style={{ flex: 1, overflow: 'auto', margin: '16px 0' }}>
          {messages.length === 0 ? (
            <Empty description="Start a conversation about your data" />
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                style={{
                  marginBottom: 16,
                  padding: 12,
                  background: msg.role === 'user' ? '#e6f7ff' : '#f6ffed',
                  borderRadius: 8,
                }}
              >
                <Text strong>{msg.role === 'user' ? 'You' : 'AI'}:</Text>
                <pre style={{ margin: '8px 0 0', whiteSpace: 'pre-wrap' }}>
                  {msg.content}
                </pre>
              </div>
            ))
          )}
          {loading && <Spin tip="AI is thinking..." />}
        </div>
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
          />
          <Button type="primary" onClick={handleSend} loading={loading}>
            Send
          </Button>
        </Space.Compact>
      </Card>

      {/* Visualization Panel */}
      <Card style={{ flex: 1 }}>
        <Title level={4}>Visualization</Title>
        {chartOption ? (
          <ReactECharts option={chartOption} style={{ height: 400 }} />
        ) : (
          <Empty description="Generate a chart through conversation" />
        )}
      </Card>
    </div>
  )
}
