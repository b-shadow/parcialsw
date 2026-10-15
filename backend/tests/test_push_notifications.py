from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from pywebpush import WebPushException

from app.modules.notificaciones.services import push_service
from app.modules.notificaciones.services.push_service import PushNotificationService


def _subscription():
    return SimpleNamespace(
        endpoint="https://push.example.test/subscription",
        p256dh="public-encryption-key",
        auth="authentication-secret",
        expires_at=None,
        last_success_at=None,
        failure_count=0,
        is_active=True,
    )


def _service(subscription):
    db = Mock()
    service = PushNotificationService(db)
    service.subscriptions = Mock()
    service.subscriptions.list_active_for_users.return_value = [subscription]
    return service, db


def test_push_service_sends_json_payload_and_records_success(monkeypatch) -> None:
    subscription = _subscription()
    service, db = _service(subscription)
    send = Mock()
    monkeypatch.setattr(push_service, "webpush", send)
    monkeypatch.setattr(push_service.settings, "vapid_public_key", "public")
    monkeypatch.setattr(push_service.settings, "vapid_private_key", "private")
    monkeypatch.setattr(push_service.settings, "vapid_subject", "mailto:test@example.com")

    result = service.send_to_users({uuid4()}, {"title": "Version guardada", "url": "/"})

    assert result == {"sent": 1, "failed": 0, "removed": 0}
    assert subscription.last_success_at is not None
    assert subscription.failure_count == 0
    assert '"title": "Version guardada"' in send.call_args.kwargs["data"]
    db.commit.assert_called_once()


def test_push_service_removes_expired_remote_subscription(monkeypatch) -> None:
    subscription = _subscription()
    service, db = _service(subscription)
    response = SimpleNamespace(status_code=410)
    monkeypatch.setattr(
        push_service,
        "webpush",
        Mock(side_effect=WebPushException("gone", response=response)),
    )
    monkeypatch.setattr(push_service.settings, "vapid_public_key", "public")
    monkeypatch.setattr(push_service.settings, "vapid_private_key", "private")
    monkeypatch.setattr(push_service.settings, "vapid_subject", "mailto:test@example.com")

    result = service.send_to_users({uuid4()}, {"title": "Prueba"})

    assert result == {"sent": 0, "failed": 0, "removed": 1}
    service.subscriptions.delete.assert_called_once_with(subscription)
    db.commit.assert_called_once()
