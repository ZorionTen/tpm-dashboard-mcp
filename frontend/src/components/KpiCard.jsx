import { Box, Paper, Typography } from '@mui/material'

// One KPI card from the Stitch design: label + icon, big value, sub-line, optional progress bar.
export default function KpiCard({ label, value, icon, iconColor, sub, subColor, badge, progress, accent }) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: 2, sm: 2.5 },
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: 0.5,
        borderColor: accent ? 'divider' : 'divider',
        '&:hover': { borderColor: 'grey.600' },
        transition: 'border-color 150ms',
        minHeight: 132,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="caption" sx={{ fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'text.secondary' }}>
          {label}
        </Typography>
        {badge ? (
          <Typography component="span" className="mono" sx={{ fontSize: 10, fontWeight: 700, px: 0.75, py: 0.25, borderRadius: 1, border: '1px solid', borderColor: 'divider', bgcolor: 'rgba(113,113,122,0.15)', color: 'text.secondary' }}>
            {badge}
          </Typography>
        ) : (
          <span className="material-symbols-outlined" style={{ fontSize: 17, opacity: 0.7, color: iconColor ?? 'inherit' }}>
            {icon}
          </span>
        )}
      </Box>
      <Typography component="div" sx={{ fontSize: { xs: 30, sm: 36 }, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.1, color: 'text.primary', mt: 1 }}>
        {value}
      </Typography>
      {progress !== undefined && (
        <Box sx={{ mt: 1, width: '100%', height: 6, borderRadius: 999, bgcolor: 'rgba(113,113,122,0.25)', overflow: 'hidden' }}>
          <Box sx={{ height: '100%', borderRadius: 999, width: `${progress}%`, bgcolor: 'text.primary', transition: 'width 500ms' }} />
        </Box>
      )}
      {sub && (
        <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.75, color: subColor || 'text.secondary', fontWeight: subColor ? 500 : 400 }}>
          {sub}
        </Typography>
      )}
    </Paper>
  )
}
