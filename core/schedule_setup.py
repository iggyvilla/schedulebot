import asyncio
from datetime import datetime

import discord
import discord_slash
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow
from discord_slash.utils.manage_components import wait_for_component

from utils.sched_utils import get_schedule, get_schedule_assignments, write_schedule_assignments
from utils.sched_utils import EMBED_COLOR, HEDCEN_LOGO


class GuildScheduleSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        print(f"Joined server {guild.name} at {datetime.now()}!")
        assignments = get_schedule_assignments()

        assignments[str(guild.id)] = {
            "schedule": None,
            "notified_channel": None,
            "notify_role": None
        }

        write_schedule_assignments(assignments)

    @commands.Cog.listener()
    async def on_guild_leave(self, guild: discord.Guild):
        print(f"Left server {guild.name} at {datetime.now()} :(")
        assignments = get_schedule_assignments()
        try:
            del assignments[str(guild.id)]
        except KeyError:
            return
        write_schedule_assignments(assignments)

    @cog_ext.cog_slash(name="ping",
                       description="Test command to see if the bot is still alive.")
    async def _ping(self, ctx: discord_slash.SlashContext):
        await ctx.send(f"Pong {ctx.author}!")

    @cog_ext.cog_slash(name="setup",
                       description="Run this command to setup the notification channel.")
    async def _setup(self, ctx: discord_slash.SlashContext):
        """Command to setup the Notifier channel and Notifier"""

        def check_if_role_tag(message):
            # Used later to check if msg is a role
            return (message.author == ctx.author) and (len(message.content) == 22) and message.content.startswith("<@&")

        assignments = get_schedule_assignments()

        try:
            guild_assignments = assignments[str(ctx.guild_id)]
            # Check if the server already has been setup
            await ctx.send("You already set up in this server!")
            return
        except KeyError:
            assignments[str(ctx.guild_id)] = {"notified_channel": ctx.channel_id}
            guild_assignments = assignments[str(ctx.guild_id)]
            # PHASE 1 and 2 Create the "pick a schedule" part of the setup
            schedules = get_schedule()
            options = create_select(
                options=[create_select_option(name, value=name) for name in schedules],
                placeholder="Choose an option",
                min_values=1,
                max_values=1,
                custom_id="SETUP_SELECT_SCHEDULE"
            )
            action_row = create_actionrow(options)
            embed = discord.Embed(color=EMBED_COLOR,
                                  description="""✅ Successfully set this channel as your notify channel
                                              \n Please select a schedule below:""")
            embed.set_author(icon_url=HEDCEN_LOGO, name="Notifier Setup")
            msg = await ctx.send(embed=embed, components=[action_row])

            try:
                selected_ctx: discord_slash.ComponentContext = await wait_for_component(self.bot,
                                                                                        components=action_row,
                                                                                        timeout=60)
                # Grab the schedule in the returned list of selected options
                selected_schedule = selected_ctx.selected_options[0]
                # Set it as the selected schedule
                guild_assignments["schedule"] = selected_schedule
                write_schedule_assignments(assignments)
            except asyncio.TimeoutError:
                await ctx.send("You took too long! Run /setup again.")
                return

            # PHASE 3 Setting the notifier role
            embed = discord.Embed(color=EMBED_COLOR,
                                  description=f"Successfully set the schedule `{selected_schedule}` "
                                              f"for {ctx.guild.name}!\n"
                                              f"Last one! Please ping the role that you want me to notify.")
            embed.set_author(icon_url=HEDCEN_LOGO, name="Notifier Setup")
            await msg.edit(embed=embed, components=[])

            try:
                notify_ctx = await self.bot.wait_for('message',
                                                     check=check_if_role_tag,
                                                     timeout=60)
                guild_assignments["notify_role"] = notify_ctx.content
                embed = discord.Embed(color=EMBED_COLOR,
                                      description=f"✅ Notifications are all set up! Enjoy.")
                embed.set_author(icon_url=HEDCEN_LOGO, name="Notifier Setup")
                # Write to guild_assignments
                write_schedule_assignments(assignments)
                await ctx.send(embed=embed)
            except asyncio.TimeoutError:
                await ctx.send("You took too long! Run /setup again.")
                return


def setup(bot):
    bot.add_cog(GuildScheduleSetup(bot))
