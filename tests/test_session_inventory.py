from session_inventory import Session, sessions_to_sign_out


def test_keeps_current_device_and_selects_only_active_others():
    sessions = [
        Session("phone", "seller phone"),
        Session("laptop", "seller laptop"),
        Session("old-tablet", "old tablet", active=False),
    ]
    selected = sessions_to_sign_out(sessions, "laptop")
    assert [session.session_id for session in selected] == ["phone"]
