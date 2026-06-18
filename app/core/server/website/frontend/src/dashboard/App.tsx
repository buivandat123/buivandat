import { useEffect, useMemo, useRef, useState } from "react"
import { type ApiResponse, getReq, postReq } from "../shared/http"
import { errorMessage, notifyError, notifySuccess, sileo } from "../shared/notify"
import { setupAntiDebugGuard } from "../shared/security"
import { cutText, ts } from "../shared/time"

const MAX_LOG_CHARS = 220000
const THEME_KEY = "ebug.dashboard.theme"

type AdminSection = "overview" | "clusters" | "system" | "notify"

interface MeResp extends ApiResponse {
  account?: string
  username?: string
  botIntId?: string
  isAdmin?: boolean
}

interface BotInfoResp extends ApiResponse {
  bot?: {
    prefix?: string
    username?: string
    status?: boolean
  }
}

interface AdminCluster {
  botIntId?: string
  username?: string
  botAccount?: string
  status?: boolean
  isExpired?: boolean
  expiredTime?: string
  prefix?: string
  running?: boolean
}

interface AdminSystemInfo {
  os?: string
  kernel?: string
  arch?: string
  ramUsedMb?: string | number
  ramTotalMb?: string | number
  ramPct?: number | null
  cpu?: string
  cpuCores?: string | number
  cpuLoadAvg?: string
  uptime?: string
  diskRoot?: string
  diskPct?: number | null
  vga?: string
  gpu?: string
  vram?: string
  vramPct?: number | null
  tempCpu?: string
  tempGpu?: string
  software?: string
  python?: string
  time?: string
}

interface AdminOverviewResp extends ApiResponse {
  clusters?: AdminCluster[]
  system?: AdminSystemInfo
  summary?: {
    activeClusters?: number
    totalClusters?: number
    stoppedClusters?: number
  }
}

interface AdminSystemResp extends ApiResponse {
  system?: AdminSystemInfo
}

interface LoggerItem {
  id?: number
  created_at?: string
  level?: string
  prefix?: string
  chat_type?: string
  user_name?: string
  user_id?: string
  group_name?: string
  group_id?: string
  ref?: string
  content?: string
}

interface LoggerResp extends ApiResponse {
  items?: LoggerItem[]
}

interface StateMe {
  account: string
  username: string
  botIntId: string
  isAdmin: boolean
}

interface UiActivityItem {
  id: number
  time: string
  text: string
  ok: boolean
}

const logFmt = (x: LoggerItem) => {
  const head = `[${x.id ?? ""}] [${x.created_at ?? ""}] [${x.level ?? ""}] [${x.prefix ?? ""}] [${x.chat_type ?? ""}]`
  const who = `${x.user_name ?? ""}${x.user_id ? ` - ${x.user_id}` : ""}`
  const grp = x.group_name ? ` | ${x.group_name}${x.group_id ? ` - ${x.group_id}` : ""}` : ""
  const ref = x.ref ? `\n→ ${x.ref}` : ""
  const body = String(x.content ?? "")
  return `${head} ${who}${grp}\n${body}${ref}\n`
}

const toNumber = (v: unknown) => {
  const n = Number(String(v ?? "").replace(/[^0-9.-]/g, ""))
  return Number.isFinite(n) ? n : 0
}

const clamp = (n: number, min = 0, max = 100) => Math.max(min, Math.min(max, n))

const parseCpuPct = (system: AdminSystemInfo | null) => {
  if (!system) return 0
  const load = String(system.cpuLoadAvg || "0").split(/\s+/)[0] || "0"
  const cores = Math.max(1, toNumber(system.cpuCores || 1))
  return clamp(Math.round((toNumber(load) / cores) * 100))
}

const parseRamPct = (system: AdminSystemInfo | null) => {
  if (!system) return 0
  if (typeof system.ramPct === "number") return clamp(system.ramPct)
  const used = toNumber(system.ramUsedMb)
  const total = Math.max(1, toNumber(system.ramTotalMb))
  return clamp(Math.round((used / total) * 100))
}

const parseGpuPct = (system: AdminSystemInfo | null) => {
  if (!system) return 0
  if (typeof system.vramPct === "number") return clamp(system.vramPct)
  const parts = String(system.vram || "").split("/")
  if (parts.length < 2) return 0
  return clamp(Math.round((toNumber(parts[0]) / Math.max(1, toNumber(parts[1]))) * 100))
}

