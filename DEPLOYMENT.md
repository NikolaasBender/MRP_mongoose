# Deployment Guide for Raspberry Pi

This guide explains how to deploy the application to a Raspberry Pi and set it up for automatic updates using Watchtower.

## Prerequisites

- Raspberry Pi (Pi 4 or 5 recommended) with Raspberry Pi OS (64-bit recommended).
- Internet connection.
- `SHOPIFY_API_KEY`, `SHOPIFY_ACCESS_TOKEN`, etc.

## 1. Install Docker on Raspberry Pi

SSH into your Pi and run:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```
*Logout and login again for the group change to take effect.*

## 2. Docker Login

Generate a Classic Personal Access Token (PAT) on GitHub with `read:packages` permissions.

```bash
echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

## 3. Create Deployment Directory

Create a folder for the app:

```bash
mkdir -p ~/bullmose
cd ~/bullmose
```

## 4. Environment File

Create an `.env` file with your secrets:

```bash
nano .env
```

Paste your secrets:

```env
SHOPIFY_SHOP_URL=your-shop.myshopify.com
SHOPIFY_API_VERSION=2023-10
SHOPIFY_API_KEY=your_key
SHOPIFY_ACCESS_TOKEN=your_token
QUERY_INTERVAL=3
```

## 5. Persistence (Database)

Create an empty database file if you don't have one, or copy your existing one:

```bash
touch inventory.db
```

## 6. Run the Application

Run the following command to start the container. Replace `ghcr.io/your-username/bullmose:latest` with your actual image path.

```bash
docker run -d \
  --name bullmose \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/inventory.db:/app/inventory.db \
  -p 5000:5000 \
  ghcr.io/your-username/bullmose:latest
```

## 7. Automatic Updates with Watchtower

Run Watchtower to automatically check for new images and update your container.

```bash
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 300 \
  bullmose
```
*This checks every 5 minutes (300 seconds) and updates the `bullmose` container if a new image is found.*
