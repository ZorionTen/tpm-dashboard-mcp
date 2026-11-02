import { useMemo, useState } from 'react'
import {
  Box, InputAdornment, Paper, Table, TableBody, TableCell, TableHead, TableRow,
  TextField, ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material'
import { jiraUrl, statusMeta, splitLines } from '../utils'

const FILTERS = [
  ['all', 'All'],
  ['Done', 'Done'],
  ['In Progress', 'In Progress'],
  ['Blocked', 'Blocked'],
  ['To Do', 'To Do'],
]

export default function IssueTable({ issues, totalPoints, footerNote }) {
  const [status, setStatus] = useState('all')
  const [query, setQuery] = useState('')

  const counts = useMemo(() => {
    const by = { all: issues.length }
    issues.forEach((i) => { by[i.status] = (by[i.status] || 0) + 1 })
    return by
  }, [issues])

  const rows = issues.filter((i) => {
    const okStatus = status === 'all' || i.status === status
    const q = query.toLowerCase().trim()
    const okQuery = !q || i.summary.toLowerCase().includes(q) || i.key.toLowerCase().includes(q)
    return okStatus && okQuery
  })

  return (
    <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
      <Box sx={{ p: 2, display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <ToggleButtonGroup size="small" exclusive value={status} onChange={(_e, v) => v && setStatus(v)} sx={{ gap: 1, flexWrap: 'wrap', '& .MuiToggleButton-root': { borderRadius: '999px !important', border: '1px solid', borderColor: 'divider', px: 1.5, py: 0.25, fontSize: 12, textTransform: 'none' } }}>
          {FILTERS.map(([key, label]) =>
            counts[key] ? (
              <ToggleButton key={key} value={key} sx={{ fontWeight: status === key ? 700 : 400 }}>
                {label} ({counts[key]})
              </ToggleButton>
            ) : null,
          )}
        </ToggleButtonGroup>
        <TextField
          size="small"
          placeholder="Search key or summary..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ width: { xs: '100%', md: 260 } }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <span className="material-symbols-outlined" style={{ fontSize: 16, opacity: 0.6 }}>search</span>
              </InputAdornment>
            ),
          }}
        />
      </Box>

      <Table sx={{ minWidth: 640 }}>
        <TableHead>
          <TableRow sx={{ bgcolor: 'rgba(9,9,11,0.6)' }}>
            {['Key', 'Summary', 'Status', 'Story Points', 'Action'].map((h, i) => (
              <TableCell key={h} align={i === 2 ? 'center' : i >= 3 ? 'right' : 'left'} sx={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'text.secondary', bgcolor: 'transparent' }}>
                {h}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((i) => {
            const m = statusMeta(i.status)
            return (
              <TableRow key={i.key} hover>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>
                  <Box component="a" href={jiraUrl(i.key)} target="_blank" rel="noopener noreferrer" className="mono" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75, color: 'text.primary', fontSize: 12.5, fontWeight: 600, textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 15, color: m.color }}>{m.icon}</span>
                    {i.key}
                  </Box>
                </TableCell>
                <TableCell sx={{ fontWeight: 500 }}>{i.summary}</TableCell>
                <TableCell align="center">
                  <Box component="span" sx={{ display: 'inline-flex', px: 1.25, py: 0.25, borderRadius: 999, fontSize: 12, fontWeight: 600, color: m.color, bgcolor: m.bg, border: `1px solid ${m.border}` }}>
                    {i.status}
                  </Box>
                </TableCell>
                <TableCell align="right" className="mono" sx={{ fontWeight: 700 }}>{i.story_points}</TableCell>
                <TableCell align="right">
                  <Box component="a" href={jiraUrl(i.key)} target="_blank" rel="noopener noreferrer" title="Open Jira item" sx={{ color: 'text.secondary', display: 'inline-flex', '&:hover': { color: 'text.primary' } }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 17 }}>open_in_new</span>
                  </Box>
                </TableCell>
              </TableRow>
            )
          })}
          {!rows.length && (
            <TableRow>
              <TableCell colSpan={5} align="center" sx={{ color: 'text.secondary', py: 4 }}>
                No work items match the current filter.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      <Box sx={{ px: 2.5, py: 1, bgcolor: 'rgba(9,9,11,0.55)', borderTop: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12, color: 'text.secondary' }}>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Showing <Box component="b" sx={{ color: 'text.primary' }}>{rows.length}</Box> of {issues.length} work items
        </Typography>
        <Typography variant="caption" className="mono" sx={{ color: 'text.secondary' }}>
          Total Points: <Box component="b" sx={{ color: 'text.primary' }}>{totalPoints} pts</Box>
        </Typography>
      </Box>
    </Paper>
  )
}