const buildPath = (vals: number[]) => vals.map((v, i) => {
  const x = vals.length <= 1 ? 0 : (i / (vals.length - 1)) * 100
  const y = 100 - clamp(v)
  return `${i === 0 ? "M" : "L"}${x},${y}`
}).join(" ")

function Sparkline({ values, color }: { values: number[]; color: string }) {
  const gid = `sg${color.replace('#', '')}`
  const d = buildPath(values)
  const areaD = `${d} L100,100 L0,100 Z`
  return (
    <svg className="Sparkline" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity=".22" />
          <stop offset="100%" stopColor={color} stopOpacity=".02" />
        </linearGradient>
      </defs>
      <path d={areaD} fill={`url(#${gid})`} />
      <path d={d} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function DashboardApp() {
  const [ui, setUi] = useState({ ok: true, text: "Ready" })
  const [runtime, setRuntime] = useState(`Online ${ts()}`)
  const [loading, setLoading] = useState({ on: false, text: "Processing..." })
  const [theme, setTheme] = useState("light")
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [tab, setTab] = useState("eBot")
  const [adminSection, setAdminSection] = useState<AdminSection>("overview")
  const [me, setMe] = useState<StateMe>({ account: "", username: "", botIntId: "", isAdmin: false })
  const [botPrefix, setBotPrefix] = useState("-")
  const [botStatus, setBotStatus] = useState(false)
  const [avatarUrl, setAvatarUrl] = useState("")

  const [newPrefix, setNewPrefix] = useState("")
  const [newUsername, setNewUsername] = useState("")
  const [newPassword, setNewPassword] = useState("")

  const [adminBots, setAdminBots] = useState<AdminCluster[]>([])
  const [adminSummary, setAdminSummary] = useState({ activeClusters: 0, totalClusters: 0, stoppedClusters: 0 })
  const [adminSystem, setAdminSystem] = useState<AdminSystemInfo | null>(null)
  const [adminBotId, setAdminBotId] = useState("")
  const [adminTimeExpr, setAdminTimeExpr] = useState("")
  const [adminNotifyText, setAdminNotifyText] = useState("")
  const [clusterAvatars, setClusterAvatars] = useState<Record<string, string>>({})

  const [logKind, setLogKind] = useState("message")
  const [logQ, setLogQ] = useState("")
  const [logLimit, setLogLimit] = useState("80")
  const [logOut, setLogOut] = useState("Waiting...")
  const [logSub, setLogSub] = useState("-")
  const [chartSeries, setChartSeries] = useState({ cpu: [12, 18, 14, 22, 20, 26], ram: [28, 32, 35, 37, 33, 40], gpu: [0, 0, 0, 0, 0, 0] })
  const [uiLogs, setUiLogs] = useState<UiActivityItem[]>([{ id: Date.now(), time: ts(), text: "Dashboard initialized", ok: true }])

  const [confirmState, setConfirmState] = useState({ open: false, text: "Bạn có chắc chắn?" })
  const confirmResolveRef = useRef<((ok: boolean) => void) | null>(null)
  const loadingCounterRef = useRef(0)
  const loggerRef = useRef({ lastMaxId: 0, lines: 0 })

  useEffect(() => {
    const off = setupAntiDebugGuard()
    return () => off()
  }, [])

  useEffect(() => {
    const id = window.setInterval(() => {
      setRuntime(`${ui.ok ? "Online" : "Error"} ${ts()}`)
    }, 500)
    return () => window.clearInterval(id)
  }, [ui.ok])

  useEffect(() => {
    document.body.setAttribute("data-theme", theme)
  }, [theme])

  useEffect(() => {
    if (!adminSystem) return
    setChartSeries((prev) => ({
      cpu: [...prev.cpu.slice(-11), parseCpuPct(adminSystem)],
      ram: [...prev.ram.slice(-11), parseRamPct(adminSystem)],
      gpu: [...prev.gpu.slice(-11), parseGpuPct(adminSystem)],
    }))
  }, [adminSystem])

  const setLoadingState = (on: boolean, text = "Processing...") => {
    loadingCounterRef.current = Math.max(0, loadingCounterRef.current + (on ? 1 : -1))
    setLoading({ on: loadingCounterRef.current > 0, text })
  }

  const pushUiLog = (text: string, ok = true) => {
    const line = String(text || "").trim()
    if (!line) return
    setUiLogs((prev) => [{ id: Date.now() + Math.floor(Math.random() * 1000), time: ts(), text: line, ok }, ...prev].slice(0, 24))
  }

  const print = (text: string, ok = true, toast = false) => {
    const nextText = String(text || "")
    setUi({ ok, text: nextText })
    pushUiLog(nextText, ok)
    if (toast) {
      if (ok) notifySuccess("Thành công", nextText)
      else notifyError("Lỗi", nextText)
    }
  }

  const wrap = async <T,>(fn: () => Promise<T>, okText = "OK") => {
    try {
      setLoadingState(true, "Processing request...")
      const j = await fn()
      print(okText, true, true)
      return j
    } catch (e) {
      const err = errorMessage(e)
      print(err, false, true)
      throw e
    } finally {
      setLoadingState(false)
    }
  }

  const askConfirm = (text = "Bạn có chắc chắn?") => new Promise<boolean>((resolve) => {
    confirmResolveRef.current = resolve
    setConfirmState({ open: true, text })
  })

  const closeConfirm = (ok: boolean) => {
    confirmResolveRef.current?.(ok)
    confirmResolveRef.current = null
    setConfirmState({ open: false, text: "Bạn có chắc chắn?" })
  }

  const resetLogger = () => {
    loggerRef.current.lastMaxId = 0
    loggerRef.current.lines = 0
    setLogOut("Waiting...")
    setLogSub("-")
  }

  const buildLogQuery = () => {
    const kind = logKind.trim() || "message"
    const q = logQ.trim()
    const limit = Math.min(Math.max(parseInt(logLimit || "80", 10) || 80, 10), 200)
    const qs = new URLSearchParams()
    qs.set("kind", kind)
    qs.set("limit", String(limit))
    if (q) qs.set("q", q)
    return qs.toString()
  }

  const loggerPull = async () => {
    const j = await getReq<LoggerResp>(`/api/logger/list?${buildLogQuery()}`).catch(() => null)
    if (!j?.ok) return
    const items = Array.isArray(j.items) ? j.items : []
    if (!items.length) return
    let maxId = loggerRef.current.lastMaxId || 0
    for (const it of items) {
      const id = Number(it.id) || 0
      if (id > maxId) maxId = id
    }
    const fresh = items.filter((it) => (Number(it.id) || 0) > (loggerRef.current.lastMaxId || 0))
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

  const loadAdminOverview = async (silent = false) => {
    try {
      if (!silent) setLoadingState(true, "Loading admin dashboard...")
      const j = await getReq<AdminOverviewResp>("/api/admin/overview")
      const clusters = Array.isArray(j.clusters) ? j.clusters : []
      const summary = j.summary || {}
      setAdminBots(clusters)
      setAdminSystem(j.system || null)
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
      if (!silent) print("Admin overview loaded", true, true)
    } catch (e) {
      print(errorMessage(e), false, !silent)
      throw e
    } finally {
      if (!silent) setLoadingState(false)
    }
  }

  const loadAdminSystemOnly = async () => {
    const j = await getReq<AdminSystemResp>("/api/admin/system").catch(() => null)
    if (j?.ok && j.system) setAdminSystem(j.system)
  }

  const currentAdminBotId = () => {
    if (adminBotId) return adminBotId
    const one = adminBots[0]
    return one ? String(one.botIntId || "") : ""
  }

  const adminBotAction = async (action: string, botIntId = "", timeExpr = "") => {
    const bid = String(botIntId || currentAdminBotId()).trim()
    if (!bid) return print("Missing bot selection", false, true)
    const payload: { action: string; botIntId: string; timeExpr?: string } = { action, botIntId: bid }
    if (timeExpr) payload.timeExpr = timeExpr
    await wrap(() => postReq("/api/admin/bot/action", payload), `Admin action: ${action}`)
    await loadAdminOverview(true)
  }

  const adminSystemAction = async (action: "restart_all_clusters" | "stop_all_clusters" | "notify_group") => {
    await wrap(() => postReq("/api/admin/system/action", { action, text: adminNotifyText.trim() || undefined }), action === "notify_group" ? "Đã gửi thông báo hệ thống" : "Đã cập nhật cụm hệ thống")
    if (action === "notify_group") setAdminNotifyText("")
    await loadAdminOverview(true)
  }

  const loadBotInfo = async () => {
    const j = await getReq<BotInfoResp>("/api/bot/info").catch(() => null)
    if (j?.ok) {
      setBotPrefix(String(j.bot?.prefix || "-"))
      setBotStatus(!!j.bot?.status)
    }
  }

  useEffect(() => {
    const readTheme = localStorage.getItem(THEME_KEY)
    setTheme(readTheme === "dark" ? "dark" : "light")
    let mounted = true
    ;(async () => {
      try {
        setLoadingState(true, "Booting dashboard...")
        const meData = await getReq<MeResp>("/api/auth/me").catch(() => ({ ok: false } as MeResp))
        if (!meData.ok) {
          location.href = "/"
          return
        }
        if (!mounted) return
        const nextMe: StateMe = {
          account: String(meData.account || ""),
          username: String(meData.username || ""),
          botIntId: String(meData.botIntId || ""),
          isAdmin: !!meData.isAdmin,
        }
        setMe(nextMe)
        if (nextMe.isAdmin) {
          setTab("Admin")
          await loadAdminOverview(true)
        } else {
          setTab("eBot")
          const av = await getReq<{ ok: boolean; avatarUrl?: string }>("/api/bot/getavatar").catch(() => null)
          if (av?.ok && mounted) setAvatarUrl(String(av.avatarUrl || ""))
          const info = await getReq<BotInfoResp>("/api/bot/info").catch(() => null)
          if (info?.ok && mounted) {
            setBotPrefix(String(info.bot?.prefix || "-"))
            setBotStatus(!!info.bot?.status)
            if (!nextMe.username && info.bot?.username) setMe((prev) => ({ ...prev, username: String(info.bot?.username || "") }))
          }
        }
        print("Ready", true)
      } catch (e) {
        print(errorMessage(e), false, true)
      } finally {
        setLoadingState(false)
      }
    })()
    return () => { mounted = false }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (tab !== "Logger") return
    const id = window.setInterval(() => { void loggerPull() }, 1000)
    void loggerPull()
    return () => window.clearInterval(id)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, logKind, logQ, logLimit])

  useEffect(() => {
    if (!me.isAdmin || tab !== "Admin") return
    const id = window.setInterval(() => { void loadAdminSystemOnly() }, 7000)
    return () => window.clearInterval(id)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me.isAdmin, tab, adminSection])

  useEffect(() => {
    if (!me.isAdmin || tab !== "Admin" || adminSection !== "clusters" || !adminBots.length) return
    const needs = adminBots.filter((b) => {
      const bid = String(b.botIntId || "").trim()
      return !!bid && !clusterAvatars[bid]
    })
    if (!needs.length) return
    let cancelled = false
    ;(async () => {
      const rows = await Promise.all(needs.map(async (b) => {
        const bid = String(b.botIntId || "").trim()
        if (!bid) return null
        const sourceIds = [String(b.botAccount || "").trim(), bid].filter(Boolean)
        for (const source of sourceIds) {
          const av = await getReq<{ ok: boolean; avatarUrl?: string }>(`/api/bot/getadminavatar?id=${encodeURIComponent(source)}`).catch(() => null)
          const url = String(av?.avatarUrl || "").trim()
          if (av?.ok && url) return [bid, url] as const
        }
        return null
      }))
      if (cancelled) return
      const pairs = rows.filter((x): x is readonly [string, string] => !!x)
      if (!pairs.length) return
      setClusterAvatars((prev) => {
        const next = { ...prev }
        for (const [bid, url] of pairs) next[bid] = url
        return next
      })
    })()
    return () => { cancelled = true }
  }, [me.isAdmin, tab, adminSection, adminBots, clusterAvatars])

  const meLine = me.account ? `${me.username || ""} - ${me.account}` : "-"
  const botIdText = me.isAdmin ? "admin" : cutText(me.botIntId || "", 10)
  const botTitle = me.username || me.account || "eBug"
  const cpuPct = useMemo(() => parseCpuPct(adminSystem), [adminSystem])
  const ramPct = useMemo(() => parseRamPct(adminSystem), [adminSystem])
  const gpuPct = useMemo(() => parseGpuPct(adminSystem), [adminSystem])
  const uiLogPreview = useMemo(() => uiLogs.slice(0, 10), [uiLogs])

  const onThemeToggle = () => {
    const next = theme === "dark" ? "light" : "dark"
    localStorage.setItem(THEME_KEY, next)
    setTheme(next)
  }

  const setTabAndClose = (nextTab: string) => {
    setTab(nextTab)
    setSidebarOpen(false)
  }

  return (
    <>
      <div className="Bg" />
      <div className={`AppLoading ${loading.on ? "" : "Hidden"}`} aria-hidden={loading.on ? "false" : "true"}><div className="LoaderSpinner" /><div className="LoaderText">{loading.text}</div></div>
      <div className={`ConfirmOverlay ${confirmState.open ? "" : "Hidden"}`} onClick={(e) => { if ((e.target as HTMLElement).classList.contains("ConfirmOverlay")) closeConfirm(false) }}><div className="ConfirmBox"><div className="ConfirmTitle">Xác nhận thao tác</div><div className="ConfirmText">{confirmState.text}</div><div className="ConfirmActions"><button className="Btn Ghost2" onClick={() => closeConfirm(false)}>Hủy</button><button className="Btn Danger" onClick={() => closeConfirm(true)}>Xóa</button></div></div></div>
      <header className="mobile-topbar"><button className="topbar-menu-btn" onClick={() => setSidebarOpen(true)}><i className="fa-solid fa-bars" /></button><div className="topbar-logo"><i className="fa-solid fa-bug" /> eBug <strong>Bot</strong></div><button className="topbar-action" onClick={onThemeToggle} title="Theme"><i className={`fa-solid ${theme === "dark" ? "fa-sun" : "fa-moon"}`} /></button></header>
      <div className="app-layout">
        <div className={`sidebar-overlay ${sidebarOpen ? "show" : ""}`} onClick={() => setSidebarOpen(false)} />
        <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
          <div className="sidebar-logo"><i className="fa-solid fa-bug" /><span>eBug <strong>Manager</strong></span><button className="sidebar-close" onClick={() => setSidebarOpen(false)}><i className="fa-solid fa-xmark" /></button></div>
          <nav className="sidebar-nav">
            <div className="sidebar-section">Tổng quan</div>
            {!me.isAdmin && <button className={`sidebar-link ${tab === "eBot" ? "active" : ""}`} onClick={() => setTabAndClose("eBot")}><i className="fa-solid fa-house" /> Bot Manager</button>}
            {me.isAdmin && <>
              <button className={`sidebar-link ${tab === "Admin" && adminSection === "overview" ? "active" : ""}`} onClick={() => { setTabAndClose("Admin"); setAdminSection("overview") }}><i className="fa-solid fa-chart-pie" /> Tổng quan</button>
              <button className={`sidebar-link ${tab === "Admin" && adminSection === "clusters" ? "active" : ""}`} onClick={() => { setTabAndClose("Admin"); setAdminSection("clusters") }}><i className="fa-solid fa-server" /> Quản lý Cụm</button>
              <button className={`sidebar-link ${tab === "Admin" && adminSection === "system" ? "active" : ""}`} onClick={() => { setTabAndClose("Admin"); setAdminSection("system") }}><i className="fa-solid fa-gear" /> Hệ thống</button>
              <button className={`sidebar-link ${tab === "Admin" && adminSection === "notify" ? "active" : ""}`} onClick={() => { setTabAndClose("Admin"); setAdminSection("notify") }}><i className="fa-solid fa-bell" /> Thông báo</button>
            </>}
            {!me.isAdmin && <><div className="sidebar-section">Cài đặt</div><button className={`sidebar-link ${tab === "Account" ? "active" : ""}`} onClick={() => setTabAndClose("Account")}><i className="fa-solid fa-user-gear" /> Account</button><button className={`sidebar-link ${tab === "Logger" ? "active" : ""}`} onClick={() => setTabAndClose("Logger")}><i className="fa-solid fa-scroll" /> Logger</button></>}
          </nav>
          <div className="sidebar-footer"><div className="sidebar-user"><div className="sidebar-avatar">{(me.username || me.account || "E").slice(0, 1).toUpperCase()}</div><div className="sidebar-user-info"><div className="sidebar-user-name">{me.username || me.account || "eBug"}</div><div className="sidebar-user-email">{me.account || "-"}</div></div></div><button className="sidebar-logout" onClick={async () => { try { await wrap(() => postReq("/api/auth/logout", {}), "Logged out") } finally { location.href = "/" } }}><i className="fa-solid fa-right-from-bracket" /> Logout</button></div>
        </aside>
        <main className="main-content">

          {!me.isAdmin && <><section className="BotHeroCard"><div className="BotHeroHeader"><div className="BotHeroIdentity"><div className="BotHeroAvatar">{avatarUrl ? <img src={avatarUrl} alt="avatar" /> : <i className="fa-solid fa-robot" />}</div><div><div className="BotHeroEyebrow">Bot phụ</div><h2 className="BotHeroTitle">{botTitle}</h2><p className="BotHeroSub">Quản lý tác vụ, theo dõi trạng thái và cấu hình nhanh.</p></div></div><div className={`BotStatusPill ${botStatus ? "online" : "offline"}`}>{botStatus ? "Đang hoạt động" : "Đã dừng"}</div></div><div className="BotInfoGrid"><article className="BotInfoItem"><span>Prefix</span><strong>{botPrefix || "-"}</strong></article><article className="BotInfoItem"><span>Bot ID</span><strong>{botIdText}</strong></article><article className="BotInfoItem"><span>Tài khoản</span><strong>{me.account || "-"}</strong></article><article className="BotInfoItem"><span>Runtime</span><strong>{runtime}</strong></article></div></section>
          <section className="QuickActionGrid">
            <section className={`Panel PanelTab UserOnly ${tab === "eBot" ? "is-active" : "Hidden"}`}><div className="PanelHead"><div><h2 className="H2">Bot Controls</h2><div className="SubLine">Tác vụ điều khiển nhanh với UI/UX gọn hơn.</div></div></div><div className="Actions"><button className="Btn Primary" onClick={async () => { await wrap(() => postReq("/api/bot/run", {}), "Started"); await loadBotInfo() }}>Run</button><button className="Btn Danger" onClick={async () => { await wrap(() => postReq("/api/bot/stop", {}), "Stopped"); await loadBotInfo() }}>Stop</button><button className="Btn Warn" onClick={async () => { await wrap(() => postReq("/api/bot/restart", {}), "Restarted"); await loadBotInfo() }}>Restart</button></div><div className="Divider" /><div className="PrefixEditor"><div className="Field PrefixField"><label>New Prefix</label><input value={newPrefix} onChange={(e) => setNewPrefix(e.target.value)} placeholder="?" /></div><button className="Btn Primary PrefixBtn" onClick={async () => { const np = newPrefix.trim(); if (!np) return print("Missing newPrefix", false, true); await wrap(() => postReq("/api/bot/prefix", { newPrefix: np }), "Prefix updated"); setNewPrefix(""); await loadBotInfo() }}>Change Prefix</button></div></section>
            <section className={`Panel PanelTab UserOnly ${tab === "Account" ? "is-active" : "Hidden"}`}><div className="PanelHead"><div><h2 className="H2">Account</h2><div className="SubLine">Cập nhật tài khoản đăng nhập dashboard.</div></div></div><div className="Row"><div className="Field"><label>New Username</label><input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} placeholder="leave blank" /></div><div className="Field"><label>New Password</label><input value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="leave blank" type="password" /></div></div><div className="Actions"><button className="Btn Primary" onClick={async () => { const u = newUsername.trim(); const p = newPassword.trim(); if (!u && !p) return print("Nothing to update", false, true); const j = await wrap(() => postReq<ApiResponse & { relogin?: boolean }>("/api/account/update", { username: u || undefined, password: p || undefined }), "Account updated"); if (j.relogin) location.href = "/"; setNewUsername(""); setNewPassword("") }}>Save</button></div></section>
            <section className={`Panel PanelTab UserOnly ${tab === "Logger" ? "is-active" : "Hidden"}`}><div className="PanelHead"><div><h2 className="H2">Logger</h2><div className="SubLine">Lọc và theo dõi log message/error.</div></div><div className="Mini">{logSub}</div></div><div className="Row Row3"><div className="Field"><label>Kind</label><select className="Select" value={logKind} onChange={(e) => setLogKind(e.target.value)}><option value="message">message</option><option value="error">error</option></select></div><div className="Field"><label>Search</label><input value={logQ} onChange={(e) => setLogQ(e.target.value)} placeholder="user/group/text" /></div><div className="Field"><label>Limit</label><input value={logLimit} onChange={(e) => setLogLimit(e.target.value)} /></div></div><div className="Actions"><button className="Btn" onClick={async () => { setLoadingState(true, "Reloading logger..."); try { resetLogger(); await loggerPull(); print("Logger reloaded", true, true) } finally { setLoadingState(false) } }}>Reload</button><button className="Btn Ghost2" onClick={() => { resetLogger(); sileo.info({ title: "Thông báo", description: "Logger cleared" }) }}>Clear</button></div><div className="Card Soft InlineConsole"><div className="CardTop"><div className="CardTitle">Logger Stream</div><div className="CardSub">Live terminal</div></div><pre className="Console Light">{logOut}</pre></div></section>
          </section></>}

          {me.isAdmin && <section className={`Panel PanelTab ${tab === "Admin" ? "is-active" : "Hidden"}`}>
            {adminSection === "overview" && <>
              <div className="PanelHead"><div><h2 className="H2">Tổng quan Hệ thống</h2><div className="SubLine">Theo dõi hiệu suất, trạng thái cụm bot và tài nguyên máy chủ.</div></div><button className="Btn Ghost" onClick={() => void loadAdminOverview()}>Refresh</button></div>
              <section className="AdminMetricsGrid"><article className="MetricCard"><span>Active Clusters</span><strong>{adminSummary.activeClusters}</strong></article><article className="MetricCard"><span>Total Clusters</span><strong>{adminSummary.totalClusters}</strong></article><article className="MetricCard"><span>RAM Usage</span><strong>{ramPct}%</strong></article><article className="MetricCard"><span>CPU Load</span><strong>{cpuPct}%</strong></article></section>
              <section className="AdminOverviewFShape">
                <div className="AdminMainFlow">
                  <div className="MonitorChartsGrid">
                    <article className="SparkCard cpu"><div className="SparkHeader"><span>CPU</span><strong>{cpuPct}%</strong></div><Sparkline values={chartSeries.cpu} color="#2563eb" /><div className="SparkMeta">Load avg {adminSystem?.cpuLoadAvg || "0"} - Temp {adminSystem?.tempCpu || "unknown"}</div></article>
                    <article className="SparkCard ram"><div className="SparkHeader"><span>RAM</span><strong>{ramPct}%</strong></div><Sparkline values={chartSeries.ram} color="#16a34a" /><div className="SparkMeta">{adminSystem?.ramUsedMb || 0} / {adminSystem?.ramTotalMb || 0} MB</div></article>
                    <article className="SparkCard gpu"><div className="SparkHeader"><span>GPU</span><strong>{gpuPct}%</strong></div><Sparkline values={chartSeries.gpu} color="#7c3aed" /><div className="SparkMeta">VRAM {adminSystem?.vram || "unknown"} - Temp {adminSystem?.tempGpu || "unknown"}</div></article>
                  </div>
                </div>
                <aside className="AdminRightRail">
                  <div className="MonitorPanel">
                    <div className="MonitorPanelHead"><div><h3>Cụm bot</h3><p>Danh sách cụm đang chạy trong hệ thống.</p></div></div>
                    <div className="ClusterCompactList">{adminBots.map((b) => { const live = !!(b.status && !b.isExpired); return <div key={String(b.botIntId || "")} className="ClusterRow"><div><strong>{b.username || b.botAccount || "-"}</strong><small>{b.prefix || "?"} - {cutText(String(b.botIntId || ""), 10)}</small></div><span className={`StatusDot ${live ? "live" : "stop"}`}>{live ? "RUNNING" : "STOPPED"}</span></div> })}</div>
                  </div>
                </aside>
              </section>
            </>}

            {adminSection === "clusters" && <>
              <div className="PanelHead"><div><h2 className="H2">Quản lý Cụm Bot</h2><div className="SubLine">Điều khiển từng cụm bot: chạy, dừng, gia hạn thời gian.</div></div><button className="Btn Ghost" onClick={() => void loadAdminOverview()}>Sync</button></div>
              <div className="Row Row3"><div className="Field"><label>Cụm</label><select className="Select" value={adminBotId} onChange={(e) => setAdminBotId(e.target.value)}>{adminBots.map((b) => <option key={String(b.botIntId || "")} value={String(b.botIntId || "")}>{b.username || b.botAccount || "Cum"}</option>)}</select></div><div className="Field"><label>Time Expr</label><input value={adminTimeExpr} onChange={(e) => setAdminTimeExpr(e.target.value)} placeholder="2d6h / 30m" /></div><div className="Field FieldBtn"><label>&nbsp;</label><div className="Actions"><button className="Btn Primary" onClick={() => void adminBotAction("run")}>Run</button><button className="Btn Danger" onClick={() => void adminBotAction("stop")}>Stop</button><button className="Btn Warn" onClick={() => void adminBotAction("restart")}>Restart</button></div></div></div>
              <div className="Actions" style={{marginTop:12}}><button className="Btn" onClick={() => void adminBotAction("add_time", "", adminTimeExpr.trim())}>Extend Time</button><button className="Btn Ghost" onClick={() => void adminBotAction("sub_time", "", adminTimeExpr.trim())}>Minus Time</button></div>
              <div className="ClusterManageList">{adminBots.map((b, idx) => { const isLive = !!(b.status && !b.isExpired); const bid = String(b.botIntId || ""); const avatar = clusterAvatars[bid] || ""; const fallback = (b.username || b.botAccount || "B").slice(0, 1).toUpperCase(); return <div key={bid} className="AdminBotItem"><div className="AdminBotIdentity"><div className="AdminBotAvatar">{avatar ? <img src={avatar} alt={b.username || b.botAccount || "cluster"} loading="lazy" /> : <span>{fallback}</span>}</div><div><div className="AdminBotMain"><span className="AdminBotIndex">{idx + 1}. </span>{b.username || b.botAccount || "-"}</div><div className="AdminBotSub">{cutText(bid, 12)} - expired: {b.expiredTime || "-"}</div></div></div><div><span className={`AdminState ${isLive ? "live" : ""}`}>{isLive ? "RUNNING" : "STOPPED"}</span></div><div className="AdminMiniActions"><button className="AdminMiniBtn" onClick={() => void adminBotAction("run", bid, adminTimeExpr.trim())}>Run</button><button className="AdminMiniBtn" onClick={() => void adminBotAction("restart", bid, adminTimeExpr.trim())}>Restart</button><button className="AdminMiniBtn Danger" onClick={async () => { const ok = await askConfirm("Bạn có chắc muốn xóa vĩnh viễn cụm này không?"); if (!ok) return; await wrap(() => postReq("/api/admin/bot/delete", { botIntId: bid }), "Cluster deleted"); await loadAdminOverview(true) }}><i className="fa-regular fa-trash-can" /></button></div></div> })}</div>
            </>}

            {}
            {adminSection === "system" && <>
              <div className="PanelHead"><div><h2 className="H2">Thông tin Hệ thống</h2><div className="SubLine">Chi tiết phần cứng và phần mềm máy chủ.</div></div><button className="Btn Ghost" onClick={() => void loadAdminOverview()}>Refresh</button></div>
              <div className="MonitorPanel"><div className="DeviceGrid"><article className="DeviceCard"><span>OS</span><strong>{adminSystem?.os || "unknown"}</strong><small>{adminSystem?.kernel || "-"}</small></article><article className="DeviceCard"><span>CPU</span><strong>{adminSystem?.cpu || "unknown"}</strong><small>{adminSystem?.cpuCores || "-"} cores</small></article><article className="DeviceCard"><span>GPU</span><strong>{adminSystem?.gpu && adminSystem.gpu !== "0" ? adminSystem.gpu : (adminSystem?.vga || "unknown")}</strong><small>{adminSystem?.vram || "unknown"}</small></article><article className="DeviceCard"><span>Uptime</span><strong>{adminSystem?.uptime || "unknown"}</strong><small>{adminSystem?.arch || "-"}</small></article><article className="DeviceCard"><span>Disk</span><strong>{adminSystem?.diskRoot || "unknown"}</strong><small>{adminSystem?.diskPct !== null ? `${adminSystem?.diskPct}% used` : "-"}</small></article><article className="DeviceCard"><span>Python</span><strong>{adminSystem?.python || "unknown"}</strong><small>-</small></article></div></div>
              <div className="Actions" style={{marginTop:16}}><button className="Btn Warn" onClick={() => void adminSystemAction("restart_all_clusters")}>Restart All Clusters</button><button className="Btn Danger" onClick={() => void adminSystemAction("stop_all_clusters")}>Stop All Clusters</button></div>
            </>}

            {}
            {adminSection === "notify" && <>
              <div className="PanelHead"><div><h2 className="H2">Gửi Thông báo</h2><div className="SubLine">Gửi thông báo hệ thống vào nhóm quản trị.</div></div></div>
              <div className="Field"><label>Nội dung thông báo</label><textarea className="AdminTextarea" value={adminNotifyText} onChange={(e) => setAdminNotifyText(e.target.value)} placeholder="Nhập nội dung thông báo gửi vào nhóm quản trị..." /></div>
              <div className="Actions"><button className="Btn Primary" onClick={() => void adminSystemAction("notify_group")}>Gửi thông báo</button></div>
            </>}
          </section>}
        </main>
      </div>
    </>
  )
}
