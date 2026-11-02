export default function Narrative({ title, text, tone = 'neutral' }) {
  const lines = String(text).split('\n').map((l) => l.trim()).filter(Boolean)
  return (
    <section className={`panel ${tone}`}>
      <h2>{title}</h2>
      <ul>
        {lines.map((line, i) => (
          <li key={i}>{line}</li>
        ))}
      </ul>
    </section>
  )
}
