import React, { useEffect, useState } from "https://esm.sh/react@18.3.1"
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client"
import htm from "https://esm.sh/htm@3.1.1"

const html = htm.bind(React.createElement)

const ts = () => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, "0")
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

const post = async (url, body) => {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body || {}),
  })
  const j = await r.json().catch(() => ({}))
  if (!r.ok || !j.ok) throw new Error(j.error || `HTTP ${r.status}`)
  return j
}

function LoginApp() {
  const [account, setAccount] = useState("")
  const [password, setPassword] = useState("")
  const [status, setStatus] = useState({ ok: true, text: "Ready" })
  const [loading, setLoading] = useState(false)
  const [now, setNow] = useState(`${ts()} - OK`)

  useEffect(() => {
    const id = setInterval(() => {
      setNow(`${ts()} - ${status.ok ? "OK" : "ERR"}`)
    }, 500)
    return () => clearInterval(id)
  }, [status.ok])

  const print = (v, ok = true) => {
    const text = typeof v === "string" ? v : JSON.stringify(v, null, 2)
    setStatus({ ok, text })
  }

  const onLogin = async () => {
    try {
      setLoading(true)
      print("Loading...", true)
      const j = await post("/api/auth/login", {
        account: account.trim(),
        password: password.trim(),
      })
      print(j, true)
      location.href = "/dashboard"
    } catch (e) {
      print({ ok: false, error: e.message }, false)
    } finally {
      setLoading(false)
    }
  }

  return html`
    <div class="LoginBg"></div>
    <div class="LoginCard">
      <div class="LoginCardTop">
        <div class="LoginTopTitle">Authentication</div>
      </div>
      <div class="LoginHeader">
        <div class="LoginAvatar">
          <div class="LoginAvatarCircle">
            <svg width="58" height="58" viewBox="0 0 24 24" fill="none">
              <path d="M12 12a4.2 4.2 0 1 0 0-8.4A4.2 4.2 0 0 0 12 12Z" fill="rgba(13,78,78,.35)"></path>
              <path d="M4.5 20.4c1.8-4.2 13.2-4.2 15 0" stroke="rgba(13,78,78,.45)" stroke-width="2" stroke-linecap="round"></path>
            </svg>
          </div>
        </div>
        <div class="LoginHeadText">
          <div class="LoginTitle">Sign in</div>
          <div class="LoginSub">Use your bot account credentials.</div>
        </div>
      </div>
      <div class="LoginForm">
        <div class="LoginField">
          <div class="LoginIcon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M4 6.8A2.8 2.8 0 0 1 6.8 4h10.4A2.8 2.8 0 0 1 20 6.8v10.4A2.8 2.8 0 0 1 17.2 20H6.8A2.8 2.8 0 0 1 4 17.2V6.8Z" stroke="rgba(13,78,78,.55)" stroke-width="1.6"></path>
              <path d="M6.4 7.2 12 11.2l5.6-4" stroke="rgba(13,78,78,.55)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </div>
          <input value=${account} onInput=${(e) => setAccount(e.target.value)} placeholder="Bot Account" />
          <div class="LoginLine"></div>
        </div>
        <div class="LoginField">
          <div class="LoginIcon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M7.2 11V8.4A4.8 4.8 0 0 1 12 3.6a4.8 4.8 0 0 1 4.8 4.8V11" stroke="rgba(13,78,78,.55)" stroke-width="1.6" stroke-linecap="round"></path>
              <path d="M6.4 11h11.2A2.4 2.4 0 0 1 20 13.4v5.2A2.4 2.4 0 0 1 17.6 21H6.4A2.4 2.4 0 0 1 4 18.6v-5.2A2.4 2.4 0 0 1 6.4 11Z" stroke="rgba(13,78,78,.55)" stroke-width="1.6"></path>
            </svg>
          </div>
          <input value=${password} onInput=${(e) => setPassword(e.target.value)} placeholder="Password" type="password" />
          <div class="LoginLine"></div>
        </div>
        <button class="LoginBtn" onClick=${onLogin} disabled=${loading}>${loading ? "Loading..." : "LOGIN"}</button>
        <div class="LoginConsoleWrap">
          <div class="LoginConsoleTop">
            <div class="LoginConsoleSub">${now}</div>
            <div class="LoginPill">${status.ok ? "OK" : "ERR"}</div>
          </div>
          <pre class="LoginConsole">${status.text}</pre>
        </div>
      </div>
    </div>
  `
}

const node = document.getElementById("root")
if (node) createRoot(node).render(html`<${LoginApp} />`)
