"""Repository CRUD tests against an in-memory SQLite database."""

from __future__ import annotations

from datetime import timedelta

from selfbot.database.models import (
    AutoReplyRule,
    ProfileBackup,
    Reminder,
    ReminderStatus,
    ReminderType,
    TimerJob,
    utcnow,
)
from selfbot.database.repository import (
    AutoReplyRepository,
    BioItemRepository,
    BioTimeRepository,
    ChatPermissionRepository,
    ConfigRepository,
    ProfileBackupRepository,
    ReminderRepository,
    StopwatchRepository,
    TimerRepository,
)


async def test_config_key_value(session) -> None:
    repo = ConfigRepository(session)
    assert await repo.get("missing", "default") == "default"
    await repo.set("welcome", "hello")
    assert await repo.get("welcome") == "hello"
    await repo.set("welcome", "updated")
    assert await repo.get("welcome") == "updated"
    await repo.set_bool("flag", True)
    assert await repo.get_bool("flag") is True
    await repo.delete("welcome")
    assert await repo.get("welcome", "gone") == "gone"


async def test_autoreply_crud(session) -> None:
    repo = AutoReplyRepository(session)
    rule = AutoReplyRule(pattern="سلام", response="درود", match_type="exact", priority=5)
    saved = await repo.add(rule)
    assert saved.id is not None

    rules = await repo.list_all()
    assert len(rules) == 1
    assert (await repo.get(saved.id)).pattern == "سلام"

    assert await repo.delete(saved.id) is True
    assert await repo.delete(saved.id) is False
    assert await repo.list_all() == []


async def test_autoreply_ordering(session) -> None:
    repo = AutoReplyRepository(session)
    await repo.add(AutoReplyRule(pattern="low", response="l", match_type="exact", priority=1))
    await repo.add(AutoReplyRule(pattern="high", response="h", match_type="exact", priority=9))
    rules = await repo.list_all()
    assert rules[0].pattern == "high"


async def test_reminder_crud(session) -> None:
    repo = ReminderRepository(session)
    reminder = Reminder(
        type=ReminderType.DAILY,
        schedule="09:00",
        text="چک کردن ایمیل",
        status=ReminderStatus.ACTIVE,
        next_run_at=utcnow() + timedelta(hours=1),
    )
    saved = await repo.add(reminder)
    assert saved.id is not None

    active = await repo.list_active()
    assert len(active) == 1

    await repo.mark_done(saved)
    assert (await repo.get(saved.id)).status == ReminderStatus.DONE
    assert await repo.list_active() == []

    assert await repo.delete(saved.id) is True


async def test_permissions(session) -> None:
    repo = ChatPermissionRepository(session)
    assert await repo.is_blocked(5) is False
    await repo.set_action(5, "block")
    assert await repo.is_blocked(5) is True
    await repo.set_action(5, "allow")
    assert await repo.is_allowed(5) is True
    await repo.remove(5)
    assert await repo.is_allowed(5) is False


async def test_bio_items(session) -> None:
    repo = BioItemRepository(session)
    item = await repo.add("لبخند بزن")
    items = await repo.list_all()
    assert len(items) == 1
    assert await repo.delete(item.id) is True


async def test_bio_time_rules(session) -> None:
    repo = BioTimeRepository(session)
    from selfbot.database.models import BioTimeRule

    rule = await repo.add(BioTimeRule(start_time="09:00", end_time="17:00", bio_text="مشغول کار"))
    rules = await repo.list_all()
    assert len(rules) == 1
    assert rules[0].bio_text == "مشغول کار"
    assert await repo.delete(rule.id) is True


async def test_profile_backup(session) -> None:
    repo = ProfileBackupRepository(session)
    backup = ProfileBackup(
        first_name="تست",
        last_name="دوم",
        bio="درباره من",
        username="tester",
        photo_file_id="AaBb",
    )
    saved = await repo.add(backup)
    fetched = await repo.get(saved.id)
    assert fetched is not None
    assert fetched.username == "tester"
    assert len(await repo.list_all(limit=5)) == 1


async def test_timer_jobs(session) -> None:
    repo = TimerRepository(session)
    job = await repo.add(
        TimerJob(
            duration=300,
            fire_at=utcnow() + timedelta(minutes=5),
            chat_id=1,
            reply_to=2,
        )
    )
    pending = await repo.list_pending()
    assert len(pending) == 1
    assert pending[0].reply_to == 2
    await repo.mark_fired(job.id)
    assert await repo.list_pending() == []


async def test_stopwatch_singleton(session) -> None:
    repo = StopwatchRepository(session)
    first = await repo.get()
    second = await repo.get()
    assert first.id == second.id
    first.running = True
    await repo.save(first)
    state = await repo.get()
    assert state.running is True
