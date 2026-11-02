import { useState } from 'react'
import {
  Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Typography,
} from '@mui/material'

// "Log Risk" (btn-add-blocker): modal form → appends a Blocked row to the table (session-local).
export default function AddBlockerDialog({ open, onClose, onSubmit }) {
  const [summary, setSummary] = useState('')
  const [points, setPoints] = useState('3')
  const [touched, setTouched] = useState(false)

  const reset = () => { setSummary(''); setPoints('3'); setTouched(false) }
  const valid = summary.trim().length > 0 && Number(points) > 0

  const submit = () => {
    setTouched(true)
    if (!valid) return
    onSubmit({ summary: summary.trim(), story_points: Number(points) })
    reset()
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" PaperProps={{ sx: { borderRadius: 3 } }}>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5, fontWeight: 700 }}>
        <span className="material-symbols-outlined" style={{ fontSize: 20, color: '#ef4444' }}>add_alert</span>
        Log Risk / Add Blocker
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: '12px !important' }}>
        <TextField
          label="Blocker summary"
          placeholder="e.g. Vendor sandbox unreachable"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          error={touched && !summary.trim()}
          helperText={touched && !summary.trim() ? 'Summary is required' : 'Added to the sprint table as status Blocked (this session only)'}
          fullWidth
          required
        />
        <TextField
          label="Story points"
          type="number"
          value={points}
          onChange={(e) => setPoints(e.target.value)}
          error={touched && !(Number(points) > 0)}
          helperText={touched && !(Number(points) > 0) ? 'Points must be > 0' : 'Counted in Total Points and velocity'}
          inputProps={{ min: 1, max: 40 }}
          sx={{ maxWidth: 200 }}
          required
        />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 15, color: '#ef4444' }}>error</span>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Status is set to <b>Blocked</b>; the key is assigned automatically.
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={() => { reset(); onClose() }} sx={{ textTransform: 'none' }}>Cancel</Button>
        <Button onClick={submit} variant="contained" disableElevation sx={{ textTransform: 'none', bgcolor: 'text.primary', color: 'background.default', '&:hover': { bgcolor: 'grey.400' } }}>
          Log blocker
        </Button>
      </DialogActions>
    </Dialog>
  )
}
