import React from "react"
import { createRoot } from "react-dom/client"
import LoginApp from "./App"

const el = document.getElementById("root")
if (el) {
  createRoot(el).render(
    <React.StrictMode>
      <LoginApp />
    </React.StrictMode>,
  )
}
