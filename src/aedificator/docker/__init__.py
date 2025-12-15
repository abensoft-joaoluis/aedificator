"""
Docker management package for Aedificator.

This package handles Docker-related operations including:
- Dockerfile generation
- Docker image building
- Image pushing to registries
- docker-compose.yml generation
"""

from .manager import DockerManager

__all__ = ["DockerManager"]
