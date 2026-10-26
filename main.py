# -*- coding: utf-8 -*-
"""让 AI 在思考 / 回复 / 调用本地工具期间持续挂「对方正在输入」状态。

原理：NapCat 提供 `set_input_status` 动作（OneBot v11 扩展）。

QQ 客户端的输入状态大约 10 秒会自动消失。如果这一轮任务里包含长耗时步骤
（例如本地 TTS、RVC 变声、图片生成），状态会在工具执行期间提前过期，看起来
像「已经结束了但还在等」。本插件用心跳续期解决：

- 任务开始（on_llm_request）：立即挂上，并启动心跳，每 N 秒续一次
- 消息发送完（after_message_sent）：取消心跳，短暂延迟后撤下
  （延迟是为了兼容分段回复，避免每段之间状态闪烁）

非 NapCat 适配器自动跳过，不影响正常回复。
"""

import asyncio

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


def _split_umo(umo: str):
    """QQchat:FriendMessage:123456789 -> ("FriendMessage", "123456789")"""
    parts = str(umo or "").split(":")
    if len(parts) < 3:
        return None, None
    return parts[-2], parts[-1]


@register(
    "astrbot_plugin_typing_status",
    "Caliton-KSP",
    "LLM 思考/回复/调用本地工具期间持续挂「对方正在输入」（心跳续期），结束后撤下",
    "1.1.0",
)
class TypingStatus(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context, config)
        self.cfg = config or {}
        # umo -> 心跳任务 / 延迟撤下任务 / bot 实例
        self._hb: dict[str, asyncio.Task] = {}
        self._clear: dict[str, asyncio.Task] = {}
        self._bots: dict[str, object] = {}

    # ---------- 配置读取 ----------

    def _event_type_typing(self) -> int:
        return int(self.cfg.get("event_type_typing", 1))

    def _event_type_stop(self) -> int:
        return int(self.cfg.get("event_type_stop", 3))

    def _interval(self) -> float:
        return max(2.0, float(self.cfg.get("heartbeat_interval", 5)))

    def _delay(self) -> float:
        return max(0.0, float(self.cfg.get("clear_delay", 3)))

    # ---------- 通用判断 ----------

    def _should(self, event: AstrMessageEvent) -> bool:
        try:
            if not self.cfg.get("enable", True):
                return False
            if event.get_platform_name() != "aiocqhttp":
                logger.debug(
                    f"[typing_status] 平台={event.get_platform_name()}，跳过"
                )
                return False
            kind, sid = _split_umo(event.unified_msg_origin)
            if not sid:
                logger.debug(f"[typing_status] 无法解析 umo={event.unified_msg_origin}")
                return False
            if kind == "GroupMessage" and not self.cfg.get("group_enable", False):
                return False
            return True
        except Exception as e:
            logger.warning(f"[typing_status] _should 异常: {e}")
            return False

    # ---------- 实际发请求 ----------

    async def _send(self, bot, sid: str, event_type: int, tag: str = "") -> None:
        try:
            await bot.call_action(
                "set_input_status",
                user_id=str(sid),
                event_type=int(event_type),
            )
            logger.debug(f"[typing_status] {tag} event_type={event_type} sid={sid}")
        except Exception as e:
            logger.debug(f"[typing_status] {tag} 失败（非 NapCat 可忽略）: {e}")

    # ---------- 心跳 ----------

    async def _heartbeat(self, umo: str, bot, sid: str) -> None:
        """只要任务没结束，就每 N 秒续一次，防止客户端 10 秒过期。"""
        try:
            while True:
                await asyncio.sleep(self._interval())
                await self._send(bot, sid, self._event_type_typing(), "heartbeat")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.debug(f"[typing_status] 心跳异常退出: {e}")

    def _start_typing(self, umo: str, bot, sid: str) -> None:
        self._bots[umo] = bot
        # 有未执行的撤下任务就取消（新一轮开始了）
        old_clear = self._clear.pop(umo, None)
        if old_clear and not old_clear.done():
            old_clear.cancel()
        # 心跳已在跑就不重复启动
        old_hb = self._hb.get(umo)
        if old_hb and not old_hb.done():
            return
        self._hb[umo] = asyncio.create_task(self._heartbeat(umo, bot, sid))

    async def _delayed_clear(self, umo: str, bot, sid: str) -> None:
        """等一小段再撤下，兼容分段回复；期间若有新消息会取消本任务。"""
        try:
            delay = self._delay()
            if delay:
                await asyncio.sleep(delay)
            await self._send(bot, sid, self._event_type_stop(), "clear")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.debug(f"[typing_status] 撤下异常: {e}")
        finally:
            hb = self._hb.pop(umo, None)
            if hb and not hb.done():
                hb.cancel()
            self._clear.pop(umo, None)
            self._bots.pop(umo, None)

    # ---------- 生命周期钩子 ----------

    @filter.on_llm_request()
    async def mark_typing(self, event: AstrMessageEvent, req) -> None:
        if not self._should(event):
            return
        _, sid = _split_umo(event.unified_msg_origin)
        umo = event.unified_msg_origin
        bot = event.bot
        self._start_typing(umo, bot, sid)
        await self._send(bot, sid, self._event_type_typing(), "start")

    @filter.after_message_sent()
    async def clear_typing(self, event: AstrMessageEvent) -> None:
        if not self._should(event):
            return
        _, sid = _split_umo(event.unified_msg_origin)
        umo = event.unified_msg_origin
        bot = event.bot
        old = self._clear.pop(umo, None)
        if old and not old.done():
            old.cancel()
        self._clear[umo] = asyncio.create_task(self._delayed_clear(umo, bot, sid))
