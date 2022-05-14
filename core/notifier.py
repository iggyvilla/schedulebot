"""
NOTIFIER COG
Reads each guilds assigned notify channel  and schedule every second in the jsons/notifier.json
and sends a notification that there is a class
"""
import discord
import discord_slash
import json

from utils import sched_utils
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_components import Button, ButtonStyle


def get_schedule() -> dict:
    with open('jsons/schedules.json', 'r') as f:
        return json.load(f)


def get_schedule_assignments() -> dict:
    with open('jsons/guild_assignments.json', 'r') as f:
        return json.load(f)


def make_dismissal_embed(first_subj_tomorrow: str, notification_role: str) -> discord.Embed:
    embed = discord.Embed(color=sched_utils.EMBED_COLOR,
                          title="Dismissal!  🥳",
                          description=f"🔔 {notification_role}")
    embed.set_author(icon_url=sched_utils.HEDCEN_LOGO, name=datetime.now().strftime("%A"))
    embed.set_footer(text=f"First subject tomorrow: {first_subj_tomorrow}")
    return embed


class DiscordScheduleNotifier(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current = {}
        self.schedule_sent = {}
        self.complete = False

    @tasks.loop(seconds=1)
    async def notification_handler(self):
        # Check first if its the weekend
        day_now = datetime.now().strftime("%a")
        if day_now == "Sun" or day_now == "Sat":
            return

        assignments = get_schedule_assignments()

        # See if the guild has an assigned schedule
        for guild in self.bot.guilds:
            print(f"[{datetime.now()}] {guild}:")
            if str(guild.id) in assignments:
                print(f"└ {guild.id} found in assignments ")

                guild_assignments = assignments[str(guild.id)]
                guild_assigned_schedule = guild_assignments["schedule"]
                sched_dict = get_schedule()

                print(f"└ Detected datetime: {datetime.now()}")
                schedule = sched_utils.ScheduledClass(sched_dict, datetime.now(), guild_assigned_schedule)
                current_subj = schedule.check_classes(parse_type=0)
                next_subj = schedule.check_classes(parse_type=1)

                # Check if the day is done (if next_subj or current_sbj is None)
                if (not next_subj) and (not current_subj):
                    # Announce the good news if it hasn't been announced!
                    if self.current[guild.id] != "End of day":
                        print("└ Dismissal!")
                        self.current[guild.id] = "End of day"
                        channel = self.bot.get_channel(guild_assignments["notified_channel"])

                        # Get the datetime object for tomorrow 7:30 AM
                        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=7, minute=30)
                        # Get it's name as well to check if its a weekday or not
                        tom_day_name = tomorrow.strftime("%a")

                        if tom_day_name == "Sun" or tom_day_name == "Sat":
                            embed = make_dismissal_embed("It\'s the weekend!", guild_assignments['notify_role'])
                            await channel.send(embed=embed)
                            return

                        # Getting tomorrows first subject
                        tom_sc = sched_utils.ScheduledClass(sched_dict, tomorrow, guild_assigned_schedule)
                        first_class = tom_sc.check_classes(parse_type=3)

                        embed = make_dismissal_embed(
                            f"{first_class.name} ({first_class.start_time} - {first_class.end_time})",
                            guild_assignments['notify_role']
                        )

                        await channel.send(embed=embed)

                # If there is a new current subject, announce
                elif current_subj:
                    print(f"└ Current subject: {current_subj.name}")
                    if current_subj.name != self.current[guild.id]:
                        # Log to console the new subject
                        print(f"└ [{datetime.now().strftime('%A %I:%M %p')}] "
                              f"New subject for {guild.name} ({guild_assigned_schedule}): {current_subj.name}")

                        self.current[guild.id] = current_subj.name
                        embed, link = sched_utils.make_notify_embed(current_class=schedule,
                                                                    notify_role=guild_assignments["notify_role"])
                        channel = self.bot.get_channel(guild_assignments["notified_channel"])

                        # If there's a link, show a button
                        if link:
                            print("I SEE A LINK!", link)
                            label = "Google Meet" if "google" in link else "Zoom"
                            print("ITS FROM", label)
                            components = Button(style=ButtonStyle.URL, url=link, label=label)
                            await channel.send(embed=embed, components=[components])
                        else:
                            await channel.send(embed=embed)

    @tasks.loop(minutes=1)
    async def send_schedule_at_six(self):
        time_now = datetime.now().strftime("%I:%M %p")
        day_today = datetime.now().strftime("%A")

        print(f"[SchedSender] {time_now=}")

        if time_now == "06:00 AM":
            print("It\'s 6 AM, sending schedule...")
            for guild in self.bot.guilds:
                try:
                    guild_assignments = get_schedule_assignments()[str(guild.id)]
                    emb = sched_utils.make_schedule_embed(guild_assignments["schedule"], day_today)
                except KeyError:
                    print(f"{guild.id} not assigned, skipping...")
                    continue

                channel = self.bot.get_channel(guild_assignments["notified_channel"])
                await channel.send(embed=emb)
                print(f"Successfully sent schedule to {guild.id}!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.current[guild.id] = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded DiscordScheduleNotifier")
        self.notification_handler.start()
        self.send_schedule_at_six.start()

        # Initialize the Notify dict
        for guild in self.bot.guilds:
            self.current[guild.id] = None

    @commands.command()
    async def test_notification(self, ctx):
        assignments = get_schedule()
        time = datetime.strptime("08 9 2021 8:00 AM", "%m %d %Y %H:%M %p")
        fake_class = sched_utils.ScheduledClass(assignments, time, "HEDCen G12 1st Trim")
        embed, link = sched_utils.make_notify_embed(fake_class, "<@&874998758880985118>")

        # If there's a link then add a button to the class
        if link:
            components = Button(style=ButtonStyle.URL, url=link, label="Google Meet")
            await ctx.send(embed=embed, components=[[components]])
        else:
            await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="schedule",
                       description="See the schedule today or on a specific day",
                       options=[
                           create_option(
                               name="day",
                               description="A day of the week",
                               option_type=3,
                               required=False,
                               choices=[
                                   create_choice(
                                       name=day,
                                       value=day
                                   ) for day in sched_utils.WEEKDAYS
                               ]
                           )
                       ])
    async def see_schedule(self, ctx: discord_slash.SlashContext, day: str = None):
        # Check if its the weekend
        day_today = datetime.now().strftime("%a")

        if not day:
            if day_today == "Sun" or day_today == "Sat":
                await ctx.send("It\'s the weekend, stupid.")
                return
            day = datetime.now().strftime("%A")

        assignments = get_schedule_assignments()
        if str(ctx.guild_id) not in assignments:
            await ctx.send("You haven't setup the server yet!")
            return

        guild_assignments = assignments[str(ctx.guild_id)]
        embed = sched_utils.make_schedule_embed(guild_assignments["schedule"], day)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="notifyme",
                       description="Gives you the notify role so the bot can ping you every new subject")
    async def notify_me(self, ctx: discord_slash.SlashContext):
        assignments = get_schedule_assignments()

        # If the server isn't setup
        if str(ctx.guild.id) not in assignments:
            await ctx.send("You need to setup your server for notifications first by doing /setup!")
            return

        notify_role = ctx.guild.get_role(int(assignments[str(ctx.guild.id)]["notify_role"][3:-1]))
        await ctx.author.add_roles(notify_role)
        await ctx.send("Added you to the notifier list!")


def setup(bot):
    bot.add_cog(DiscordScheduleNotifier(bot))
