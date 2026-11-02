const STATUS_CLASS = {
  Done: 'done',
  'In Progress': 'progress',
  Blocked: 'blocked',
}

export default function IssueTable({ issues }) {
  if (!issues?.length) return <div className="banner">No issues in payload.</div>
  return (
    <table className="issues">
      <thead>
        <tr>
          <th>Key</th>
          <th>Summary</th>
          <th>Status</th>
          <th>Story Points</th>
        </tr>
      </thead>
      <tbody>
        {issues.map((i) => (
          <tr key={i.key}>
            <td className="key">{i.key}</td>
            <td>{i.summary}</td>
            <td>
              <span className={`badge ${STATUS_CLASS[i.status] || 'todo'}`}>{i.status}</span>
            </td>
            <td>{i.story_points}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
