#!/usr/bin/env python3
"""Monitor configured Telegram chats and notify the session owner via Bot API."""

import asyncio
import hashlib
import logging
import os
import re
import sqlite3
import tempfile
import unicodedata
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from telegram import Bot, InputFile
from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError, TimedOut
from telethon import TelegramClient, events, utils
from telethon.errors import FloodWaitError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.types import ChatInviteAlready


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("chat_monitor")
# Bot API tokens are embedded in request URLs, so third-party HTTP logs must
# never be emitted at INFO/DEBUG level.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.request").setLevel(logging.WARNING)

APP_DIR = Path(__file__).resolve().parent
CHATS_FILE = Path(os.getenv("MONITOR_CHATS_FILE", APP_DIR / "config/monitor_chats.txt"))
KEYWORDS_FILE = Path(os.getenv("MONITOR_KEYWORDS_FILE", APP_DIR / "config/keywords.txt"))
SOURCE_SESSION = Path(os.getenv("SESSION_FILE", APP_DIR / "botAccount.session"))
RUNTIME_SESSION = Path(os.getenv("MONITOR_SESSION_FILE", APP_DIR / "monitorAccount.session"))
CONFIG_RELOAD_SECONDS = 10
MESSAGE_LIMIT = 4000
LOCAL_TZ = ZoneInfo("Asia/Novosibirsk")


def read_config_lines(path: Path) -> List[str]:
    """Return non-empty, non-comment lines from a UTF-8 text config."""
    if not path.exists():
        logger.warning("Конфиг не найден: %s", path)
        return []

    result: List[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            result.append(line)
    return result


def normalized_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value or "").casefold()


def compile_keywords(keywords: Iterable[str]) -> List[Tuple[str, re.Pattern]]:
    """Compile ordered keyword patterns with Unicode word boundaries."""
    result: List[Tuple[str, re.Pattern]] = []
    seen: Set[str] = set()

    for original in keywords:
        keyword = normalized_text(original.strip())
        if not keyword or keyword in seen:
            continue
        seen.add(keyword)

        prefix = r"(?<!\w)" if keyword[0].isalnum() else ""
        suffix = r"(?!\w)" if keyword[-1].isalnum() else ""
        result.append((original.strip(), re.compile(prefix + re.escape(keyword) + suffix)))

    return result


def find_keywords(text: str, patterns: Sequence[Tuple[str, re.Pattern]]) -> List[str]:
    haystack = normalized_text(text)
    return [original for original, pattern in patterns if pattern.search(haystack)]


