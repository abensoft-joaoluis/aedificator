"""
Docker template generation for different projects.
"""


class DockerTemplates:
    """Generates Dockerfile content based on configurations."""

    @staticmethod
    def superleme_dockerfile(erlang_version: str, postgres_version: str) -> str:
        """
        Generate Dockerfile content for Superleme (Zotonic).

        Args:
            erlang_version: Erlang version (e.g., '28')
            postgres_version: PostgreSQL version (e.g., '17-alpine')

        Returns:
            Dockerfile content as string
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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/zotonic

# Copy application
COPY . .

# Build Zotonic
RUN make

# Expose ports
EXPOSE 8000 8443

# Default command
CMD ["bin/zotonic", "debug"]
"""

    @staticmethod
    def phoenix_dockerfile(
        elixir_version: str, erlang_version: str, node_version: str
    ) -> str:
        """
        Generate Dockerfile content for SL Phoenix.

        Args:
            elixir_version: Elixir version (e.g., '1.19.4')
            erlang_version: Erlang version (e.g., '28')
            node_version: Node.js version (e.g., '25.2.1')

        Returns:
            Dockerfile content as string
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
        Generate docker-compose.yml content for different stack configurations.

        Args:
            stack_type: 'superleme', 'phoenix', or 'full'
            postgres_version: PostgreSQL version

        Returns:
            docker-compose.yml content as string
        """
        compose_content = f"""# docker-compose.yml - {stack_type}
# Gerado automaticamente pelo Aedificator

version: '3.8'

services:
"""

        if stack_type in ["superleme", "full"]:
            compose_content += f"""
  postgres:
    image: postgres:{postgres_version}
    environment:
      POSTGRES_USER: zotonic
      POSTGRES_PASSWORD: zotonic
      POSTGRES_DB: zotonic
    volumes:
      - postgres_data:/var/lib/postgresql/data
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
      postgres:
        condition: service_healthy
    environment:
      ZOTONIC_DBHOST: postgres
      ZOTONIC_DBPORT: 5432
      ZOTONIC_DBUSER: zotonic
      ZOTONIC_DBPASSWORD: zotonic
      ZOTONIC_DBDATABASE: zotonic
    ports:
      - "8000:8000"
      - "8443:8443"
    volumes:
      - ./apps_user:/opt/zotonic/apps_user
    command: bin/zotonic debug
"""

        if stack_type in ["phoenix", "full"]:
            compose_content += f"""
  phoenix:
    build:
      context: .
      dockerfile: Dockerfile.phoenix
    environment:
      DATABASE_URL: ecto://zotonic:zotonic@postgres/zotonic
      SECRET_KEY_BASE: ${{SECRET_KEY_BASE:-changeme}}
      PHX_HOST: localhost
    ports:
      - "4000:4000"
    volumes:
      - ./priv:/app/priv
"""
            if stack_type == "phoenix":
                compose_content += f"""
  postgres:
    image: postgres:{postgres_version}
    environment:
      POSTGRES_USER: phoenix
      POSTGRES_PASSWORD: phoenix
      POSTGRES_DB: phoenix_dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
"""

        compose_content += """
volumes:
  postgres_data:
"""

        return compose_content
