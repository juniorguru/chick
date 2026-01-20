from datetime import datetime, timedelta, UTC

from jg.chick.lib.interests import Interest, NOTIFICATION_COOLDOWN, parse, should_notify


def test_parse_initializes_from_empty_state():
    current_interests: dict[int, Interest] = {}
    api_payload = [
        {"thread_id": 1, "role_id": 100},
        {"thread_id": 2, "role_id": 200},
    ]
    parsed = parse(api_payload, current_interests)

    assert parsed == {
        1: {"role_id": 100, "last_notified_at": None},
        2: {"role_id": 200, "last_notified_at": None},
    }


def test_parse_preserves_last_notified_for_existing_thread():
    last_notified = datetime.now(UTC) - timedelta(hours=2)
    current_interests: dict[int, Interest] = {
        3: {"role_id": 100, "last_notified_at": last_notified},
    }
    api_payload = [
        {"thread_id": 3, "role_id": 100},
        {"thread_id": 4, "role_id": 300},
    ]
    parsed = parse(api_payload, current_interests)

    assert parsed == {
        3: {"role_id": 100, "last_notified_at": last_notified},
        4: {"role_id": 300, "last_notified_at": None},
    }


def test_parse_resets_last_notified_for_new_thread_with_existing_role():
    last_notified = datetime.now(UTC) - timedelta(hours=1)
    current_interests: dict[int, Interest] = {
        1: {"role_id": 100, "last_notified_at": last_notified},
    }
    api_payload = [
        {"thread_id": 2, "role_id": 100},
    ]
    parsed = parse(api_payload, current_interests)

    assert parsed == {
        2: {"role_id": 100, "last_notified_at": None},
    }


def test_parse_drops_threads_missing_from_payload():
    current_interests: dict[int, Interest] = {
        1: {"role_id": 100, "last_notified_at": datetime.now(UTC)},
    }
    api_payload = [
        {"thread_id": 2, "role_id": 200},
    ]
    parsed = parse(api_payload, current_interests)

    assert list(parsed.keys()) == [2]


def test_should_notify_when_never_notified():
    now = datetime.now(UTC)
    role: Interest = {"role_id": 42, "last_notified_at": None}

    assert should_notify(role, now) is True


def test_should_notify_after_default_cooldown():
    now = datetime.now(UTC)
    role: Interest = {
        "role_id": 42,
        "last_notified_at": now - NOTIFICATION_COOLDOWN,
    }

    assert should_notify(role, now) is True


def test_should_not_notify_before_default_cooldown():
    now = datetime.now(UTC)
    role: Interest = {
        "role_id": 42,
        "last_notified_at": now - NOTIFICATION_COOLDOWN + timedelta(seconds=1),
    }

    assert should_notify(role, now) is False


def test_custom_cooldown_respected():
    now = datetime.now(UTC)
    cooldown = timedelta(hours=3)
    role: Interest = {
        "role_id": 42,
        "last_notified_at": now - timedelta(hours=2, minutes=30),
    }

    assert should_notify(role, now, cooldown=cooldown) is False
