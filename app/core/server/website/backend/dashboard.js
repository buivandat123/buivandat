import React, { useEffect, useRef, useState } from "https://esm.sh/react@18.3.1"
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client"
import htm from "https://esm.sh/htm@3.1.1"

const html = htm.bind(React.createElement)
const MAX_LOG_CHARS = 220000
const THEME_KEY = "ebug.dashboard.theme"

const setupAntiDebugGuard = () => {
  const targetUrl = "https://google.com/"
  const isMobile = () => (
    ("ontouchstart" in window) ||
    navigator.maxTouchPoints > 0 ||
    /Android|iPhone|iPad|iPod|Mobi/i.test(navigator.userAgent)
  )

  if (isMobile()) return () => {}

  const hit = () => {
    if (location.href.startsWith(targetUrl)) return
    location.replace(targetUrl)
  }

  const devtoolsHeuristic = () => {
    const ow = window.outerWidth || 0
    const iw = window.innerWidth || 0
    const oh = window.outerHeight || 0
    const ih = window.innerHeight || 0
    if (!ow || !oh || !iw || !ih) return false
    const w = Math.max(0, ow - iw)
    const h = Math.max(0, oh - ih)
    return w > 160 || h > 160
  }

  const debuggerTrip = () => {
    const t = performance.now()
    debugger
    return performance.now() - t > 80
  }

  const check = () => {
    if (devtoolsHeuristic() || debuggerTrip()) hit()
  }

  document.addEventListener("visibilitychange", check, true)
  window.addEventListener("focus", check, true)
  window.addEventListener("blur", check, true)
  window.addEventListener("resize", check, true)
  const timer = setInterval(check, 500)
  setTimeout(check, 0)

  return () => {
    clearInterval(timer)
    document.removeEventListener("visibilitychange", check, true)
    window.removeEventListener("focus", check, true)
    window.removeEventListener("blur", check, true)
    window.removeEventListener("resize", check, true)
  }
}

const ts = () => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, "0")
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

const cutText = (s, n = 12) => {
  const v = String(s ?? "")
  return v.length > n ? `${v.slice(0, n)}...` : v
}

const jsonText = (v) => (typeof v === "string" ? v : JSON.stringify(v, null, 2))

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

const logFmt = (x) => {
  const head = `[${x.id}] [${x.created_at}] [${x.level}] [${x.prefix || ""}] [${x.chat_type || ""}]`
  const who = `${x.user_name || ""}${x.user_id ? ` - ${x.user_id}` : ""}`
  const grp = x.group_name ? ` | ${x.group_name}${x.group_id ? ` - ${x.group_id}` : ""}` : ""
  const ref = x.ref ? `\n→ ${x.ref}` : ""
  const body = String(x.content || "")
  return `${head} ${who}${grp}\n${body}${ref}\n`
}

