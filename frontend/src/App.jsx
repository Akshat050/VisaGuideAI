import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import "./App.css";
import DocumentAnalyzer from "./DocumentAnalyzer";

const API_URL = "http://localhost:8000";

function cx(...c) {
  return c.filter(Boolean).join(" ");
}

function formatMessage(text) {
  if (!text) return "";
  let html = String(text);

  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  const lines = html.split("\n");
  const out = [];
  let inList = false;

  for (const line of lines) {
    const trimmed = line.trim();
    const isBullet = /^[•\-\*]\s/.test(trimmed);

    if (isBullet) {
      if (!inList) {
        out.push("<ul>");
        inList = true;
      }
      out.push(`<li>${trimmed.replace(/^[•\-\*]\s/, "")}</li>`);
      continue;
    }

    if (trimmed === "") {
      if (inList) {
        out.push("</ul>");
        inList = false;
      }
      continue;
    }

    if (inList) {
      out.push("</ul>");
      inList = false;
    }
    out.push(`<p>${trimmed}</p>`);
  }

  if (inList) out.push("</ul>");
  return out.join("");
}

function Pill({ tone = "neutral", children }) {
  return <span className={cx("pill", `pill-${tone}`)}>{children}</span>;
}

function IconBadge({ icon, label }) {
  return (
    <div className="iconBadge">
      <span className="iconBadgeIcon">{icon}</span>
      <span className="iconBadgeText">{label}</span>
    </div>
  );
}

function ProgressBar({ value }) {
  const v = Math.max(0, Math.min(100, value || 0));
  return (
    <div className="progressWrap">
      <div className="progressBar" style={{ width: `${v}%` }} />
      <div className="progressMeta">
        <span>Readiness</span>
        <strong>{v}%</strong>
      </div>
    </div>
  );
}

function Section({ title, subtitle, right, children }) {
  return (
    <div className="section">
      <div className="sectionHead">
        <div>
          <h2 className="sectionTitle">{title}</h2>
          {subtitle ? <p className="sectionSub">{subtitle}</p> : null}
        </div>
        {right ? <div className="sectionRight">{right}</div> : null}
      </div>
      <div className="sectionBody">{children}</div>
    </div>
  );
}

function EmptyState({ onStart }) {
  return (
    <div className="hero">
      <div className="heroTop">
        <div className="brandMark">
          <span className="brandEmoji">🛂</span>
        </div>
        <div>
          <h1 className="heroTitle">VisaGuide AI</h1>
          <p className="heroTag">
            Personalized visa requirements, document checklist, and form guidance — with source-aware answers.
          </p>
        </div>
      </div>

      <div className="heroActions">
        <button className="btnPrimary" onClick={onStart}>
          Start Visa Check
          <span className="btnArrow">→</span>
        </button>
        <div className="heroChips">
          <Pill tone="info">DB-first</Pill>
          <Pill tone="info">Cache</Pill>
          <Pill tone="info">AI fallback</Pill>
          <Pill tone="neutral">Not legal advice</Pill>
        </div>
      </div>

      <div className="heroGrid">
        <div className="featureCard">
          <div className="featureTop">
            <span className="featureIcon">🧭</span>
            <div>
              <div className="featureTitle">Guided Requirements</div>
              <div className="featureSub">Citizenship + destination → structured checklist.</div>
            </div>
          </div>
          <div className="featureFoot">Get mandatory, recommended, and “not required” docs instantly.</div>
        </div>

        <div className="featureCard">
          <div className="featureTop">
            <span className="featureIcon">✅</span>
            <div>
              <div className="featureTitle">Readiness & Consistency</div>
              <div className="featureSub">Know what’s missing before you apply.</div>
            </div>
          </div>
          <div className="featureFoot">Reduce mistakes with a clear readiness score and risk flags.</div>
        </div>

        <div className="featureCard">
          <div className="featureTop">
            <span className="featureIcon">💬</span>
            <div>
              <div className="featureTitle">Context-Aware Chat</div>
              <div className="featureSub">Follow-ups grounded in your selected route.</div>
            </div>
          </div>
          <div className="featureFoot">Less generic answers, more actionable steps.</div>
        </div>
      </div>

      <div className="trustNote">
        <span className="trustDot" />
        Always verify with official government sources. VisaGuide AI provides informational guidance only.
      </div>
    </div>
  );
}

