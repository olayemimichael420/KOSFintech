import json
import logging

from audit import audit_event


def test_audit_event_emits_structured_event(caplog):
    with caplog.at_level(logging.INFO, logger="kosfintech.audit"):
        audit_event(
            event_type="super_admin_transfer",
            actor_id=1,
            tenant_id="platform",
            action="transfer_super_admin",
            metadata={
                "from_user_id": 1,
                "to_user_id": 2,
            },
        )

    assert len(caplog.records) == 1

    message = caplog.records[0].message

    assert message.startswith("AUDIT ")

    payload = json.loads(message[len("AUDIT "):])

    assert payload["event_type"] == "super_admin_transfer"
    assert payload["actor_id"] == 1
    assert payload["tenant_id"] == "platform"
    assert payload["action"] == "transfer_super_admin"
    assert payload["metadata"]["from_user_id"] == 1
    assert payload["metadata"]["to_user_id"] == 2
    assert "timestamp" in payload
