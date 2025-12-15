"""
Docker template generation for different projects.
"""


class DockerTemplates:
    """Generates Dockerfile content based on configurations."""

    @staticmethod
    def superleme_dockerfile(erlang_version: str, postgres_version: str) -> str:
        """
        Generate Dockerfile content for Superleme (Zotonic).
        """
        return f"""# Dockerfile for Superleme (Zotonic)
# Gerado automaticamente pelo Aedificator
# Versões customizadas: Erlang {erlang_version}, PostgreSQL {postgres_version}

FROM erlang:{erlang_version}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    libssl-dev \\
    make \\
    imagemagick \\
    libmagickwand-dev \\
    postgresql-client \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# FIX: Install mise system-wide (binary) instead of user-local (shell script)
# This ensures it works for User 1000 (zotonic) and Root
# -----------------------------------------------------------------------------
RUN curl -L -o /usr/local/bin/mise https://mise.jdx.dev/mise-latest-linux-x64 \\
    && chmod +x /usr/local/bin/mise

# Create user zotonic (1000) inside the image
# This ensures 'mise' has a valid HOME directory to write its data to
RUN groupadd -g 1000 zotonic || true \\
    && useradd -m -u 1000 -g zotonic zotonic || true

# Set working directory
WORKDIR /opt/zotonic

# Note: Code is mounted as volume, not copied
# Compilation happens via 'make' command

# Expose ports
EXPOSE 8000 8443

CMD ["/bin/bash"]
"""

    @staticmethod
    def phoenix_dockerfile(
        elixir_version: str, erlang_version: str, node_version: str
    ) -> str:
        """
        Generate Dockerfile content for SL Phoenix.
        """
        return f"""# Dockerfile for SL Phoenix
# Gerado automaticamente pelo Aedificator
# Versões customizadas: Elixir {elixir_version}, Erlang {erlang_version}, Node.js {node_version}

# Build stage
FROM hexpm/elixir:{elixir_version}-erlang-{erlang_version}-alpine-3.20.3 AS build

# Install build dependencies
RUN apk add --no-cache build-base git npm

# Install Node.js
RUN apk add --no-cache nodejs-current={node_version}

WORKDIR /app

# Install hex and rebar
RUN mix local.hex --force && \\
    mix local.rebar --force

# Copy mix files
COPY mix.exs mix.lock ./
RUN mix deps.get --only prod
RUN mix deps.compile

# Copy application
COPY . .

# Install Node.js dependencies and build assets
RUN cd assets && npm ci && npm run deploy
RUN mix phx.digest

# Build release
RUN MIX_ENV=prod mix release

# Runtime stage
FROM alpine:3.20.3

RUN apk add --no-cache libstdc++ openssl ncurses-libs

WORKDIR /app

# Copy release from build stage
COPY --from=build /app/_build/prod/rel/sl_phoenix ./

# Expose port
EXPOSE 4000

# Default command
CMD ["bin/sl_phoenix", "start"]
"""

    @staticmethod
    def docker_compose(
        stack_type: str, postgres_version: str
    ) -> str:
        """
        Generate docker-compose.yml content with Volume Isolation.
        """
        # REMOVED: version: '3.8' (It is obsolete and causes warnings)
        compose_content = f"""# docker-compose.yml - {stack_type}
# Gerado automaticamente pelo Aedificator

services:
"""

        if stack_type in ["superleme", "full"]:
            compose_content += f"""
  postgres-zotonic:
    image: postgres:{postgres_version}
    container_name: zotonic-postgres
    environment:
      POSTGRES_USER: zotonic
      POSTGRES_PASSWORD: zotonic
      POSTGRES_DB: zotonic
    volumes:
      - postgres_zotonic_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U zotonic"]
      interval: 10s
      timeout: 5s
      retries: 5

  zotonic:
    build:
      context: .
      dockerfile: Dockerfile.superleme
    depends_on:
      postgres-zotonic:
        condition: service_healthy
    environment:
      ZOTONIC_DBHOST: postgres-zotonic
      ZOTONIC_DBPORT: 5432
      ZOTONIC_DBUSER: zotonic
      ZOTONIC_DBPASSWORD: zotonic
      ZOTONIC_DBDATABASE: zotonic
      # Explicitly set home so mise knows where to write config
      HOME: /home/zotonic
    ports:
      - "8000:8000"
      - "8443:8443"
    volumes:
      - .:/opt/zotonic
      # IMPORTANT: Isolate the build folder so Host and Docker don't conflict
      - zotonic_build:/opt/zotonic/_build
    working_dir: /opt/zotonic
    user: "1000:1000"
    entrypoint: ""
    command: ["/bin/bash"]
"""

        if stack_type in ["phoenix", "full"]:
            compose_content += f"""
  phoenix:
    build:
      context: .
      dockerfile: Dockerfile.phoenix
    environment:
      DATABASE_URL: ecto://phoenix:phoenix@postgres-phoenix/phoenix_dev
      SECRET_KEY_BASE: ${{SECRET_KEY_BASE:-changeme}}
      PHX_HOST: localhost
    ports:
      - "4000:4000"
    volumes:
      - .:/app
      # Isolate phoenix artifacts as well
      - phoenix_deps:/app/deps
      - phoenix_build:/app/_build
    working_dir: /app
    command: sh -c "mix deps.get && mix compile && mix ecto.setup && mix phx.server"
"""
            if stack_type == "phoenix":
                compose_content += f"""
  postgres-phoenix:
    image: postgres:{postgres_version}
    container_name: phoenix-postgres
    environment:
      POSTGRES_USER: phoenix
      POSTGRES_PASSWORD: phoenix
      POSTGRES_DB: phoenix_dev
    volumes:
      - postgres_phoenix_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
"""

        compose_content += """
volumes:
  postgres_zotonic_data:
  zotonic_build:
"""
        if stack_type in ["phoenix", "full"]:
            compose_content += """  postgres_phoenix_data:
  phoenix_deps:
  phoenix_build:
"""

        return compose_content