def split_text(text: str, limit: int = MESSAGE_LIMIT) -> List[str]:
    """Split long Bot API messages, preferring newline boundaries."""
    text = text or ""
    if len(text) <= limit:
        return [text]

    chunks: List[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            chunks.append(rest)
            break
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip("\n")
    return chunks


def prepare_monitor_session(source: Path, destination_base: Path) -> Path:
    """Create a persistent independent SQLite state file for the monitor."""
    source = source if source.suffix == ".session" else source.with_suffix(".session")
    destination = destination_base.with_suffix(".session")
    if not source.exists():
        raise FileNotFoundError(f"Файл Telegram-сессии не найден: {source}")

    # Keep the monitor's update state between container restarts. Re-copying the
    # main session would move its pts forward and could permanently skip events
    # that arrived while the assortment updater owned the Telegram connection.
    if destination.exists() and destination.stat().st_size > 0:
        return destination_base

    source_uri = f"file:{source.resolve()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
    return destination_base


def parse_chat_reference(value: str) -> Tuple[str, str]:
    """Return (kind, value), where kind is public, invite, or id."""
    value = value.strip()
    if re.fullmatch(r"-?\d+", value):
        return "id", value

    if value.startswith("@"):
        return "public", value

    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        if parsed.netloc.lower() not in {"t.me", "www.t.me", "telegram.me", "www.telegram.me"}:
            raise ValueError(f"Неизвестный Telegram URL: {value}")
        path = parsed.path.strip("/")
        if path.startswith("+"):
            return "invite", path[1:]
        if path.startswith("joinchat/"):
            return "invite", path.split("/", 1)[1]
        if not path or path.startswith("c/"):
            raise ValueError(f"Нужен username чата или invite-ссылка: {value}")
        return "public", f"@{path.split('/', 1)[0]}"

    return "public", f"@{value}"


class ChatMonitor:
    def __init__(self) -> None:
        api_id = int(os.environ["TELEGRAM_API_ID"])
        api_hash = os.environ["TELEGRAM_API_HASH"]
        bot_token = os.environ["TELEGRAM_BOT_TOKEN"]

        runtime_session = prepare_monitor_session(SOURCE_SESSION, RUNTIME_SESSION)
        self.client = TelegramClient(str(runtime_session), api_id, api_hash)
        self.bot = Bot(bot_token)
        self.destination_chat_id: Optional[int] = None
        self.allowed_chat_ids: Set[int] = set()
        self.keyword_patterns: List[Tuple[str, re.Pattern]] = []
        self._config_digest = ""
        self._send_lock = asyncio.Lock()
        self._seen: Set[Tuple[int, int]] = set()
        self._seen_order: List[Tuple[int, int]] = []
        self._watcher_task: Optional[asyncio.Task] = None

    async def run(self) -> None:
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError(f"Telegram-сессия не авторизована: {SOURCE_SESSION}")

        session_user = await self.client.get_me()
        self.destination_chat_id = session_user.id
        logger.info(
            "Telethon-сессия: %s (@%s), destination_chat_id=%s",
            utils.get_display_name(session_user),
            session_user.username or "без_username",
            self.destination_chat_id,
        )

        await self.bot.initialize()
        bot_user = await self.bot.get_me()
        logger.info("Bot API отправитель: %s (@%s)", bot_user.first_name, bot_user.username)
        await self._check_destination_access()

        self.client.add_event_handler(self._handle_message, events.NewMessage())
        self.client.add_event_handler(self._handle_album, events.Album())
        await self._reload_configuration(force=True)
        self._watcher_task = asyncio.create_task(self._watch_configuration())

        logger.info("Монитор запущен")
        try:
            await self.client.run_until_disconnected()
        finally:
            if self._watcher_task:
                self._watcher_task.cancel()
                await asyncio.gather(self._watcher_task, return_exceptions=True)
            await self.bot.shutdown()
            await self.client.disconnect()

    async def _check_destination_access(self) -> None:
        try:
            chat = await self.bot.get_chat(self.destination_chat_id)
            logger.info("Личная переписка с получателем доступна: %s", chat.id)
        except Forbidden:
            logger.error(
                "@GodElisManagerBot не может написать пользователю %s. "
                "Откройте бота с аккаунта сессии и нажмите /start.",
                self.destination_chat_id,
            )
        except TelegramError as exc:
            logger.warning("Не удалось проверить личную переписку: %s", exc)

    async def _watch_configuration(self) -> None:
        while True:
            await asyncio.sleep(CONFIG_RELOAD_SECONDS)
            try:
                if not self.client.is_connected():
                    await self.client.connect()
                # The assortment updater opens the same Telegram account through
                # short-lived clients. Telegram may route live updates to those
                # connections, so explicitly request and dispatch anything missed.
                await self.client.catch_up()
            except Exception:
                logger.exception("Не удалось получить пропущенные Telegram-события")
            try:
                await self._reload_configuration()
            except Exception:
                logger.exception("Ошибка горячей перезагрузки конфигурации")

    def _configuration_digest(self) -> str:
        payload = b""
        for path in (CHATS_FILE, KEYWORDS_FILE):
            payload += str(path).encode("utf-8") + b"\0"
            if path.exists():
                payload += path.read_bytes()
            payload += b"\0"
        return hashlib.sha256(payload).hexdigest()

    async def _reload_configuration(self, force: bool = False) -> None:
        digest = self._configuration_digest()
        if not force and digest == self._config_digest:
            return

        keywords = read_config_lines(KEYWORDS_FILE)
        patterns = compile_keywords(keywords)
        chat_refs = read_config_lines(CHATS_FILE)
        resolved_ids = await self._resolve_chats(chat_refs)

        self.keyword_patterns = patterns
        self.allowed_chat_ids = resolved_ids
        self._config_digest = digest
        logger.info(
            "Конфигурация загружена: чатов=%d, ключевых слов=%d",
            len(resolved_ids),
            len(patterns),
        )
        if not resolved_ids:
            logger.warning("Список чатов пуст — монитор ожидает заполнения %s", CHATS_FILE)

    async def _resolve_chats(self, references: Sequence[str]) -> Set[int]:
        result: Set[int] = set()
        for reference in references:
            try:
                kind, value = parse_chat_reference(reference)
                if kind == "invite":
                    invite_info = await self.client(CheckChatInviteRequest(value))
                    if isinstance(invite_info, ChatInviteAlready):
                        entity = invite_info.chat
                    else:
                        updates = await self.client(ImportChatInviteRequest(value))
                        entity = updates.chats[0]
                elif kind == "id":
                    numeric_id = int(value)
                    result.add(numeric_id)
                    try:
                        entity = await self.client.get_entity(numeric_id)
                    except Exception:
                        logger.info("Чат добавлен по ID без получения метаданных: %s", numeric_id)
                        continue
                else:
                    entity = await self.client.get_entity(value)
                    try:
                        await self.client(JoinChannelRequest(entity))
                    except UserAlreadyParticipantError:
                        pass
                    except Exception as join_error:
                        logger.info("Чат уже доступен или не требует вступления (%s): %s", reference, join_error)

                peer_id = utils.get_peer_id(entity)
                result.add(peer_id)
                logger.info("Источник подключён: %s (%s)", utils.get_display_name(entity), peer_id)
            except FloodWaitError as exc:
                logger.error("Telegram ограничил вступление в чаты на %s сек.: %s", exc.seconds, reference)
            except Exception as exc:
                logger.error("Не удалось подключить источник %s: %s", reference, exc)
        return result

    async def _handle_message(self, event: events.NewMessage.Event) -> None:
        message = event.message
        if message.grouped_id:
            return  # Albums are processed by the Album handler.
        await self._process_messages(event.chat_id, [message], event)

    async def _handle_album(self, event: events.Album.Event) -> None:
        await self._process_messages(event.chat_id, list(event.messages), event)

    async def _process_messages(self, chat_id: int, messages: Sequence, event) -> None:
        if chat_id not in self.allowed_chat_ids or not self.keyword_patterns:
            return

        combined_text = "\n".join(message.raw_text or "" for message in messages).strip()
        matches = find_keywords(combined_text, self.keyword_patterns)
        if not matches:
            return

        unique_id = int(messages[0].grouped_id or messages[0].id)
        dedup_key = (chat_id, unique_id)
        if dedup_key in self._seen:
            return
        self._remember(dedup_key)

        async with self._send_lock:
            try:
                chat = await event.get_chat()
                sender = await messages[0].get_sender()
                header = self._build_header(chat_id, chat, sender, messages[0], matches)
                payload = f"{header}\n\n{combined_text or '[сообщение без текста]'}"
                await self._send_text(payload)
                await self._send_media(messages)
                logger.info(
                    "Совпадение отправлено: chat_id=%s message_id=%s keywords=%s",
                    chat_id,
                    messages[0].id,
                    ", ".join(matches),
                )
            except Exception:
                logger.exception("Не удалось отправить найденное сообщение")

    def _remember(self, key: Tuple[int, int]) -> None:
        self._seen.add(key)
        self._seen_order.append(key)
        if len(self._seen_order) > 5000:
            expired = self._seen_order.pop(0)
            self._seen.discard(expired)

    def _build_header(self, chat_id: int, chat, sender, message, matches: Sequence[str]) -> str:
        chat_name = utils.get_display_name(chat) or str(chat_id)
        chat_username = getattr(chat, "username", None)
        sender_name = utils.get_display_name(sender) if sender else "Неизвестный автор"
        sender_username = getattr(sender, "username", None) if sender else None

        chat_label = f"{chat_name} (@{chat_username})" if chat_username else chat_name
        sender_label = f"{sender_name} (@{sender_username})" if sender_username else sender_name
        message_link = self._message_link(chat_id, chat_username, message.id)
        date = message.date.astimezone(LOCAL_TZ).strftime("%d.%m.%Y %H:%M:%S")

        lines = [
            f"🔎 Найдено: {', '.join(matches)}",
            f"Чат: {chat_label}",
            f"Автор: {sender_label}",
        ]
        if message_link:
            lines.append(f"Оригинал: {message_link}")
        lines.append("—" * 12)
        return "\n".join(lines)

    @staticmethod
    def _message_link(chat_id: int, username: Optional[str], message_id: int) -> Optional[str]:
        if username:
            return f"https://t.me/{username}/{message_id}"
        value = str(chat_id)
        if value.startswith("-100"):
            return f"https://t.me/c/{value[4:]}/{message_id}"
        return None

    async def _send_text(self, text: str) -> None:
        for chunk in split_text(text):
            await self._retry_bot_call(self.bot.send_message, chat_id=self.destination_chat_id, text=chunk)

    async def _send_media(self, messages: Sequence) -> None:
        media_messages = [message for message in messages if message.media]
        if not media_messages:
            return

        with tempfile.TemporaryDirectory(prefix="godmanager-media-") as temp_dir:
            for message in media_messages:
                try:
                    downloaded = await self.client.download_media(message, file=temp_dir)
                    if not downloaded:
                        continue
                    path = Path(downloaded)
                    with path.open("rb") as stream:
                        media = InputFile(stream, filename=path.name)
                        if message.photo:
                            await self._retry_bot_call(
                                self.bot.send_photo,
                                chat_id=self.destination_chat_id,
                                photo=media,
                                read_timeout=120,
                                write_timeout=120,
                                connect_timeout=30,
                                pool_timeout=30,
                            )
                        elif message.video:
                            await self._retry_bot_call(
                                self.bot.send_video,
                                chat_id=self.destination_chat_id,
                                video=media,
                                read_timeout=120,
                                write_timeout=120,
                                connect_timeout=30,
                                pool_timeout=30,
                            )
                        elif message.voice:
                            await self._retry_bot_call(
                                self.bot.send_voice,
                                chat_id=self.destination_chat_id,
                                voice=media,
                                read_timeout=120,
                                write_timeout=120,
                                connect_timeout=30,
                                pool_timeout=30,
                            )
                        else:
                            await self._retry_bot_call(
                                self.bot.send_document,
                                chat_id=self.destination_chat_id,
                                document=media,
                                read_timeout=120,
                                write_timeout=120,
                                connect_timeout=30,
                                pool_timeout=30,
                            )
                except Exception as exc:
                    logger.error("Не удалось переслать вложение message_id=%s: %s", message.id, exc)

    @staticmethod
    async def _retry_bot_call(method, **kwargs):
        for attempt in range(1, 4):
            try:
                return await method(**kwargs)
            except RetryAfter as exc:
                if attempt == 3:
                    raise
                delay = getattr(exc, "retry_after", 1)
                delay = delay.total_seconds() if hasattr(delay, "total_seconds") else float(delay)
                await asyncio.sleep(delay)
            except (TimedOut, NetworkError) as exc:
                # Bot API requests are not idempotent. A timeout can mean that
                # Telegram accepted the message but the response was lost. A
                # retry would then create a duplicate, so prefer at-most-once
                # delivery and leave the original-message link as a fallback.
                logger.warning(
                    "Bot API не подтвердил отправку (%s); повтор отключён во избежание дубля",
                    type(exc).__name__,
                )
                raise


async def main() -> None:
    monitor = ChatMonitor()
    await monitor.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Монитор остановлен")
