from __future__ import annotations

import os

import discord
import httpx
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")
API_URL = os.getenv("LICENSE_API_URL", "http://127.0.0.1:8000")
API_SECRET = os.getenv("LICENSE_API_SECRET", "")

intents = discord.Intents.none()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def api(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["X-API-Secret"] = API_SECRET
    async with httpx.AsyncClient(timeout=10) as http:
        response = await http.request(method, API_URL.rstrip("/") + path, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()


@tree.command(name="genkey", description="Generate a one-time license key")
@app_commands.describe(key_type="1d = 24 hours, lifetime = never expires")
@app_commands.choices(key_type=[
    app_commands.Choice(name="1 day", value="1d"),
    app_commands.Choice(name="Lifetime", value="lifetime"),
])
async def genkey(interaction: discord.Interaction, key_type: app_commands.Choice[str]):
    try:
        data = await api("POST", "/admin/create", json={"key_type": key_type.value, "created_by": str(interaction.user.id)})
        await interaction.response.send_message(
            f"🔐 **New {key_type.value} key**\n`{data['key']}`\n\nKeep this key private — it is returned only once.",
            ephemeral=True,
        )
    except Exception:
        await interaction.response.send_message("❌ Could not generate key.", ephemeral=True)


@tree.command(name="revoke", description="Revoke a license key")
async def revoke(interaction: discord.Interaction, key: str):
    try:
        await api("POST", "/admin/revoke", json={"key": key})
        await interaction.response.send_message("✅ Key revoked.", ephemeral=True)
    except Exception:
        await interaction.response.send_message("❌ Key not found or already revoked.", ephemeral=True)


@tree.command(name="keys", description="Show license metadata (never the plaintext keys)")
async def keys(interaction: discord.Interaction):
    try:
        data = await api("GET", "/admin/list")
        lines = []
        for item in data["licenses"][:20]:
            status = "revoked" if item["revoked_at"] else ("active" if item["activated_at"] else "unused")
            lines.append(f"• `{item['key_type']}` — **{status}** — device bound: {'yes' if item['device_id'] else 'no'}")
        text = "\n".join(lines) or "No keys yet."
        await interaction.response.send_message(text, ephemeral=True)
    except Exception:
        await interaction.response.send_message("❌ Could not load keys.", ephemeral=True)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


if not TOKEN:
    raise SystemExit("DISCORD_TOKEN is missing")

client.run(TOKEN)
