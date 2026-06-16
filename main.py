from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import unquote

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

try:
    from astrbot.api import AstrBotConfig
except Exception:  # pragma: no cover
    AstrBotConfig = dict  # type: ignore


SKY_O_LINK_RE = re.compile(
    r"(?:https?://|sky://)?sky\.thatg\.co/o=([A-Za-z0-9_\-+/=%]+)",
    re.IGNORECASE,
)
RAW_O_RE = re.compile(r"\bo=([A-Za-z0-9_\-+/=%]{24,})", re.IGNORECASE)

DEFAULT_FORMULA_BASE = 7.6
DEFAULT_SCALE_COEFFICIENT = 8.3
DEFAULT_HEIGHT_COEFFICIENT = 3.0
DEFAULT_TALLEST_HEIGHT_VALUE = 2.0
DEFAULT_SHORTEST_HEIGHT_VALUE = -2.0
DEFAULT_TIMEZONE_OFFSET = 8

OUTFIT_LABELS = (
    ("body", "裤子"),
    ("wing", "斗篷"),
    ("hair", "发型"),
    ("mask", "面具"),
    ("neck", "项链"),
    ("feet", "鞋子"),
    ("horn", "角饰"),
    ("face", "脸饰"),
    ("prop", "背饰"),
    ("hat", "头饰"),
)


