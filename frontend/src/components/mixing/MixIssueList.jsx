import { useState } from 'react'

function MixIssueList({ scores }) {
  const [openCode, setOpenCode] = useState(null)
  const highs = scores.issues.filter((issue) => issue.priority === 'high')
  const mediums = scores.issues.filter((issue) => issue.priority === 'medium')

  function IssueCard({ issue, tone }) {
    const open = openCode === issue.code
    return (
      <button
        type="button"
        className={`issue-card ${tone}`}
        onClick={() => setOpenCode(open ? null : issue.code)}
      >
        <span className="issue-title">{issue.title}</span>
        {issue.range && <span className="issue-range">{issue.range}</span>}
        <span className="issue-more">{open ? 'Hide detail' : 'View detail →'}</span>
        {open && <p className="issue-detail">{issue.detail}</p>}
      </button>
    )
  }

  return (
    <section className="panel">
      {highs.length > 0 && (
        <>
          <p className="kicker high">HIGH PRIORITY</p>
          <div className="issue-list">
            {highs.map((issue) => (
              <IssueCard key={issue.code} issue={issue} tone="high" />
            ))}
          </div>
        </>
      )}

      {mediums.length > 0 && (
        <>
          <p className="kicker medium">MEDIUM PRIORITY</p>
          <div className="issue-list">
            {mediums.map((issue) => (
              <IssueCard key={issue.code} issue={issue} tone="medium" />
            ))}
          </div>
        </>
      )}

      {scores.looks_good.length > 0 && (
        <>
          <p className="kicker good">LOOKS GOOD</p>
          <div className="issue-list">
            {scores.looks_good.map((label) => (
              <div className="issue-card good" key={label}>
                <span className="issue-title">{label}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {scores.issues.length === 0 && scores.looks_good.length === 0 && (
        <p className="note">No strong mix flags from the current measurements.</p>
      )}
    </section>
  )
}

export default MixIssueList