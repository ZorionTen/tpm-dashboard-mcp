import { createTheme } from '@mui/material/styles'

// Palette follows the Stitch design tokens (zinc/charcoal dark, zinc-50 light)
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: { default: '#09090b', paper: '#18181b' },
    divider: '#27272a',
    text: { primary: '#f4f4f5', secondary: '#a1a1aa' },
    success: { main: '#22c55e' },
    warning: { main: '#f59e0b' },
    error: { main: '#ef4444' },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    h1: { fontWeight: 800, letterSpacing: '-0.02em' },
  },
  shape: { borderRadius: 12 },
})

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    background: { default: '#fafafa', paper: '#ffffff' },
    divider: '#e4e4e7',
    text: { primary: '#18181b', secondary: '#52525b' },
    success: { main: '#16a34a' },
    warning: { main: '#d97706' },
    error: { main: '#dc2626' },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    h1: { fontWeight: 800, letterSpacing: '-0.02em' },
  },
  shape: { borderRadius: 12 },
})
