import pytest
import os
from unittest.mock import patch, MagicMock
from core.auth import AuthManager
from src.oauth_service import OAuthService


def test_oauth_providers_status():
    status = OAuthService.get_providers_status()
    assert "google" in status
    assert "github" in status
    assert status["google"]["name"] == "Google"
    assert status["github"]["name"] == "GitHub"


def test_oauth_state_creation_and_verification():
    state = OAuthService.create_state("google", redirect_path="/custom")
    assert state is not None
    assert len(state) > 10

    # Wrong provider fails
    assert OAuthService.verify_state(state, "github") is None

    # Correct provider succeeds and returns data
    state2 = OAuthService.create_state("github", redirect_path="/dashboard")
    verified = OAuthService.verify_state(state2, "github")
    assert verified is not None
    assert verified["provider"] == "github"
    assert verified["redirect_path"] == "/dashboard"

    # State is one-time use
    assert OAuthService.verify_state(state2, "github") is None


def test_build_authorization_url():
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-google-id", "GITHUB_CLIENT_ID": "test-github-id"}):
        url, err = OAuthService.build_authorization_url("google", "http://localhost:7000/callback", "state123")
        assert err is None
        assert "accounts.google.com" in url
        assert "test-google-id" in url
        assert "state123" in url

        gh_url, gh_err = OAuthService.build_authorization_url("github", "http://localhost:7000/callback", "state456")
        assert gh_err is None
        assert "github.com/login/oauth/authorize" in gh_url
        assert "test-github-id" in gh_url


def test_auth_manager_get_or_create_oauth_user(tmp_path):
    auth_file = str(tmp_path / "auth.json")
    mgr = AuthManager(auth_path=auth_file)

    # 1. Create first user via Google OAuth -> should be admin
    u1 = mgr.get_or_create_oauth_user(
        provider="google",
        oauth_id="123456789",
        email="john.doe@example.com",
        username_hint="johndoe",
        display_name="John Doe",
        avatar_url="https://example.com/avatar.png",
    )
    assert u1 == "johndoe"
    assert mgr.is_admin("johndoe") is True
    assert mgr.users["johndoe"]["oauth_provider"] == "google"
    assert mgr.users["johndoe"]["oauth_id"] == "123456789"
    assert mgr.users["johndoe"]["email"] == "john.doe@example.com"

    # 2. Subsequent call with same provider + oauth_id returns existing user
    u1_again = mgr.get_or_create_oauth_user(
        provider="google",
        oauth_id="123456789",
        email="john.doe@example.com",
    )
    assert u1_again == "johndoe"

    # 3. Create second user via GitHub -> not admin
    u2 = mgr.get_or_create_oauth_user(
        provider="github",
        oauth_id="987654321",
        email="alice@github.com",
        username_hint="alice",
        display_name="Alice Developer",
    )
    assert u2 == "alice"
    assert mgr.is_admin("alice") is False

    # 4. Create another user with colliding username hint
    u3 = mgr.get_or_create_oauth_user(
        provider="github",
        oauth_id="1122334455",
        email="alice.second@github.com",
        username_hint="alice",
    )
    assert u3 == "alice1"
