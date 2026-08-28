from policies.governance_policy import GovernanceAction, evaluate


def test_governance_policy_denies_inactive_user():
    allowed, reason = evaluate(
        action=GovernanceAction.CREATE_PROPOSAL,
        is_active_user=False,
        same_tenant=True,
    )
    assert allowed is False
    assert reason == "governance requires an active user"


def test_governance_policy_denies_cross_tenant_user():
    allowed, reason = evaluate(
        action=GovernanceAction.CAST_VOTE,
        is_active_user=True,
        same_tenant=False,
    )
    assert allowed is False
    assert reason == "governance tenant mismatch"


def test_governance_policy_denies_by_default():
    allowed, reason = evaluate(
        action=GovernanceAction.CREATE_PROPOSAL,
        is_active_user=True,
        same_tenant=True,
    )
    assert allowed is False
    assert reason == "governance action not yet constitutionally authorized"


def test_governance_actions_are_explicit():
    assert {action.value for action in GovernanceAction} == {
        "create_proposal",
        "open_proposal",
        "cast_vote",
        "close_proposal",
        "cancel_proposal",
    }

def test_governance_policy_does_not_infer_authority_from_application_role():
    allowed, reason = evaluate(
        action=GovernanceAction.CAST_VOTE,
        is_active_user=True,
        same_tenant=True,
    )

    assert allowed is False
    assert reason == "governance action not yet constitutionally authorized"
