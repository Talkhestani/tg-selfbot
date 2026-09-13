"""Reminder commands: create, list, delete, snooze."""

from __future__ import annotations

from datetime import datetime

from selfbot.database.models import Reminder, ReminderType
from selfbot.database.repository import ReminderRepository
from selfbot.messages import persian as msg
from selfbot.services import reminder_planner
from selfbot.services.reminder_planner import format_utc_for_tz, snooze_next_run
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec
from selfbot.utils.validators import ValidationError


async def remind_command(ctx: CommandContext) -> None:
    if not ctx.args:
        raise CommandError(
            "مثال‌ها:\n"
            "`/remind 20m با مشتری تماس بگیر`\n"
            "`/remind 2026-10-01 18:30 جلسه`\n"
            "`/remind daily 09:00 ورزش`\n"
            "`/remind weekly mon 09:00 جلسه هفتگی`\n"
            "`/remind monthly 1 10:00 پرداخت قبض`"
        )

    tz_name = ctx.services.settings.timezone
    text = ctx.args.strip()

    # Dispatch by leading keyword.
    first = text.split(maxsplit=1)[0].lower()
    try:
        if first == "daily":
            reminder_text, schedule, next_run = reminder_planner.plan_daily(
                text[len(first):].strip(), tz_name
            )
            rtype = ReminderType.DAILY
        elif first == "weekly":
            reminder_text, schedule, next_run = reminder_planner.plan_weekly(
                text[len(first):].strip(), tz_name
            )
            rtype = ReminderType.WEEKLY
        elif first == "monthly":
            reminder_text, schedule, next_run = reminder_planner.plan_monthly(
                text[len(first):].strip(), tz_name
            )
            rtype = ReminderType.MONTHLY
        else:
            reminder_text, schedule, next_run = reminder_planner.plan_relative_or_absolute(
                text, tz_name
            )
            rtype = ReminderType.ONE_TIME
    except ValidationError as exc:
        raise CommandError(f"{msg.REMINDER_INVALID_TIME}\n{exc}") from exc

    if not reminder_text:
        raise CommandError("متن یادآوری را وارد کنید.")

    async with ctx.services.database.session_ctx() as session:
        repo = ReminderRepository(session)
        reminder = await repo.add(
            Reminder(
                text=reminder_text,
                chat_id=ctx.chat_id,
                type=rtype,
                schedule=schedule,
                timezone=tz_name,
                next_run_at=next_run,
            )
        )

    await ctx.services.reminder_service.reschedule(reminder)

    display = format_utc_for_tz(next_run, tz_name)
    message = (
        f"{msg.REMINDER_CREATED}\n\n"
        f"📌 شناسه: {str(reminder.id)}\n"
        f"📝 متن: {reminder_text}\n"
        f"🕐 زمان بعدی: {display}\n"
        f"🔄 نوع: {msg.REMINDER_TYPES[rtype.value]}"
    )
    await ctx.respond(message)


async def reminders_command(ctx: CommandContext) -> None:
    async with ctx.services.database.session_ctx() as session:
        repo = ReminderRepository(session)
        reminders = await repo.list_all()

    if not reminders:
        await ctx.respond(msg.REMINDER_LIST_EMPTY)
        return

    tz_name = ctx.services.settings.timezone
    lines = [msg.REMINDER_LIST_HEADER, ""]
    for reminder in reminders:
        status = _status_fa(reminder.status.value)
        kind = msg.REMINDER_TYPES.get(reminder.type.value, reminder.type.value)
        schedule = reminder_planner.schedule_display(reminder.schedule, reminder.type.value)
        next_display = format_utc_for_tz(reminder.next_run_at, tz_name)
        lines.append(
            f"ⓘ {str(reminder.id)}. {reminder.text}\n"
            f"   نوع: {kind} | برنامه: {schedule}\n"
            f"   زمان بعدی: {next_display} | وضعیت: {status}"
        )
    await ctx.respond("\n".join(lines))


async def reminddel_command(ctx: CommandContext) -> None:
    if not ctx.args.strip().isdigit():
        raise CommandError("شناسه یادآوری را وارد کنید. مثال:\n`/reminddel 12`")
    reminder_id = int(ctx.args.strip())

    async with ctx.services.database.session_ctx() as session:
        repo = ReminderRepository(session)
        removed = await repo.delete(reminder_id)

    if not removed:
        raise CommandError(msg.REMINDER_NOT_FOUND)
    ctx.services.reminder_service._remove_job(reminder_id)
    await ctx.respond(f"{msg.REMINDER_DELETED}")


async def snooze_command(ctx: CommandContext) -> None:
    parts = ctx.args.strip().split(maxsplit=1)
    if len(parts) != 2 or not parts[0].isdigit():
        raise CommandError("مثال:\n`/snooze 12 30m`")
    reminder_id = int(parts[0])
    duration_text = parts[1].strip()

    async with ctx.services.database.session_ctx() as session:
        repo = ReminderRepository(session)
        reminder = await repo.get(reminder_id)

    if reminder is None:
        raise CommandError(msg.REMINDER_NOT_FOUND)
    if reminder.type != ReminderType.ONE_TIME:
        raise CommandError("فقط یادآوری‌های تک‌باره قابل تعویق هستند.")

    try:
        new_run = snooze_next_run(reminder.next_run_at or datetime.utcnow(), duration_text)
    except ValidationError:
        raise CommandError(msg.REMINDER_SNOOZE_INVALID) from None

    reminder.next_run_at = new_run
    async with ctx.services.database.session_ctx() as session:
        stored = await session.get(Reminder, reminder_id)
        if stored is not None:
            stored.next_run_at = new_run
            await session.commit()
    await ctx.services.reminder_service.reschedule(reminder)
    await ctx.respond(msg.REMINDER_SNOOZED)


def _status_fa(status: str) -> str:
    return {
        "active": "فعال",
        "paused": "مکث",
        "done": "انجام‌شده",
        "deleted": "حذف‌شده",
    }.get(status, status)


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="remind",
            handler=remind_command,
            category="reminder",
            description="ایجاد یادآوری (تک‌باره، روزانه، هفتگی، ماهانه)",
            usage="/remind <زمان> <متن>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="reminders",
            handler=reminders_command,
            category="reminder",
            description="فهرست یادآوری‌ها",
            usage="/reminders",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="reminddel",
            handler=reminddel_command,
            category="reminder",
            description="حذف یک یادآوری",
            usage="/reminddel <id>",
            owner_only=True,
        )
    )
    dispatcher.register(
        CommandSpec(
            name="snooze",
            handler=snooze_command,
            category="reminder",
            description="به تعویق انداختن یک یادآوری تک‌باره",
            usage="/snooze <id> <مدت>",
            owner_only=True,
        )
    )
