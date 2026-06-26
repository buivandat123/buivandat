import React, { useEffect, useState } from "https://esm.sh/react@18.3.1"
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client"
import htm from "https://esm.sh/htm@3.1.1"

const html = htm.bind(React.createElement)

const getReq = async (url) => {
  const r = await fetch(url, { credentials: "include" })
  const j = await r.json().catch(() => ({}))
  if (!r.ok || !j.ok) throw new Error(j.error || `HTTP ${r.status}`)
  return j
}

const postReq = async (url, body) => {
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

function DashboardApp() {
  const [loading, setLoading] = useState(false)
  const [me, setMe] = useState({ account: "", username: "", botIntId: "", isAdmin: false })
  const [bot, setBot] = useState({ prefix: "-" })
  const [adminBots, setAdminBots] = useState([])
  const [adminSummary, setAdminSummary] = useState({ activeClusters: 0, totalClusters: 0 })
  const [newPrefix, setNewPrefix] = useState("")
  const [outText, setOutText] = useState("Ready")
  const [toasts, setToasts] = useState([])

  const pushToast = (type, text) => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, type, text }])
    setTimeout(() => setToasts(prev => prev.filter(x => x.id !== id)), 3000)
  }

  const print = (text, ok = true) => {
    setOutText(text)
    pushToast(ok ? "success" : "error", text)
  }

  const loadAdminOverview = async () => {
    try {
      const j = await getReq("/api/admin/overview")
      setAdminBots(j.clusters || [])
      setAdminSummary(j.summary || {})
    } catch (e) {
      print(e.message, false)
    }
  }

  const botAction = async (botIntId, action) => {
    try {
      await postReq("/api/admin/bot/action", { botIntId, action })
      print(`Bot ${action} thành công!`)
      await loadAdminOverview()
    } catch (e) {
      print(e.message, false)
    }
  }

  useEffect(() => {
    ;(async () => {
      try {
        setLoading(true)
        const meData = await getReq("/api/auth/me")
        if (!meData.ok) {
          location.href = "/"
          return
        }
        setMe({
          account: meData.account || "",
          username: meData.username || "",
          botIntId: meData.botIntId || "",
          isAdmin: !!meData.isAdmin,
        })

        if (meData.isAdmin) {
          await loadAdminOverview()
        } else {
          const info = await getReq("/api/bot/info")
          if (info && info.ok) {
            setBot({ prefix: info.bot?.prefix || "-" })
          }
        }
        print("Ready")
      } catch (e) {
        print(e.message, false)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const onLogout = async () => {
    await postReq("/api/auth/logout", {})
    location.href = "/"
  }

  const onChangePrefix = async () => {
    if (!newPrefix.trim()) {
      print("Vui lòng nhập prefix mới", false)
      return
    }
    try {
      await postReq("/api/bot/prefix", { newPrefix: newPrefix.trim() })
      setBot({ prefix: newPrefix.trim() })
      setNewPrefix("")
      print("Đã đổi prefix thành công!")
    } catch (e) {
      print(e.message, false)
    }
  }

  return html`
    <div class="DashLayout">
      <div class="ToastStack">
        ${toasts.map(toast => html`
          <div key=${toast.id} class=${`ToastItem ${toast.type}`}>
            ${toast.text}
          </div>
        `)}
      </div>

      <header class="DashHeader">
        <div class="DashLogo"><i class="fa-solid fa-bug"></i> eBug Bot</div>
        <div class="DashUser">
          <span>${me.username || me.account || "User"}</span>
          <button class="Btn Danger" onClick=${onLogout}>Logout</button>
        </div>
      </header>

      <main class="DashMain">
        ${me.isAdmin ? html`
          <section class="DashSection">
            <h2>Admin Dashboard</h2>
            <div class="Stats">
              <div class="StatCard">
                <div class="StatValue">${adminSummary.totalClusters || 0}</div>
                <div class="StatLabel">Total Bots</div>
              </div>
              <div class="StatCard">
                <div class="StatValue">${adminSummary.activeClusters || 0}</div>
                <div class="StatLabel">Running</div>
              </div>
            </div>
            <div class="BotList">
              ${adminBots.map(b => html`
                <div class="BotItem" key=${b.botIntId}>
                  <div class="BotInfo">
                    <strong>${b.username || b.botAccount || "Unknown"}</strong>
                    <span class=${`Badge ${b.status ? "success" : "danger"}`}>
                      ${b.status ? "Running" : "Stopped"}
                    </span>
                    <span>Prefix: ${b.prefix || "?"}</span>
                  </div>
                  <div class="BotActions">
                    <button class="Btn Success" onClick=${() => botAction(b.botIntId, "start")}>Start</button>
                    <button class="Btn Danger" onClick=${() => botAction(b.botIntId, "stop")}>Stop</button>
                    <button class="Btn Warn" onClick=${() => botAction(b.botIntId, "restart")}>Restart</button>
                  </div>
                </div>
              `)}
            </div>
          </section>
        ` : html`
          <section class="DashSection">
            <h2>Bot Controls</h2>
            <div class="Stats">
              <div class="StatCard">
                <div class="StatValue">${bot.prefix || "-"}</div>
                <div class="StatLabel">Prefix</div>
              </div>
              <div class="StatCard">
                <div class="StatValue">${me.botIntId || "-"}</div>
                <div class="StatLabel">Bot ID</div>
              </div>
            </div>
            <div class="ControlGroup">
              <div class="ControlItem">
                <label>Change Prefix</label>
                <input value=${newPrefix} onInput=${(e) => setNewPrefix(e.target.value)} placeholder="New prefix" />
                <button class="Btn Primary" onClick=${onChangePrefix}>Update</button>
              </div>
            </div>
          </section>
        `}
      </main>
    </div>
  `
}

const node = document.getElementById("root")
if (node) createRoot(node).render(html`<${DashboardApp} />`)
