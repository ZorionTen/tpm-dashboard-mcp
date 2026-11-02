import { Box, Paper, Typography } from '@mui/material'

// Per-person committed vs assumed capacity (8 pts/sprint) — from payload.team_capacity.
export default function TeamCapacityCard({ capacity }) {
  if (!capacity?.length) return null
  return (
    <Paper variant="outlined" sx={{ p: { xs: 2, sm: 2.5 } }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1, mb: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 17 }}>groups</span>
          <Typography sx={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'text.secondary' }}>
            Team Capacity
          </Typography>
        </Box>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          assumed {capacity[0].capacity_pts} pts / person / sprint
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {capacity.map((c) => {
          const over = c.load_pct > 100
          const fill = Math.min(c.load_pct, 100)
          return (
            <Box key={c.name} sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '140px 1fr 170px' }, gap: 1, alignItems: 'center' }}>
              <Typography sx={{ fontSize: 13.5, fontWeight: 600 }}>
                {c.name}
                <Box component="span" sx={{ ml: 0.75, color: 'text.secondary', fontWeight: 400, fontSize: 12 }}>
                  {c.issues} issue{c.issues === 1 ? '' : 's'}
                </Box>
              </Typography>
              <Box sx={{ height: 8, borderRadius: 999, bgcolor: 'rgba(113,113,122,0.25)', overflow: 'hidden' }}>
                <Box sx={{ height: '100%', width: `${fill}%`, borderRadius: 999, bgcolor: over ? '#ef4444' : '#22c55e', transition: 'width 400ms' }} />
              </Box>
              <Typography className="mono" sx={{ fontSize: 12.5, color: over ? '#f85149' : 'text.secondary', textAlign: { xs: 'left', sm: 'right' } }}>
                {c.committed_pts}/{c.capacity_pts} pts · {c.load_pct}%
                <Box component="span" sx={{ ml: 0.75, color: 'text.secondary' }}>({c.done_pts} done)</Box>
              </Typography>
            </Box>
          )
        })}
      </Box>
    </Paper>
  )
}
