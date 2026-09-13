"""Calculator and time-utility commands."""

from __future__ import annotations

from selfbot.messages import persian as msg
from selfbot.services.calculator import CalculationError, Calculator
from selfbot.services.random_tools import PASSWORD_MAX, PASSWORD_MIN, random_choice, random_int
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec
from selfbot.utils.validators import ValidationError, parse_duration


async def calc_command(ctx: CommandContext) -> None:
    expression = ctx.args.strip()
    if not expression:
        raise CommandError(msg.CALC_MISSING)
    calculator = Calculator()
    try:
        result = calculator.evaluate(expression)
    except CalculationError as exc:
        raise CommandError(f"{msg.CALC_INVALID}\n{exc}") from exc
    text = str(result)
    formatted = str(text)
    await ctx.respond(f"🧮 نتیجه:\n`{formatted}`")


async def stopwatch_command(ctx: CommandContext) -> None:
    action = ctx.args.strip().lower()
    stopwatch = ctx.services.stopwatch
    if action in {"start", "شروع"}:
        await ctx.respond(await stopwatch.start())
        return
    if action in {"stop", "توقف"}:
        result = await stopwatch.stop()
        await ctx.respond(result or msg.STOPWATCH_NOT_RUNNING)
        return
    if action in {"reset", "تنظیم"}:
        await ctx.respond(await stopwatch.reset())
        return
    if action in {"status", "وضعیت"}:
        elapsed = await stopwatch.elapsed()
        if elapsed is None:
            await ctx.respond(msg.STOPWATCH_NOT_RUNNING)
            return
        await ctx.respond(f"⏱ کرنومتر: {msg.format_duration(elapsed)}")
        return
    raise CommandError(msg.INVALID_USAGE)


async def timer_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError(msg.TIMER_MISSING)
    try:
        seconds = parse_duration(ctx.args.strip())
    except ValidationError:
        raise CommandError(msg.TIMER_INVALID) from None
    if seconds < 5 or seconds > 86400:
        raise CommandError("مدت زمان باید بین ۵ ثانیه تا ۲۴ ساعت باشد")
    await ctx.services.timer.create(seconds, ctx.chat_id, reply_to=ctx.event.id)
    duration_text = msg.format_duration(seconds)
    await ctx.respond(msg.TIMER_STARTED.format(duration_text))


async def random_command(ctx: CommandContext) -> None:
    parts = ctx.args.strip().split()
    if len(parts) != 2:
        raise CommandError(msg.RANDOM_MISSING)
    try:
        start, end = int(parts[0]), int(parts[1])
    except ValueError:
        raise CommandError(msg.RANDOM_INVALID) from None
    if start > end:
        start, end = end, start
    await ctx.respond(msg.RANDOM_RESULT.format(str(random_int(start, end))))


async def choose_command(ctx: CommandContext) -> None:
    options = [opt.strip() for opt in ctx.args.split(",") if opt.strip()]
    if not options:
        raise CommandError(msg.CHOOSE_MISSING)
    if len(options) == 1:
        await ctx.respond("🎯 فقط یک گزینه وارد شده است.")
        return
    await ctx.respond(f"🎯 انتخاب: **{random_choice(options)}**")


async def password_command(ctx: CommandContext) -> None:
    length_text = ctx.args.strip()
    length = 20
    if length_text:
        try:
            length = int(length_text)
        except ValueError:
            raise CommandError(msg.PASSWORD_INVALID) from None
    if not PASSWORD_MIN <= length <= PASSWORD_MAX:
        raise CommandError(msg.PASSWORD_INVALID)
    generated = ctx.services.generate_password(length)
    await ctx.respond(f"{msg.PASSWORD_RESULT} `{generated}`")


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="calc",
            handler=calc_command,
            category="calc",
            description="محاسبه عبارت ریاضی به‌صورت امن",
            usage="/calc <عبارت ریاضی>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="stopwatch",
            handler=stopwatch_command,
            category="calc",
            description="کرنومتر",
            usage="/stopwatch start|stop|reset|status",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="timer",
            handler=timer_command,
            category="calc",
            description="تنظیم تایمر",
            usage="/timer <مدت>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="random",
            handler=random_command,
            category="calc",
            description="تولید عدد تصادفی در بازه",
            usage="/random <min> <max>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="choose",
            handler=choose_command,
            category="calc",
            description="انتخاب تصادفی بین گزینه‌ها",
            usage="/choose <a,b,c>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="password",
            handler=password_command,
            category="calc",
            description="تولید رمز عبور امن",
            usage="/password <طول>",
            owner_only=True,
            sensitive=True,
        )
    )
