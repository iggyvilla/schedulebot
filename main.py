import discord
from discord.ext import commands
from discord_slash import SlashCommand
from discord_components import DiscordComponents

bot = commands.Bot(command_prefix='hc ',
                   intents=discord.Intents.all(),
                   activity=discord.Activity(type=discord.ActivityType.watching, name="your schedule"))
slash = SlashCommand(bot, sync_commands=True)
# Paths to the different cogs
COGS = ("core.schedule_setup", "core.notifier", "core.attendance")


@bot.event
async def on_ready():
    DiscordComponents(bot)
    print("HEDCen bot online!")

# Loading the cogs
for cog in COGS:
    bot.load_extension(cog)

bot.run("put your token here")
