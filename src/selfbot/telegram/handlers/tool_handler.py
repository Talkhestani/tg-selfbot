"""Utility tool commands: JSON, encoding, hash, regex, QR and more."""

from __future__ import annotations

import contextlib
import json
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from selfbot.messages import persian as msg
from selfbot.services import toolbox
from selfbot.services.media_tools import MediaToolError, generate_barcode, generate_qr
from selfbot.services.shortener import ShortenerError
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec
from selfbot.utils.ssrf import SSRFBlockedError
from selfbot.utils.validators import is_valid_url, parse_date_time


async def _split_json_args(args: str) -> tuple[str, str]:
    """Return (subcommand, json text)."""
    parts = args.split(maxsplit=1)
    subcommand = parts[0] if parts else ""
    text = parts[1] if len(parts) > 1 else ""
    return subcommand, text


async def json_command(ctx: CommandContext) -> None:
    subcommand, text = await _split_json_args(ctx.args)
    if not text:
        raise CommandError(msg.JSON_MISSING_TEXT)
    if subcommand in {"format", "pretty", "f"}:
        try:
            output = toolbox.format_json(text)
        except toolbox.ToolError as exc:
            raise CommandError(f"{msg.JSON_INVALID.format(exc)}") from exc
        await ctx.respond(f"{msg.JSON_FORMAT_OK}\n\n```json\n{output}\n```", parse_mode="md")
        return
    if subcommand in {"validate", "v"}:
        valid, error = toolbox.validate_json(text)
        await ctx.respond(msg.JSON_VALID if valid else f"{msg.JSON_INVALID.format(error)}")
        return
    if subcommand == "minify":
        try:
            output = toolbox.minify_json(text)
        except toolbox.ToolError as exc:
            raise CommandError(f"{msg.JSON_INVALID.format(exc)}") from exc
        await ctx.respond(f"✅ JSON فشرده شد:\n\n```\n{output}\n```")
        return
    raise CommandError(msg.JSON_MISSING_TEXT)


async def b64_command(ctx: CommandContext) -> None:
    parts = ctx.args.split(maxsplit=1)
    action = parts[0].lower() if parts else ""
    text = parts[1] if len(parts) > 1 else ""
    if action in {"encode", "e"}:
        if not text:
            raise CommandError(msg.B64_MISSING_TEXT)
        await ctx.respond(f"🔐 خروجی:\n```\n{toolbox.b64_encode(text)}\n```")
        return
    if action in {"decode", "d"}:
        if not text:
            raise CommandError(msg.B64_MISSING_TEXT)
        try:
            result = toolbox.b64_decode(text)
        except toolbox.ToolError as exc:
            raise CommandError(msg.B64_DECODE_ERROR) from exc
        await ctx.respond(f"🔓 خروجی:\n```\n{result}\n```")
        return
    raise CommandError(msg.B64_MISSING_TEXT)


async def urlencode_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError("متن را وارد کنید. مثال:\n`/urlencode سلام دنیا`")
    await ctx.respond(f"🔗 کدشده:\n`{toolbox.url_encode(ctx.args)}`")


async def urldecode_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError("متن را وارد کنید. مثال:\n`/urldecode %D8%B3%D9%84%D8%A7%D9%85`")
    try:
        result = unquote(ctx.args)
    except Exception as exc:  # noqa: BLE001
        raise CommandError("رمزگشایی URL انجام نشد") from exc
    await ctx.respond(f"🔓 رمزگشایی‌شده:\n`{result}`")


async def uuid_command(ctx: CommandContext) -> None:
    count = 1
    if ctx.args.strip():
        try:
            count = int(ctx.args.strip())
        except ValueError:
            raise CommandError(msg.UUID_INVALID_COUNT) from None
    if not 1 <= count <= 20:
        raise CommandError(msg.UUID_INVALID_COUNT)
    uuids = toolbox.generate_uuids(count)
    text = f"{msg.UUID_HEADER}\n\n" + "\n".join(f"• `{u}`" for u in uuids)
    await ctx.respond(text)


