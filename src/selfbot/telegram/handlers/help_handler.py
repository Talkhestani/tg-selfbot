"""Help command generated from command metadata."""

from __future__ import annotations

from selfbot.messages import persian as msg
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec

_CATEGORY_MAP = {
    "reminder": msg.HELP_REMINDER,
    "autoreply": msg.HELP_AUTOREPLY,
    "message": msg.HELP_MESSAGE,
    "tools": msg.HELP_TOOLS,
    "network": msg.HELP_NETWORK,
    "calc": msg.HELP_CALC,
    "convert": msg.HELP_CONVERT,
    "profile": msg.HELP_PROFILE,
    "ai": msg.HELP_AI,
}

_CATEGORY_TITLES = {
    "reminder": "یادآوری‌ها",
    "autoreply": "پاسخ خودکار",
    "message": "مدیریت پیام‌ها",
    "tools": "ابزارهای کمکی",
    "network": "ابزارهای شبکه",
    "calc": "ماشین حساب و زمان",
    "convert": "تبدیل‌ها",
    "profile": "پروفایل",
    "ai": "هوش مصنوعی",
}


async def help_command(ctx: CommandContext) -> None:
    topic = ctx.args.strip().lower()
    if not topic:
        await ctx.respond(msg.HELP_MAIN)
        return

    category_text = _CATEGORY_MAP.get(topic)
    if category_text:
        await ctx.respond(category_text)
        return

    spec = _find_spec(ctx, topic)
    if spec is None:
        raise CommandError(msg.HELP_UNKNOWN_CATEGORY)

    lines = [
        f"📘 راهنمای دستور `@{spec.name}`",
        "",
        spec.description,
        "",
    ]
    if spec.usage:
        lines.append(f"🧩 نحو: `{spec.usage}`")
        lines.append("")
    if spec.aliases:
        lines.append(f"👥 نام‌های دیگر: {', '.join(spec.aliases)}")
    await ctx.respond("\n".join(lines))


def _find_spec(ctx: CommandContext, topic: str) -> CommandSpec | None:
    dispatcher = ctx.services.dispatcher
    return dispatcher.find(topic)


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="help",
            handler=help_command,
            category="main",
            description="نمایش راهنمای ربات. مثال: `@help reminder`",
            usage="@help [بخش یا دستور]",
        )
    )
