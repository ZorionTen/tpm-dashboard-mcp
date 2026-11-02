// Data helpers: payload shape comes from the MCP generate_dashboard tool.
// Sample data from the mock Jira; no invented owners/labels.

export const JIRA_BASE = 'https://jira.example.com/browse'

export const STATUS_META = {
  Done: { icon: 'check_box', color: '#22c55e', bg: 'rgba(34,197,94,0.15)', border: 'rgba(34,197,94,0.3)' },
  'In Progress': { icon: 'pending', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.3)' },
  Blocked: { icon: 'error', color: '#ef4444', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.3)' },
  'To Do': { icon: 'radio_button_unchecked', color: '#a1a1aa', bg: 'rgba(161,161,170,0.12)', border: 'rgba(161,161,170,0.3)' },
}

export const statusMeta = (s) => STATUS_META[s] || STATUS_META['To Do']

export function splitLines(text = '') {
  return String(text).split('\n').map((l) => l.replace(/^\s*[-•*]\s*/, '').trim()).filter(Boolean)
}

// "- Payments integration blocked by vendor (HIGH): mitigated by ..."
export function parseRisks(text = '') {
  return splitLines(text).map((line) => {
    const m = line.match(/^(.*?)\s*\((HIGH|MED|LOW|CRITICAL)\):\s*(.*)$/i)
    if (!m) return { title: line, severity: null, detail: '' }
    return { title: m[1].trim(), severity: m[2].toUpperCase(), detail: m[3].trim() }
  })
}

const SEV_COLOR = { HIGH: '#ef4444', CRITICAL: '#ef4444', MED: '#f59e0b', LOW: '#22c55e' }
export const sevColor = (s) => SEV_COLOR[s] || '#a1a1aa'

export function deriveStats(issues) {
  const pts = (i) => Number(i.story_points) || 0
  const total = issues.reduce((a, i) => a + pts(i), 0)
  const done = issues.reduce((a, i) => (i.status === 'Done' ? a + pts(i) : a), 0)
  const countBy = (s) => issues.filter((i) => i.status === s).length
  return {
    total_points: total,
    done_points: done,
    remaining: total - done,
    velocity: total ? Math.round((done / total) * 1000) / 10 : 0,
    issue_count: issues.length,
    completed_count: countBy('Done'),
    completion_pct: issues.length ? Math.round((countBy('Done') / issues.length) * 100) : 0,
    counts: {
      Done: countBy('Done'),
      'In Progress': countBy('In Progress'),
      Blocked: countBy('Blocked'),
      'To Do': countBy('To Do'),
    },
  }
}

export function nextKey(issues) {
  const max = issues.reduce((a, i) => {
    const n = Number(String(i.key).split('-')[1])
    return Number.isFinite(n) ? Math.max(a, n) : a
  }, 105)
  return `PROJ-${max + 1}`
}

export const jiraUrl = (key) => `${JIRA_BASE}/${key}`
