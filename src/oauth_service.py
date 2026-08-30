"""OAuth 2.0 service for Google and GitHub authentication in MultiVision AI."""

import os
import time
import secrets
import logging
import urllib.parse
from typing import Dict, Any, Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

# State storage with expiry (15 minutes TTL) to prevent CSRF
_OAUTH_STATES: Dict[str, Dict[str, Any]] = {}
_STATE_TTL_SECONDS = 900


def _cleanup_expired_states():
    now = time.time()
    expired = [s for s, data in _OAUTH_STATES.items() if now - data.get("created_at", 0) > _STATE_TTL_SECONDS]
    for s in expired:
        _OAUTH_STATES.pop(s, None)


class OAuthService:
    @staticmethod
    def get_google_config() -> Dict[str, Any]:
        client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        enabled = bool(client_id and client_secret)
        return {
            "name": "Google",
            "provider": "google",
            "enabled": enabled,
            "configured": bool(client_id),
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scopes": ["openid", "email", "profile"],
        }

    @staticmethod
    def get_github_config() -> Dict[str, Any]:
        client_id = os.getenv("GITHUB_CLIENT_ID", "").strip()
        client_secret = os.getenv("GITHUB_CLIENT_SECRET", "").strip()
        enabled = bool(client_id and client_secret)
        return {
            "name": "GitHub",
            "provider": "github",
            "enabled": enabled,
            "configured": bool(client_id),
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "emails_url": "https://api.github.com/user/emails",
            "scopes": ["read:user", "user:email"],
        }

    @classmethod
    def get_providers_status(cls) -> Dict[str, Any]:
        """Return public status of OAuth providers for frontend rendering."""
        g = cls.get_google_config()
        gh = cls.get_github_config()
        return {
            "google": {
                "name": "Google",
                "enabled": g["enabled"],
                "configured": g["configured"],
            },
            "github": {
                "name": "GitHub",
                "enabled": gh["enabled"],
                "configured": gh["configured"],
            },
        }

    @classmethod
    def create_state(cls, provider: str, redirect_path: str = "/") -> str:
        _cleanup_expired_states()
        state = secrets.token_urlsafe(32)
        _OAUTH_STATES[state] = {
            "provider": provider,
            "redirect_path": redirect_path or "/",
            "created_at": time.time(),
        }
        return state

    @classmethod
    def verify_state(cls, state: str, expected_provider: str) -> Optional[Dict[str, Any]]:
        _cleanup_expired_states()
        if not state or state not in _OAUTH_STATES:
            return None
        data = _OAUTH_STATES.pop(state)
        if data.get("provider") != expected_provider:
            return None
        return data

    @classmethod
    def build_authorization_url(cls, provider: str, redirect_uri: str, state: str) -> Tuple[str, Optional[str]]:
        """Return (authorization_url, error_message)."""
        provider = provider.lower()
        if provider == "google":
            cfg = cls.get_google_config()
            if not cfg["client_id"]:
                return "", "GOOGLE_CLIENT_ID is not configured in .env"
            params = {
                "client_id": cfg["client_id"],
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(cfg["scopes"]),
                "state": state,
                "access_type": "offline",
                "prompt": "select_account",
            }
            url = f"{cfg['auth_url']}?{urllib.parse.urlencode(params)}"
            return url, None

        elif provider == "github":
            cfg = cls.get_github_config()
            if not cfg["client_id"]:
                return "", "GITHUB_CLIENT_ID is not configured in .env"
            params = {
                "client_id": cfg["client_id"],
                "redirect_uri": redirect_uri,
                "scope": " ".join(cfg["scopes"]),
                "state": state,
                "allow_signup": "true",
            }
            url = f"{cfg['auth_url']}?{urllib.parse.urlencode(params)}"
            return url, None

        return "", f"Unsupported OAuth provider: {provider}"

    @classmethod
    async def exchange_code_and_get_user(
        cls, provider: str, code: str, redirect_uri: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Exchange auth code for access token and fetch user profile.
        Returns (user_dict, error_message).
        """
        provider = provider.lower()
        if provider == "google":
            cfg = cls.get_google_config()
            if not cfg["enabled"]:
                return None, "Google OAuth is not fully configured (missing client ID or secret)"

            token_data = {
                "code": code,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    token_res = await client.post(cfg["token_url"], data=token_data)
                    if token_res.status_code != 200:
                        logger.error(f"Google token exchange failed: {token_res.text}")
                        return None, f"Google token exchange failed: {token_res.text}"
                    token_json = token_res.json()
                    access_token = token_json.get("access_token")
                    if not access_token:
                        return None, "Missing access_token in Google response"

                    # Fetch userinfo
                    headers = {"Authorization": f"Bearer {access_token}"}
                    info_res = await client.get(cfg["userinfo_url"], headers=headers)
                    if info_res.status_code != 200:
                        return None, f"Failed to fetch Google profile: {info_res.text}"
                    info = info_res.json()

                    return {
                        "provider": "google",
                        "oauth_id": str(info.get("sub") or info.get("id")),
                        "email": info.get("email"),
                        "name": info.get("name"),
                        "username_hint": (info.get("email", "").split("@")[0] if info.get("email") else info.get("given_name")),
                        "avatar_url": info.get("picture"),
                    }, None
            except Exception as e:
                logger.exception("Google OAuth error")
                return None, f"Google OAuth request failed: {str(e)}"

        elif provider == "github":
            cfg = cls.get_github_config()
            if not cfg["enabled"]:
                return None, "GitHub OAuth is not fully configured (missing client ID or secret)"

            token_data = {
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code": code,
                "redirect_uri": redirect_uri,
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    token_res = await client.post(
                        cfg["token_url"],
                        data=token_data,
                        headers={"Accept": "application/json"},
                    )
                    if token_res.status_code != 200:
                        logger.error(f"GitHub token exchange failed: {token_res.text}")
                        return None, f"GitHub token exchange failed: {token_res.text}"
                    token_json = token_res.json()
                    access_token = token_json.get("access_token")
                    if not access_token:
                        err_desc = token_json.get("error_description", token_json.get("error", "No access token"))
                        return None, f"GitHub OAuth error: {err_desc}"

                    # Fetch user info
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "MultiVision-AI-OAuth",
                    }
                    user_res = await client.get(cfg["userinfo_url"], headers=headers)
                    if user_res.status_code != 200:
                        return None, f"Failed to fetch GitHub user: {user_res.text}"
                    user_info = user_res.json()

                    email = user_info.get("email")
                    # If email is null/private, fetch from emails endpoint
                    if not email:
                        emails_res = await client.get(cfg["emails_url"], headers=headers)
                        if emails_res.status_code == 200:
                            for em in emails_res.json():
                                if em.get("primary") and em.get("verified"):
                                    email = em.get("email")
                                    break
                                elif not email and em.get("verified"):
                                    email = em.get("email")

                    return {
                        "provider": "github",
                        "oauth_id": str(user_info.get("id")),
                        "email": email,
                        "name": user_info.get("name") or user_info.get("login"),
                        "username_hint": user_info.get("login"),
                        "avatar_url": user_info.get("avatar_url"),
                    }, None
            except Exception as e:
                logger.exception("GitHub OAuth error")
                return None, f"GitHub OAuth request failed: {str(e)}"

        return None, f"Unsupported OAuth provider: {provider}"
