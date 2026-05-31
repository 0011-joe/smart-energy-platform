import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, theme, Typography } from 'antd'
import {
  DashboardOutlined,
  CloudServerOutlined,
  ThunderboltOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = AntLayout
const { Title } = Typography

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: <Link to="/">仪表盘</Link>,
  },
  {
    key: '/devices',
    icon: <CloudServerOutlined />,
    label: <Link to="/devices">设备管理</Link>,
  },
]

export default function Layout() {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // 获取当前选中的菜单项
  const getSelectedKey = () => {
    if (location.pathname.startsWith('/devices')) {
      return '/devices'
    }
    return '/'
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          borderRight: '1px solid #f0f0f0',
        }}
      >
        <div className="flex items-center justify-center py-4">
          <ThunderboltOutlined
            style={{ fontSize: collapsed ? 28 : 32, color: '#0ea5e9' }}
          />
          {!collapsed && (
            <Title level={4} style={{ margin: '0 0 0 12px', color: '#0ea5e9' }}>
              Smart Energy
            </Title>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <AntLayout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Title level={4} style={{ margin: 0 }}>
            {location.pathname === '/' && '仪表盘'}
            {location.pathname === '/devices' && '设备管理'}
            {location.pathname.startsWith('/devices/') && '设备详情'}
          </Title>
          <SettingOutlined style={{ fontSize: 18, color: '#666' }} />
        </Header>

        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}