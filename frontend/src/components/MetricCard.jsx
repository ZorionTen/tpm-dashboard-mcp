export default function MetricCard({ label, value, accent = false }) {
  return (
    <div className={`card${accent ? ' accent' : ''}`}>
      <div className="card-value">{value}</div>
      <div className="card-label">{label}</div>
    </div>
  )
}
