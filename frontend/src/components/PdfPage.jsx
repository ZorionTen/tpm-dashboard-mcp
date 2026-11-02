import { useEffect } from 'react'
import { Box, Button, Paper, Typography } from '@mui/material'
import { parseRisks, splitLines, statusMeta } from '../utils'

const PAPER = { bg: '#ffffff', fg: '#0b1c30', muted: '#45464d', low: '#eff4ff', high: '#e5eeff', higher: '#d3e4fe', errBg: '#ffdad6', err: '#ba1a1a', ok: '#069669' }

const mono = { fontFamily: "'JetBrains Mono', 'Roboto Mono', monospace", fontSize: 12 }

function Label({ children, color = PAPER.muted }) {
  return (
    <Typography sx={{ fontSize: 10.5, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color }}>
      {children}
    </Typography>
  )
}

export default function PdfPage({ data, stats, issues, printPending, onPrinted }) {
  const risks = parseRisks(data?.risks_mitigations)
  const wins = splitLines(data?.key_wins)
  const milestone = data?.milestone_status || '—'
  const generated = data?.generated_at || '—'
  const sysDate = String(generated).slice(0, 10).replaceAll('-', '')

  // Export flow: navigate here, then open the browser print dialog.
  useEffect(() => {
    if (!printPending) return
    const t = setTimeout(() => { window.print(); onPrinted() }, 600)
    return () => clearTimeout(t)
  }, [printPending, onPrinted])

  if (!data) {
    return (
      <Box sx={{ maxWidth: 850, mx: 'auto', px: 3, py: 6, textAlign: 'center' }}>
        <Typography sx={{ mb: 2, color: 'text.secondary' }}>No dashboard data yet — generate a dashboard first.</Typography>
        <Button className="no-print" onClick={() => { window.location.hash = '#/' }} variant="outlined" sx={{ textTransform: 'none' }}>
          Back to dashboard
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ py: { xs: 2 }, '@media print': { py: 0 } }}>
      <Box
        component="article"
        sx={{
          maxWidth: 850,
          mx: 'auto',
          bgcolor: PAPER.bg,
          color: PAPER.fg,
          p: { xs: 2.5, md: 5 },
          boxShadow: '0 4px 24px rgba(0,0,0,0.35)',
          borderRadius: '2px',
          display: 'flex',
          flexDirection: 'column',
          gap: 2.5,
          '@media print': { p: 0, boxShadow: 'none', maxWidth: 'none', width: '100%', gap: 2 },
        }}
      >
        {/* Running header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1.5, borderBottom: `1px solid ${PAPER.higher}` }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Label>Engineering Delivery Assurance</Label>
            <span style={{ opacity: 0.4 }}>•</span>
            <Label color={PAPER.fg}>Confidential &amp; Internal Use</Label>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ...mono }}>
            <span style={{ color: PAPER.muted }}>SYS_ID: S24-HLTH-{sysDate}</span>
          </Box>
        </Box>

        {/* Title block */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', justifyContent: 'space-between', gap: 2, pb: 2, borderBottom: `1px solid ${PAPER.higher}` }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Label>Project Health Report</Label>
            </Box>
            <Typography component="h1" sx={{ mt: 0.75, fontSize: { xs: 24, md: 32 }, fontWeight: 700, letterSpacing: '-0.01em' }}>
              Sprint 24 Executive Status Report
            </Typography>
            <Typography sx={{ fontSize: 14, color: PAPER.muted, mt: 0.5 }}>
              Sprint Cycle 24 (Oct 21 – Nov 04, 2026) • TPM Engineering Group
            </Typography>
          </Box>
          <Box sx={{ textAlign: { xs: 'left', md: 'right' }, ...mono, color: PAPER.muted, display: 'flex', flexDirection: 'column', gap: 0.4 }}>
            <span><Label as="span">Authored:</Label> <span style={{ color: PAPER.fg }}>Technical Program Management</span></span>
            <span><Label as="span">Generated:</Label> <span style={{ color: PAPER.fg }}>{generated}</span></span>
          </Box>
        </Box>

        {/* Executive summary */}
        <Box sx={{ bgcolor: PAPER.low, p: 2.5, borderRadius: '2px', display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <span className="material-symbols-outlined" style={{ fontSize: 17, color: PAPER.fg }}>verified</span>
              <Typography sx={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                Executive Summary &amp; Milestone Trajectory
              </Typography>
            </Box>
            <Box component="span" sx={{ px: 1.25, py: 0.5, borderRadius: '2px', bgcolor: PAPER.bg, color: PAPER.ok, fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ● On Track for Release
            </Box>
          </Box>
          <Typography sx={{ fontSize: 15, lineHeight: 1.65 }}>
            Sprint 24 core objective—<b>{milestone}</b>—is tracking to plan for the November 14 deployment window. Delivery pace sits at <b>{stats.velocity}%</b> with {stats.done_points} of {stats.total_points} points verified Done. {risks.length} material risk{risks.length === 1 ? '' : 's'} tracked with documented mitigations; {stats.counts.Blocked} ticket{stats.counts.Blocked === 1 ? '' : 's'} currently blocked.
          </Typography>
        </Box>

        {/* KPI strip */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', md: 'repeat(4, 1fr)' }, gap: 1.5 }}>
          <Kpi label="Total Committed" value={stats.total_points} unit="pts" footL="Scope locked" footR={`${stats.issue_count} items`} />
          <Kpi label="Points Delivered" value={stats.done_points} unit="pts done" footL="Remaining:" footR={`${stats.remaining} pts`} footRStrong />
          <Box sx={{ bgcolor: PAPER.low, p: 2, borderRadius: '2px', display: 'flex', flexDirection: 'column', gap: 0.75 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Label>Velocity Pace</Label>
              <Box component="span" sx={{ ...mono, fontWeight: 700 }}>{stats.velocity}%</Box>
            </Box>
            <Box sx={{ height: 8, borderRadius: '2px', bgcolor: PAPER.higher, overflow: 'hidden' }}>
              <Box sx={{ height: '100%', width: `${stats.velocity}%`, bgcolor: PAPER.fg }} />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', ...mono, color: PAPER.muted }}>
              <span>Completion</span>
              <span style={{ color: PAPER.ok, fontWeight: 600 }}>{stats.completed_count}/{stats.issue_count} done</span>
            </Box>
          </Box>
          <Box sx={{ bgcolor: PAPER.low, p: 2, borderRadius: '2px', display: 'flex', flexDirection: 'column', gap: 0.75 }}>
            <Label>Ticket Distribution</Label>
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.75 }}>
              <Box component="span" sx={{ fontSize: 30, fontWeight: 800 }}>{stats.issue_count}</Box>
              <Box component="span" sx={{ ...mono, color: PAPER.muted, textTransform: 'uppercase' }}>tickets</Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', ...mono, color: PAPER.muted, fontSize: 11.5 }}>
              <b style={{ color: PAPER.ok }}>{stats.counts.Done} Done</b>
              <span>•</span>
              <span>{stats.counts['In Progress']} In Prog</span>
              <span>•</span>
              <b style={{ color: PAPER.err }}>{stats.counts.Blocked} Blk</b>
            </Box>
          </Box>
        </Box>

        {/* Risks / Wins columns */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
          <Box sx={{ bgcolor: PAPER.bg, border: `1px solid ${PAPER.higher}`, p: 2, borderRadius: '2px' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1, mb: 1.25 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 15, color: PAPER.err }}>warning</span>
                <Typography sx={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Material Risks &amp; Mitigations</Typography>
              </Box>
              <Box component="span" sx={{ px: 0.75, py: 0.25, borderRadius: '2px', bgcolor: PAPER.errBg, color: PAPER.err, fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase' }}>
                {risks.length} Active
              </Box>
            </Box>
            {risks.map((r, i) => (
              <Box key={i} sx={{ bgcolor: PAPER.low, p: 1.25, mb: 1, borderRadius: '2px', display: 'flex', flexDirection: 'column', gap: 0.4 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1 }}>
                  <Typography sx={{ fontSize: 13.5, fontWeight: 600 }}>{r.title}</Typography>
                  {r.severity && (
                    <Box component="span" sx={{ px: 0.75, borderRadius: '2px', bgcolor: PAPER.higher, color: PAPER.err, fontSize: 10, fontWeight: 800, textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                      {r.severity} Risk
                    </Box>
                  )}
                </Box>
                {r.detail && <Typography sx={{ fontSize: 12, color: PAPER.muted, lineHeight: 1.55 }}>{r.detail}</Typography>}
              </Box>
            ))}
            {!risks.length && <Typography sx={{ fontSize: 12, color: PAPER.muted }}>No risks flagged.</Typography>}
          </Box>

          <Box sx={{ bgcolor: PAPER.bg, border: `1px solid ${PAPER.higher}`, p: 2, borderRadius: '2px' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1, mb: 1.25 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 15, color: PAPER.ok }}>task_alt</span>
                <Typography sx={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Key Wins &amp; Milestones</Typography>
              </Box>
              <Box component="span" sx={{ px: 0.75, py: 0.25, borderRadius: '2px', bgcolor: PAPER.high, color: PAPER.ok, fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase' }}>
                {wins.length} Completed
              </Box>
            </Box>
            {wins.map((w, i) => (
              <Box key={i} sx={{ bgcolor: PAPER.low, p: 1.25, mb: 1, borderRadius: '2px', display: 'flex', alignItems: 'flex-start', gap: 0.75 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 14, color: PAPER.ok, lineHeight: 1.4 }}>check_circle</span>
                <Typography sx={{ fontSize: 13.5, fontWeight: 600, lineHeight: 1.45 }}>{w}</Typography>
              </Box>
            ))}
            {!wins.length && <Typography sx={{ fontSize: 12, color: PAPER.muted }}>No wins recorded.</Typography>}
          </Box>
        </Box>

        {/* Work breakdown */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1 }}>
            <Typography sx={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Detailed Sprint Scope Breakdown
            </Typography>
            <Box component="span" sx={{ ...mono, color: PAPER.muted }}>{issues.length} Epics / Work Items Tracked</Box>
          </Box>
          <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <Box component="thead">
              <tr>
                {['Key', 'Summary & Deliverable', 'Status', 'Points'].map((h, i) => (
                  <th key={h} style={{ backgroundColor: PAPER.high, color: PAPER.muted, fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', textAlign: i === 2 ? 'center' : i === 3 ? 'right' : 'left', padding: '10px 14px' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </Box>
            <tbody>
              {issues.map((it, idx) => {
                const blocked = it.status === 'Blocked'
                return (
                  <tr key={it.key} style={{ background: idx % 2 ? PAPER.low : PAPER.bg }}>
                    <td style={{ padding: '10px 14px', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: 12, color: blocked ? PAPER.err : PAPER.fg }}>{it.key}</td>
                    <td style={{ padding: '10px 14px', fontWeight: 600, color: blocked ? PAPER.err : PAPER.fg }}>{it.summary}</td>
                    <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                      <PdfStatusChip status={it.status} />
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, color: blocked ? PAPER.err : PAPER.fg }}>{it.story_points}</td>
                  </tr>
                )
              })}
            </tbody>
            <tfoot>
              <tr style={{ backgroundColor: PAPER.high }}>
                <td colSpan={2} style={{ padding: '10px 14px', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, textTransform: 'uppercase', fontSize: 12 }}>
                  Sprint Total Scope Summary: {issues.length} Issues Tracked
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'right', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>{stats.total_points} pts</td>
                <td style={{ padding: '10px 14px', textAlign: 'right', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>{stats.velocity}% Done</td>
              </tr>
            </tfoot>
          </Box>
        </Box>

        {/* Running footer */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 1, pt: 2, mt: 2, borderTop: `1px solid ${PAPER.higher}`, ...mono, color: PAPER.muted, fontSize: 11 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <span>Sprint record</span><span>•</span>
            <span>Generated {generated}</span><span>•</span>
            <span>Confidential &amp; Proprietary</span>
          </Box>
        </Box>
      </Box>

      {/* Screen-only control strip (the design's floating print-preview controls) */}
      <Box className="no-print" sx={{ position: 'fixed', bottom: 16, left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: 1.5, bgcolor: 'rgba(24,24,27,0.95)', border: '1px solid', borderColor: 'divider', borderRadius: 999, px: 1.5, py: 1, boxShadow: 6, zIndex: 100 }}>
        <Button size="small" onClick={() => { window.location.hash = '#/' }} sx={{ textTransform: 'none', color: 'text.primary' }}>
          ← Back to dashboard
        </Button>
        <Button size="small" variant="contained" disableElevation onClick={() => window.print()} sx={{ textTransform: 'none', bgcolor: '#f4f4f5', color: '#18181b', '&:hover': { bgcolor: '#e4e4e7' } }}>
          Print / Save PDF
        </Button>
      </Box>
    </Box>
  )
}

function Kpi({ label, value, unit, footL, footR, footRStrong }) {
  return (
    <Box sx={{ bgcolor: PAPER.low, p: 2, borderRadius: '2px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 0.75 }}>
      <Label>{label}</Label>
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.75 }}>
        <Box component="span" sx={{ fontSize: 30, fontWeight: 800 }}>{value}</Box>
        <Box component="span" sx={{ ...mono, color: PAPER.muted, textTransform: 'uppercase' }}>{unit}</Box>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', ...mono, color: PAPER.muted, pt: 0.75 }}>
        <span>{footL}</span>
        <span style={footRStrong ? { color: PAPER.fg, fontWeight: 700 } : undefined}>{footR}</span>
      </Box>
    </Box>
  )
}

function PdfStatusChip({ status }) {
  const map = {
    Done: { bg: PAPER.low, fg: PAPER.ok, weight: 600 },
    'In Progress': { bg: PAPER.high, fg: PAPER.fg, weight: 600 },
    Blocked: { bg: PAPER.errBg, fg: PAPER.err, weight: 800 },
    'To Do': { bg: PAPER.high, fg: PAPER.muted, weight: 600 },
  }
  const s = map[status] || map['To Do']
  return (
    <span style={{ display: 'inline-block', padding: '3px 8px', borderRadius: '2px', background: s.bg, color: s.fg, fontSize: 10.5, fontWeight: s.weight, textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
      {status}
    </span>
  )
}
