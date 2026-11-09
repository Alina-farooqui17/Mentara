
import React, { useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  BookOpen,
  Brain,
  Check,
  ChevronLeft,
  ChevronRight,
  FileText,
  Home as HomeIcon,
  Menu,
  MessageCircle,
  Moon,
  Paperclip,
  RefreshCw,
  Send,
  Settings,
  Sparkles,
  Target,
  UploadCloud,
  UserRound,
  X
} from "lucide-react";
import API_BASE_URL from "./api";
import "./styles.css";

const tools = [
  {
    id: "ask",
    title: "Ask AI",
    text: "Get instant answers from your study material.",
    icon: MessageCircle,
    tone: "cyan"
  },
  {
    id: "notes",
    title: "AI Notes",
    text: "Turn your material into clear study notes.",
    icon: FileText,
    tone: "violet"
  },
  {
    id: "quiz",
    title: "MCQs & Quiz",
    text: "Practice with AI-generated questions.",
    icon: Brain,
    tone: "pink"
  }
];

function Mark() {
  return (
    <span className="mark">
      <Sparkles size={14} />
    </span>
  );
}

// SIDEBAR
function Sidebar({ active, setActive, mobile, close }) {
  const items = [
    ["home", "Home", HomeIcon],
    ["upload", "Upload PDF", UploadCloud],
    ["ask", "Ask AI", MessageCircle],
    ["notes", "AI Notes", FileText],
    ["quiz", "MCQs & Quiz", Brain]
  ];

  return (
    <>
      {mobile && <div className="overlay" onClick={close} />}

      <aside className={mobile ? "side open" : "side"}>
        <div className="side-head">
          <div className="brand">
            <Mark /> Mentara
          </div>

          <button className="x" onClick={close}>
            <X />
          </button>
        </div>

        <nav>
          {items.map(([id, title, Icon]) => (
            <button
              key={id}
              className={active === id ? "nav active" : "nav"}
              onClick={() => {
                setActive(id);
                close();
              }}
            >
              <Icon size={17} />
              {title}
            </button>
          ))}
        </nav>

        <div className="side-bottom">
          <button className="nav">
            <Settings size={17} />
            Settings
          </button>

          <button className="nav">
            <Moon size={17} />
            Appearance
          </button>
        </div>
      </aside>
    </>
  );
}