async def hash_command(ctx: CommandContext) -> None:
    parts = ctx.args.split(maxsplit=1)
    if len(parts) != 2:
        raise CommandError(msg.HASH_MISSING_TEXT)
    algorithm, text = parts
    try:
        digest = toolbox.hash_text(algorithm, text)
    except toolbox.ToolError:
        raise CommandError(msg.HASH_UNSUPPORTED) from None
    await ctx.respond(f"{msg.HASH_HEADER}\n\n`{digest}`")


async def regex_command(ctx: CommandContext) -> None:
    parts = ctx.args.split(maxsplit=1)
    if len(parts) != 2:
        raise CommandError(msg.REGEX_MISSING)
    pattern, text = parts
    try:
        count, matches = toolbox.regex_match(pattern, text)
    except toolbox.ToolError as exc:
        raise CommandError(f"{msg.REGEX_INVALID.format(exc)}") from exc
    if count == 0:
        await ctx.respond(msg.REGEX_NO_MATCH)
        return
    lines = [msg.REGEX_MATCHES.format(str(count), ""), ""]
    for index, match in enumerate(matches[:20], start=1):
        lines.append(
            f"{str(index)}. «{match['match']}» "
            f"(موقعیت {str(match['start'])}-{str(match['end'])})"
        )
    await ctx.respond("\n".join(lines))


async def timestamp_command(ctx: CommandContext) -> None:
    if not ctx.args:
        now = datetime.now()
        unix = toolbox.now_unix()
        text = (
            f"{msg.TIMESTAMP_NOW} {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{msg.TS_TO_UNIX} `{str(unix)}`"
        )
        await ctx.respond(text)
        return
    try:
        source = parse_date_time(ctx.args)
        unix = toolbox.datetime_to_unix(source)
    except Exception as exc:  # noqa: BLE001
        raise CommandError(msg.TIMESTAMP_INVALID) from exc
    await ctx.respond(f"{msg.TS_TO_UNIX} `{unix}`")


async def unixtime_command(ctx: CommandContext) -> None:
    if not ctx.args:
        await ctx.respond(f"{msg.TS_TO_UNIX} `{str(toolbox.now_unix())}`")
        return
    text = ctx.args.strip()
    try:
        unix = int(text)
    except ValueError:
        raise CommandError("مقدار یونیکس باید عدد باشد") from None
    try:
        dt = toolbox.unix_to_datetime(unix)
    except (ValueError, OverflowError, OSError):
        raise CommandError("مقدار یونیکس خارج از محدوده است") from None
    await ctx.respond(f"{msg.TS_FROM_UNIX} `{dt.strftime('%Y-%m-%d %H:%M:%S')}`")


async def jwt_command(ctx: CommandContext) -> None:
    token = ctx.args.strip()
    if not token:
        raise CommandError(msg.JWT_MISSING)
    try:
        header, payload = toolbox.decode_jwt(token)
    except toolbox.ToolError:
        raise CommandError(msg.JWT_INVALID) from None
    output = (
        f"{msg.JWT_DISCLAIMER}\n\n"
        f"**سرصفحه (header):**\n```json\n{json.dumps(header, ensure_ascii=False, indent=2)}\n```\n"
        f"**پیلود (payload):**\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```"
    )
    await ctx.respond(output)


async def short_command(ctx: CommandContext) -> None:
    url = ctx.args.strip()
    if not url:
        raise CommandError(msg.URL_SHORTENER_INVALID_URL)
    if "://" not in url:
        url = f"https://{url}"
    if not is_valid_url(url):
        raise CommandError(msg.URL_SHORTENER_INVALID_URL)
    try:
        result = await ctx.services.shortener.shorten(url)
    except ShortenerError as exc:
        raise CommandError(str(exc)) from exc
    await ctx.respond(f"{msg.URL_SHORTENED}\n{result}")


