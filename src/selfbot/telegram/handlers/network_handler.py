"""Network tool commands: ping, dns, ip, whois, ssl, http checks."""

from __future__ import annotations

from selfbot.messages import persian as msg
from selfbot.services.network import NetworkError
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec


def _url_or_error(ctx: CommandContext) -> str:
    url = ctx.args.strip()
    if not url:
        raise CommandError(msg.NET_URL_MISSING)
    if "://" not in url:
        url = f"https://{url}"
    return url


async def ping_command(ctx: CommandContext) -> None:
    host = ctx.args.strip()
    if not host:
        raise CommandError(msg.NET_PING_MISSING)
    network = ctx.services.network
    result = await network.ping(host)
    if result.error:
        await ctx.respond(f"{msg.ERR} {msg.PING_FAILED.format(_safe_error(result.error))}")
        return
    lines = [msg.PING_RESULT.format(host=result.host), ""]
    lines.append(f"آدرس: `{result.ip}`")
    lines.append(f"ارسال/دریافت: {str(result.sent)}/{str(result.received)}")
    lines.append(f"اتلاف: %{str(round(result.loss_percent, 1))}")
    if result.rtts:
        rtt_text = "/".join(str(r) for r in result.rtts)
        lines.append(f"میانگین پاسخ: {rtt_text} میلی‌ثانیه")
    await ctx.respond("\n".join(lines))


async def dns_command(ctx: CommandContext) -> None:
    host = ctx.args.strip()
    if not host:
        raise CommandError(msg.NET_DNS_MISSING)
    network = ctx.services.network
    try:
        records = await network.dns_lookup(host)
    except NetworkError as exc:
        raise CommandError(_safe_error(str(exc))) from exc
    if not records:
        await ctx.respond(msg.DNS_NO_RECORDS.format(host=host))
        return
    lines = [msg.DNS_RESULT.format(host=host), ""]
    for record in records[:20]:
        lines.append(f"• `{record}`")
    await ctx.respond("\n".join(lines))


async def ip_command(ctx: CommandContext) -> None:
    target = ctx.args.strip()
    if not target:
        raise CommandError(msg.NET_IP_MISSING)
    network = ctx.services.network
    try:
        info = await network.ip_lookup(target)
    except NetworkError as exc:
        raise CommandError(_safe_error(str(exc))) from exc
    lines = [
        msg.IP_RESULT.format(target=target),
        "",
        f"IP: `{info['ip']}`",
        f"نام میزبان: `{info['hostname']}`",
    ]
    if "reverse" in info:
        lines.append(f"نام معکوس: `{info['reverse']}`")
    await ctx.respond("\n".join(lines))


async def whois_command(ctx: CommandContext) -> None:
    domain = ctx.args.strip()
    if not domain:
        raise CommandError(msg.NET_WHOIS_MISSING)
    network = ctx.services.network
    try:
        text = await network.whois(domain)
    except NetworkError as exc:
        raise CommandError(_safe_error(str(exc))) from exc
    if not text:
        raise CommandError("اطلاعاتی برای این دامنه یافت نشد")
    await ctx.respond(f"{msg.WHOIS_RESULT.format(domain=domain)}\n\n" + text)


async def status_url_command(ctx: CommandContext) -> None:
    url = _url_or_error(ctx)
    network = ctx.services.network
    try:
        data = await network.status_url(url)
    except NetworkError as exc:
        raise CommandError(_safe_error(str(exc))) from exc
    code = data["status_code"]
    emoji = "🟢" if code < 400 else ("🟠" if code < 500 else "🔴")
    lines = [
        msg.STATUS_RESULT,
        "",
        f"{emoji} کد: {str(code)} ({data['reason']})",
    ]
    await ctx.respond("\n".join(lines))


async def ssl_command(ctx: CommandContext) -> None:
    host = ctx.args.strip()
    if not host:
        raise CommandError(msg.NET_SSL_MISSING)
    network = ctx.services.network
    try:
        info = await network.ssl_info(host)
    except NetworkError as exc:
        raise CommandError(_safe_error(str(exc))) from exc
    lines = [
        msg.SSL_RESULT.format(host=host),
        "",
        f"موضوع: {info['subject']}",
        f"صادرکننده: {info['issuer']}",
        f"اعتبار از: {info['not_before']}",
        f"اعتبار تا: {info['not_after']}",
    ]
    await ctx.respond("\n".join(lines))


async def uptime_command(ctx: CommandContext) -> None:
    url = _url_or_error(ctx)
    network = ctx.services.network
    try:
        data = await network.uptime(url)
    except NetworkError as exc:
        raise CommandError(_safe_error(str(exc))) from exc
    if data["success"] > 0:
        await ctx.respond(msg.UPTIME_STATUS.format(url=url, uptime="✓"))
    else:
        detail = _safe_error(data["error"] or "بدون پاسخ")
        await ctx.respond(f"{msg.UPTIME_DOWN.format(url=url)}\n{detail}")


async def headers_command(ctx: CommandContext) -> None:
    url = _url_or_error(ctx)
    network = ctx.services.network
    try:
        headers = await network.fetch_headers(url)
    except NetworkError as exc:
        raise CommandError(_safe_error(str(exc))) from exc
    if not headers:
        await ctx.respond(f"{msg.HEADERS_RESULT.format(url)}\n\n(بدون هدر)")
        return
    lines = [msg.HEADERS_RESULT.format(url=url), ""]
    for key, value in list(headers.items())[:30]:
        lines.append(f"`{key}`: {value}")
    await ctx.respond("\n".join(lines))


def _safe_error(text: str) -> str:
    """Strip any raw hostnames/details that might leak internals."""
    return text[:200]


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="ping",
            handler=ping_command,
            category="network",
            description="بررسی دسترسی به یک میزبان",
            usage="@ping <host>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="dns",
            handler=dns_command,
            category="network",
            description="جستجوی رکوردهای DNS",
            usage="@dns <host>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="ip",
            handler=ip_command,
            category="network",
            description="بررسی آدرس IP یک میزبان",
            usage="@ip <host|ip>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="whois",
            handler=whois_command,
            category="network",
            description="مشاهده اطلاعات ثبت دامنه",
            usage="@whois <domain>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="statusurl",
            handler=status_url_command,
            category="network",
            description="بررسی وضعیت HTTP یک لینک",
            usage="@statusurl <url>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="ssl",
            handler=ssl_command,
            category="network",
            description="مشاهده اطلاعات گواهی SSL",
            usage="@ssl <host>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="uptime",
            handler=uptime_command,
            category="network",
            description="بررسی در دسترس بودن یک وب‌سایت",
            usage="@uptime <url>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="headers",
            handler=headers_command,
            category="network",
            description="مشاهده هدرهای HTTP یک لینک",
            usage="@headers <url>",
            owner_only=True,
        )
    )
