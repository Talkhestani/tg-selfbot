"""Auto-reply, AI, and chat-permission commands plus the incoming-reply engine."""

from __future__ import annotations

import logging
from typing import Any

from telethon.tl.types import Message

from selfbot.database.models import AutoReplyRule
from selfbot.database.repository import (
    AutoReplyRepository,
    ChatPermissionRepository,
    ConfigRepository,
)
from selfbot.messages import persian as msg
from selfbot.services.autoreply_service import AutoReplyService, validate_rule
from selfbot.services.rates import RatesError, format_rates
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec

logger = logging.getLogger(__name__)

_RATES_KEYWORDS = ("نرخ امروز", "قیمت امروز", "نرخ لحظه‌ای")

_AI_KEY_PROMPT = "ai_prompt"
_AI_KEY_ENABLED = "ai_enabled"
_AR_KEY_ENABLED = "autoreply_enabled"
_AR_KEY_DEFAULT = "autoreply_default"


async def autoreply_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    async with ctx.services.database.session_ctx() as session:
        config = ConfigRepository(session)
        if args == "on":
            await config.set_bool(_AR_KEY_ENABLED, True)
            await ctx.respond(msg.AUTOREPLY_ENABLED)
            return
        if args == "off":
            await config.set_bool(_AR_KEY_ENABLED, False)
            await ctx.respond(msg.AUTOREPLY_DISABLED)
            return
        if args in {"status", "؟", ""}:
            enabled = await config.get_bool(_AR_KEY_ENABLED, False)
            await ctx.respond(msg.AUTOREPLY_STATUS_ON if enabled else msg.AUTOREPLY_STATUS_OFF)
            return
        if args.startswith("set "):
            response = args[len("set "):].strip()
            if not response:
                raise CommandError(msg.AUTOREPLY_NO_DEFAULT)
            await config.set(_AR_KEY_DEFAULT, response)
            await ctx.respond(msg.AUTOREPLY_SET)
            return
    raise CommandError(msg.INVALID_USAGE + "\n`@autoreply on|off|set <پاسخ>`")


async def arule_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    async with ctx.services.database.session_ctx() as session:
        repo = AutoReplyRepository(session)
        if args == "list":
            rules = await repo.list_all()
            if not rules:
                await ctx.respond(msg.RULE_LIST_EMPTY)
                return
            lines = [msg.RULE_LIST_HEADER, ""]
            for rule in rules:
                status = "فعال" if rule.enabled else "غیرفعال"
                lines.append(
                    f"{rule.id}. {rule.pattern} → {rule.response}"
                    f"\n   نوع: {rule.match_type} | اولویت: {rule.priority} | {status}"
                )
            await ctx.respond("\n".join(lines))
            return

        if args.startswith("add "):
            body = args[len("add "):].strip()
            pattern, _, response = body.partition("=>")
            pattern = pattern.strip()
            response = response.strip()
            validate_rule(pattern, response, "contains")
            rule = await repo.add(
                AutoReplyRule(pattern=pattern, response=response, match_type="contains")
            )
            await ctx.respond(f"{msg.RULE_ADDED}\n**`{str(rule.id)}`** — `{pattern}` → {response}")
            return

        if args.startswith("remove "):
            try:
                rule_id = int(args[len("remove "):].strip())
            except ValueError:
                raise CommandError("شناسه قانون باید عدد باشد") from None
            removed = await repo.delete(rule_id)
            if not removed:
                raise CommandError(msg.RULE_NOT_FOUND)
            await ctx.respond(msg.RULE_REMOVED)
            return
    raise CommandError(msg.INVALID_USAGE + "\n`@arule add کلیدواژه => پاسخ`")


async def ai_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    services = ctx.services
    if not services.ai.available and args not in {"off", "status", ""}:
        raise CommandError(msg.AI_NOT_CONFIGURED)

    async with services.database.session_ctx() as session:
        config = ConfigRepository(session)
        if args == "on":
            await config.set_bool(_AI_KEY_ENABLED, True)
            await ctx.respond(msg.AI_ENABLED)
            return
        if args == "off":
            await config.set_bool(_AI_KEY_ENABLED, False)
            await ctx.respond(msg.AI_DISABLED)
            return
        if args.startswith("setprompt "):
            prompt = args[len("setprompt "):].strip()
            if not prompt:
                raise CommandError(msg.AI_PROMPT_INVALID)
            await config.set(_AI_KEY_PROMPT, prompt)
            await ctx.respond(msg.AI_PROMPT_SET)
            return
        if args in {"status", ""}:
            enabled = await config.get_bool(_AI_KEY_ENABLED, False)
            await ctx.respond(msg.AI_STATUS_ON if enabled else msg.AI_STATUS_OFF)
            return
    raise CommandError(msg.INVALID_USAGE)


async def owneronly_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    async with ctx.services.database.session_ctx() as session:
        config = ConfigRepository(session)
        if args == "on":
            await config.set_bool("owner_only", True)
            await ctx.respond(msg.OWNER_ONLY_ENABLED)
            return
        if args == "off":
            await config.set_bool("owner_only", False)
            await ctx.respond(msg.OWNER_ONLY_DISABLED)
            return
    raise CommandError(msg.INVALID_USAGE)


async def allowchat_command(ctx: CommandContext) -> None:
    await _set_chat_permission(ctx, "allow")


async def denychat_command(ctx: CommandContext) -> None:
    await _set_chat_permission(ctx, "block")