@register(
    name="astrbot_plugin_sky_o_height_decoder",
    desc="解析 sky.thatg.co/o= 扫码链接中的光遇身高数据",
    version="1.0.0",
    author="hp",
)
class Main(Star):
    def __init__(self, context: Context, config: Optional["AstrBotConfig"] = None):
        super().__init__(context)
        self.config = config or {}

    @filter.regex(r"^\s*[/!！。.]?\s*(?:扫码身高帮助|o身高帮助|光遇扫码身高帮助)\s*$")
    async def help_handler(self, event: AstrMessageEvent):
        yield event.plain_result(self._help_text())

    @filter.regex(r"(?is).*(?:sky\.thatg\.co/o=|\bo=[A-Za-z0-9_\-+/=%]{24,}).*")
    async def decode_handler(self, event: AstrMessageEvent):
        message = self._get_message_text(event)
        payload = self._extract_payload(message)
        if not payload:
            return

        try:
            decoded = self.decode_payload(payload)
            output = self._format_result(decoded)
            yield event.plain_result(output)
        except ValueError as exc:
            logger.warning("sky o height decode failed: %s", exc)
            yield event.plain_result(f"解析失败：{exc}")
        except Exception as exc:
            logger.exception("sky o height decode unexpected error")
            yield event.plain_result(f"解析失败：{exc}")
        finally:
            self._stop_event(event)

    @classmethod
    def decode_url(cls, text: str) -> Dict[str, Any]:
        payload = cls._extract_payload_from_text(text)
        if not payload:
            raise ValueError("没有找到 sky.thatg.co/o= 数据")
        return cls.decode_payload(payload)

    @classmethod
    def decode_payload(cls, payload: str) -> Dict[str, Any]:
        cleaned = cls._clean_payload(payload)
        if not cleaned:
            raise ValueError("o= 后面的数据为空")

        try:
            compressed = base64.urlsafe_b64decode(cleaned + "=" * ((4 - len(cleaned) % 4) % 4))
        except Exception as exc:
            raise ValueError("Base64 解码失败，请确认链接是否完整") from exc

        if not compressed:
            raise ValueError("Base64 解码结果为空")

        try:
            raw = cls._lz4_block_decompress(compressed)
        except Exception as exc:
            raise ValueError("LZ4 解压失败，请确认链接是否完整") from exc

        try:
            decoded_text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("解压后不是 UTF-8 文本") from exc

        try:
            payload_obj = json.loads(decoded_text)
        except json.JSONDecodeError as exc:
            raise ValueError("解压后不是合法 JSON") from exc

        if not isinstance(payload_obj, dict):
            raise ValueError("JSON 根节点不是对象")
        return payload_obj

    @classmethod
    def _extract_payload_from_text(cls, text: str) -> str:
        raw = str(text or "").strip()
        if not raw:
            return ""

        link_match = SKY_O_LINK_RE.search(raw)
        if link_match:
            return cls._clean_payload(link_match.group(1))

        raw_match = RAW_O_RE.search(raw)
        if raw_match:
            return cls._clean_payload(raw_match.group(1))

        return ""

    def _extract_payload(self, text: str) -> str:
        return self._extract_payload_from_text(text)

    @staticmethod
    def _clean_payload(payload: str) -> str:
        text = unquote(str(payload or "")).strip()
        text = re.split(r"[\s<>\]\)）】。；;，,]+", text, maxsplit=1)[0]
        return text.rstrip("=")

    @staticmethod
    def _lz4_block_decompress(src: bytes) -> bytes:
        i = 0
        out = bytearray()
        n = len(src)

        while i < n:
            token = src[i]
            i += 1

            literal_len = token >> 4
            if literal_len == 15:
                while True:
                    if i >= n:
                        raise ValueError("literal length truncated")
                    b = src[i]
                    i += 1
                    literal_len += b
                    if b != 255:
                        break

            if i + literal_len > n:
                raise ValueError("literal data truncated")
            out.extend(src[i : i + literal_len])
            i += literal_len

            if i >= n:
                break

            if i + 2 > n:
                raise ValueError("offset truncated")
            offset = src[i] | (src[i + 1] << 8)
            i += 2
            if offset <= 0 or offset > len(out):
                raise ValueError("invalid match offset")

            match_len = token & 0x0F
            if match_len == 15:
                while True:
                    if i >= n:
                        raise ValueError("match length truncated")
                    b = src[i]
                    i += 1
                    match_len += b
                    if b != 255:
                        break
            match_len += 4

            start = len(out) - offset
            for j in range(match_len):
                out.append(out[start + j])

        return bytes(out)

    def _format_result(self, decoded: Dict[str, Any]) -> str:
        height = self._to_float(decoded.get("height"))
        scale = self._to_float(decoded.get("scale"))
        if height is None:
            raise ValueError("数据中缺少 height 身高值")
        if scale is None:
            raise ValueError("数据中缺少 scale 体型值")

        current_height = self._calculate_height_index(height_value=height, scale=scale)
        max_height = self._calculate_height_index(
            height_value=self._cfg_float("tallest_height_value", DEFAULT_TALLEST_HEIGHT_VALUE),
            scale=scale,
        )
        min_height = self._calculate_height_index(
            height_value=self._cfg_float("shortest_height_value", DEFAULT_SHORTEST_HEIGHT_VALUE),
            scale=scale,
        )
        query_time = self._now_text()

        lines = [
            "光遇扫码身高解析成功",
            "==================",
            f"体型值：{self._fmt_number(scale)}",
            f"身高值：{self._fmt_number(height)}",
            f"当前身高：{self._fmt_number(current_height)}",
            f"最高身高：{self._fmt_number(max_height)}",
            f"最矮身高：{self._fmt_number(min_height)}",
            f"查询时间：{query_time}",
        ]

        self._append_outfit_lines(lines, decoded)
        lines.append("==================")
        return "\n".join(lines)

    def _append_outfit_lines(self, lines: list[str], decoded: Dict[str, Any]) -> None:
        outfit_lines = []
        for key, label in OUTFIT_LABELS:
            value = decoded.get(key)
            if isinstance(value, dict):
                outfit_lines.append(f"{label}：{self._format_outfit_item(value)}")
            elif value is not None and str(value).strip():
                outfit_lines.append(f"{label}：{value}")

        if outfit_lines:
            lines.extend(["==================", "装扮信息"])
            lines.extend(outfit_lines)

    def _format_outfit_item(self, item: Dict[str, Any]) -> str:
        return f"ID {self._value_text(item.get('id'))}"

    def _calculate_height_index(self, height_value: float, scale: float) -> float:
        base = self._cfg_float("formula_base", DEFAULT_FORMULA_BASE)
        scale_coefficient = self._cfg_float("scale_coefficient", DEFAULT_SCALE_COEFFICIENT)
        height_coefficient = self._cfg_float("height_coefficient", DEFAULT_HEIGHT_COEFFICIENT)
        return base - scale_coefficient * scale - height_coefficient * height_value

    def _now_text(self) -> str:
        tz = timezone(timedelta(hours=self._cfg_int("timezone_offset", DEFAULT_TIMEZONE_OFFSET)))
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    def _help_text(self) -> str:
        return (
            "光遇扫码身高解析使用说明\n"
            "==================\n"
            "发送 sky.thatg.co/o= 开头的扫码链接即可解析。\n"
            "返回：体型值、身高值、当前身高、最高身高、最矮身高、查询时间。\n"
            "==================\n"
            "说明：解析过程完全离线，不会消费好友码。"
        )

    def _get_message_text(self, event: AstrMessageEvent) -> str:
        if hasattr(event, "get_message_str") and callable(event.get_message_str):
            try:
                return str(event.get_message_str() or "").strip()
            except Exception:
                pass
        return str(getattr(event, "message_str", "") or "").strip()

    def _stop_event(self, event: AstrMessageEvent) -> None:
        try:
            event.stop_event()
        except Exception:
            pass

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None or str(value).strip() == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _fmt_number(value: Any) -> str:
        try:
            text = f"{float(value):.9f}".rstrip("0").rstrip(".")
            return text if text else "0"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _value_text(value: Any) -> str:
        if value is None or str(value).strip() == "":
            return "未知"
        return str(value).strip()

    def _cfg(self, key: str, default: Any) -> Any:
        try:
            return self.config.get(key, default)
        except Exception:
            return default

    def _cfg_int(self, key: str, default: int) -> int:
        value = self._cfg(key, default)
        try:
            return int(value)
        except Exception:
            return default

    def _cfg_float(self, key: str, default: float) -> float:
        value = self._cfg(key, default)
        try:
            return float(value)
        except Exception:
            return default

    async def terminate(self):
        logger.info("sky o height decoder plugin unloaded")


SkyOHeightDecoderPlugin = Main
