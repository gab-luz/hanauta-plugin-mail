# hanauta-plugin-hanauta-mail

Standalone Hanauta Mail plugin extracted from core Hanauta.

## Location
This plugin lives at:
- `/mnt/outros/DEV/hanauta-plugin-mail`

## WebUI
- Uses `code.html` as the primary WebUI source.
- `email_client.py` renders `code.html` in a Qt WebEngine window with a runtime React/Tailwind wrapper.

## Theme behavior
- When Hanauta is in light mode (`appearance.theme_choice == light` or `appearance.theme_mode == light`), the mail UI automatically switches to light appearance mode.
- Otherwise it uses dark mode.

## Plugin entrypoints
- `hanauta_plugin.py` (service registration)
- `email_client.py` (mail UI launcher)

## Included extracted code
- `plugin_core/mail_store.py`
- `plugin_core/xdg_mail.py`
- `open_mail_message.py`
- `config/applications/hanauta-mail.desktop`
- `scripts/install_mail_desktop.sh`
- `scripts/install_mail_desktop_system.sh`
- `assets/hanauta-mail.svg`
- `assets/hanauta-mail.png`
