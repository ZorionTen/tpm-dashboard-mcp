import { useCallback, useEffect, useMemo, useState } from 'react'
import { Box, CssBaseline, ThemeProvider, Typography } from '@mui/material'
import { darkTheme, lightTheme } from './theme'
import DashboardPage from './components/DashboardPage'
import PdfPage from './components/PdfPage'
import AddBlockerDialog from './components/AddBlockerDialog'
import { deriveStats, nextKey } from './utils'

const route = () => (window.location.hash === '#/pdf' ? 'pdf' : 'dash')

export default function App() {
  const [data, setData] = useState(null)
  const [mode, setMode] = useState('dark')
  const [currentRoute, setCurrentRoute] = useState(route)
  const [toast, setToast] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const [blockers, setBlockers] = useState([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [printPending, setPrintPending] = useState(false)

  const showToast = useCallback((msg) => {
    setToast({ msg, id: Date.now() })
    setTimeout(() => setToast((t) => (t && Date.now() - t.id >= 2400 ? null : t)), 2600)
  }, [])

  const loadData = useCallback(async () => {
    try {
      const r = await fetch('/data.json', { cache: 'no-store' })
      const j = await r.json()
      setData(j)
      return j
    } catch {
      setData({ error: 'Dashboard server unreachable — is the app running? (./start.sh)' })
      return null
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])
  useEffect(() => {
    const h = () => setCurrentRoute(route())
    window.addEventListener('hashchange', h)
    return () => window.removeEventListener('hashchange', h)
  }, [])

  const issues = useMemo(() => [...(data?.issues || []), ...blockers], [data, blockers])
  const stats = useMemo(() => deriveStats(issues), [issues])

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadData()
    setRefreshing(false)
    showToast('Sprint metrics synced with Jira')
  }

  const handleToggleTheme = () => {
    const next = mode === 'dark' ? 'light' : 'dark'
    setMode(next)
    showToast(`Switched to ${next} theme`)
  }

  const handleExportPdf = () => {
    showToast('Opening print dialog...')
    setPrintPending(true)
    window.location.hash = '#/pdf'
  }

  const handleAddBlocker = ({ summary, story_points }) => {
    setBlockers((b) => [...b, { key: nextKey([...issues]), summary, status: 'Blocked', story_points }])
    setDialogOpen(false)
    showToast('Blocker logged (session only)')
  }

  const theme = mode === 'dark' ? darkTheme : lightTheme

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {currentRoute === 'pdf' ? (
        <PdfPage
          data={data}
          stats={stats}
          issues={issues}
          printPending={printPending}
          onPrinted={() => setPrintPending(false)}
        />
      ) : !data ? (
        <Box sx={{ textAlign: 'center', py: 10 }}>
          <Typography sx={{ color: 'text.secondary' }}>Loading dashboard data…</Typography>
        </Box>
      ) : (
        <DashboardPage
          data={data}
          stats={stats}
          issues={issues}
          mode={mode}
          onToggleTheme={handleToggleTheme}
          onRefresh={handleRefresh}
          refreshing={refreshing}
          onExportPdf={handleExportPdf}
          onAddBlocker={() => setDialogOpen(true)}
        />
      )}

      <AddBlockerDialog open={dialogOpen} onClose={() => setDialogOpen(false)} onSubmit={handleAddBlocker} />

      {/* Toast (bottom-right pill from the design) */}
      <Box
        key={toast?.id}
        className="no-print"
        sx={{
          position: 'fixed', bottom: 20, right: 20, zIndex: 1100,
          display: 'flex', alignItems: 'center', gap: 1.25,
          px: 2, py: 1.25, borderRadius: 3,
          bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider',
          boxShadow: 8,
          fontSize: 12.5, fontWeight: 600,
          opacity: toast ? 1 : 0,
          transform: toast ? 'translateY(0)' : 'translateY(80px)',
          transition: 'all 250ms ease',
          pointerEvents: 'none',
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 16, color: '#3fb950' }}>check_circle</span>
        {toast?.msg || ''}
      </Box>
    </ThemeProvider>
  )
}
