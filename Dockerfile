FROM python:3.10-slim

ARG USER_GID=1000
ARG USER_UID=1000

# 1. Install sudo (CRITICAL for Dev Containers to fix permissions dynamically)
RUN apt-get update && apt-get install -y \
    bash \
    wget \
    procps \
    git \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 2. Create the user and add to sudoers (Passwordless sudo)
RUN groupadd --gid ${USER_GID} vscode \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

WORKDIR /app

# 3. Use --chown to ensure the copied files belong to the user, not root
COPY --chown=vscode:vscode . /app

USER vscode

EXPOSE 80
EXPOSE 5000

# 4. PATH update is often needed for pip --user installs to work immediately
ENV PATH="/home/vscode/.local/bin:${PATH}"

RUN pip install --user --no-cache-dir -r requirements.txt