#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow

try:
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyQt6 WebEngine is required for Hanauta Mail WebUI: {exc}")

PLUGIN_ROOT = Path(__file__).resolve().parent
CODE_HTML = PLUGIN_ROOT / "code.html"
SETTINGS_FILE = Path.home() / ".local" / "state" / "hanauta" / "notification-center" / "settings.json"

ICON_NAMES = [
    "Archive",
    "Bell",
    "CheckCircle2",
    "ChevronDown",
    "Clock",
    "Inbox",
    "Mail",
    "MailOpen",
    "Menu",
    "MoreVertical",
    "Paperclip",
    "Pencil",
    "Plus",
    "Reply",
    "Search",
    "Send",
    "Settings",
    "ShieldCheck",
    "Sparkles",
    "Star",
    "Trash2",
    "UserCircle2",
    "X",
]


def _load_theme_mode() -> str:
    try:
        payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return "dark"
    appearance = payload.get("appearance", {}) if isinstance(payload, dict) else {}
    if not isinstance(appearance, dict):
        return "dark"
    theme_choice = str(appearance.get("theme_choice", "")).strip().lower()
    theme_mode = str(appearance.get("theme_mode", "")).strip().lower()
    if theme_choice == "light" or theme_mode == "light":
        return "light"
    return "dark"


def _transform_code_to_babel(code: str) -> str:
    transformed = code
    transformed = re.sub(r"^\s*import\s+React[^\n]*\n", "", transformed, flags=re.M)
    transformed = re.sub(r"^\s*import\s+\{\s*motion\s*,\s*AnimatePresence\s*\}\s+from\s+\"framer-motion\";?\s*$", "", transformed, flags=re.M)
    transformed = re.sub(r"^\s*import\s+\{[\s\S]*?\}\s+from\s+\"lucide-react\";?\s*$", "", transformed, flags=re.M)
    transformed = re.sub(r"^\s*layout\s*$", "", transformed, flags=re.M)
    transformed = transformed.replace("export default function HanautaEmailInterface()", "function HanautaEmailInterface()")

    icon_defs = "\n".join(
        f"const {name} = (props) => React.createElement('span', {{...props, style: {{display: 'inline-block', width: '1em', height: '1em', borderRadius: '999px', border: '1.4px solid currentColor'}}}});"
        for name in ICON_NAMES
    )

    scaffolding = f"""
const {{ useMemo, useState }} = React;
const motion = new Proxy({{}}, {{
  get: (_target, key) => (props) => React.createElement(typeof key === 'string' ? key : 'div', props, props && props.children)
}});
const AnimatePresence = ({{ children }}) => React.createElement(React.Fragment, null, children);
{icon_defs}
"""

    render_call = """
const rootEl = document.getElementById('root');
if (rootEl) {
  const root = ReactDOM.createRoot(rootEl);
  root.render(React.createElement(HanautaEmailInterface));
}
"""

    return scaffolding + "\n" + transformed + "\n" + render_call


def _build_runtime_html(theme_mode: str) -> str:
    if not CODE_HTML.exists():
        raise FileNotFoundError(f"Missing WebUI source: {CODE_HTML}")
    raw = CODE_HTML.read_text(encoding="utf-8")
    babel_code = _transform_code_to_babel(raw)

    light_css = ""
    if theme_mode == "light":
        light_css = """
:root { color-scheme: light; }
body[data-theme='light'] {
  filter: invert(1) hue-rotate(180deg) saturate(0.95);
  background: #f5f7fb !important;
}
body[data-theme='light'] img,
body[data-theme='light'] svg,
body[data-theme='light'] video,
body[data-theme='light'] canvas {
  filter: invert(1) hue-rotate(180deg);
}
"""

    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Hanauta Mail</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <script crossorigin src=\"https://unpkg.com/react@18/umd/react.development.js\"></script>
    <script crossorigin src=\"https://unpkg.com/react-dom@18/umd/react-dom.development.js\"></script>
    <script src=\"https://unpkg.com/@babel/standalone/babel.min.js\"></script>
    <style>
      html, body, #root {{ width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden; }}
      {light_css}
    </style>
  </head>
  <body data-theme=\"{theme_mode}\">
    <div id=\"root\"></div>
    <script type=\"text/babel\" data-presets=\"env,react\">{babel_code}</script>
  </body>
</html>
"""


class MailWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hanauta Mail")
        self.resize(1360, 860)
        self.web = QWebEngineView(self)
        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.web.loadStarted.connect(lambda: print("[hanauta-mail] WebUI load started"))
        self.web.loadFinished.connect(self._on_load_finished)
        self.setCentralWidget(self.web)

        theme_mode = _load_theme_mode()
        html = _build_runtime_html(theme_mode)
        self.web.setHtml(html, baseUrl=QUrl.fromLocalFile(str(PLUGIN_ROOT) + "/"))

    def _on_load_finished(self, ok: bool) -> None:
        if ok:
            print("[hanauta-mail] WebUI load finished successfully")
            return
        print("[hanauta-mail] WebUI failed to load")


def main() -> int:
    chromium_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
    if "--disable-vulkan" not in chromium_flags:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (chromium_flags + " --disable-vulkan").strip()
    app = QApplication(sys.argv)
    window = MailWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
