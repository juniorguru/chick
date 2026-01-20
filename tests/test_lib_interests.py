from datetime import datetime, timedelta

from jg.chick.lib.interests import NOTIFICATION_COOLDOWN, Role, should_notify


def test_should_notify_when_never_notified():
    now = datetime.now()
    role: Role = {"id": 42, "last_notified_at": None}

    assert should_notify(role, now) is True


def test_should_notify_after_default_cooldown():
    now = datetime.now()
    role: Role = {"id": 42, "last_notified_at": now - NOTIFICATION_COOLDOWN}

    assert should_notify(role, now) is True


def test_should_not_notify_before_default_cooldown():
    now = datetime.now()
    role: Role = {
        "id": 42,
        "last_notified_at": now - NOTIFICATION_COOLDOWN + timedelta(seconds=1),
    }

    assert should_notify(role, now) is False


def test_custom_cooldown_respected():
    now = datetime.now()
    cooldown = timedelta(hours=3)
    role: Role = {
        "id": 42,
        "last_notified_at": now - timedelta(hours=2, minutes=30),
    }

    assert should_notify(role, now, cooldown=cooldown) is False
