import { Box, Paper, Typography } from '@mui/material'
import KpiCard from './KpiCard'
import IssueTable from './IssueTable'
import TeamCapacityCard from './TeamCapacityCard'
import { parseRisks, splitLines, sevColor } from '../utils'

const HEALTH_COLOR = {
  'On Track': { color: '#3fb950', border: 'rgba(34,197,94,0.3)', bg: 'rgba(34,197,94,0.1)' },
  'At Risk': { color: '#f59e0b', border: 'rgba(245,158,11,0.35)', bg: 'rgba(245,158,11,0.1)' },
  'Off Track': { color: '#f85149', border: 'rgba(239,68,68,0.35)', bg: 'rgba(239,68,68,0.1)' },
}

function SectionCard({ children, sx }) {
  return <Paper variant="outlined" sx={{ p: { xs: 2, sm: 2.5 }, ...sx }}>{children}</Paper>
}

export default function DashboardPage({
  data, stats, issues, mode, onToggleTheme, onRefresh, refreshing,
  onExportPdf, onAddBlocker,
}) {
  const risks = parseRisks(data?.risks_mitigations)
  const wins = splitLines(data?.key_wins)
  const milestone = data?.milestone_status || ''
  const blockers = issues.filter((i) => i.status === 'Blocked')

  return (
    <Box sx={{ maxWidth: 1280, mx: 'auto', px: { xs: 2, sm: 3 }, py: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Header + action toolbar */}
      <Box component="header" sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 2, pb: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ width: 44, height: 44, borderRadius: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid', borderColor: 'divider', bgcolor: 'rgba(113,113,122,0.12)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 24 }}>monitoring</span>
          </Box>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
              <Typography component="h1" sx={{ fontSize: { xs: 22, sm: 28 }, fontWeight: 800, letterSpacing: '-0.02em' }}>
                Sprint Health Dashboard
              </Typography>
              <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75, px: 1.25, py: 0.25, borderRadius: 999, fontSize: 11.5, fontWeight: 700, color: '#3fb950', bgcolor: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)' }}>
                <Box component="span" sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#3fb950', animation: 'pulse 1.5s infinite' }} />
                Live
              </Box>
              {data?.health && (
                <Box
                  component="span"
                  title={data.health.reasons.join(' · ')}
                  sx={{
                    display: 'inline-flex', alignItems: 'center', gap: 0.75, px: 1.25, py: 0.25,
                    borderRadius: 999, fontSize: 11.5, fontWeight: 700,
                    color: (HEALTH_COLOR[data.health.status] || HEALTH_COLOR['On Track']).color,
                    bgcolor: (HEALTH_COLOR[data.health.status] || HEALTH_COLOR['On Track']).bg,
                    border: `1px solid ${(HEALTH_COLOR[data.health.status] || HEALTH_COLOR['On Track']).border}`,
                    cursor: 'help',
                  }}
                >
                  {data.health.status}
                </Box>
              )}
            </Box>
            <Typography sx={{ mt: 0.25, display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary', fontSize: 13 }}>
              Sprint 24 • Active Cycle
              <span style={{ opacity: 0.45 }}>•</span>
              <span className="material-symbols-outlined" style={{ fontSize: 13 }}>schedule</span>
              Generated {data?.generated_at || '—'}
            </Typography>
          </Box>
        </Box>

        <Box className="no-print" sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          {/* Static sprint label (per spec) */}
          <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75, px: 1.5, py: 1, borderRadius: 1.5, fontSize: 12, fontWeight: 600, border: '1px solid', borderColor: 'divider', color: 'text.primary', bgcolor: 'rgba(113,113,122,0.1)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 15, opacity: 0.7 }}>calendar_month</span>
            Sprint 24 (Current)
            <span className="material-symbols-outlined" style={{ fontSize: 15, opacity: 0.7 }}>expand_more</span>
          </Box>
          <Box component="button" onClick={onRefresh} disabled={refreshing} title="Sync Metrics" sx={toolBtn}>
            <span className="material-symbols-outlined" style={{ fontSize: 18, display: 'block', animation: refreshing ? 'spin 0.7s linear infinite' : 'none' }}>sync</span>
          </Box>
          <Box component="button" onClick={onToggleTheme} title="Toggle Dark/Light Mode" sx={toolBtn}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{mode === 'dark' ? 'light_mode' : 'dark_mode'}</span>
          </Box>
          <Box component="button" onClick={onExportPdf} sx={{ ...toolBtn, px: 1.75, gap: 0.75, fontWeight: 700, fontSize: 12, bgcolor: 'rgba(113,113,122,0.18)', borderColor: 'grey.700' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 15, opacity: 0.75 }}>picture_as_pdf</span>
            Export PDF
          </Box>
          <Box component="button" onClick={onAddBlocker} sx={{ ...toolBtn, px: 1.75, gap: 0.75, fontWeight: 700, fontSize: 12, bgcolor: '#f4f4f5', color: '#18181b', borderColor: '#f4f4f5', '&:hover': { bgcolor: '#e4e4e7', borderColor: '#e4e4e7' } }}>
            <span className="material-symbols-outlined" style={{ fontSize: 15, color: '#18181b' }}>add_alert</span>
            Log Risk
          </Box>
        </Box>
      </Box>

      {data?.error && (
        <Paper variant="outlined" sx={{ p: 2, borderLeft: '4px solid', borderLeftColor: 'error.main' }}>
          <Typography sx={{ color: 'error.main', fontWeight: 600, fontSize: 14 }}>⚠ {data.error}</Typography>
        </Paper>
      )}

      {/* KPI row */}
      <Box aria-label="Sprint Velocity & Issue KPIs" sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', lg: 'repeat(5, 1fr)' }, gap: { xs: 1.5, sm: 2 } }}>
        <KpiCard label="Total Points" value={stats.total_points} icon="format_list_numbered" sub="Committed backlog" />
        <KpiCard label="Done Points" value={stats.done_points} icon="task_alt" sub={`•  ${stats.remaining} pts remaining`} subColor="#3fb950" />
        <KpiCard label="Velocity" value={`${stats.velocity}%`} badge="Pace" progress={stats.velocity} />
        <KpiCard label="Issue Count" value={stats.issue_count} icon="dataset" sub="Total scoped tickets" />
        <KpiCard label="Completed Issues" value={stats.completed_count} icon="check_circle" sub={`${stats.completion_pct}% ticket resolution`} />
      </Box>

      {/* Milestone status (single line — omitted when empty) */}
      {milestone && (
        <SectionCard>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
            <Box>
              <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1, fontSize: 11.5, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'text.secondary' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 15 }}>flag</span>
                Milestone Status
              </Typography>
              <Typography sx={{ mt: 0.75, fontSize: { xs: 15, sm: 18 }, fontWeight: 600 }}>{milestone}</Typography>
            </Box>
            <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 1, px: 1.5, py: 0.75, borderRadius: 999, fontSize: 12, border: '1px solid', borderColor: 'divider', color: 'text.secondary', bgcolor: 'rgba(113,113,122,0.12)' }}>
              <Box component="span" sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'grey.400' }} />
              Target: Nov 14, 2026
            </Box>
          </Box>
        </SectionCard>
      )}

      {/* Blockers + Risks + Key Wins (omitted when empty) */}
      {(blockers.length > 0 || risks.length > 0 || wins.length > 0) && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
          {blockers.length > 0 && (
            <SectionCard sx={{ borderLeft: '4px solid', borderLeftColor: '#ef4444' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1, mb: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 17, color: '#f85149' }}>block</span>
                  <Typography sx={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#f85149' }}>
                    Blockers
                  </Typography>
                </Box>
                <Box component="span" sx={{ px: 1, py: 0.25, borderRadius: 999, fontSize: 11, fontWeight: 700, color: '#f85149', bgcolor: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
                  {blockers.length} Open
                </Box>
              </Box>
              <Box component="ul" sx={{ m: 0, pl: 2.5, display: 'flex', flexDirection: 'column', gap: 1.25 }}>
                {blockers.map((b) => (
                  <Box component="li" key={b.key} sx={{ color: 'text.secondary' }}>
                    <Typography sx={{ fontSize: 14, lineHeight: 1.55 }}>
                      <Box component="span" className="mono" sx={{ color: 'text.primary', fontWeight: 600, mr: 0.75 }}>{b.key}</Box>
                      <Box component="span" sx={{ color: 'text.primary', fontWeight: 600 }}>{b.summary}</Box>
                      <Box component="span" sx={{ ml: 0.75, fontSize: 12 }}>
                        · {b.story_points} pts{b.assignee ? ` · ${b.assignee}` : ''}
                      </Box>
                    </Typography>
                  </Box>
                ))}
              </Box>
            </SectionCard>
          )}

          {risks.length > 0 && (
            <SectionCard sx={{ borderLeft: '4px solid', borderLeftColor: '#ef4444' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1, mb: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 17, color: '#f85149' }}>warning</span>
                  <Typography sx={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#f85149' }}>
                    Risks &amp; Mitigations
                  </Typography>
                </Box>
                <Box component="span" sx={{ px: 1, py: 0.25, borderRadius: 999, fontSize: 11, fontWeight: 700, color: '#f85149', bgcolor: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
                  {risks.length} Flagged
                </Box>
              </Box>
              <Box component="ul" sx={{ m: 0, pl: 2.5, display: 'flex', flexDirection: 'column', gap: 1.75 }}>
                {risks.map((r, idx) => (
                  <Box component="li" key={idx} sx={{ color: 'text.secondary' }}>
                    <Typography sx={{ fontSize: 14, lineHeight: 1.6 }}>
                      <Box component="b" sx={{ color: 'text.primary', fontWeight: 600 }}>{r.title}</Box>
                      {r.severity && (
                        <Box component="span" sx={{ ml: 0.75, px: 0.75, py: 0.1, mx: 0.75, borderRadius: 0.75, fontSize: 10, fontWeight: 800, color: sevColor(r.severity), bgcolor: `${sevColor(r.severity)}26`, border: `1px solid ${sevColor(r.severity)}4d` }}>
                          {r.severity}
                        </Box>
                      )}
                      {r.detail ? `: ${r.detail}` : ''}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </SectionCard>
          )}

          {wins.length > 0 && (
            <SectionCard sx={{ borderLeft: '4px solid', borderLeftColor: '#22c55e' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1, mb: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 17, color: '#3fb950' }}>verified</span>
                  <Typography sx={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#3fb950' }}>
                    Key Wins
                  </Typography>
                </Box>
                <Box component="span" sx={{ px: 1, py: 0.25, borderRadius: 999, fontSize: 11, fontWeight: 700, color: '#3fb950', bgcolor: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)' }}>
                  {wins.length} Delivered
                </Box>
              </Box>
              <Box component="ul" sx={{ m: 0, pl: 2.5, display: 'flex', flexDirection: 'column', gap: 1.75 }}>
                {wins.map((w, idx) => (
                  <Box component="li" key={idx} sx={{ fontSize: 14, lineHeight: 1.6, color: 'text.secondary' }}>{w}</Box>
                ))}
              </Box>
            </SectionCard>
          )}
        </Box>
      )}

      {/* Team Capacity */}
      <TeamCapacityCard capacity={data?.team_capacity} />

      <IssueTable issues={issues} totalPoints={stats.total_points} />

      {/* Footer */}
      <Box component="footer" sx={{ pt: 2, mt: 1, borderTop: '1px solid', borderColor: 'divider', fontSize: 12, color: 'text.secondary' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 15 }}>dashboard_customize</span>
          Generated by TPM Dashboard MCP • Prototype
        </Box>
      </Box>
    </Box>
  )
}

const toolBtn = {
  display: 'inline-flex',
  alignItems: 'center',
  p: 1,
  borderRadius: 1.5,
  border: '1px solid',
  borderColor: 'divider',
  bgcolor: 'rgba(113,113,122,0.1)',
  color: 'text.primary',
  cursor: 'pointer',
  lineHeight: 1,
  '&:hover': { bgcolor: 'rgba(113,113,122,0.2)' },
  '&:disabled': { opacity: 0.6 },
}
