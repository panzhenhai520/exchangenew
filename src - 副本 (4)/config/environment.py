#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Environment configuration helpers.

The backend no longer performs any automatic network probing.  Instead we
read everything from environment variables, and as a convenience fall back to
the front-end `.env.local` file so that maintaining a single configuration
source remains possible.
"""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from dotenv import dotenv_values


class EnvironmentConfig:
    """Read-only environment configuration sourced from explicit settings."""

    def __init__(self) -> None:
        self._current_ip = self._load_current_ip()
        self._backend_port = self._load_port("BACKEND_PORT", 5001)
        self._frontend_port = self._load_port("FRONTEND_PORT", 8080)

    @property
    def current_ip(self) -> str:
        """Return the configured IP address."""
        return self._current_ip

    @property
    def backend_port(self) -> int:
        """Return the backend port."""
        return self._backend_port

    @property
    def frontend_port(self) -> int:
        """Return the frontend port."""
        return self._frontend_port

    @property
    def backend_url(self) -> str:
        """Return the backend service URL."""
        return f"http://{self.current_ip}:{self.backend_port}"

    @property
    def frontend_url(self) -> str:
        """Return the frontend service URL."""
        return f"http://{self.current_ip}:{self.frontend_port}"

    def _load_current_ip(self) -> str:
        """
        Determine the current IP.

        Precedence:
          1. Environment variable CURRENT_IP (recommended).
          2. Host extracted from project-root/.env.local -> VUE_APP_API_BASE_URL.
        """
        env_ip = os.environ.get("CURRENT_IP")
        if env_ip:
            if self._is_valid_ip(env_ip):
                return env_ip
            raise ValueError(f"环境变量 CURRENT_IP 的值无效: {env_ip}")

        # Fallback: read .env.local so that front-end configuration can drive backend.
        env_local_ip = self._load_ip_from_env_local()
        if env_local_ip:
            return env_local_ip

        raise RuntimeError(
            "未检测到有效的 IP 配置。请在环境变量 CURRENT_IP 中设置服务器 IP，"
            "或在项目根目录的 .env.local 中设置 VUE_APP_API_BASE_URL。"
        )

    def _load_ip_from_env_local(self) -> str | None:
        """Attempt to read VUE_APP_API_BASE_URL from .env.local and extract IP."""
        root_dir = Path(__file__).resolve().parents[2]  # project root
        env_local_path = root_dir / ".env.local"
        if not env_local_path.exists():
            return None

        config = dotenv_values(env_local_path)
        url = config.get("VUE_APP_API_BASE_URL")
        if not url:
            return None

        parsed = urlparse(url if "://" in url else f"http://{url}")
        host = parsed.hostname
        if host and self._is_valid_ip(host):
            return host
        return None

    def _load_port(self, env_name: str, default: int) -> int:
        """Read a port from environment or use the provided default."""
        value = os.environ.get(env_name)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"环境变量 {env_name} 必须是数字，当前值: {value}") from exc

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IPv4 string."""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def get_cors_origins(self) -> List[str]:
        """Return a list of allowed CORS origins."""
        origins: List[str] = [
            r"http://localhost:\d+",
            r"http://127\.0\.0\.1:\d+",
            f"http://{self.current_ip}:{self.frontend_port}",
            f"http://{self.current_ip}:{self.backend_port}",
            "null",
        ]

        for port in [3000, 8080, 8081, 8082, 8083, 5001, 5173]:
            origins.append(f"http://{self.current_ip}:{port}")

        return origins


env_config = EnvironmentConfig()


def get_current_ip() -> str:
    """Convenience wrapper."""
    return env_config.current_ip


def get_backend_url() -> str:
    """Convenience wrapper."""
    return env_config.backend_url


def get_frontend_url() -> str:
    """Convenience wrapper."""
    return env_config.frontend_url