function Stepper({ step }) {
  const steps = [
    { k: "profile", t: "Profile" },
    { k: "requirements", t: "Requirements" },
    { k: "checklist", t: "Checklist" },
  ];
  return (
    <div className="stepper">
      {steps.map((s, idx) => {
        const active = s.k === step;
        const done = steps.findIndex((x) => x.k === step) > idx;
        return (
          <div key={s.k} className={cx("step", active && "active", done && "done")}>
            <div className="stepDot">{done ? "✓" : idx + 1}</div>
            <div className="stepText">{s.t}</div>
            {idx !== steps.length - 1 ? <div className="stepLine" /> : null}
          </div>
        );
      })}
    </div>
  );
}

// ✅ simple session id generator (for caching continuity)
function makeSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export default function App() {
  const [view, setView] = useState("requirements"); // requirements | chat | documents
  const [step, setStep] = useState("profile"); // profile | requirements | checklist

  // Countries & routes
  const [countriesLoading, setCountriesLoading] = useState(false);
  const [countriesError, setCountriesError] = useState("");
  const [sourceCountries, setSourceCountries] = useState([]);
  const [destinationCountries, setDestinationCountries] = useState([]);
  const [routes, setRoutes] = useState({});

  const [sourceCountry, setSourceCountry] = useState("");
  const [destinationCountry, setDestinationCountry] = useState("");

  // Requirements payload
  const [reqLoading, setReqLoading] = useState(false);
  const [reqError, setReqError] = useState("");
  const [data, setData] = useState(null);

  // ✅ store route profile_id returned by /api/get-requirements
  const [profileId, setProfileId] = useState(null);

  // ✅ persist session_id so cache works across chat messages
  const [sessionId, setSessionId] = useState(makeSessionId());

  // Checklist selection
  const [haveDocs, setHaveDocs] = useState({}); // {docId: boolean}

  // Chat
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const allowedDestinations = useMemo(() => {
    return (routes?.[sourceCountry] ?? destinationCountries) || [];
  }, [routes, sourceCountry, destinationCountries]);

  // Load countries once
  useEffect(() => {
    const load = async () => {
      setCountriesLoading(true);
      setCountriesError("");
      try {
        const res = await axios.get(`${API_URL}/api/countries`, { timeout: 15000 });
        setSourceCountries(res.data?.source_countries ?? []);
        setDestinationCountries(res.data?.destination_countries ?? []);
        setRoutes(res.data?.routes ?? {});
        const defaultSource = (res.data?.source_countries ?? [])[0] ?? "";
        setSourceCountry(defaultSource);
        const possible = res.data?.routes?.[defaultSource] ?? (res.data?.destination_countries ?? []);
        setDestinationCountry(possible?.[0] ?? "");
      } catch {
        setCountriesError("Could not load countries. Make sure the backend is running on port 8000.");
      } finally {
        setCountriesLoading(false);
      }
    };
    load();
  }, []);

  // Keep destination valid when source changes
  useEffect(() => {
    if (!sourceCountry) return;
    const allowed = routes?.[sourceCountry] ?? destinationCountries;
    if (allowed?.length && destinationCountry && !allowed.includes(destinationCountry)) {
      setDestinationCountry(allowed[0]);
    }
  }, [sourceCountry, routes, destinationCountries, destinationCountry]);

  // Scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatLoading]);

  const readiness = useMemo(() => {
    const mandatory = data?.requirements?.mandatory ?? [];
    if (!mandatory.length) return 0;
    const haveCount = mandatory.filter((d) => haveDocs[d.id]).length;
    return Math.round((haveCount / mandatory.length) * 100);
  }, [data, haveDocs]);

  const onStart = () => {
    setView("requirements");
    setStep("profile");
    setData(null);
    setProfileId(null);
    setReqError("");
    setMessages([]);
    setSessionId(makeSessionId()); // ✅ new session
  };

  const fetchRequirements = async () => {
    if (!sourceCountry || !destinationCountry) return;
    setReqLoading(true);
    setReqError("");
    setData(null);
    setProfileId(null);
    setHaveDocs({});
    try {
      const res = await axios.post(
        `${API_URL}/api/get-requirements`,
        { source_country: sourceCountry, destination_country: destinationCountry },
        { timeout: 20000 }
      );

      if (!res.data?.found) {
        setReqError("This route is not available yet. Try another combination.");
      } else {
        setData(res.data);
        setProfileId(res.data.profile_id || null);
        setStep("requirements");

        const next = {};
        (res.data?.requirements?.mandatory ?? []).forEach((d) => (next[d.id] = false));
        setHaveDocs(next);

        // ✅ Reset chat session when route changes (prevents cross-route confusion)
        setSessionId(makeSessionId());

        // Auto-seed chat context
        setMessages([
          {
            role: "assistant",
            content:
              `You’re on **${res.data.route?.visa_type}** (${res.data.route?.from} → ${res.data.route?.to}).\n` +
              `Ask me anything — I’ll answer based on this route.\n\n` +
              `Try: **“How do I apply step-by-step?”** or **“What documents should I carry?”**`,
            source: "database",
          },
        ]);
      }
    } catch {
      setReqError("Could not fetch requirements. Please try again.");
    } finally {
      setReqLoading(false);
    }
  };

  // ✅ Key fix: never hardcode us_b1b2; always send route context properly
  const sendMessage = async () => {
    const q = input.trim();
    if (!q || chatLoading) return;

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setInput("");
    setChatLoading(true);

    try {
      const res = await axios.post(
        `${API_URL}/api/chat`,
        {
          message: q,
          // send route visa_type if known, otherwise null (lets backend decide)
          visa_type: data?.route?.visa_type || null,
          profile_id: profileId || data?.profile_id || null,
          source_country: data?.route?.from || sourceCountry || null,
          destination_country: data?.route?.to || destinationCountry || null,
          session_id: sessionId,
        },
        { timeout: 30000 }
      );

      const answer = res.data?.response || "I couldn’t generate a response. Try again.";

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: answer, source: res.data?.source || "ai" },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Connection error. Please ensure the backend is running.", source: "ai" },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const headerSubtitle = useMemo(() => {
    if (view === "documents") return "Analyze a document for completeness and gaps.";
    if (view === "chat") return "Ask follow-ups with confidence (source-aware).";
    return "Personalized requirements, checklist, and guidance.";
  }, [view]);

  const routeLabel = data?.route ? `${data.route.visa_type} • ${data.route.from} → ${data.route.to}` : null;

  const mandatory = data?.requirements?.mandatory ?? [];
  const recommended = data?.requirements?.recommended ?? [];
  const notRequired = data?.requirements?.not_required ?? [];

  return (
    <div className="shell">
      <div className="bgGlow" />

      <aside className="sidebar">
        <div className="sideBrand">
          <div className="sideLogo">🛂</div>
          <div>
            <div className="sideName">VisaGuide AI</div>
            <div className="sideMini">Source-aware • DB-first</div>
          </div>
        </div>

        <nav className="nav">
          <button className={cx("navItem", view === "requirements" && "active")} onClick={() => setView("requirements")}>
            <span className="navIcon">🧭</span> Requirements
          </button>
          <button className={cx("navItem", view === "chat" && "active")} onClick={() => setView("chat")}>
            <span className="navIcon">💬</span> Ask AI
          </button>
          <button className={cx("navItem", view === "documents" && "active")} onClick={() => setView("documents")}>
            <span className="navIcon">📄</span> Analyze Document
          </button>
        </nav>

        <div className="sideFoot">
          <IconBadge icon="✓" label="Always verify with official sources" />
          <div className="sideDisclaimer">Informational guidance only. Not legal advice.</div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="topLeft">
            <div className="topTitle">
              {view === "requirements" ? "Visa Check" : view === "chat" ? "Ask AI" : "Analyze Document"}
            </div>
            <div className="topSub">{headerSubtitle}</div>
          </div>

          <div className="topRight">
            {routeLabel ? <Pill tone="info">{routeLabel}</Pill> : <Pill tone="neutral">No route selected</Pill>}
            <Pill tone="neutral">Verified Dec 14, 2025</Pill>
          </div>
        </header>

        <div className="content">
          {view === "documents" ? (
            <div className="panel">
              <DocumentAnalyzer />
            </div>
          ) : view === "chat" ? (
            <div className="panel">
              <Section
                title="Chat (Context-Aware)"
                subtitle={data?.route ? "Questions are grounded in the selected route." : "Select a route first for the best answers."}
                right={
                  <button className="btnGhost" onClick={() => setView("requirements")}>
                    Select Route
                  </button>
                }
              >
                <div className="chatWrap">
                  <div className="chatMessages">
                    {messages.length === 0 ? (
                      <div className="chatEmpty">
                        <div className="chatEmptyTitle">Start with a route for best results</div>
                        <div className="chatEmptySub">
                          Go to <strong>Requirements</strong> → choose citizenship & destination → <strong>Get Requirements</strong>.
                        </div>
                      </div>
                    ) : (
                      messages.map((m, idx) => (
                        <div key={idx} className={cx("bubbleRow", m.role === "user" ? "user" : "assistant")}>
                          <div className="bubble">
                            <div className="bubbleHead">
                              <span className="bubbleIcon">{m.role === "user" ? "👤" : "🤖"}</span>
                              <span className="bubbleName">{m.role === "user" ? "You" : "VisaGuide AI"}</span>
                              {m.source ? (
                                <span className="bubbleTag">
                                  {m.source === "database" ? "📚 Verified" : m.source === "cache" ? "⚡ Cached" : "✨ AI"}
                                </span>
                              ) : null}
                            </div>
                            <div className="bubbleBody" dangerouslySetInnerHTML={{ __html: formatMessage(m.content) }} />
                          </div>
                        </div>
                      ))
                    )}

                    {chatLoading ? (
                      <div className="bubbleRow assistant">
                        <div className="bubble">
                          <div className="bubbleHead">
                            <span className="bubbleIcon">🤖</span>
                            <span className="bubbleName">VisaGuide AI</span>
                            <span className="bubbleTag">Thinking</span>
                          </div>
                          <div className="typing">
                            <span />
                            <span />
                            <span />
                          </div>
                        </div>
                      </div>
                    ) : null}

                    <div ref={messagesEndRef} />
                  </div>

                  <div className="chatInput">
                    <input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                      placeholder={data?.route ? `Ask about ${data.route.visa_type}…` : "Select a route first for best answers…"}
                      disabled={chatLoading}
                    />
                    <button className="btnPrimary" onClick={sendMessage} disabled={!input.trim() || chatLoading}>
                      Send →
                    </button>
                  </div>
                </div>
              </Section>
            </div>
          ) : (
            <>
              {!data && step === "profile" ? <EmptyState onStart={() => setStep("profile")} /> : null}

              <div className="panel">
                <Section
                  title="Your Visa Path"
                  subtitle="Select citizenship and destination to generate a structured checklist."
                  right={<Stepper step={step} />}
                >
                  <div className="formGrid">
                    <div className="field">
                      <label>Citizenship (Passport)</label>
                      <select value={sourceCountry} onChange={(e) => setSourceCountry(e.target.value)} disabled={countriesLoading}>
                        {sourceCountries.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="field">
                      <label>Destination</label>
                      <select
                        value={destinationCountry}
                        onChange={(e) => setDestinationCountry(e.target.value)}
                        disabled={countriesLoading}
                      >
                        {allowedDestinations.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="fieldBtn">
                      <button className="btnPrimary" onClick={fetchRequirements} disabled={countriesLoading || reqLoading}>
                        {reqLoading ? "Generating…" : "Get Requirements"}
                        <span className="btnArrow">→</span>
                      </button>
                      <div className="miniHint">DB → Cache → AI fallback</div>
                    </div>
                  </div>

                  {countriesError ? <div className="alert danger">{countriesError}</div> : null}
                  {reqError ? <div className="alert danger">{reqError}</div> : null}
                </Section>
              </div>

              {data ? (
                <div className="grid2">
                  <div className="panel">
                    <Section
                      title="Quick Facts"
                      subtitle="A clear summary before you start collecting documents."
                      right={<Pill tone="neutral">Verification: {data.verification_status}</Pill>}
                    >
                      <div className="facts">
                        <div className="fact">
                          <div className="factK">Visa</div>
                          <div className="factV">{data.route?.visa_name}</div>
                        </div>
                        <div className="fact">
                          <div className="factK">Fee</div>
                          <div className="factV">${data.quick_facts?.visa_fee_usd}</div>
                        </div>
                        <div className="fact">
                          <div className="factK">Processing</div>
                          <div className="factV">{data.quick_facts?.processing_days}</div>
                        </div>
                        <div className="fact">
                          <div className="factK">Interview</div>
                          <div className="factV">{data.quick_facts?.interview_required ? "Required" : "Not required"}</div>
                        </div>
                        <div className="fact">
                          <div className="factK">Typical Validity</div>
                          <div className="factV">{data.quick_facts?.validity_typical}</div>
                        </div>
                        <div className="fact">
                          <div className="factK">Timeline</div>
                          <div className="factV">{data.timeline?.total}</div>
                        </div>
                      </div>

                      <div className="divider" />

                      <div className="badgesRow">
                        <IconBadge icon="🧠" label="Smart route profile" />
                        <IconBadge icon="✅" label="Structured checklist" />
                        <IconBadge icon="🧾" label="Form guidance via chat" />
                      </div>
                    </Section>
                  </div>

                  <div className="panel">
                    <Section
                      title="Checklist & Readiness"
                      subtitle="Tick what you already have — we’ll show what’s missing."
                      right={<ProgressBar value={readiness} />}
                    >
                      <div className="checklist">
                        {mandatory.map((d) => (
                          <label key={d.id} className="checkRow">
                            <input
                              type="checkbox"
                              checked={!!haveDocs[d.id]}
                              onChange={(e) => setHaveDocs((prev) => ({ ...prev, [d.id]: e.target.checked }))}
                            />
                            <div className="checkMain">
                              <div className="checkTitle">
                                {d.name}{" "}
                                <Pill
                                  tone={
                                    d.rejection_risk === "CRITICAL"
                                      ? "danger"
                                      : d.rejection_risk === "HIGH"
                                      ? "warn"
                                      : "neutral"
                                  }
                                >
                                  {d.rejection_risk}
                                </Pill>
                              </div>
                              <div className="checkSub">{d.requirement}</div>
                            </div>
                          </label>
                        ))}
                      </div>

                      <div className="ctaRow">
                        <button className="btnGhost" onClick={() => setView("chat")}>
                          Ask AI about forms →
                        </button>
                        <div className="ctaHint">Tip: Ask “How do I apply step-by-step?” or “What should I carry to the interview?”</div>
                      </div>
                    </Section>
                  </div>

                  <div className="panel">
                    <Section title="Recommended Documents" subtitle="Not mandatory, but strongly improves your case.">
                      <div className="list">
                        {recommended.map((d) => (
                          <div key={d.id} className="listRow">
                            <div>
                              <div className="listTitle">{d.name}</div>
                              <div className="listSub">Importance: {d.importance}</div>
                            </div>
                            <Pill tone="info">{d.importance}</Pill>
                          </div>
                        ))}
                      </div>
                    </Section>
                  </div>

                  <div className="panel">
                    <Section title="Not Required" subtitle="Avoid unnecessary bookings before approval.">
                      <div className="list">
                        {notRequired.map((d, i) => (
                          <div key={`${d.document}-${i}`} className="listRow">
                            <div>
                              <div className="listTitle">{d.document}</div>
                              <div className="listSub">{d.reason}</div>
                            </div>
                            <Pill tone="neutral">OK</Pill>
                          </div>
                        ))}
                      </div>
                    </Section>
                  </div>

                  <div className="panel">
                    <Section title="Common Rejections" subtitle="This is where most people lose time.">
                      <div className="list">
                        {(data.common_rejections ?? []).map((r, i) => (
                          <div key={`${r.reason}-${i}`} className="listRow">
                            <div>
                              <div className="listTitle">{r.reason}</div>
                              <div className="listSub">Frequency: {r.frequency}</div>
                            </div>
                            <Pill
                              tone={r.frequency === "VERY HIGH" ? "danger" : r.frequency === "HIGH" ? "warn" : "neutral"}
                            >
                              {r.frequency}
                            </Pill>
                          </div>
                        ))}
                      </div>
                    </Section>
                  </div>

                  <div className="panel">
                    <Section title="Interview" subtitle="What to expect and where to go.">
                      <div className="facts">
                        <div className="fact">
                          <div className="factK">Required</div>
                          <div className="factV">{data.interview?.required ? "Yes" : "No"}</div>
                        </div>
                        <div className="fact">
                          <div className="factK">Duration</div>
                          <div className="factV">{data.interview?.duration_typical}</div>
                        </div>
                        <div className="fact">
                          <div className="factK">Locations</div>
                          <div className="factV">{(data.interview?.locations ?? []).join(", ")}</div>
                        </div>
                      </div>

                      <div className="divider" />

                      <div className="list">
                        {(data.country_specific_tips ?? []).map((t, i) => (
                          <div key={`${t}-${i}`} className="tipRow">
                            <span className="tipDot">•</span>
                            <span>{t}</span>
                          </div>
                        ))}
                      </div>
                    </Section>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
