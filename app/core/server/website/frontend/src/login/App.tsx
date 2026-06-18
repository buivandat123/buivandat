import { useCallback, useEffect, useRef, useState } from "react"
import { getReq, postReq, type ApiResponse } from "../shared/http"
import { sileo } from "../shared/notify"

interface LoginResponse extends ApiResponse {
  ok: boolean
}

interface QrGenResp extends ApiResponse {
  ok: boolean
  qrImage?: string
  code?: string
}

type QrStatus = "waiting" | "scanned" | "confirmed" | "expired"

interface QrStatusResp extends ApiResponse {
  ok: boolean
  status?: QrStatus
  userId?: string
  cookies?: Record<string, string>
  imei?: string
}

type QrStep = "idle" | "loading" | "showing" | "scanned" | "confirmed" | "expired" | "phone"

const initQrData = {
  image: "",
  code: "",
  userId: "",
  cookies: {} as Record<string, string>,
  imei: "",
  phone: "",
}

export default function LoginApp() {
  const [account, setAccount] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [phoneLoading, setPhoneLoading] = useState(false)
  const [qrStep, setQrStep] = useState<QrStep>("idle")
  const [qrData, setQrData] = useState(initQrData)

  const qrPollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const qrStatusRef = useRef<QrStatus | null>(null)
  const qrFinalizedRef = useRef(false)

  const toast = useCallback((text: string, type: "success" | "error" | "info" = "info") => {
    sileo[type]({ title: text })
  }, [])

  const stopQrPoll = () => {
    if (!qrPollRef.current) return
    clearInterval(qrPollRef.current)
    qrPollRef.current = null
  }

  const resetQr = useCallback(() => {
    stopQrPoll()
    qrStatusRef.current = null
    qrFinalizedRef.current = false
    setQrStep("idle")
    setQrData(initQrData)
  }, [])

  useEffect(() => () => stopQrPoll(), [])

  const onLogin = async () => {
    const acc = account.trim()
    const pass = password.trim()

    if (!acc || !pass) {
      toast("Vui lòng nhập tài khoản và mật khẩu", "error")
      return
    }

    try {
      setLoading(true)
      await postReq<LoginResponse>("/api/auth/login", { account: acc, password: pass })
      toast("Đăng nhập thành công!", "success")
      setTimeout(() => {
        location.href = "/dashboard"
      }, 600)
    } catch (e) {
      toast(e instanceof Error ? e.message : "Đăng nhập thất bại", "error")
    } finally {
      setLoading(false)
    }
  }

  const applyQrStatus = (resp: QrStatusResp) => {
    if (!resp.status || qrFinalizedRef.current) return

    if (resp.status === "scanned") {
      if (qrStatusRef.current === "scanned") return
      qrStatusRef.current = "scanned"
      setQrStep("scanned")
      toast("Đã quét! Đang chờ xác nhận...", "info")
      return
    }

    if (resp.status === "confirmed") {
      if (qrStatusRef.current === "confirmed") return
      qrStatusRef.current = "confirmed"
      qrFinalizedRef.current = true
      stopQrPoll()
      setQrStep("confirmed")
      setQrData((prev) => ({
        ...prev,
        userId: resp.userId || "",
        cookies: resp.cookies || {},
        imei: resp.imei || "",
      }))
      toast("Xác thực thành công!", "success")
      setTimeout(() => setQrStep("phone"), 1800)
      return
    }

    if (resp.status === "expired") {
      if (qrStatusRef.current === "expired") return
      qrStatusRef.current = "expired"
      qrFinalizedRef.current = true
      stopQrPoll()
      setQrStep("expired")
      toast("Mã QR đã hết hạn", "error")
    }
  }

  const pollQrStatus = (code: string) => {
    stopQrPoll()
    qrPollRef.current = setInterval(async () => {
      try {
        const resp = await getReq<QrStatusResp>(`/api/qr/status?code=${encodeURIComponent(code)}`)
        if (resp.ok) applyQrStatus(resp)
      } catch {}
    }, 2500)
  }

  const startQrLogin = async () => {
    try {
      stopQrPoll()
      qrStatusRef.current = null
      qrFinalizedRef.current = false
      setQrStep("loading")
      toast("Đang tạo mã QR...", "info")

      const resp = await getReq<QrGenResp>("/api/qr/generate")
      if (!resp.ok || !resp.qrImage || !resp.code) {
        setQrStep("idle")
        toast("Không thể tạo mã QR", "error")
        return
      }

      setQrData((prev) => ({
        ...prev,
        image: resp.qrImage!,
        code: resp.code!,
      }))
      setQrStep("showing")
      toast("Quét mã QR bằng thiết bị khác", "info")
      pollQrStatus(resp.code)
    } catch (e) {
      setQrStep("idle")
      toast(e instanceof Error ? e.message : "Lỗi tạo QR", "error")
    }
  }

  const onSubmitPhone = async () => {
    const phone = qrData.phone.trim()

    if (!phone) {
      toast("Vui lòng nhập số điện thoại", "error")
      return
    }

    try {
      setPhoneLoading(true)
      toast("Đang gửi yêu cầu đăng ký bot...", "info")

      await postReq("/api/qr/register-bot", {
        phone,
        userId: qrData.userId,
        cookies: qrData.cookies,
        imei: qrData.imei,
      })

      toast("Đã gửi yêu cầu! Đợi admin duyệt.", "success")
      setTimeout(resetQr, 2000)
    } catch (e) {
      toast(e instanceof Error ? e.message : "Lỗi đăng ký bot", "error")
    } finally {
      setPhoneLoading(false)
    }
  }

  const qrOverlayOpen = qrStep !== "idle"
  const showQrBox = qrStep === "showing" || qrStep === "scanned" || qrStep === "expired" || qrStep === "confirmed"

  return (
    <>
      <div className={`AppLoading ${loading ? "" : "Hidden"}`} aria-hidden={loading ? "false" : "true"}>
        <div className="LoaderSpinner" />
        <div className="LoaderText">Đang đăng nhập...</div>
      </div>

      <main className="NxMain">
        <div className="NxCard">
          {qrStep === "loading" && (
            <div className="NxCenter">
              <div className="LoaderSpinner" />
              <p className="NxHint">Đang tạo mã QR...</p>
            </div>
          )}

          {showQrBox && (
            <div className="NxCenter">
              <div className="NxQrWrap">
                <img
                  src={qrData.image}
                  alt="QR Code"
                  className={`NxQrImg ${qrStep === "expired" || qrStep === "confirmed" ? "blurred" : ""}`}
                />

                {qrStep === "expired" && (
                  <button className="NxQrRetry" onClick={startQrLogin}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="23 4 23 10 17 10" />
                      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                    </svg>
                    Tạo lại
                  </button>
                )}

                {qrStep === "confirmed" && (
                  <div className="NxQrSuccess">
                    <svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                      <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                  </div>
                )}

                {qrStep === "scanned" && (
                  <div className="NxQrSuccess">
                    <div className="LoaderSpinner small" />
                  </div>
                )}
              </div>

              <p className="NxHint">
                {qrStep === "showing" && "Quét mã QR bằng Zalo"}
                {qrStep === "scanned" && "Đang chờ xác nhận..."}
                {qrStep === "expired" && "Mã QR đã hết hạn"}
                {qrStep === "confirmed" && "Thành công!"}
              </p>

              <button className="NxLink" onClick={resetQr}>
                ← Quay lại
              </button>
            </div>
          )}

          {qrStep === "phone" && (
            <div className="NxCenter">
              <svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>

              <h2 className="NxTitle NxTitleSub">Nhập số điện thoại</h2>
              <p className="NxHint">Số điện thoại Zalo bot vừa quét</p>

              <div className="NxInputWrap">
                <svg className="NxInputIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
                </svg>
                <input
                  className="NxInput"
                  value={qrData.phone}
                  onChange={(e) => setQrData((prev) => ({ ...prev, phone: e.target.value }))}
                  placeholder="Số điện thoại"
                  type="tel"
                  autoFocus
                />
              </div>

              <button className="NxBtnPrimary" onClick={onSubmitPhone} disabled={phoneLoading}>
                {phoneLoading ? "Đang gửi..." : "Xác nhận"}
              </button>

              <p className="NxNote">Admin sẽ duyệt yêu cầu sau khi gửi</p>
            </div>
          )}

          {!qrOverlayOpen && (
            <>
              <h1 className="NxTitle">Bot UI</h1>

              <div className="NxInputWrap">
                <svg className="NxInputIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <input
                  className="NxInput"
                  value={account}
                  onChange={(e) => setAccount(e.target.value)}
                  placeholder="Username"
                  autoComplete="username"
                />
              </div>

              <div className="NxInputWrap">
                <svg className="NxInputIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <input
                  className="NxInput"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  type="password"
                  autoComplete="current-password"
                />
              </div>

              <button className="NxBtnPrimary NxBtnLogin" onClick={onLogin} disabled={loading}>
                {loading ? "Đang xử lý..." : "Login"}
              </button>

              <div className="NxDivider">
                <span>Or</span>
              </div>

              <button className="NxBtnSecondary" onClick={startQrLogin} disabled={loading}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                  <path d="M14 14h3v3" />
                  <path d="M20 14v7h-7" />
                </svg>
                Sign in with QR code
              </button>
            </>
          )}
        </div>
      </main>
    </>
  )
}