// MAIN APP
function App() {
  const [name, setName] = useState(
    () => localStorage.getItem("mentaraUserName") || ""
  );

  const [active, setActive] = useState("home");
  const [pdf, setPdf] = useState(null);
  const [busy, setBusy] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [notice, setNotice] = useState(null);

  const onboard = !name;

  const notify = (type, msg) => {
    setNotice({ type, msg });
    setTimeout(() => setNotice(null), 4500);
  };

  const saveName = (value) => {
    value = value.trim();

    if (!value) return;

    localStorage.setItem("mentaraUserName", value);
    setName(value);
  };

  const upload = async (file) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return notify("error", "Please choose a PDF file.");
    }

    setBusy(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE_URL}/upload-pdf`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw Error(data.detail || "Upload failed.");
      }

      setPdf(data);

      notify("success", `${data.filename} uploaded successfully.`);
      setActive("ask");
    } catch (error) {
      notify("error", error.message);
    } finally {
      setBusy(false);
    }
  };

  if (onboard) {
    return <Welcome onSave={saveName} />;
  }

  return (
    <div className="app">
      <Sidebar
        active={active}
        setActive={setActive}
        mobile={mobile}
        close={() => setMobile(false)}
      />

      <section className="main">
        <header>
          <button className="menu" onClick={() => setMobile(true)}>
            <Menu />
          </button>

          <div className="mobile-brand">
            <Mark /> Mentara
          </div>

          <div className="user">
            <span className="avatar">{name[0].toUpperCase()}</span>
            Hi, {name}
          </div>
        </header>

        {notice && (
          <div className={`toast ${notice.type}`}>
            {notice.msg}

            <button onClick={() => setNotice(null)}>
              <X size={14} />
            </button>
          </div>
        )}

        <main>
          {active === "home" && (
            <Home
              name={name}
              pdf={pdf}
              setActive={setActive}
              upload={upload}
              busy={busy}
            />
          )}

          {active === "upload" && (
            <Upload pdf={pdf} upload={upload} busy={busy} />
          )}

          {active === "ask" && (
            <Ask pdf={pdf} notify={notify} setActive={setActive} />
          )}

          {active === "notes" && (
            <Notes pdf={pdf} notify={notify} setActive={setActive} />
          )}

          {active === "quiz" && (
            <Quiz pdf={pdf} notify={notify} setActive={setActive} />
          )}
        </main>
      </section>
    </div>
  );
}

// WELCOME SCREEN
function Welcome({ onSave }) {
  const [value, setValue] = useState("");

  return (
    <div className="welcome">
      <div className="glow g1" />
      <div className="glow g2" />

      <div className="welcome-card">
        <div className="brand">
          <Mark /> Mentara
        </div>

        <div className="welcome-art">
          <div className="book">📖</div>
          <div className="bot">✦</div>
          <i>AI</i>
          <b>✦</b>
        </div>

        <small>YOUR PERSONAL AI LEARNING SPACE</small>

        <h1>
          Welcome to <em>Mentara</em>!
        </h1>

        <p>
          Let's personalize your learning experience.
          What should we call you?
        </p>

        <div className="name">
          <UserRound size={17} />

          <input
            autoFocus
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" && onSave(value)
            }
            placeholder="What's your name?"
          />
        </div>

        <button
          className="primary full"
          onClick={() => onSave(value)}
        >
          Continue <ArrowRight size={17} />
        </button>

        <div className="privacy">
          🔒 Your name is saved locally on this device.
        </div>
      </div>
    </div>
  );
}

// HOME
function Home({ name, pdf, setActive, upload, busy }) {
  const ref = useRef();

  return (
    <div className="fade">
      <section className="hero">
        <div>
          <small>✦ YOUR AI LEARNING COMPANION</small>

          <h1>
            Good evening, <span>{name}!</span> 👋
          </h1>

          <p>
            Turn your study material into answers, notes and quizzes
            — all in one intelligent workspace.
          </p>

          <div className="actions">
            <button
              className="primary"
              onClick={() => setActive("upload")}
            >
              Start Learning <ArrowRight size={17} />
            </button>

            <button
              className="secondary"
              onClick={() => setActive("ask")}
            >
              Ask Mentara
            </button>
          </div>
        </div>

        <div className="hero-art">
          <div className="ai-orb">✦</div>
          <div className="mountain" />
        </div>
      </section>

      <div className="section">
        <div>
          <small>GET STARTED</small>
          <h2>Your study space</h2>
        </div>

        <span className="status">
          ● {pdf ? "PDF ready" : "No material uploaded"}
        </span>
      </div>

      <div
        className="upload-row"
        onClick={() => ref.current?.click()}
      >
        <input
          ref={ref}
          hidden
          type="file"
          accept=".pdf"
          onChange={(e) => upload(e.target.files?.[0])}
        />

        <span className="upload-icon">
          <UploadCloud />
        </span>

        <div>
          <strong>
            {pdf ? pdf.filename : "Upload your study material"}
          </strong>

          <p>
            {pdf
              ? `${pdf.pages} pages · ${pdf.total_chunks} chunks indexed`
              : "Drag & drop your PDF here or click to browse"}
          </p>
        </div>

        <button
          className="primary"
          disabled={busy}
          onClick={(e) => {
            e.stopPropagation();
            ref.current?.click();
          }}
        >
          {busy ? "Uploading..." : pdf ? "Change PDF" : "Choose PDF"}
          <ArrowRight size={16} />
        </button>
      </div>

      <div className="section">
        <div>
          <small>SMART TOOLS</small>
          <h2>What would you like to do?</h2>
        </div>
      </div>

      <div className="tools">
        {tools.map(({ id, title, text, icon: Icon, tone }) => (
          <button
            className={`tool ${tone}`}
            key={id}
            onClick={() => setActive(id)}
          >
            <span>
              <Icon />
            </span>

            <div>
              <strong>{title}</strong>
              <p>{text}</p>
            </div>

            <ArrowRight className="arr" size={17} />
          </button>
        ))}
      </div>
    </div>
  );
}

// COMMON TOOL LAYOUT
function Tool({ title, sub, icon: Icon, children }) {
  return (
    <div className="fade tool-page">
      <div className="title">
        <span>
          <Icon />
        </span>

        <div>
          <small>MENTARA TOOL</small>
          <h1>{title}</h1>
          <p>{sub}</p>
        </div>
      </div>

      {children}
    </div>
  );
}

// EMPTY STATE
function Empty({ go }) {
  return (
    <div className="empty">
      <span>
        <UploadCloud />
      </span>

      <h2>Upload a PDF first</h2>

      <p>
        Mentara needs your study material before it can generate
        personalized learning content.
      </p>

      <button className="primary" onClick={go}>
        Upload PDF <ArrowRight size={16} />
      </button>
    </div>
  );
}

// UPLOAD
function Upload({ pdf, upload, busy }) {
  const ref = useRef();

  return (
    <Tool
      title="Upload PDF"
      sub="Add your study material to get started"
      icon={UploadCloud}
    >
      <div
        className="drop"
        onClick={() => ref.current?.click()}
      >
        <input
          ref={ref}
          hidden
          type="file"
          accept=".pdf"
          onChange={(e) => upload(e.target.files?.[0])}
        />

        <span>
          <FileText />
        </span>

        <h2>{pdf ? pdf.filename : "Drop your PDF here"}</h2>

        <p>
          {pdf
            ? `${pdf.pages} pages · ${pdf.total_chunks} chunks indexed`
            : "or click to browse from your device"}
        </p>

        <button className="primary" disabled={busy}>
          {busy
            ? "Uploading..."
            : pdf
            ? "Choose another PDF"
            : "Choose PDF"}
          <ArrowRight size={16} />
        </button>
      </div>

      {pdf && (
        <div className="success">
          <Check />

          <div>
            <b>PDF uploaded successfully!</b>
            <p>
              {pdf.filename} · {pdf.pages} pages · {pdf.total_chunks} chunks indexed
            </p>
          </div>
        </div>
      )}
    </Tool>
  );
}

// ASK AI
function Ask({ pdf, notify, setActive }) {
  const [q, setQ] = useState("");
  const [msgs, setMsgs] = useState([]);
  const [load, setLoad] = useState(false);

  const send = async () => {
    if (!pdf) {
      return notify("error", "Upload a PDF before asking Mentara.");
    }

    if (!q.trim() || load) return;

    const question = q.trim();
    setQ("");

    setMsgs((messages) => [
      ...messages,
      { r: "u", t: question }
    ]);

    setLoad(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/ask?question=${encodeURIComponent(question)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw Error(data.detail || "AI request failed.");
      }

      setMsgs((messages) => [
        ...messages,
        {
          r: "a",
          t: data.answer,
          s: data.sources
        }
      ]);
    } catch (error) {
      notify("error", error.message);
    } finally {
      setLoad(false);
    }
  };

  return (
    <Tool
      title="Ask Mentara"
      sub="Ask questions grounded in your uploaded material"
      icon={MessageCircle}
    >
      {!pdf ? (
        <Empty go={() => setActive("upload")} />
      ) : (
        <div className="chat">
          <div className="chat-head">
            <span>
              <Sparkles />
            </span>

            <div>
              <b>Ask anything about your PDF</b>
              <p>
                Mentara answers from your uploaded material
                and shows source pages.
              </p>
            </div>
          </div>

          <div className="messages">
            {!msgs.length && (
              <div className="suggest">
                {[
                  "Explain supervised learning",
                  "Give me the key concepts",
                  "What should I remember for an exam?"
                ].map((question) => (
                  <button
                    key={question}
                    onClick={() => setQ(question)}
                  >
                    {question}
                    <ArrowRight size={14} />
                  </button>
                ))}
              </div>
            )}

            {msgs.map((message, index) => (
              <div
                className={`msg ${message.r}`}
                key={index}
              >
                <span>
                  {message.r === "a" ? (
                    <Sparkles size={14} />
                  ) : (
                    "U"
                  )}
                </span>

                <div>
                  <p>{message.t}</p>

                  {message.s && (
                    <div className="sources">
                      {message.s.map((source, j) => (
                        <small key={j}>
                          <FileText size={12} />
                          {source.filename} · Page {source.page}
                        </small>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {load && (
              <div className="msg a">
                <span>
                  <Sparkles size={14} />
                </span>

                <div className="typing">● ● ●</div>
              </div>
            )}
          </div>

          <div className="chat-input">
            <Paperclip size={17} />

            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask something about your study material..."
            />

            <button onClick={send}>
              <Send size={17} />
            </button>
          </div>
        </div>
      )}
    </Tool>
  );
}

// AI NOTES
function Notes({ pdf, notify, setActive }) {
  const [n, setN] = useState("");
  const [load, setLoad] = useState(false);

  const gen = async () => {
    if (!pdf) {
      return notify("error", "Upload a PDF before generating notes.");
    }

    setLoad(true);

    try {
      const response = await fetch(`${API_BASE_URL}/generate-notes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          filename: pdf.filename
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw Error(data.detail || "Could not generate notes.");
      }

      setN(data.notes);
    } catch (error) {
      notify("error", error.message);
    } finally {
      setLoad(false);
    }
  };

  return (
    <Tool
      title="AI Generated Notes"
      sub="Turn your study material into concise, exam-oriented notes"
      icon={FileText}
    >
      {!pdf ? (
        <Empty go={() => setActive("upload")} />
      ) : (
        <div className="notes">
          <div className="strip">
            <div>
              <b>{pdf.filename}</b>
              <small>{pdf.pages} pages indexed</small>
            </div>

            <button
              className="primary"
              onClick={gen}
              disabled={load}
            >
              {load
                ? "Generating..."
                : n
                ? "Regenerate Notes"
                : "Generate Notes"}
              <Sparkles size={16} />
            </button>
          </div>

          {!n ? (
            <div className="empty">
              <span>
                <FileText />
              </span>

              <h2>Ready to create your notes</h2>

              <p>
                Mentara will organize definitions, key concepts,
                explanations and exam points.
              </p>
            </div>
          ) : (
            <div className="note-body">
              <div className="ai-label">
                <Sparkles size={14} />
                AI-generated from your material
              </div>

              {n.split("\n").map((line, index) =>
                line.trim() ? (
                  <p
                    key={index}
                    className={
                      /^[#*-]/.test(line)
                        ? "note-line strong"
                        : "note-line"
                    }
                  >
                    {line
                      .replace(/^#+\s*/, "")
                      .replace(/^[-*]\s*/, "• ")}
                  </p>
                ) : (
                  <br key={index} />
                )
              )}
            </div>
          )}
        </div>
      )}
    </Tool>
  );
}

// MCQS AND QUIZ
function Quiz({ pdf, notify, setActive }) {
  const [m, setM] = useState([]);
  const [a, setA] = useState([]);
  const [i, setI] = useState(0);
  const [res, setRes] = useState(null);
  const [load, setLoad] = useState(false);

  const gen = async () => {
    if (!pdf) {
      return notify("error", "Upload a PDF before generating a quiz.");
    }

    setLoad(true);

    try {
      const response = await fetch(`${API_BASE_URL}/generate-mcqs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          filename: pdf.filename,
          number: 5
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw Error(data.detail || "Could not generate MCQs.");
      }

      setM(data.mcqs || []);
      setA(Array(data.mcqs?.length || 0).fill(null));
      setI(0);
    } catch (error) {
      notify("error", error.message);
    } finally {
      setLoad(false);
    }
  };

  const submit = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/submit-quiz`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          correct_answers: m.map((question) => question.answer),
          user_answers: a.map((answer) => answer || "")
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw Error(data.detail || "Could not submit quiz.");
      }

      setRes(data);
    } catch (error) {
      notify("error", error.message);
    }
  };

  if (!pdf) {
    return (
      <Tool
        title="MCQs & Quiz"
        sub="Practice with AI-generated questions"
        icon={Brain}
      >
        <Empty go={() => setActive("upload")} />
      </Tool>
    );
  }

  if (res) {
    return (
      <Tool
        title="Quiz Complete"
        sub="Here's how you performed"
        icon={Brain}
      >
        <div className="result">
          <div className="trophy">🏆</div>

          <small>QUIZ COMPLETE</small>

          <h2>Great work!</h2>

          <div className="score">
            <b>
              {res.score}/{res.total_questions}
            </b>

            <span>{res.percentage}%</span>
          </div>

          <p>Keep learning and building your skills.</p>

          <button
            className="secondary"
            onClick={() => {
              setRes(null);
              setM([]);
            }}
          >
            <RefreshCw size={16} />
            Try Again
          </button>
        </div>
      </Tool>
    );
  }

  return (
    <Tool
      title="MCQs & Quiz"
      sub="Practice with AI-generated questions from your study material"
      icon={Brain}
    >
      {!m.length ? (
        <div className="quiz-start">
          <span>
            <Target />
          </span>

          <small>PERSONALIZED PRACTICE</small>

          <h2>Ready to test yourself?</h2>

          <p>
            Generate five questions from <b>{pdf.filename}</b>.
          </p>

          <button
            className="primary"
            onClick={gen}
            disabled={load}
          >
            {load ? "Generating MCQs..." : "Generate MCQs"}
            <Sparkles size={16} />
          </button>
        </div>
      ) : (
        <div className="quiz-card">
          <div className="quiz-meta">
            Question {i + 1} of {m.length}

            <span>
              {Math.round(((i + 1) / m.length) * 100)}%
            </span>
          </div>

          <div className="bar">
            <i
              style={{
                width: `${((i + 1) / m.length) * 100}%`
              }}
            />
          </div>

          <h2>{m[i].question}</h2>

          <div className="options">
            {m[i].options.map((option, j) => {
              const letter = String.fromCharCode(65 + j);

              return (
                <button
                  className={
                    a[i] === letter
                      ? "option selected"
                      : "option"
                  }
                  key={letter}
                  onClick={() =>
                    setA((answers) =>
                      answers.map((answer, index) =>
                        index === i ? letter : answer
                      )
                    )
                  }
                >
                  <span>{letter}</span>
                  {option}

                  {a[i] === letter && <Check size={16} />}
                </button>
              );
            })}
          </div>

          <div className="quiz-actions">
            {i > 0 && (
              <button
                className="secondary"
                onClick={() => setI(i - 1)}
              >
                <ChevronLeft size={16} />
                Previous
              </button>
            )}

            <i />

            {i < m.length - 1 ? (
              <button
                className="primary"
                disabled={!a[i]}
                onClick={() => setI(i + 1)}
              >
                Next <ChevronRight size={16} />
              </button>
            ) : (
              <button
                className="primary"
                disabled={!a[i]}
                onClick={submit}
              >
                Finish <Check size={16} />
              </button>
            )}
          </div>
        </div>
      )}
    </Tool>
  );
}

// RENDER APP
createRoot(document.getElementById("root")).render(<App />);
