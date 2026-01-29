import { Card, Row, Col, Statistic, Button } from 'antd'
import { DatasetOutlined, CloudUploadOutlined, LineChartOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Dashboard</h1>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Datasets"
              value={0}
              prefix={<DatasetOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Conversations"
              value={0}
              prefix={<LineChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Reports"
              value={0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 24 }}>
        <h2>Quick Actions</h2>
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} sm={8}>
            <Button
              type="primary"
              icon={<CloudUploadOutlined />}
              size="large"
              block
              onClick={() => navigate('/datasets')}
            >
              Upload Dataset
            </Button>
          </Col>
          <Col xs={24} sm={8}>
            <Button
              size="large"
              block
              onClick={() => navigate('/datasets')}
            >
              Browse Datasets
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  )
}
