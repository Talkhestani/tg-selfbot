"""Converter commands: units, currency, timezone, weather, dates, BMI."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from selfbot.messages import persian as msg
from selfbot.services.converter import ConversionError
from selfbot.services.currency import CurrencyError
from selfbot.services.datecalc import DateCalculator
from selfbot.services.rates import RatesError, format_rates
from selfbot.services.weather import WeatherError
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec
from selfbot.utils.validators import ValidationError


async def convert_command(ctx: CommandContext) -> None:
    parts = ctx.args.strip().split()
    if len(parts) != 3:
        raise CommandError(msg.CONVERT_MISSING)
    value_text, from_unit, to_unit = parts
    try:
        value = float(value_text)
    except ValueError:
        raise CommandError(msg.CONVERT_INVALID_VALUE) from None
    if abs(value) > 1e15:
        raise CommandError("مقدار بیش از حد بزرگ است")

    converter = ctx.services.converter
    try:
        result = converter.convert(value, from_unit, to_unit)
    except ConversionError as exc:
        raise CommandError(str(exc)) from exc
    formatted = _format_number(result)
    await ctx.respond(msg.CONVERT_RESULT.format(str(value_text), from_unit.lower(), formatted, to_unit.lower()))


async def currency_command(ctx: CommandContext) -> None:
    parts = ctx.args.strip().split()

    if not parts:
        try:
            items = await ctx.services.rates.fetch()
        except RatesError as exc:
            raise CommandError(str(exc)) from exc
        await ctx.respond(format_rates(items))
        return

    if len(parts) != 3:
        raise CommandError(msg.CURRENCY_MISSING)
    amount_text, src, dst = parts
    try:
        amount = float(amount_text)
    except ValueError:
        raise CommandError(msg.CURRENCY_INVALID_AMOUNT) from None
    if amount < 0 or amount > 1e12:
        raise CommandError("مقدار معتبر نیست")
    try:
        conversion = await ctx.services.currency.convert(amount, src, dst)
    except CurrencyError as exc:
        raise CommandError(str(exc)) from exc
    lines = [
        msg.CURRENCY_RESULT.format(
            str(round(amount, 4)),
            src.upper(),
            str(round(conversion.result, 4)),
            dst.upper(),
        ),
        "",
        msg.CURRENCY_RATE_HINT.format(
            str(round(conversion.rate, 6)),
            conversion.fetched_at.strftime("%H:%M"),
        ),
    ]
    await ctx.respond("\n".join(lines))


async def tz_command(ctx: CommandContext) -> None:
    parts = ctx.args.strip().split()
    if len(parts) < 3:
        raise CommandError(msg.TZ_MISSING)
    time_text = parts[0]
    zones = parts[1:]
    try:
        hour, minute = (int(x) for x in time_text.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        base = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError:
        raise CommandError(msg.TZ_INVALID_TIME) from None

    lines = [msg.TZ_RESULT, ""]
    for zone in zones:
        try:
            tz = ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError, KeyError):
            raise CommandError(msg.TZ_INVALID_ZONE.format(zone)) from None
        converted = base.astimezone(tz)
        lines.append(f"🌐 `{zone}`: {str(converted.strftime('%H:%M'))}")
    await ctx.respond("\n".join(lines))


async def weather_command(ctx: CommandContext) -> None:
    city = ctx.args.strip()
    if not city:
        raise CommandError(msg.WEATHER_MISSING)
    try:
        info = await ctx.services.weather.fetch(city)
    except WeatherError as exc:
        raise CommandError(f"{msg.WEATHER_ERROR.format(str(exc))}") from exc
    lines = [
        msg.WEATHER_RESULT.format(city=info.city),
        "",
        f"🌡 دما: {str(round(info.temperature, 1))}°C",
        f"☁️ وضعیت: {info.description}",
    ]
    if info.humidity is not None:
        lines.append(f"💧 رطوبت: %{str(info.humidity)}")
    if info.wind_speed is not None:
        lines.append(f"💨 باد: {str(round(info.wind_speed, 1))} km/h")
    await ctx.respond("\n".join(lines))


async def datecalc_command(ctx: CommandContext) -> None:
    expression = ctx.args.strip()
    if not expression:
        raise CommandError(msg.DATEDIFF_MISSING)
    try:
        result = DateCalculator.calculate(expression)
    except ValidationError as exc:
        raise CommandError(f"{msg.DATEDIFF_INVALID}\n{exc}") from exc
    await ctx.respond(f"{msg.DATEDIFF_RESULT}\n{result}")


async def age_command(ctx: CommandContext) -> None:
    birth_text = ctx.args.strip()
    if not birth_text:
        raise CommandError(msg.AGE_MISSING)
    try:
        birth = date.fromisoformat(birth_text)
    except ValueError:
        raise CommandError(msg.AGE_INVALID) from None
    today = date.today()
    if birth > today:
        raise CommandError(msg.AGE_FUTURE)
    years = today.year - birth.year
    months = today.month - birth.month
    days = today.day - birth.day
    if days < 0:
        months -= 1
        days += _days_in_month(today.year, today.month - 1)
    if months < 0:
        years -= 1
        months += 12
    parts = []
    if years:
        parts.append(f"{str(years)} سال")
    if months:
        parts.append(f"{str(months)} ماه")
    if days or not parts:
        parts.append(f"{str(days)} روز")
    await ctx.respond(msg.AGE_RESULT.format(" و ".join(parts)))


async def bmi_command(ctx: CommandContext) -> None:
    parts = ctx.args.strip().split()
    if len(parts) != 2:
        raise CommandError(msg.BMI_MISSING)
    try:
        height_cm = float(parts[0])
        weight_kg = float(parts[1])
    except ValueError:
        raise CommandError(msg.BMI_INVALID) from None
    if not (50 <= height_cm <= 300):
        raise CommandError("قد باید بین ۵۰ تا ۳۰۰ سانتی‌متر باشد")
    if not (2 <= weight_kg <= 600):
        raise CommandError("وزن باید بین ۲ تا ۶۰۰ کیلوگرم باشد")
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m * height_m)
    category = _bmi_category(bmi)
    await ctx.respond(
        f"{msg.BMI_RESULT.format(str(round(bmi, 2)))}\n"
        f"{msg.BMI_CATEGORY.format(category)}"
    )


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return msg.BMI_CATEGORIES["below"]
    if bmi < 25:
        return msg.BMI_CATEGORIES["normal"]
    if bmi < 30:
        return msg.BMI_CATEGORIES["over"]
    return msg.BMI_CATEGORIES["obese"]


def _days_in_month(year: int, month: int) -> int:
    if month <= 0:
        month = 12
        year -= 1
    if month == 2:
        leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        return 29 if leap else 28
    return 31 if month in {1, 3, 5, 7, 8, 10, 12} else 30


def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="convert",
            handler=convert_command,
            category="convert",
            description="تبدیل واحدهای طول/وزن/دما/زمان/حجم داده",
            usage="/convert <مقدار> <مبدأ> <مقصد>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="currency",
            handler=currency_command,
            category="convert",
            description="نرخ لحظه‌ای ارز، طلا و کریپتو یا تبدیل ارز",
            usage="/currency | /currency <مقدار> <کد مبدأ> <کد مقصد>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="tz",
            handler=tz_command,
            category="convert",
            description="نمایش یک زمان در مناطق زمانی مختلف",
            usage="/tz <HH:MM> <منطقه1> <منطقه2> ...",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="weather",
            handler=weather_command,
            category="convert",
            description="مشاهده وضعیت آب‌وهوا",
            usage="/weather <شهر>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="datecalc",
            handler=datecalc_command,
            category="convert",
            description="محاسبه تاریخ با جمع/تفریق روز یا ماه",
            usage="/datecalc <تاریخ> + 30d",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="age",
            handler=age_command,
            category="convert",
            description="محاسبه سن از تاریخ تولد",
            usage="/age <YYYY-MM-DD>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="bmi",
            handler=bmi_command,
            category="convert",
            description="محاسبه شاخص توده بدنی",
            usage="/bmi <قد-cm> <وزن-kg>",
            owner_only=True,
        )
    )
