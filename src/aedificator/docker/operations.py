"""
Docker operations for building and pushing images.
"""

import os
from typing import Optional
from .. import console
from ..executor import Executor


class DockerOperations:
    """Handles Docker build and push operations."""

    @staticmethod
    def build_image(
        dockerfile_path: str,
        image_name: str,
        image_tag: str,
        build_context: str,
        build_args: dict | None = None,
    ):
        """
        Build Docker image using Dockerfile.

        Args:
            dockerfile_path: Path to Dockerfile
            image_name: Name of the image (e.g., 'superleme')
            image_tag: Tag for the image (e.g., 'latest')
            build_context: Build context directory
        """
        console.print(f"[info]Buildando imagem Docker: {image_name}:{image_tag}[/info]")

        # Append build-arg flags when provided
        arg_flags = ""
        if build_args:
            parts = []
            for k, v in build_args.items():
                if v is None:
                    continue
                parts.append(f"--build-arg {k}={v}")
            if parts:
                arg_flags = " " + " ".join(parts)

        command = f"docker build -f {dockerfile_path} -t {image_name}:{image_tag}{arg_flags} {build_context}"

        # Use executor to run with real-time output
        Executor.run_command(command, build_context, background=False, use_docker=False)

    @staticmethod
    def push_image(image_name: str, image_tag: str, registry: Optional[str] = None, cwd: Optional[str] = None):
        """
        Push Docker image to registry.

        Args:
            image_name: Name of the image
            image_tag: Tag of the image
            registry: Optional registry URL (defaults to Docker Hub)
            cwd: Working directory (defaults to home directory)
        """
        if cwd is None:
            cwd = os.path.expanduser("~")

        if registry:
            full_image = f"{registry}/{image_name}:{image_tag}"
            # Tag image with registry
            tag_command = f"docker tag {image_name}:{image_tag} {full_image}"
            Executor.run_command(
                tag_command, cwd, background=False, use_docker=False
            )
        else:
            full_image = f"{image_name}:{image_tag}"

        console.print(f"[info]Enviando imagem para registry: {full_image}[/info]")

        command = f"docker push {full_image}"

        # Use executor to run with real-time output
        Executor.run_command(command, cwd, background=False, use_docker=False)

    @staticmethod
    def list_images(cwd: Optional[str] = None):
        """List all Docker images.

        Args:
            cwd: Working directory (defaults to home directory)
        """
        if cwd is None:
            cwd = os.path.expanduser("~")

        console.print("[info]Listando imagens Docker locais:[/info]")
        Executor.run_command(
            "docker images", cwd, background=False, use_docker=False
        )

    @staticmethod
    def remove_image(image_name: str, image_tag: str, force: bool = False, cwd: Optional[str] = None):
        """
        Remove Docker image.

        Args:
            image_name: Name of the image
            image_tag: Tag of the image
            force: Force removal even if image is in use
            cwd: Working directory (defaults to home directory)
        """
        if cwd is None:
            cwd = os.path.expanduser("~")

        full_image = f"{image_name}:{image_tag}"
        console.print(f"[info]Removendo imagem: {full_image}[/info]")

        force_flag = "-f" if force else ""
        command = f"docker rmi {force_flag} {full_image}"

        Executor.run_command(command, cwd, background=False, use_docker=False)

    @staticmethod
    def prune_images(all_images: bool = False, cwd: Optional[str] = None):
        """
        Remove unused Docker images.

        Args:
            all_images: Remove all unused images, not just dangling ones
            cwd: Working directory (defaults to home directory)
        """
        if cwd is None:
            cwd = os.path.expanduser("~")

        console.print("[info]Removendo imagens Docker não utilizadas...[/info]")

        all_flag = "-a" if all_images else ""
        command = f"docker image prune {all_flag} -f"

        Executor.run_command(command, cwd, background=False, use_docker=False)
