#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

PLUGIN_ROOT = Path(__file__).resolve().parent
SERVICE_KEY = "hanauta_mail"
EMAIL_CLIENT = PLUGIN_ROOT / "email_client.py"


def _launch_mail(window, api: dict[str, object]) -> None:
    status = getattr(window, "hanauta_mail_status", None)
    if not EMAIL_CLIENT.exists():
        if isinstance(status, QLabel):
            status.setText("email_client.py not found in plugin folder.")
        return
    entry_command = api.get("entry_command")
    run_bg = api.get("run_bg")
    command: list[str] = []
    if callable(entry_command):
        try:
            command = list(entry_command(EMAIL_CLIENT))
        except Exception:
            command = []
    if not command:
        command = ["python3", str(EMAIL_CLIENT)]

    if callable(run_bg):
        try:
            run_bg(command)
        except Exception:
            pass
    else:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    if isinstance(status, QLabel):
        status.setText("Opened Hanauta Mail.")


def build_mail_service_section(window, api: dict[str, object]) -> QWidget:
    SettingsRow = api["SettingsRow"]
    ExpandableServiceSection = api["ExpandableServiceSection"]
    material_icon = api["material_icon"]

    content = QWidget()
    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    open_button = QPushButton("Open Hanauta Mail")
    open_button.setObjectName("secondaryButton")
    open_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    open_button.clicked.connect(lambda: _launch_mail(window, api))

    layout.addWidget(
        SettingsRow(
            material_icon("open_in_new"),
            "Open Mail",
            "Launch the standalone Hanauta Mail plugin client.",
            window.icon_font,
            window.ui_font,
            open_button,
        )
    )

    status = QLabel("Hanauta Mail is now provided by plugin.")
    status.setWordWrap(True)
    status.setStyleSheet("color: rgba(246,235,247,0.72);")
    layout.addWidget(status)
    window.hanauta_mail_status = status

    section = ExpandableServiceSection(
        SERVICE_KEY,
        "Hanauta Mail",
        "Standalone mail plugin service.",
        material_icon("mail"),
        window.icon_font,
        window.ui_font,
        content,
        window._service_enabled(SERVICE_KEY),
        lambda enabled: window._set_service_enabled(SERVICE_KEY, enabled),
    )
    window.service_sections[SERVICE_KEY] = section
    return section


def register_hanauta_plugin() -> dict[str, object]:
    return {
        "id": SERVICE_KEY,
        "name": "Hanauta Mail",
        "api_min_version": 1,
        "service_sections": [
            {
                "key": SERVICE_KEY,
                "builder": build_mail_service_section,
                "supports_show_on_bar": False,
            }
        ],
    }