async def qr_command(ctx: CommandContext) -> None:
    data = (ctx.args or "").strip()
    if not data:
        # Reply mode: turn the replied-to message's text into a QR code.
        get_reply = getattr(ctx.event, "get_reply_message", None)
        reply = await get_reply() if callable(get_reply) else None
        if reply is not None:
            data = (reply.text or "").strip()
    if not data:
        raise CommandError(msg.QR_INVALID_TEXT)
    if data.startswith(("http://", "https://")) and not is_valid_url(data):
        raise CommandError(msg.QR_INVALID_URL)
    with tempfile.TemporaryDirectory() as tmp:
        path = generate_qr(data, Path(tmp) / "qr.png")
        await ctx.event.respond(file=str(path))


async def barcode_command(ctx: CommandContext) -> None:
    data = ctx.args.strip()
    if not data:
        raise CommandError(msg.BARCODE_INVALID)
    if not data.isdigit():
        raise CommandError(msg.BARCODE_INVALID_VALUE)
    with tempfile.TemporaryDirectory() as tmp:
        try:
            path = generate_barcode(data, Path(tmp) / "barcode.png")
        except MediaToolError as exc:
            raise CommandError(str(exc)) from exc
        await ctx.event.respond(file=str(path))


async def color_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError(msg.COLOR_INVALID)
    try:
        info = toolbox.describe_color(ctx.args.strip())
    except toolbox.ToolError as exc:
        raise CommandError(f"{msg.COLOR_INVALID}\n{exc}") from exc
    lines = [
        msg.COLOR_RESULT,
        "",
        f"HEX: `{info['hex']}`",
        f"RGB: `{info['rgb']}`",
        f"HSL: `{info['hsl']}`",
    ]
    await ctx.respond("\n".join(lines))


async def mdhtml_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError(msg.MDHTML_MISSING)
    output = toolbox.markdown_to_html(ctx.args)
    await ctx.respond(f"✅ تبدیل انجام شد:\n\n```html\n{output}\n```")


async def htmlmd_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError(msg.HTMLMD_MISSING)
    output = toolbox.html_to_markdown(ctx.args)
    await ctx.respond(f"✅ تبدیل انجام شد:\n\n```\n{output}\n```")


async def textqr_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError(msg.QR_INVALID_TEXT)
    with tempfile.TemporaryDirectory() as tmp:
        path = generate_qr(ctx.args.strip(), Path(tmp) / "textqr.png")
        await ctx.event.respond(file=str(path))


async def screenshot_command(ctx: CommandContext) -> None:
    url = ctx.args.strip()
    if not url:
        raise CommandError(msg.SCREENSHOT_MISSING)
    if "://" not in url:
        url = f"https://{url}"

    screenshot = ctx.services.screenshot
    if not screenshot.available:
        raise CommandError(msg.SCREENSHOT_DISABLED)

    processing = await ctx.respond(msg.PROCESSING)
    output_path = ctx.services.settings.data_dir / f"screenshot_{ctx.chat_id}_{toolbox.now_unix()}.png"
    try:
        result = await screenshot.capture(url, output_path)
    except SSRFBlockedError:
        raise CommandError(msg.NET_BLOCKED) from None
    except Exception as exc:  # noqa: BLE001
        reason = str(exc).strip() or exc.__class__.__name__
        raise CommandError(msg.SCREENSHOT_ERROR.format(reason)) from exc
    try:
        await ctx.event.respond(file=str(result))
    finally:
        if result.exists():
            result.unlink(missing_ok=True)

    # Once the screenshot has been sent, the command message showing
    # "در حال پردازش..." is no longer needed; remove it to keep the chat clean.
    if processing is not None:
        with contextlib.suppress(Exception):  # noqa: BLE001
            await processing.delete()


async def quote_command(ctx: CommandContext) -> None:
    quote = toolbox.random_quote()
    if quote is None:
        raise CommandError("فایل نقل‌قول‌ها پیدا نشد یا خالی است")
    text, author = quote
    if author:
        await ctx.respond(f"💬 {text}\n\n— __{author}__")
    else:
        await ctx.respond(f"💬 {text}")


