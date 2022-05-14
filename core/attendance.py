import asyncio

import discord
import discord_slash
from datetime import datetime
from utils import sched_utils
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow
from discord_slash.utils.manage_components import wait_for_component


class AttendanceHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g12_students = [
            "Put your classmates here"
        ]

    @cog_ext.cog_slash(
        name="attendance",
        description="Record the class attendance during the current subject"
    )
    async def capture_attendance(self, ctx: discord_slash.SlashContext):
        guild_schedule = sched_utils.get_schedule_assignments()[str(ctx.guild_id)]["schedule"]
        schedule = sched_utils.get_schedule()

        # TODO: Remove before launch!
        # testing_time = datetime.now().replace(day=2, hour=7, minute=30)

        subject_now_sc = sched_utils.ScheduledClass(schedule, datetime.now(), guild_schedule)
        subject_now = subject_now_sc.check_classes(parse_type=0)

        if subject_now:
            # Making the select options
            options = create_select(
                options=[create_select_option(label=name.split(',')[0], value=name) for name in self.g12_students],
                placeholder="Select students...",
                min_values=0,
                max_values=len(self.g12_students),
                custom_id="CAPTURE_ATTENDANCE"
            )
            actionrow = create_actionrow(options)
            # Creating the embed
            schedule_embed = discord.Embed(
                title=f"Attendance for {subject_now.name}",
                description="Please select students who are present:",
                color=sched_utils.EMBED_COLOR
            )
            schedule_embed.set_author(name="Attendance Recorder", icon_url=sched_utils.HEDCEN_LOGO)
            # Send the embed with components
            msg = await ctx.send(embed=schedule_embed, components=[actionrow])

            # Handling of selected students
            try:
                now = datetime.now().strftime("%d/%m/%y")
                selected_ctx = await wait_for_component(self.bot,
                                                        components=actionrow,
                                                        timeout=120)
                attendance = sched_utils.get_attendance()
                key = f"{subject_now.name} ({subject_now.start_time} - {subject_now.end_time})"

                try:
                    attendance[now][key] = selected_ctx.selected_options
                except KeyError:
                    attendance[now] = {key: selected_ctx.selected_options}

                sched_utils.write_attendance(attendance)

                await msg.delete()
                await ctx.channel.send(f"Successfully tracked attendance for `{key}`!")
            except asyncio.TimeoutError:
                await msg.edit(content="You took too long to select! Try again.", components=[])
                return
        else:
            # subject_now returned None
            await ctx.send("You can\'t track attendance now. It\'s either the weekend or school is done.")


def setup(bot):
    bot.add_cog(AttendanceHandler(bot))
