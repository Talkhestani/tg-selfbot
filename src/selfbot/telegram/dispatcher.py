"""Command registry and event dispatcher."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from telethon import TelegramClient
from telethon.events import NewMessage
from telethon.tl.types import Message

from selfbot.messages import persian as msg
from selfbot.telegram.confirmation import ConfirmationManager
from selfbot.telegram.permissions import PermissionService
from selfbot.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)


class CommandError(Exception):
    """A user-facing command error (shown verbatim in Persian)."""


class CommandNotFoundError(CommandError):
    """Raised when an unknown command is invoked."""


CommandHandler = Callable[["CommandContext"], Awaitable[Any]]


async def reply_or_edit(message: Message, text: str, **kwargs: Any) -> Message | None:
    """Answer a command by editing its own message when possible.

    Commands are usually typed by the owner from the same account, so the
    message is outgoing and editable; this keeps the chat clean instead of
    creating a new message per command. When the message belongs to someone
    else (owner second account, group members) fall back to a normal reply.
    """
    if getattr(message, "out", False):
        try:
            return await message.edit(text, **kwargs)
        except Exception as exc:  # noqa: BLE001 - fall back to a new reply
            logger.debug("edit failed for outgoing message: %s", exc)
    return await message.respond(text, **kwargs)


@dataclass(frozen=True)
class CommandSpec:
    """Metadata for a single command."""

    name: str
    handler: CommandHandler
    category: str
    description: str
    usage: str = ""
    aliases: tuple[str, ...] = ()
    owner_only: bool = False
    sensitive: bool = False


@dataclass
class CommandContext:
    """Everything a command handler needs."""

    event: Message
    client: TelegramClient
    args: str
    services: Any
    command: str = ""
    started_at: float = field(default_factory=time.monotonic)

    @property
    def chat_id(self) -> int:
        return self.event.chat_id

    @property
    def sender_id(self) -> int | None:
        return self.event.sender_id

    @property
    def is_owner(self) -> bool:
        services = self.services
        permission = getattr(services, "permission", None)
        return bool(permission and permission.is_owner(self.sender_id))

    async def respond(self, text: str, **kwargs: Any) -> Message | None:
        """Answer the command, returning the message that carries the text.

        For outgoing command messages the answer is written by editing that
        message, so the returned object can be edited again later (e.g. to
        show a live progress bar). Falls back to a plain reply otherwise.
        """
        return await reply_or_edit(self.event, text, **kwargs)


class Dispatcher:
    """Parses incoming messages, matches commands, enforces permissions."""

    def __init__(
        self,
        client: TelegramClient,
        services: Any,
        confirmation: ConfirmationManager,
        permission: PermissionService,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.client = client
        self.services = services
        self.confirmation = confirmation
        self.permission = permission
        self.rate_limiter = rate_limiter or RateLimiter()
        self._commands: dict[str, CommandSpec] = {}
        self._registered_handlers: list[Any] = []
        self._tasks: set[asyncio.Task[Any]] = set()

    # -- registry ---------------------------------------------------------
    def register(self, spec: CommandSpec) -> None:
        self._commands[spec.name] = spec
        for alias in spec.aliases:
            self._commands.setdefault(alias, spec)

    @property
    def commands(self) -> dict[str, CommandSpec]:
        """Registered commands keyed by canonical name."""
        return {
            spec.name: spec
            for spec in self._commands.values()
            if spec.name in self._commands
        }

    def list_specs(self, category: str | None = None) -> list[CommandSpec]:
        specs = {spec.name: spec for spec in self._commands.values() if spec.name in self._commands}
        unique = list(specs.values())
        if category:
            unique = [s for s in unique if s.category == category]
        return sorted(unique, key=lambda s: s.name)

    def find(self, name: str) -> CommandSpec | None:
        return self._commands.get(name)

    # -- wiring -----------------------------------------------------------
    async def start(self) -> None:
        self._registered_handlers.append(
            self.client.on(NewMessage())(self._on_new_message)
        )

    async def stop(self) -> None:
        for handler in self._registered_handlers:
            with contextlib.suppress(ValueError):
                self.client.remove_event_handler(handler)

    # -- main entry -------------------------------------------------------
    async def _on_new_message(self, event: NewMessage.Event) -> None:
        message: Message = event.message
        text = message.text or ""
        chat_id = message.chat_id

        # Check incoming text for pending confirmations (owner answers only,
        # so strangers in a group cannot confirm destructive actions). The
        # owner's confirmation answer is removed right away to keep chats clean.
        if text.strip():
            from_owner = bool(message.out) or self.permission.is_owner(message.sender_id)
            consumed = await self.confirmation.handle_incoming(
                chat_id, text, from_owner=from_owner
            )
            if consumed:
                if message.out:
                    with contextlib.suppress(Exception):  # noqa: BLE001
                        await self.client.delete_messages(chat_id, [message.id])
                return

        prefix = self.services.settings.command_prefix
        if not text.startswith(prefix):
            await self._maybe_autoreply(message, text)
            return

        from_owner = bool(message.out) or self.permission.is_owner(message.sender_id)
        if from_owner:
            self._schedule_command(message, text[len(prefix):].lstrip())
            return
        # Commands from anyone else (in groups or private chats) are answered
        # only when the owner explicitly allowed the chat; otherwise they are
        # ignored silently — no error, no reply.
        decision = await self.permission.can_execute(message.sender_id, message.chat_id)
        if decision.allowed:
            self._schedule_command(message, text[len(prefix):].lstrip())

    def _schedule_command(self, message: Message, body: str) -> None:
        """Run a command without blocking the update loop."""
        task = asyncio.create_task(self._run_command_task(message, body), name="command")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run_command_task(self, message: Message, body: str) -> None:
        try:
            await self._dispatch(message, body)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - never crash the update loop
            logger.error("command dispatch error: %s", exc)
            with contextlib.suppress(Exception):  # noqa: BLE001
                await reply_or_edit(message, f"{msg.ERR} {msg.INTERNAL_ERROR}")

    async def _dispatch(self, message: Message, body: str) -> None:
        command, _, _args = body.partition(" ")
        args = _args.strip()
        name = command.lower()
        spec = self.find(name)
        if spec is None:
            await reply_or_edit(message, f"{msg.ERR} {msg.INVALID_USAGE}\n\nبرای راهنما: `@help`")
            return

        started = time.monotonic()
        ctx = CommandContext(
            event=message,
            client=self.client,
            args=args,
            services=self.services,
            command=name,
            started_at=started,
        )

        try:
            decision = await self.permission.can_execute(message.sender_id, message.chat_id)
            if not decision.allowed:
                raise CommandError(decision.reason)

            if not self.rate_limiter.allow(f"cmd:{name}"):
                await reply_or_edit(message, msg.COMMAND_RATE_LIMITED)
                return

            await spec.handler(ctx)
            elapsed = time.monotonic() - started
            logger.info(
                "command=%s ok chat=%s elapsed=%.2fs", name, message.chat_id, elapsed
            )
        except CommandError as exc:
            logger.info("command=%s failed reason=%s", name, str(exc)[:120])
            await self._report_error(message, str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error("command=%s unexpected error=%s", name, exc.__class__.__name__)
            await self._report_error(message, msg.INTERNAL_ERROR)

    async def _report_error(self, message: Message, text: str) -> None:
        try:
            await reply_or_edit(message, f"{msg.ERR} {text}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("could not report error: %s", exc.__class__.__name__)

    # -- auto reply -------------------------------------------------------
    async def _maybe_autoreply(self, message: Message, text: str) -> None:
        services = self.services
        autoreply = getattr(services, "autoreply_logic", None)
        if autoreply is None or message.out or not text:
            return
        # The full auto-reply decision logic lives in the dedicated handler module.
        from selfbot.telegram.handlers.autoreply_handler import handle_incoming_auto_reply

        await handle_incoming_auto_reply(message, services, autoreply)
