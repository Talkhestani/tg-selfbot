"""Profile automation commands: bio and name clock."""

from __future__ import annotations

import logging

from selfbot.database.repository import BioItemRepository, ConfigRepository
from selfbot.messages import persian as msg
from selfbot.services.profile_service import ProfileError, validate_bio
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec
from selfbot.utils.validators import ValidationError

logger = logging.getLogger(__name__)

_BASE_BIO_KEY = "base_bio"


async def bio_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    profile = ctx.services.profile

    if args == "list":
        await _bio_list(ctx)
        return

    if args.startswith("add "):
        text = args[len("add "):].strip().strip('"')
        try:
            text = validate_bio(text)
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc
        async with ctx.services.database.session_ctx() as session:
            await BioItemRepository(session).add(text)
        await ctx.respond(msg.BIO_ADDED)
        return

    if args.startswith("remove "):
        try:
            item_id = int(args[len("remove "):].strip())
        except ValueError:
            raise CommandError("شناسه بیو باید عدد باشد") from None
        async with ctx.services.database.session_ctx() as session:
            removed = await BioItemRepository(session).delete(item_id)
        if not removed:
            raise CommandError(msg.BIO_NOT_FOUND)
        await ctx.respond(msg.BIO_REMOVED)
        return

    if args == "random":
        await _apply_random_bio(ctx)
        return

    if args == "clock on":
        async with ctx.services.database.session_ctx() as session:
            await ConfigRepository(session).set("bio_clock", "1")
        await ctx.respond(msg.BIO_CLOCK_ON)
        return

    if args == "clock off":
        async with ctx.services.database.session_ctx() as session:
            await ConfigRepository(session).set("bio_clock", "0")
        await ctx.respond(msg.BIO_CLOCK_OFF)
        return

    if args == "online on":
        await _set_online_bio(ctx, True)
        return

    if args == "online off":
        await _set_online_bio(ctx, False)
        return

    if args.startswith("set "):
        text = args[len("set "):].strip().strip('"')
        try:
            bio = validate_bio(text)
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc
        try:
            await profile.set_bio(bio)
        except ProfileError as exc:
            raise CommandError(str(exc)) from exc
        async with ctx.services.database.session_ctx() as session:
            await ConfigRepository(session).set(_BASE_BIO_KEY, bio)
        await ctx.respond(msg.BIO_SET)
        return

    raise CommandError(
        "مثال‌ها:\n"
        "`/bio set متن`\n"
        "`/bio add متن` / `/bio list` / `/bio remove 3`\n"
        "`/bio random`\n"
        "`/bio clock on|off`\n"
        "`/bio online on|off`"
    )


async def autobio_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    async with ctx.services.database.session_ctx() as session:
        config = ConfigRepository(session)
        if args == "on":
            await config.set_bool("autobio", True)
            await ctx.respond(msg.AUTO_BIO_ON)
            return
        if args == "off":
            await config.set_bool("autobio", False)
            await ctx.respond(msg.AUTO_BIO_OFF)
            return
    raise CommandError(msg.INVALID_USAGE)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
async def _bio_list(ctx: CommandContext) -> None:
    async with ctx.services.database.session_ctx() as session:
        items = await BioItemRepository(session).list_all()
    if not items:
        await ctx.respond(msg.BIO_LIST_EMPTY)
        return
    lines = [msg.BIO_LIST_HEADER, ""]
    for item in items:
        lines.append(f"{str(item.id)}. {item.text}")
    await ctx.respond("\n".join(lines))


async def _apply_random_bio(ctx: CommandContext) -> None:
    async with ctx.services.database.session_ctx() as session:
        items = await BioItemRepository(session).list_all()
    if not items:
        raise CommandError(msg.BIO_LIST_EMPTY)
    import random

    bio = random.choice(items).text
    try:
        await ctx.services.profile.set_bio(bio)
    except ProfileError as exc:
        raise CommandError(str(exc)) from exc
    await ctx.respond(f"{msg.BIO_RANDOM_SET}\n\n{bio}")


async def _set_online_bio(ctx: CommandContext, enabled: bool) -> None:
    if enabled:
        async with ctx.services.database.session_ctx() as session:
            await ConfigRepository(session).set("bio_online", "1")
        # Telegram does not expose the "online" flag for display in a bio.
        await ctx.respond(msg.BIO_ONLINE_ON)
    else:
        async with ctx.services.database.session_ctx() as session:
            await ConfigRepository(session).set("bio_online", "0")
        await ctx.respond(msg.BIO_ONLINE_OFF)


async def nameclock_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    automation = ctx.services.profile_automation
    if args == "on":
        await automation.set_name_clock(True)
        await ctx.respond(msg.NAMECLOCK_ON)
        return
    if args == "off":
        await automation.set_name_clock(False)
        await ctx.respond(msg.NAMECLOCK_OFF)
        return
    raise CommandError("مثال:\n`/nameclock on|off`")


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="bio",
            handler=bio_command,
            category="profile",
            description="مدیریت بیو (تنظیم، فهرست، تصادفی، ساعت)",
            usage="/bio set/list/add/remove/random/clock/online",
            owner_only=True,
            sensitive=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="autobio",
            handler=autobio_command,
            category="profile",
            description="فعال/غیرفعال‌سازی بیوی خودکار",
            usage="/autobio on|off",
            owner_only=True,
            sensitive=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="nameclock",
            handler=nameclock_command,
            category="profile",
            description="نمایش ساعت زنده در نام پروفایل (مثل: Talkhestani [13:13])",
            usage="/nameclock on|off",
            owner_only=True,
            sensitive=True,
        )
    )
