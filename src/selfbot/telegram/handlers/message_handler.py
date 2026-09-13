"""Message management commands: .del, .delold and .delword."""

from __future__ import annotations

import contextlib
import logging
import re

from selfbot.messages import persian as msg
from selfbot.services.message_service import DeleteResult
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec, reply_or_edit
from selfbot.utils.validators import ValidationError, parse_duration

logger = logging.getLogger(__name__)

DEL_MAX_COUNT = 1000


def parse_days(text: str) -> int:
    """Parse a day count from ``30`` (days) or ``7d``@"""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        seconds = parse_duration(text)
        return max(1, seconds // 86400)
    except ValidationError:
        raise CommandError(msg.DELOLD_INVALID) from None


async def del_command(ctx: CommandContext) -> None:
    """Delete the last N messages of the current chat."""
    parts = ctx.args.strip().split()
    if not parts or not parts[0].lstrip("+").isdigit():
        raise CommandError(msg.DEL_MISSING)
    count = int(parts[0].lstrip("+"))
    if count < 1 or count > DEL_MAX_COUNT:
        raise CommandError(msg.DEL_INVALID)
    service = ctx.services.message_service

    confirmed = await _request_confirmation(
        ctx, f"حذف {str(count)} پیام آخر این گفتگو"
    )
    if not confirmed:
        await ctx.respond(msg.PERM_CONFIRM_DENIED)
        return

    await ctx.respond(msg.DEL_STARTED)
    command_id = getattr(ctx.event, "id", None)
    exclude = [command_id] if isinstance(command_id, int) else []
    result = await service.delete_last(ctx.chat_id, count, exclude_ids=exclude)

    # Remove the trigger message too (best effort, not counted).
    if isinstance(command_id, int):
        with contextlib.suppress(Exception):
            await ctx.client.delete_messages(ctx.chat_id, [command_id])

    if result.deleted == 0 and result.errors == 0:
        # Sent without reply_to: the command message may already be gone.
        await ctx.client.send_message(ctx.chat_id, msg.DEL_NO_MESSAGES)
        return
    text = msg.DEL_DONE.format(str(result.deleted))
    if result.errors:
        text += f"\n({str(result.errors)} مورد با مشکل مواجه شد)"
    await ctx.client.send_message(ctx.chat_id, text)


async def delold_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError("مثال:\n`@delold 30` برای حذف پیام‌های قدیمی‌تر از ۳۰ روز")
    days = parse_days(ctx.args)
    service = ctx.services.message_service

    confirmed = await _request_confirmation(ctx, f"عملیات حذف {days} روز گذشته")
    if not confirmed:
        await ctx.respond(msg.PERM_CONFIRM_DENIED)
        return

    await ctx.respond(msg.DELOLD_STARTED)
    result = await service.delete_older_than(ctx.chat_id, days)
    if result.deleted == 0 and result.errors == 0:
        await ctx.respond(msg.DELOLD_NO_MESSAGES)
        return
    text = msg.DELOLD_DONE.format(str(result.deleted))
    if result.errors:
        text += f"\n({str(result.errors)} مورد با مشکل مواجه شد)"
    await ctx.respond(text)


async def delword_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError("مثال:\n`@delword spam` یا `@delword spam,scam --limit 100`")

    kwargs = _parse_flags(ctx.args)
    keywords = kwargs["keywords"]
    use_regex = kwargs.get("regex", False)
    limit = kwargs.get("limit", 1000)

    for keyword in keywords:
        if len(keyword) > 100:
            raise CommandError("کلیدواژه بیش از حد طولانی است")
        if use_regex:
            try:
                re.compile(keyword)
            except re.error as exc:
                raise CommandError(f"{msg.DELWORD_INVALID_REGEX}\n{exc}") from exc

    confirmed = await _request_confirmation(ctx, f"حذف پیام‌های حاوی: {', '.join(keywords[:5])}")
    if not confirmed:
        await ctx.respond(msg.PERM_CONFIRM_DENIED)
        return

    result: DeleteResult = await ctx.services.message_service.delete_by_keywords(
        ctx.chat_id, keywords, limit=limit, use_regex=use_regex, case_insensitive=True
    )
    if result.deleted == 0 and result.errors == 0:
        await ctx.respond(msg.DELWORD_NO_MESSAGES)
        return
    text = msg.DELWORD_DONE.format(str(result.deleted))
    if result.errors:
        text += f"\n({str(result.errors)} مورد با مشکل مواجه شد)"
    await ctx.respond(text)


def _parse_flags(args: str) -> dict:
    """Extract ``--key value`` flags and the raw keywords."""
    limit = 1000
    use_regex = False
    keyword_text = args
    parts = args.split()
    cleaned: list[str] = []
    index = 0
    while index < len(parts):
        token = parts[index]
        if token == "--limit":
            if index + 1 >= len(parts):
                raise CommandError("بعد از --limit یک عدد وارد کنید")
            try:
                limit = int(parts[index + 1])
            except ValueError:
                raise CommandError("مقدار --limit باید عدد باشد") from None
            if limit < 1 or limit > 5000:
                raise CommandError("محدودیت باید بین ۱ تا ۵۰۰۰ باشد")
            index += 2
            continue
        if token == "--regex":
            use_regex = True
            index += 1
            continue
        cleaned.append(token)
        index += 1
    keyword_text = " ".join(cleaned)
    keywords = [k.strip() for k in keyword_text.split(",") if k.strip()]
    if not keywords:
        raise CommandError("حداقل یک کلیدواژه وارد کنید")
    return {"keywords": keywords, "limit": limit, "regex": use_regex}


async def _request_confirmation(ctx: CommandContext, action_text: str) -> bool:
    settings = ctx.services.settings
    if not settings.require_confirmation:
        return True
    return await ctx.services.confirmation.ask(
        ctx.chat_id,
        f"⚠️ {action_text}",
        responder=lambda text: reply_or_edit(ctx.event, text),
    )


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="del",
            handler=del_command,
            category="message",
            description="حذف N پیام آخر همین گفتگو",
            usage="@del <count>",
            owner_only=True,
            sensitive=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="delold",
            handler=delold_command,
            category="message",
            description="حذف پیام‌های قدیمی‌تر از تعداد روز مشخص",
            usage="@delold <days> | <Nd>",
            owner_only=True,
            sensitive=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="delword",
            handler=delword_command,
            category="message",
            description="حذف پیام‌های حاوی کلیدواژه مشخص",
            usage="@delword <keywords> [--limit 100] [--regex]",
            owner_only=True,
            sensitive=True,
        )
    )
