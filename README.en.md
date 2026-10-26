# Typing Status (astrbot_plugin_typing_status)

Show a **"typing…" indicator** in QQ private chats while the LLM is thinking or
generating a reply, and clear it automatically once the message is sent.

> **Problem it solves:** while the AI is thinking, calling tools, or generating a
> long answer, the chat window is completely silent — you can't tell whether it's
> still working or has crashed. With this plugin you can see it's alive.

---

## How it works

NapCat implements the OneBot v11 extension action `set_input_status`:

```json
POST /set_input_status
{ "user_id": "123456789", "event_type": 1 }
```

The plugin calls it at two points in the AstrBot lifecycle:

| Hook | Action |
|------|--------|
| `on_llm_request` (LLM starts processing) | `event_type=1` (typing) |
| `after_message_sent` (reply delivered) | `event_type=3` (clear) |

> **Note on `event_type` values.** Only `1` reliably *shows* the indicator.
> For clearing it, `3` worked empirically on QQ/NapCat; `0`, `2` and `4` did not.
> Both values are configurable, so you can adjust them for your own NapCat version.

---

## Supported platforms

**Only `aiocqhttp` + NapCat.**

Other adapters (Telegram, WeChat, Feishu, …) are skipped automatically — the plugin
is designed to degrade gracefully and will **never** interfere with normal replies.

---

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `enable` | `true` | Master switch |
| `group_enable` | `false` | Also show in group chats. **NapCat currently supports private chats only**; enabling this may have no effect |
| `event_type_typing` | `1` | Event type sent when the LLM starts |
| `event_type_stop` | `3` | Event type sent when the reply is delivered |

---

## Installation

1. Copy this directory to `AstrBot/data/plugins/astrbot_plugin_typing_status/`
2. Restart AstrBot (or reload plugins from the dashboard)
3. The plugin is enabled by default — no further configuration required

---

## Known limitations

- **QQ clients render the indicator themselves.** The text ("typing…" /
  "对方正在输入") is hard-coded by the QQ client and **cannot be customised**
  server-side. Only the *signal* is under our control.
- **QQ NT for PC does not render the indicator at all.** It shows up on mobile
  QQ clients only. This is a client-side limitation, not a plugin bug.
- **Group chats are not supported** by NapCat's `set_input_status` at the time
  of writing.

---

## License

MIT — see [LICENSE](LICENSE).
