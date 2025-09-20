# Use an official Python runtime as a parent image
FROM python:3.10-alpine

# Arguments for user and group IDs, defaulting to 1000
ARG USER_GID=1000
ARG USER_UID=1000

# Create a non-root user and group
RUN addgroup -g ${USER_GID} vscode && adduser -u ${USER_UID} -G vscode -s /bin/sh -D vscode

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Switch to the non-root user
USER vscode

# Make port 80 available to the world outside this container
EXPOSE 80

# Run your python script
CMD ["python", "main.py"]
