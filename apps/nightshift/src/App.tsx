import { useEffect, useState } from "react";

const TRACKS = [
  {
    num: "01",
    title: "AI, but make it useful",
    desc: "Ship assistants, agents, or tools that solve a real problem in one night. Demos over decks.",
    tags: ["LLM", "Agents", "Data"],
  },
  {
    num: "02",
    title: "Web3 without the noise",
    desc: "Build on-chain or off-chain experiences that feel fast, legible, and worth using after sunrise.",
    tags: ["DeFi", "Identity", "Infra"],
  },
  {
    num: "03",
    title: "Design systems that ship",
    desc: "Prototype interfaces, motion, and design tokens that teams could adopt Monday morning.",
    tags: ["UI", "Motion", "Brand"],
  },
  {
    num: "04",
    title: "Open track",
    desc: "No brief, no boundaries. Bring your wildest side project and make it the main character.",
    tags: ["Wildcard", "Hardware", "Games"],
  },
];

const SCHEDULE = [
  { time: "6:00 PM", name: "The spark", note: "Kickoff, team formation, and track intros." },
  { time: "7:30 PM", name: "Into the build zone", note: "Hacking begins. Mentors on rotation." },
  { time: "12:00 AM", name: "Midnight check-in", note: "Progress demos and snack reload." },
  { time: "3:00 AM", name: "Deep focus block", note: "Quiet hours. Coffee on tap." },
  { time: "5:30 AM", name: "Sunrise submissions", note: "Upload repos and two-minute demos." },
  { time: "6:30 PM", name: "Awards & afterglow", note: "Judges, prizes, and post-build stories." },
];

const FAQS = [
  {
    q: "Who can join Nightshift?",
    a: "Builders of any level. Solo hackers and teams up to four are welcome. You need a laptop, curiosity, and stamina.",
  },
  {
    q: "Is it really 24 hours?",
    a: "Yes. The clock starts at kickoff and submissions close at sunrise. Breaks are encouraged; sleep is tactical.",
  },
  {
    q: "Do I need a team?",
    a: "No. We run team formation at kickoff if you want to find collaborators by track or skill.",
  },
  {
    q: "What do I need to submit?",
    a: "A public repo or demo link, a short README, and a two-minute Loom or live demo clip.",
  },
  {
    q: "Are prizes per track?",
    a: "Grand prizes are overall, with honorable mentions per track. All winners demo on the main stage.",
  },
];

function MoonIcon() {
  return (
    <svg className="logo-icon" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M21 14.5A8.5 8.5 0 0 1 9.5 3 7 7 0 1 0 21 14.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="currentColor"
        fillOpacity="0.15"
      />
    </svg>
  );
}

