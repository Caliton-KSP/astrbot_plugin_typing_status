# 更新日志

本文件记录本插件的所有重要变更。
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-10-26

### 新增

- **心跳续期**：任务未结束期间，每隔 `heartbeat_interval` 秒补发一次
  `set_input_status` 信号，避免长耗时工具（本地 TTS、RVC 变声、图片生成）
  执行时「正在输入」提前过期
- **延迟撤下**：消息发送完后延迟 `clear_delay` 秒才撤下状态，避免分段回复时
  每段之间反复闪烁
- 两个新配置项：`heartbeat_interval`（默认 5 秒）、`clear_delay`（默认 3 秒）

### 变更

- 心跳和撤下操作改为按会话（umo）分别管理的 asyncio 任务，支持多会话并发
- 日志级别下调：正常流程走 `debug`，不再刷屏；平台不匹配时静默跳过

### 修复

- 分段回复时状态在每段之间闪烁的问题

## [1.0.0] - 2026-10-26

### 新增

- 首次发布
- LLM 开始处理时挂「对方正在输入」（`on_llm_request` → `set_input_status`
  `event_type=1`）
- 消息发送完后撤下（`after_message_sent` → `event_type=3`）
- 非 `aiocqhttp` 平台自动跳过，不影响正常回复
- 支持配置开关、群聊开关、两个事件类型值

---

## 已知限制（非缺陷）

以下均为 QQ 客户端 / NapCat 侧的限制，插件层面无法消除：

- 「正在输入」是一次性动画，约 6~10 秒自动消失
- 客户端对重复信号有去重/节流，表现为周期性闪烁（约 6 秒显示 + 短暂在线）
- `set_input_status` 仅支持私聊（NapCat 内 `chatType` 固定为 `KCHATTYPEC2C`）
- PC 端 QQ NT 不渲染该状态，仅手机 QQ 可见

## 英文版

[README.en.md](README.en.md)
