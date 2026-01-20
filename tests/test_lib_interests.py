from datetime import UTC, datetime, timedelta

from jg.chick.lib.interests import NOTIFICATION_COOLDOWN, Role, should_notify, update


def test_update_preserves_last_notified_when_role_reappears():
    last_notified = datetime.now(UTC) - timedelta(hours=2)
    current_interests: dict[int, Role] = {
        1: Role(id=100, last_notified_at=last_notified),
        2: Role(id=200, last_notified_at=datetime.now(UTC)),
    }
    new_interests: dict[int, Role] = {
        3: Role(id=100, last_notified_at=None),
        4: Role(id=300, last_notified_at=None),
    }
    updated_interests = update(current_interests, new_interests)

    assert updated_interests == {
        3: Role(id=100, last_notified_at=last_notified),
        4: Role(id=300, last_notified_at=None),
    }


def test_update_drops_threads_missing_from_new_interests():
    current_interests: dict[int, Role] = {
        1: Role(id=100, last_notified_at=datetime.now(UTC)),
    }
    new_interests: dict[int, Role] = {
        2: Role(id=200, last_notified_at=None),
    }
    updated_interests = update(current_interests, new_interests)

    assert list(updated_interests.keys()) == [2]


def test_should_notify_when_never_notified():
    now = datetime.now(UTC)
    role: Role = {"id": 42, "last_notified_at": None}

    assert should_notify(role, now) is True


def test_should_notify_after_default_cooldown():
    now = datetime.now(UTC)
    role: Role = {"id": 42, "last_notified_at": now - NOTIFICATION_COOLDOWN}

    assert should_notify(role, now) is True


def test_should_not_notify_before_default_cooldown():
    now = datetime.now(UTC)
    role: Role = {
        "id": 42,
        "last_notified_at": now - NOTIFICATION_COOLDOWN + timedelta(seconds=1),
    }

    assert should_notify(role, now) is False


def test_custom_cooldown_respected():
    now = datetime.now(UTC)
    cooldown = timedelta(hours=3)
    role: Role = {
        "id": 42,
        "last_notified_at": now - timedelta(hours=2, minutes=30),
    }

    assert should_notify(role, now, cooldown=cooldown) is False