async def spam_command(ctx: CommandContext) -> None:
    import asyncio

    args = ctx.args.strip()
    if args:
        try:
            count = int(args)
        except ValueError:
            raise CommandError("تعداد باید عدد باشد") from None
    else:
        count = 1
    if not 1 <= count <= 50:
        raise CommandError("تعداد باید بین 1 تا 50 باشد")

    texts = toolbox.random_spam(count)
    if not texts:
        raise CommandError("فهرست اسپم ها خالی است")

    for text in texts:
        await ctx.client.send_message(ctx.chat_id, text)
        await asyncio.sleep(0.2)


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="json",
            handler=json_command,
            category="tools",
            description="قالب‌بندی و اعتبارسنجی JSON",
            usage="/json format|validate|minify <json>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="b64",
            handler=b64_command,
            category="tools",
            description="کدگذاری/رمزگشایی Base64",
            usage="/b64 encode|decode <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="urlencode",
            handler=urlencode_command,
            category="tools",
            description="کدگذاری متن برای URL",
            usage="/urlencode <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="urldecode",
            handler=urldecode_command,
            category="tools",
            description="رمزگشایی متن کدشده URL",
            usage="/urldecode <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="uuid",
            handler=uuid_command,
            category="tools",
            description="تولید شناسه یکتا (UUID)",
            usage="/uuid [تعداد]",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="hash",
            handler=hash_command,
            category="tools",
            description="محاسبه هش (md5/sha1/sha256/sha512)",
            usage="/hash <الگوریتم> <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="regex",
            handler=regex_command,
            category="tools",
            description="آزمایش عبارت منظم",
            usage="/regex <الگو> <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="timestamp",
            handler=timestamp_command,
            category="tools",
            description="تبدیل زمان به یونیکس و بالعکس",
            usage="/timestamp [YYYY-MM-DD HH:MM]",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="unixtime",
            handler=unixtime_command,
            category="tools",
            description="نمایش زمان یونیکس فعلی یا تبدیل آن",
            usage="/unixtime [مقدار]",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="jwt",
            handler=jwt_command,
            category="tools",
            description="رمزگشایی هدر و پیلود توکن JWT (بدون بررسی امضا)",
            usage="/jwt <token>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="short",
            handler=short_command,
            category="tools",
            description="کوتاه‌کردن لینک",
            usage="/short <url>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="qr",
            handler=qr_command,
            category="tools",
            description="ساخت کد QR از متن یا لینک",
            usage="/qr [متن|لینک] (خالی = ریپلای روی پیام)",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="barcode",
            handler=barcode_command,
            category="tools",
            description="ساخت بارکد از اعداد",
            usage="/barcode <رشته عددی>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="color",
            handler=color_command,
            category="tools",
            description="تبدیل رنگ‌ها (HEX/RGB/HSL)",
            usage="/color <#hex | r,g,b>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="mdhtml",
            handler=mdhtml_command,
            category="tools",
            description="تبدیل Markdown به HTML",
            usage="/mdhtml <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="htmlmd",
            handler=htmlmd_command,
            category="tools",
            description="تبدیل HTML ساده به Markdown",
            usage="/htmlmd <html>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="textqr",
            handler=textqr_command,
            category="tools",
            description="ساخت کد QR از متن",
            usage="/textqr <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="ss",
            handler=screenshot_command,
            category="tools",
            description="گرفتن اسکرین‌شات از یک لینک",
            usage="/ss <url>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="quote",
            handler=quote_command,
            category="tools",
            description="یک نقل‌قول تصادفی از فایل نقل‌قول‌ها",
            usage="/quote",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="spam",
            handler=spam_command,
            category="tools",
            description="ارسال چند اسپم تصادفی",
            usage="/spam [تعداد]",
            owner_only=True,
        )
    )
