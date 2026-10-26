# 正在输入状态（astrbot_plugin_typing_status）

中文 | [English](README.en.md)

让 AI 在**思考 / 回复 / 调用本地工具的时候**，QQ 私聊里显示「对方正在输入…」，
回复完自动撤下。

> **解决什么问题**：AI 思考、调工具、生成回复时，聊天窗口是静默的，你以为它挂了。
> 挂上这个状态后，你就知道它还在干活。

---

## 原理

NapCat 实现了 OneBot v11 的扩展动作 `set_input_status`：

```json
POST /set_input_status
{ "user_id": "123456789", "event_type": 1 }
```

插件在 AstrBot 的生命周期节点调用它：

| 节点 | 动作 |
|------|------|
| `on_llm_request`（LLM 开始处理） | `event_type=1`（正在输入）+ 启动心跳 |
| `after_message_sent`（消息发送完） | 停止心跳，延迟后发 `event_type=3`（撤下） |

### 为什么要心跳

QQ 客户端的「正在输入」是**一次性动画**，收到信号后约 6~10 秒自动消失。
如果这一轮任务里有长耗时步骤（本地 TTS、RVC 变声、图片生成），状态会在工具
执行期间提前过期，看起来像「已经结束了但还在等」。

所以插件在任务未结束时每隔 `heartbeat_interval` 秒补发一次信号，尽量维持显示。

> **已知限制**：QQ 客户端对重复信号有去重/节流，实际表现是「显示约 6 秒 → 短暂
> 变回在线 → 再次显示」。这是协议层面的限制，**无法完全消除**。

---

## 支持平台

**仅 `aiocqhttp` + NapCat。**

其他适配器（Telegram、微信、飞书等）会自动跳过并打 debug 日志，
**不影响正常回复**——这是刻意做的优雅降级。

---

## 配置项

| 配置 | 默认 | 说明 |
|------|------|------|
| `enable` | `true` | 总开关 |
| `group_enable` | `false` | 群聊是否也挂。**NapCat 目前只支持私聊**，群聊打开可能没反应 |
| `event_type_typing` | `1` | 开始输入的事件类型 |
| `event_type_stop` | `3` | 结束输入的事件类型（实测 `0`/`2`/`4` 都无效） |
| `heartbeat_interval` | `5` | 心跳续期间隔（秒）。任务未结束期间每隔这么久补发一次 |
| `clear_delay` | `3` | 消息发送完后延迟多久撤下，避免分段回复时闪烁 |

---

## 安装

1. 把本插件目录放到 `AstrBot/data/plugins/astrbot_plugin_typing_status/`
2. 重启 AstrBot（或在 WebUI 插件页重载）
3. 私聊 AI，看聊天窗口顶部是否出现「对方正在输入…」

无需额外依赖（`requirements.txt` 为空）。

---

## 注意事项

- **只对私聊生效**：NapCat 的 `sendShowInputStatusReq` 里 `chatType` 固定为
  `KCHATTYPEC2C`，群聊不会显示
- **PC 端 QQ NT 不显示**：手机 QQ 能显示，PC 版客户端不渲染这个状态
- AI 回复特别快（< 1 秒）时，「正在输入」可能一闪而过，属于正常
- 显示会周期性闪烁（见上文「已知限制」）

---

## License

MIT

---

## English

AstrBot plugin that shows the **"typing…" indicator** in QQ private chats while the
LLM is thinking or generating a reply, and clears it automatically afterwards.

- **Works with:** AstrBot + NapCat (OneBot v11) only — skips other platforms gracefully
- **Heartbeat:** re-sends the signal every `heartbeat_interval` seconds so long-running
  tools (local TTS, voice conversion, image generation) don't make the bot look dead
- **Known limitation:** QQ clients de-duplicate repeated signals, so the indicator
  cycles on/off (~6s on). This is a protocol limitation, not a bug
- **Not supported:** group chats (NapCat hardcodes private-chat type), and PC QQ NT
  does not render the indicator at all

Full English documentation: [README.en.md](README.en.md)