function DashboardApp() {
  const [ui, setUi] = useState({ ok: true, text: "Ready" })
  const [outText, setOutText] = useState("Waiting...")
  const [runtime, setRuntime] = useState(`Online ${ts()}`)
  const [loading, setLoading] = useState({ on: false, text: "Processing..." })
  const [theme, setTheme] = useState("light")
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [tab, setTab] = useState("eBot")

  const [me, setMe] = useState({ account: "", username: "", botIntId: "", isAdmin: false })
  const [bot, setBot] = useState({ prefix: "-" })
  const [avatarUrl, setAvatarUrl] = useState("")

  const [newPrefix, setNewPrefix] = useState("")
  const [newUsername, setNewUsername] = useState("")
  const [newPassword, setNewPassword] = useState("")

  const [adminBots, setAdminBots] = useState([])
  const [adminSummary, setAdminSummary] = useState({ activeClusters: 0, totalClusters: 0, stoppedClusters: 0 })
  const [adminBotId, setAdminBotId] = useState("")
  const [adminTimeExpr, setAdminTimeExpr] = useState("")

  const [logKind, setLogKind] = useState("message")
  const [logQ, setLogQ] = useState("")
  const [logLimit, setLogLimit] = useState("80")
  const [logOut, setLogOut] = useState("Waiting...")
  const [logSub, setLogSub] = useState("-")

  const [toasts, setToasts] = useState([])
  const [confirmState, setConfirmState] = useState({ open: false, text: "Bạn có chắc chắn?", resolve: null })

  const loadingCounterRef = useRef(0)
  const loggerRef = useRef({ lastMaxId: 0, lines: 0 })

  const pushToast = (type, text, ttl = 3200) => {
    const id = `${Date.now()}-${Math.random()}`
    setToasts((prev) => [...prev, { id, type, text: String(text || "") }])
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((x) => x.id !== id))
    }, ttl)
  }

  const print = (text, ok = true, toast = false) => {
    const nextText = String(text || "")
    setUi({ ok, text: nextText })
    setOutText(nextText)
    if (toast) pushToast(ok ? "success" : "error", nextText)
  }

  useEffect(() => {
    const off = setupAntiDebugGuard()
    return () => off()
  }, [])

  useEffect(() => {
    const id = setInterval(() => {
      setRuntime(`${ui.ok ? "Online" : "Error"} ${ts()}`)
    }, 500)
    return () => clearInterval(id)
  }, [ui.ok])

  useEffect(() => {
    document.body.setAttribute("data-theme", theme)
  }, [theme])

  const setLoadingState = (on, text = "Processing...") => {
    loadingCounterRef.current = Math.max(0, loadingCounterRef.current + (on ? 1 : -1))
    setLoading({ on: loadingCounterRef.current > 0, text })
  }

  const wrap = async (fn, okText = "OK") => {
    try {
      setLoadingState(true, "Processing request...")
      const j = await fn()
      print(okText, true, true)
      return j
    } catch (e) {
      print(e.message, false, true)
      throw e
    } finally {
      setLoadingState(false)
    }
  }

  const wrapJson = async (fn, okText = "OK") => {
    try {
      setLoadingState(true, "Loading data...")
      const j = await fn()
      setUi({ ok: true, text: okText })
      setOutText(jsonText(j))
      return j
    } catch (e) {
      print(e.message, false, true)
      throw e
    } finally {
      setLoadingState(false)
    }
  }

  const askConfirm = (text = "Bạn có chắc chắn?") => new Promise((resolve) => {
    setConfirmState({ open: true, text, resolve })
  })

  const closeConfirm = (ok) => {
    if (confirmState.resolve) confirmState.resolve(ok)
    setConfirmState({ open: false, text: "Bạn có chắc chắn?", resolve: null })
  }

  const loadAdminOverview = async () => {
    const j = await wrapJson(() => getReq("/api/admin/overview"), "Admin overview loaded")
    const clusters = Array.isArray(j.clusters) ? j.clusters : []
    const summary = j.summary || {}
    setAdminBots(clusters)
    setAdminSummary({
      activeClusters: Number(summary.activeClusters || 0),
      totalClusters: Number(summary.totalClusters || 0),
      stoppedClusters: Number(summary.stoppedClusters || 0),
    })
    setAdminBotId((prev) => {
      if (prev && clusters.some((x) => String(x.botIntId || "") === prev)) return prev
      const first = clusters[0]
      return first ? String(first.botIntId || "") : ""
    })
  }

  const currentAdminBotId = () => {
    if (adminBotId) return adminBotId
    const one = adminBots[0]
    return one ? String(one.botIntId || "") : ""
  }

  const adminBotAction = async (action, botIntId = "", timeExpr = "") => {
    const bid = String(botIntId || currentAdminBotId()).trim()
    if (!bid) {
      print("Missing bot selection", false, true)
      return
    }
    const payload = { action, botIntId: bid }
    if (timeExpr) payload.timeExpr = timeExpr
    await wrap(() => postReq("/api/admin/bot/action", payload), `Admin action: ${action}`)
    await loadAdminOverview()
  }

  const resetLogger = () => {
    loggerRef.current.lastMaxId = 0
    loggerRef.current.lines = 0
    setLogOut("Waiting...")
    setLogSub("-")
  }

  const buildLogQuery = () => {
    const kind = (logKind || "message").trim()
    const q = logQ.trim()
    const limit = Math.min(Math.max(parseInt(logLimit || "80", 10) || 80, 10), 200)
    const qs = new URLSearchParams()
    qs.set("kind", kind)
    qs.set("limit", String(limit))
    if (q) qs.set("q", q)
    return qs.toString()
  }

  const loggerPull = async () => {
    const j = await getReq(`/api/logger/list?${buildLogQuery()}`).catch(() => null)
    if (!j || !j.ok) return
    const items = Array.isArray(j.items) ? j.items : []
    if (!items.length) return

    let maxId = loggerRef.current.lastMaxId || 0
    for (const it of items) {
      const id = Number(it && it.id) || 0
      if (id > maxId) maxId = id
    }

    const fresh = items.filter((it) => (Number(it && it.id) || 0) > (loggerRef.current.lastMaxId || 0))
    if (!fresh.length) {
      loggerRef.current.lastMaxId = maxId
      return
    }

    fresh.sort((a, b) => (Number(a.id) || 0) - (Number(b.id) || 0))
    const chunk = fresh.map(logFmt).join("\n")

    loggerRef.current.lastMaxId = maxId
    loggerRef.current.lines += fresh.length

    setLogSub(`${ts()} - +${fresh.length} - total ${loggerRef.current.lines}`)
    setLogOut((prev) => {
      const cur = prev === "Waiting..." ? "" : prev
      let next = cur ? `${cur}\n${chunk}` : chunk
      if (next.length > MAX_LOG_CHARS) next = next.slice(next.length - MAX_LOG_CHARS)
      return next
    })
  }

  useEffect(() => {
    const readTheme = localStorage.getItem(THEME_KEY)
    setTheme(readTheme === "dark" ? "dark" : "light")

    let mounted = true
    ;(async () => {
      try {
        setLoadingState(true, "Booting dashboard...")
        const meData = await getReq("/api/auth/me").catch(() => ({ ok: false }))
        if (!meData.ok) {
          location.href = "/"
          return
        }

        if (!mounted) return
        const nextMe = {
          account: String(meData.account || ""),
          username: String(meData.username || ""),
          botIntId: String(meData.botIntId || ""),
          isAdmin: !!meData.isAdmin,
        }
        setMe(nextMe)

        if (nextMe.isAdmin) {
          setBot({ prefix: "admin" })
          setTab("Admin")
          await loadAdminOverview()
        } else {
          setTab("eBot")
          const av = await getReq("/api/bot/getavatar").catch(() => null)
          if (av && av.ok && mounted) setAvatarUrl(String(av.avatarUrl || ""))

          const info = await getReq("/api/bot/info").catch(() => null)
          if (info && info.ok && mounted) {
            setBot({ prefix: String(info.bot?.prefix || "-") })
            if (!nextMe.username && info.bot?.username) {
              setMe((prev) => ({ ...prev, username: String(info.bot.username || "") }))
            }
          }
        }

        print("Ready", true)
      } catch (e) {
        print(e.message, false, true)
      } finally {
        setLoadingState(false)
      }
    })()

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (tab !== "Logger") return
    const id = setInterval(() => {
      loggerPull()
    }, 1000)
    loggerPull()
    return () => clearInterval(id)
  }, [tab, logKind, logQ, logLimit])

  const setTabAndClose = (nextTab) => {
    setTab(nextTab)
    setSidebarOpen(false)
  }

  const meLine = me.account ? `${me.username || ""} - ${me.account}` : "-"
  const botIdText = me.isAdmin ? "admin" : cutText(me.botIntId || "", 6)
  const botTitle = me.username || me.account || "eBot"

  const onThemeToggle = () => {
    const next = theme === "dark" ? "light" : "dark"
    localStorage.setItem(THEME_KEY, next)
    setTheme(next)
  }

  const loadBotInfo = async () => {
    const j = await getReq("/api/bot/info").catch(() => null)
    if (j && j.ok) setBot({ prefix: String(j.bot?.prefix || "-") })
  }

  return html`
    <>
      <div class="Bg"></div>

      <div class=${`AppLoading ${loading.on ? "" : "Hidden"}`} aria-hidden=${loading.on ? "false" : "true"}>
        <div class="LoaderSpinner"></div>
        <div class="LoaderText">${loading.text}</div>
      </div>

      <div class="ToastStack">
        ${toasts.map((toast) => html`
          <div key=${toast.id} class=${`ToastItem ${toast.type}`}>
            <i class=${`fa-solid ${toast.type === "success" ? "fa-circle-check" : toast.type === "error" ? "fa-circle-xmark" : "fa-circle-info"}`}></i>
            <span>${toast.text}</span>
          </div>
        `)}
      </div>

      <div class=${`ConfirmOverlay ${confirmState.open ? "" : "Hidden"}`} onClick=${(e) => {
        if (e.target.classList.contains("ConfirmOverlay")) closeConfirm(false)
      }}>
        <div class="ConfirmBox">
          <div class="ConfirmTitle">Xác nhận thao tác</div>
          <div class="ConfirmText">${confirmState.text}</div>
          <div class="ConfirmActions">
            <button class="Btn Ghost2" onClick=${() => closeConfirm(false)}>Hủy</button>
            <button class="Btn Danger" onClick=${() => closeConfirm(true)}>Xóa</button>
          </div>
        </div>
      </div>

      <header class="MobileTopbar">
        <button class="TopbarMenuBtn" onClick=${() => setSidebarOpen(true)}><i class="fa-solid fa-bars"></i></button>
        <div class="TopbarLogo"><i class="fa-solid fa-bug"></i> eBug <strong>Bot</strong></div>
        <button class="TopbarAction" onClick=${onThemeToggle} title="Theme">
          <i class=${`fa-solid ${theme === "dark" ? "fa-sun" : "fa-moon"}`}></i>
        </button>
      </header>

      <div class="FLayout">
        <div class=${`SidebarOverlay ${sidebarOpen ? "open" : ""}`} onClick=${() => setSidebarOpen(false)}></div>

        <aside class=${`FSidebar ${sidebarOpen ? "open" : ""}`}>
          <div class="FSidebarLogo">
            <div class="FSidebarLogoMark"><i class="fa-solid fa-bug"></i></div>
            <span>eBug <strong>Manager</strong></span>
            <button class="FSidebarClose" onClick=${() => setSidebarOpen(false)}><i class="fa-solid fa-xmark"></i></button>
          </div>

          <nav class="FSidebarNav">
            <div class="FSidebarSection">Tổng quan</div>
            ${me.isAdmin ? null : html`
              <button class=${`FSidebarItem ${tab === "eBot" ? "active" : ""}`} onClick=${() => setTabAndClose("eBot")}>
                <i class="fa-solid fa-house"></i> Bot Manager
              </button>
            `}

            <button class=${`FSidebarItem ${tab === "Admin" ? "active" : ""} ${me.isAdmin ? "" : "Hidden"}`} onClick=${() => me.isAdmin && setTabAndClose("Admin")}>
              <i class="fa-solid fa-shield-halved"></i> Admin
            </button>

            ${me.isAdmin ? null : html`
              <div class="FSidebarSection">Cài đặt</div>
              <button class=${`FSidebarItem ${tab === "Account" ? "active" : ""}`} onClick=${() => setTabAndClose("Account")}>
                <i class="fa-solid fa-user-gear"></i> Account
              </button>
              <button class=${`FSidebarItem ${tab === "Logger" ? "active" : ""}`} onClick=${() => setTabAndClose("Logger")}>
                <i class="fa-solid fa-scroll"></i> Logger
              </button>
            `}
          </nav>

          <div class="FSidebarFooter">
            <div class="FSidebarUser">
              <div class="FSidebarAvatar">${(me.username || me.account || "E").slice(0, 1).toUpperCase()}</div>
              <div>
                <div class="FSidebarUserName">${me.username || me.account || "eBug"}</div>
                <div class="FSidebarUserSub">${me.account || "-"}</div>
              </div>
            </div>
            <button
              class="Btn Ghost"
              onClick=${async () => {
                try {
                  await wrap(() => postReq("/api/auth/logout", {}), "Logged out")
                } finally {
                  location.href = "/"
                }
              }}
            >Logout</button>
          </div>
        </aside>

        <main class="FMain">
          <section class="FTopStats">
            <article class="FStatCard">
              <div class="FStatLabel">User</div>
              <div class="FStatValue">${meLine}</div>
            </article>
            <article class="FStatCard">
              <div class="FStatLabel">Runtime</div>
              <div class="FStatValue">${runtime}</div>
            </article>
            <article class="FStatCard">
              <div class="FStatLabel">Bot ID</div>
              <div class="FStatValue">${botIdText || "-"}</div>
            </article>
            <article class="FStatCard Actions">
              <div class="FStatLabel">Theme</div>
              <button class="Btn Ghost" onClick=${onThemeToggle}>${theme === "dark" ? "Light" : "Dark"}</button>
            </article>
          </section>

          ${me.isAdmin ? null : html`
            <section class="TopSummary UserOnly">
              <article class="StatCard">
                <div class="StatCardTitle">Prefix</div>
                <div class="StatCardValue">${bot.prefix || "-"}</div>
              </article>
              <article class="StatCard AvatarStat">
                <div>
                  <div class="StatCardTitle">Bot</div>
                  <div class="StatCardValue">${botTitle}</div>
                </div>
                <div class="BotAvatar">
                  ${avatarUrl ? html`<img src=${avatarUrl} alt="avatar" />` : null}
                </div>
              </article>
            </section>
          `}

          <section class="DashGrid FContentGrid">
            <div class="Col">
              <section class=${`Panel PanelTab ${tab === "Admin" ? "is-active" : "Hidden"} ${me.isAdmin ? "" : "AdminOnly"}`}>
                <div class="PanelHead">
                  <div>
                    <h2 class="H2">eBug Admin</h2>
                    <div class="SubLine">Bảng điều khiển cụm theo thời gian thực.</div>
                  </div>
                  <button class="Btn" onClick=${loadAdminOverview}>Refresh</button>
                </div>

                <section class="AdminProfileCard">
                  <div class="AdminShield"><i class="fa-solid fa-shield-virus"></i></div>
                  <div class="AdminTitle">Admin</div>
                  <div class="AdminCounterWrap">
                    <div class="AdminCounterRow">
                      <span class="AdminCounterIcon"><i class="fa-solid fa-server"></i></span>
                      <span class="AdminCounterSub">Tổng cụm: <strong>${adminSummary.totalClusters}</strong></span>
                    </div>
                    <div class="AdminCounterRow">
                      <span class="AdminCounterIcon"><i class="fa-solid fa-database"></i></span>
                      <span class="AdminCounterSub">Đang hoạt động: <strong>${adminSummary.activeClusters}</strong></span>
                    </div>
                  </div>
                </section>

                <div class="Divider"></div>

                <div class="Row Row3" style=${{ marginTop: "12px" }}>
                  <div class="Field">
                    <label>Cụm</label>
                    <select class="Select" value=${adminBotId} onChange=${(e) => setAdminBotId(e.target.value)}>
                      ${adminBots.map((b) => html`<option value=${String(b.botIntId || "")}>${b.username || b.botAccount || "Cum"}</option>`)}
                    </select>
                  </div>

                  <div class="Field">
                    <label>Time Expr</label>
                    <input value=${adminTimeExpr} onInput=${(e) => setAdminTimeExpr(e.target.value)} placeholder="Input time..!" />
                  </div>

                  <div class="Field">
                    <label>&nbsp;</label>
                    <button class="Btn" onClick=${loadAdminOverview}>Sync Selected</button>
                  </div>
                </div>

                <div class="Actions">
                  <button class="Btn Primary" onClick=${() => adminBotAction("run")}>Run</button>
                  <button class="Btn Danger" onClick=${() => adminBotAction("stop")}>Stop</button>
                  <button class="Btn Warn" onClick=${() => adminBotAction("restart")}>Restart</button>
                  <button class="Btn" onClick=${() => adminBotAction("add_time", "", adminTimeExpr.trim())}>Extend</button>
                  <button class="Btn" onClick=${() => adminBotAction("sub_time", "", adminTimeExpr.trim())}>Minus</button>
                </div>

                <div class="Card Soft InlineConsole" style=${{ marginTop: "10px" }}>
                  <div class="CardTop">
                    <div class="CardTitle">Quản Lý Cụm</div>
                  </div>
                  <div class="AdminBotList">
                    ${adminBots.map((b) => {
                      const isLive = !!(b.status && !b.isExpired)
                      const bid = String(b.botIntId || "")
                      return html`
                        <div class="AdminBotItem">
                          <div>
                            <div class="AdminBotMain">${b.username || b.botAccount || "-"}</div>
                          </div>
                          <div><span class=${`AdminState ${isLive ? "live" : ""}`}>${isLive ? "RUNNING" : "STOPPED"}</span></div>
                          <div class="AdminBotSub">expired: ${b.expiredTime || "-"}</div>
                          <div class="AdminMiniActions">
                            <button class="AdminMiniBtn" onClick=${() => adminBotAction("run", bid, adminTimeExpr.trim())}>Run</button>
                            <button class="AdminMiniBtn" onClick=${() => adminBotAction("stop", bid, adminTimeExpr.trim())}>Stop</button>
                            <button class="AdminMiniBtn" onClick=${() => adminBotAction("restart", bid, adminTimeExpr.trim())}>Restart</button>
                            <button
                              class="AdminMiniBtn Danger"
                              title="Delete cluster"
                              onClick=${async () => {
                                const ok = await askConfirm("Bạn có chắc muốn xóa vĩnh viễn cụm này không?")
                                if (!ok) return
                                await wrap(() => postReq("/api/admin/bot/delete", { botIntId: bid }), "Cluster deleted")
                                await loadAdminOverview()
                              }}
                            ><i class="fa-regular fa-trash-can"></i></button>
                          </div>
                        </div>
                      `
                    })}
                  </div>
                </div>
              </section>

              <section class=${`Panel PanelTab UserOnly ${tab === "eBot" ? "is-active" : "Hidden"}`}>
                <div class="PanelHead">
                  <div>
                    <h2 class="H2">Bot Controls</h2>
                    <div class="SubLine">Quản lý bot nhanh theo thời gian thực.</div>
                  </div>
                </div>

                <div class="Actions">
                  <button
                    class="Btn Primary"
                    onClick=${async () => {
                      await wrap(() => postReq("/api/bot/run", {}), "Started")
                      await loadBotInfo()
                    }}
                  >Run</button>

                  <button
                    class="Btn Danger"
                    onClick=${async () => {
                      await wrap(() => postReq("/api/bot/stop", {}), "Stopped")
                      await loadBotInfo()
                    }}
                  >Stop</button>

                  <button
                    class="Btn Warn"
                    onClick=${async () => {
                      await wrap(() => postReq("/api/bot/restart", {}), "Restarted")
                      await loadBotInfo()
                    }}
                  >Restart</button>
                </div>

                <div class="Divider"></div>

                <div class="Row">
                  <div class="Field">
                    <label>New Prefix</label>
                    <input value=${newPrefix} onInput=${(e) => setNewPrefix(e.target.value)} placeholder="?" />
                  </div>
                  <div class="Field FieldBtn">
                    <label>&nbsp;</label>
                    <button
                      class="Btn"
                      onClick=${async () => {
                        const np = newPrefix.trim()
                        if (!np) {
                          print("Missing newPrefix", false, true)
                          return
                        }
                        await wrap(() => postReq("/api/bot/prefix", { newPrefix: np }), "Prefix updated")
                        setNewPrefix("")
                        await loadBotInfo()
                      }}
                    >Change Prefix</button>
                  </div>
                </div>
              </section>

              <section class=${`Panel PanelTab UserOnly ${tab === "Account" ? "is-active" : "Hidden"}`}>
                <div class="PanelHead">
                  <div>
                    <h2 class="H2">Account</h2>
                    <div class="SubLine">Cập nhật tài khoản đăng nhập dashboard.</div>
                  </div>
                </div>

                <div class="Row">
                  <div class="Field">
                    <label>New Username</label>
                    <input value=${newUsername} onInput=${(e) => setNewUsername(e.target.value)} placeholder="leave blank" />
                  </div>
                  <div class="Field">
                    <label>New Password</label>
                    <input value=${newPassword} onInput=${(e) => setNewPassword(e.target.value)} placeholder="leave blank" type="password" />
                  </div>
                </div>

                <div class="Actions">
                  <button
                    class="Btn Primary"
                    onClick=${async () => {
                      const u = newUsername.trim()
                      const p = newPassword.trim()
                      if (!u && !p) {
                        print("Nothing to update", false, true)
                        return
                      }
                      const j = await wrap(() => postReq("/api/account/update", {
                        username: u || undefined,
                        password: p || undefined,
                      }), "Account updated")
                      if (j.relogin) location.href = "/"
                      setNewUsername("")
                      setNewPassword("")
                    }}
                  >Save</button>
                </div>
              </section>

              <section class=${`Panel PanelTab UserOnly ${tab === "Logger" ? "is-active" : "Hidden"}`}>
                <div class="PanelHead">
                  <div>
                    <h2 class="H2">Logger</h2>
                    <div class="SubLine">Lọc và theo dõi log message/error.</div>
                  </div>
                  <div class="Mini">${logSub}</div>
                </div>

                <div class="Row Row3">
                  <div class="Field">
                    <label>Kind</label>
                    <select class="Select" value=${logKind} onChange=${(e) => setLogKind(e.target.value)}>
                      <option value="message">message</option>
                      <option value="error">error</option>
                    </select>
                  </div>
                  <div class="Field">
                    <label>Search</label>
                    <input value=${logQ} onInput=${(e) => setLogQ(e.target.value)} placeholder="user/group/text" />
                  </div>
                  <div class="Field">
                    <label>Limit</label>
                    <input value=${logLimit} onInput=${(e) => setLogLimit(e.target.value)} />
                  </div>
                </div>

                <div class="Actions">
                  <button
                    class="Btn"
                    onClick=${async () => {
                      setLoadingState(true, "Reloading logger...")
                      try {
                        resetLogger()
                        await loggerPull()
                        print("Logger reloaded", true, true)
                      } finally {
                        setLoadingState(false)
                      }
                    }}
                  >Reload</button>
                  <button class="Btn Ghost2" onClick=${() => {
                    resetLogger()
                    pushToast("info", "Logger cleared")
                  }}>Clear</button>
                </div>

                <div class="Card Soft InlineConsole">
                  <div class="CardTop">
                    <div class="CardTitle">Logger Stream</div>
                    <div class="CardSub">Live terminal</div>
                  </div>
                  <pre class="Console Light">${logOut}</pre>
                </div>
              </section>
            </div>

            ${me.isAdmin ? null : html`
              <div class="Col UserOnly">
                <div class="Card">
                  <div class="CardTop">
                    <div class="CardTitle">Response Console</div>
                    <div class="CardSub">API status output</div>
                  </div>
                  <pre class="Console Light">${outText}</pre>
                </div>
              </div>
            `}
          </section>
        </main>
      </div>
    </>
  `
}

const node = document.getElementById("root")
if (node) createRoot(node).render(html`<${DashboardApp} />`)
