const actions = [
  {
    number: "01",
    priority: "High priority",
    title: "Review top opportunities",
    description:
      "Three investment cases deserve a closer look before capital is deployed.",
    meta: "3 cases ready",
  },
  {
    number: "02",
    priority: "Market context",
    title: "Understand today’s market",
    description:
      "Technology weakened while energy strengthened. Review what changed and why.",
    meta: "5 min review",
  },
  {
    number: "03",
    priority: "Portfolio preparation",
    title: "Prepare capital deployment",
    description:
      "Define the amount you are prepared to invest when conviction becomes sufficient.",
    meta: "$100,000 available",
  },
];

const marketItems = [
  { label: "S&P 500", value: "-0.8%", tone: "negative" },
  { label: "Nasdaq", value: "-2.4%", tone: "negative" },
  { label: "Oil", value: "+6.0%", tone: "positive" },
  { label: "Fear & Greed", value: "72", tone: "neutral" },
  { label: "Portfolio", value: "No change", tone: "neutral" },
];

const committee = [
  { label: "Market", value: "Neutral", score: 52 },
  { label: "Risk", value: "Moderate", score: 64 },
  { label: "Opportunity", value: "Emerging", score: 71 },
  { label: "Portfolio", value: "Ready", score: 82 },
];

export default function Home() {
  return (
    <main className="workspace">
      <header className="topbar">
        <a className="brand" href="#">
          <span className="brandMark">M</span>
          <span>MOVRvest</span>
        </a>

        <nav className="nav" aria-label="Primary navigation">
          <a className="active" href="#">
            Executive
          </a>
          <a href="#">Portfolio</a>
          <a href="#">Markets</a>
          <a href="#">Investment cases</a>
          <a href="#">Research</a>
        </nav>

        <button className="profile" type="button" aria-label="Open profile">
          MV
        </button>
      </header>

      <section className="hero">
        <div className="eyebrowRow">
          <p className="eyebrow">Executive brief · Today</p>
          <p className="updated">Updated moments ago</p>
        </div>

        <div className="heroGrid">
          <div className="heroCopy">
            <p className="greeting">Good evening, Marcos.</p>

            <h1>No urgent decision today.</h1>

            <p className="lead">
              Markets remain neutral while your portfolio is entirely in cash.
              You have maximum flexibility, but your capital is not yet
              compounding.
            </p>

            <div className="heroConclusion">
              <span className="conclusionLabel">MOVRvest view</span>
              <p>
                Stay selective. Review the strongest opportunities, but deploy
                capital only when conviction is supported by evidence.
              </p>
            </div>
          </div>

          <aside className="decisionCard">
            <div className="decisionTop">
              <span className="statusDot" />
              <span>Current stance</span>
            </div>

            <p className="decision">WAIT</p>

            <div className="confidenceBlock">
              <div className="confidenceLine">
                <span>Confidence</span>
                <strong>72%</strong>
              </div>
              <div className="confidenceTrack">
                <div className="confidenceFill" style={{ width: "72%" }} />
              </div>
            </div>

            <p className="decisionNote">
              Conditions are constructive, but not strong enough to justify
              immediate deployment.
            </p>

            <button className="primaryButton" type="button">
              Explore investment cases
              <span aria-hidden="true">→</span>
            </button>
          </aside>
        </div>
      </section>

      <section className="section agendaSection">
        <div className="sectionHeading">
          <div>
            <p className="eyebrow">Recommended actions</p>
            <h2>Your executive agenda</h2>
          </div>
          <p className="sectionIntro">
            Three actions, ordered by relevance to your current situation.
          </p>
        </div>

        <div className="actionGrid">
          {actions.map((action) => (
            <button className="actionCard" key={action.number} type="button">
              <div className="actionTop">
                <span className="actionNumber">{action.number}</span>
                <span className="actionPriority">{action.priority}</span>
              </div>

              <div>
                <h3>{action.title}</h3>
                <p>{action.description}</p>
              </div>

              <div className="actionFooter">
                <span>{action.meta}</span>
                <span className="actionArrow" aria-hidden="true">
                  ↗
                </span>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="section todaySection">
        <div className="sectionHeading compact">
          <div>
            <p className="eyebrow">Situation awareness</p>
            <h2>Today</h2>
          </div>
          <button className="textButton" type="button">
            Open market briefing →
          </button>
        </div>

        <div className="marketStrip">
          {marketItems.map((item) => (
            <div className="marketItem" key={item.label}>
              <span>{item.label}</span>
              <strong className={item.tone}>{item.value}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="section lowerGrid">
        <article className="panel portfolioPanel">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">Portfolio</p>
              <h2>Your capital position</h2>
            </div>
            <span className="healthBadge">68 / 100 health</span>
          </div>

          <div className="portfolioValue">
            <strong>$100,000</strong>
            <span>Total portfolio value</span>
          </div>

          <div className="allocation">
            <div className="allocationHeader">
              <span>Cash allocation</span>
              <strong>100%</strong>
            </div>
            <div className="allocationTrack">
              <div className="allocationFill" />
            </div>
          </div>

          <div className="portfolioSignals">
            <div>
              <span className="signalIcon good">✓</span>
              <div>
                <strong>Maximum flexibility</strong>
                <p>No leverage and no active market exposure.</p>
              </div>
            </div>

            <div>
              <span className="signalIcon attention">!</span>
              <div>
                <strong>Cash concentration</strong>
                <p>Your capital is protected, but not currently compounding.</p>
              </div>
            </div>
          </div>

          <button className="secondaryButton" type="button">
            Review portfolio
            <span aria-hidden="true">→</span>
          </button>
        </article>

        <article className="panel committeePanel">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">Executive committee</p>
              <h2>Where the committee agrees</h2>
            </div>
            <span className="agreement">72% agreement</span>
          </div>

          <p className="committeeSummary">
            The committee supports patience while continuing to investigate
            emerging opportunities.
          </p>

          <div className="committeeList">
            {committee.map((member) => (
              <div className="committeeRow" key={member.label}>
                <div className="committeeMeta">
                  <span>{member.label}</span>
                  <strong>{member.value}</strong>
                </div>
                <div className="committeeTrack">
                  <div
                    className="committeeFill"
                    style={{ width: `${member.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <button className="secondaryButton" type="button">
            Read committee reasoning
            <span aria-hidden="true">→</span>
          </button>
        </article>
      </section>
    </main>
  );
}
