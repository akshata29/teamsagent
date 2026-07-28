import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from '@/components/layout/AppLayout'
import DemoPage from '@/pages/DemoPage'
import WorkflowPage from '@/pages/WorkflowPage'
import ArchitecturePage from '@/pages/ArchitecturePage'
import SettingsPage from '@/pages/SettingsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/demo" replace />} />
        <Route path="demo" element={<DemoPage />} />
        <Route path="workflow" element={<WorkflowPage />} />
        <Route path="architecture" element={<ArchitecturePage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