async def _set_chat_permission(ctx: CommandContext, action: str) -> None:
    args = ctx.args.strip()
    chat_id = await _resolve_chat_id(ctx, args)

    async with ctx.services.database.session_ctx() as session:
        repo = ChatPermissionRepository(session)
        if action == "allow":
            if await repo.is_allowed(chat_id):
                raise CommandError(msg.CHAT_ALREADY_ALLOWED)
            await repo.set_action(chat_id, "allow")
        else:
            if await repo.is_blocked(chat_id):
                raise CommandError(msg.CHAT_ALREADY_BLOCKED)
            await repo.set_action(chat_id, "block")
    await ctx.respond(
        msg.ALLOWED_CHATS_SET if action == "allow" else msg.BLOCKED_CHATS_SET
    )


async def allowlist_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    async with ctx.services.database.session_ctx() as session:
        config = ConfigRepository(session)
        if args == "on":
            await config.set_bool("allowlist_enabled", True)
            await ctx.respond("**حالت لیست مجاز فعال شد.**")
            return
        if args == "off":
            await config.set_bool("allowlist_enabled", False)
            await ctx.respond("**حالت لیست مجاز غیرفعال شد.**")
            return
    raise CommandError(msg.INVALID_USAGE)


async def chatperms_command(ctx: CommandContext) -> None:
    async with ctx.services.database.session_ctx() as session:
        repo = ChatPermissionRepository(session)
        entries = await repo.list_all()
    if not entries:
        await ctx.respond(msg.CHAT_PERMS_EMPTY)
        return
    lines = [msg.CHAT_PERMS_LIST, ""]
    for entry in entries:
        label = "مجاز" if entry.action == "allow" else "مسدود"
        lines.append(f"{entry.chat_id}: {label}")
    await ctx.respond("\n".join(lines))


async def _resolve_chat_id(ctx: CommandContext, text: str) -> int:
    if not text:
        return ctx.chat_id
    text = text.strip()
    if text.lstrip("-").isdigit():
        return int(text)
    if text.startswith("@"):
        raise CommandError("از شناسه عددی گفتگو استفاده کنید (در Setings > Advanced قابل مشاهده است)")
    raise CommandError("شناسه گفتگو معتبر نیست")


# ---------------------------------------------------------------------------
# Incoming auto-reply engine
# ---------------------------------------------------------------------------
async def _sender_is_allowed(services: Any, sender_id: int | None, chat_id: int) -> bool:
    """Return True when the sender is the owner or the chat is on the allowlist.

    Auto-reply keyword rules fire in private chats by default; turning
    ``@allowlist on`` narrows replies down to explicitly allowed chats only.
    """
    if sender_id is None:
        return False
    if services.permission.is_owner(sender_id):
        return True
    async with services.database.session_ctx() as session:
        allowlist = await ConfigRepository(session).get_bool("allowlist_enabled", False)
        if not allowlist:
            return True
        return await ChatPermissionRepository(session).is_allowed(chat_id)


def _is_private_chat(message: Message) -> bool:
    """Return True when the message is from a private (one-to-one) chat."""
    chat_id = message.chat_id
    return chat_id is not None and chat_id > 0


async def handle_incoming_auto_reply(
    message: Message, services: Any, autoreply: AutoReplyService
) -> None:
    """Evaluate and possibly respond to an incoming message.

    Auto-reply only fires in private chats and only when a keyword rule matches.
    The default/static response is ignored — use ``@arule add`` to add rules.
    """
    if not _is_private_chat(message):
        return

    chat_id = message.chat_id
    sender_id = message.sender_id

    if not await _sender_is_allowed(services, sender_id, chat_id):
        return

    if not await services.permission.can_respond_autoreply(chat_id):
        return

    async with services.database.session_ctx() as session:
        config = ConfigRepository(session)
        autoreply_enabled = await config.get_bool(_AR_KEY_ENABLED, False)
        if not autoreply_enabled:
            return

        rules = await AutoReplyRepository(session).list_all()

    text = message.text or ""

    for keyword in _RATES_KEYWORDS:
        if keyword in text:
            try:
                items = await services.rates.fetch()
            except RatesError as exc:
                await _send_safe(message, str(exc), services)
            else:
                await _send_safe(message, format_rates(items), services)
            return

    response, matched_rule = autoreply.evaluate(text, rules)

    if response is not None and matched_rule is not None and autoreply.allows_cooldown(chat_id, matched_rule):
        await _send_safe(message, response, services)


async def _send_safe(message: Message, text: str, services) -> None:  # type: ignore[no-untyped-def]
    try:
        await message.reply(text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("autoreply send failed: %s", exc.__class__.__name__)


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="autoreply",
            handler=autoreply_command,
            category="autoreply",
            description="مدیریت پاسخ خودکار",
            usage="@autoreply on|off|set <پاسخ>|status",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="arule",
            handler=arule_command,
            category="autoreply",
            description="مدیریت قوانین کلیدواژه پاسخ خودکار",
            usage="@arule add <کلیدواژه> => <پاسخ> | list | remove <id>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="ai",
            handler=ai_command,
            category="ai",
            description="مدیریت پاسخ هوشمند",
            usage="@ai on|off|setprompt <متن>|status",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="owneronly",
            handler=owneronly_command,
            category="autoreply",
            description="فعال/غیرفعال‌سازی حالت مالک‌فقط",
            usage="@owneronly on|off",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="allowchat",
            handler=allowchat_command,
            category="autoreply",
            description="افزودن گفتگو به لیست مجاز",
            usage="@allowchat [chat_id]",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="denychat",
            handler=denychat_command,
            category="autoreply",
            description="مسدودسازی گفتگو",
            usage="@denychat [chat_id]",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="allowlist",
            handler=allowlist_command,
            category="autoreply",
            description="فعال/غیرفعال‌سازی حالت لیست مجاز",
            usage="@allowlist on|off",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="chatperms",
            handler=chatperms_command,
            category="autoreply",
            description="فهرست دسترسی گفتگوها",
            usage="@chatperms",
            owner_only=True,
        )
    )