function useCountdown() {
  const [display, setDisplay] = useState("24:00:00");

  useEffect(() => {
    const target = Date.now() + 24 * 60 * 60 * 1000;
    const tick = () => {
      const left = Math.max(0, target - Date.now());
      const h = Math.floor(left / 3_600_000);
      const m = Math.floor((left % 3_600_000) / 60_000);
      const s = Math.floor((left % 60_000) / 1000);
      setDisplay(
        [h, m, s].map((n) => String(n).padStart(2, "0")).join(":"),
      );
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, []);

  return display;
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="faq-item">
      <button
        type="button"
        className="faq-trigger"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span>{q}</span>
        <span className="faq-icon" aria-hidden>
          {open ? "−" : "+"}
        </span>
      </button>
      {open ? <div className="faq-answer">{a}</div> : null}
    </div>
  );
}

export default function App() {
  const countdown = useCountdown();

  return (
    <div className="page">
      <header className="site-header">
        <div className="container header-inner">
          <a href="#" className="logo">
            <MoonIcon />
            Nightshift
          </a>
          <nav className="nav-links" aria-label="Primary">
            <a href="#home">Home</a>
            <a href="#tracks">Tracks</a>
            <a href="#schedule">Schedule</a>
            <a href="#faq">FAQ</a>
          </nav>
          <a className="btn btn-primary" href="#cta">
            Get your spot
          </a>
        </div>
      </header>

      <section id="home" className="hero grid-bg">
        <div className="container hero-grid">
          <div>
            <p className="eyebrow">24-hour online hackathon</p>
            <h1 className="hero-title">
              Build
              <span className="accent">after dark.</span>
            </h1>
            <p className="hero-lead">
              One night to turn your side project into the main event. Four tracks, global
              builders, and prizes for what you ship before sunrise.
            </p>
            <div className="hero-actions">
              <a className="btn btn-primary" href="#cta">
                Join the hackathon
              </a>
              <a className="btn btn-outline" href="#tracks">
                Explore the tracks
              </a>
            </div>
          </div>
          <aside className="terminal-card" aria-label="Event countdown">
            <div className="terminal-bar">
              <span className="terminal-dot" />
              <span className="terminal-dot" />
              <span className="terminal-dot" />
            </div>
            <div className="terminal-body">
              <p className="terminal-greet">HELLO, NIGHT OWLS</p>
              <p className="terminal-countdown">{countdown}</p>
              <pre className="terminal-code">
                <span className="kw">const</span> nightshift = {"{"}
                {"\n"}  mode: <span className="kw">&quot;build&quot;</span>,
                {"\n"}  hours: <span className="kw">24</span>,
                {"\n"}  sleep: <span className="kw">optional</span>
                {"\n"}
                {"}"};
              </pre>
            </div>
          </aside>
        </div>

        <div className="stats-ribbon">
          <div className="container stats-grid">
            {[
              ["24 Hours", "Non-stop build window"],
              ["300+", "Builders"],
              ["4", "Tracks"],
              ["$10K", "In prizes"],
            ].map(([value, label]) => (
              <div key={label} className="stat-item">
                <div className="stat-value">{value}</div>
                <div className="stat-label">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container intro-split">
          <div>
            <h2 className="section-title">
              Your side project.
              <br />
              Its main character era.
            </h2>
            <div className="intro-tags">
              {["AI", "WEB3", "DESIGN"].map((t) => (
                <span key={t} className="tag">
                  {t}
                </span>
              ))}
            </div>
          </div>
          <p className="intro-copy">
            Nightshift is built for makers who do their best work when the world goes quiet.
            Whether you are prototyping an agent, polishing a protocol, or pushing pixels until
            dawn, you will join a distributed room of builders who treat one night like a
            launchpad.
          </p>
        </div>
      </section>

      <section id="tracks" className="section grid-bg">
        <div className="container">
          <div className="section-head">
            <h2 className="section-title">
              Four tracks. <span className="muted">No limits.</span>
            </h2>
          </div>
          <div className="tracks-grid">
            {TRACKS.map((t) => (
              <article key={t.num} className="track-card">
                <span className="track-num">{t.num}</span>
                <h3 className="track-name">{t.title}</h3>
                <p className="track-desc">{t.desc}</p>
                <div className="track-tags">
                  {t.tags.map((tag) => (
                    <span key={tag} className="track-tag">
                      {tag}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="schedule" className="section">
        <div className="container schedule-layout">
          <div>
            <h2 className="section-title">
              One night.
              <br />A whole lot can happen.
            </h2>
          </div>
          <ul className="schedule-list">
            {SCHEDULE.map((ev) => (
              <li key={ev.name} className="schedule-item">
                <span className="schedule-time">{ev.time}</span>
                <div>
                  <div className="schedule-name">{ev.name}</div>
                  <div className="schedule-note">{ev.note}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-head">
            <h2 className="section-title">
              Make a dent. <span className="muted">Take a prize.</span>
            </h2>
          </div>
          <div className="prizes-grid">
            <div className="prize-card featured">
              <div className="prize-rank">1st place</div>
              <div className="prize-amount">$5,000</div>
            </div>
            <div className="prize-card">
              <div className="prize-rank">2nd place</div>
              <div className="prize-amount">$3,000</div>
            </div>
            <div className="prize-card">
              <div className="prize-rank">3rd place</div>
              <div className="prize-amount">$2,000</div>
            </div>
          </div>
        </div>
      </section>

      <section id="faq" className="section">
        <div className="container faq-layout">
          <h2 className="section-title">
            Good questions.
            <br />
            Straight answers.
          </h2>
          <div className="faq-list">
            {FAQS.map((item) => (
              <FaqItem key={item.q} q={item.q} a={item.a} />
            ))}
          </div>
        </div>
      </section>

      <section id="cta" className="cta-banner grid-bg">
        <div className="container">
          <h2 className="cta-title">Don&apos;t sleep on your next big idea.</h2>
          <a className="btn btn-primary" href="#">
            Ok let&apos;s build
          </a>
        </div>
      </section>

      <footer className="site-footer">
        <div className="container footer-inner">
          <a href="#" className="logo">
            <MoonIcon />
            Nightshift
          </a>
          <span>© {new Date().getFullYear()} Nightshift Hackathon</span>
          <div className="footer-social">
            <a href="#">Discord</a>
            <a href="#">X</a>
            <a href="#">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}