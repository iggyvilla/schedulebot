"""
Holds all the classes that holds data about a set schedule and a class
Also holds the NotifyEmbed, a class that creates a discord.Embed with all the formatting
"""
from datetime import datetime
from typing import Union
import json
import discord

EMBED_COLOR = 0x998449
HEDCEN_LOGO = 'http://hedcen.education/wp-content/uploads/2018/03/HEDCen-Tree-of-Life-Logo-white.png'
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def get_gmeet_link(schedule: str, class_name: str) -> Union[str, None]:
    with open('jsons/subject_links.json', 'r') as f:
        links = json.load(f)
    try:
        if class_name.endswith("i2"):
            return links[schedule][class_name[:-3]]
        else:
            return links[schedule][class_name]
    except KeyError:
        return None


class ClassInformation:
    """Parses the info list from the schedules.json file, just for readability"""
    def __init__(self, start_time: str, class_attrs: list, schedule_name: str):
        self.name = class_attrs[0]
        self.is_i2 = class_attrs[0].endswith("i2")
        self.end_time = class_attrs[1]
        self.start_time = start_time
        self.gmeet_link = get_gmeet_link(schedule_name, class_attrs[0])

    def __repr__(self):
        return f"<Subject \"{self.name}\" ({self.start_time} - {self.end_time})>"


class ScheduledEvent:
    def __init__(self, date_start: datetime, date_end: datetime, name: str, description: str):
        self.date_start = date_start
        self.date_end = date_end
        self.name = name
        self.description = description

    def serialize(self):
        return {"date_start": self.date_start,
                "date_end": self.date_end,
                "name": self.name,
                "description": self.description}


class ScheduledClass:
    """Finds the current and next class depending on the time you give"""
    def __init__(self, schedule: dict, current_time: datetime, schedule_name: str):
        day = current_time.strftime("%A")
        self.schedule = schedule[schedule_name]
        self.schedule_name = schedule_name
        self.now = current_time
        self.day = day
        # Pointer to schedule to check in the schedule.json
        self.ptr = self.schedule[day]

    def check_classes(self, parse_type=0) -> Union[ClassInformation, None]:
        """
        Parses through the times in the schedules.json and checks with current time
        parse_type:
            0 - current subject
            1 - next subject
            3 - first subject
        """
        # We can easily get the first subject without a loop
        if parse_type == 3:
            first_key = list(self.ptr.items())[0]
            return ClassInformation(first_key[0], first_key[1], self.schedule_name)

        for time in self.ptr:

            ptr_time = datetime.strptime(time, "%I:%M %p")
            class_time = self.now.replace(minute=ptr_time.minute, hour=ptr_time.hour)
            ptr_end_time = datetime.strptime(self.ptr[time][1], "%I:%M %p")
            class_end_time = self.now.replace(minute=ptr_end_time.minute, hour=ptr_end_time.hour)

            # If its the weekend
            if self.day == "Sat" or self.day == "Sun":
                return None

            # if parse_type == 1:
            #     # Next subject
            #     try:
            #         return ClassInformation(self.ptr[time][1], self.ptr[self.ptr[time][1]], self.schedule_name)
            #     except KeyError:
            #         return None

            if parse_type == 0:
                if class_time <= self.now < class_end_time:
                    # Current subject
                    return ClassInformation(time, self.ptr[time], self.schedule_name)
            if parse_type == 1:
                if class_time > self.now:
                    # Next subject
                    return ClassInformation(time, self.ptr[time], self.schedule_name)


def make_notify_embed(current_class: ScheduledClass, notify_role: str):
    """Creates a notify embed"""
    now = datetime.now()
    day_today = now.strftime("%A")
    subject_now = current_class.check_classes(parse_type=0)
    subject_next = current_class.check_classes(parse_type=1)

    embed = discord.Embed(color=EMBED_COLOR,
                          title=f"{subject_now.name} (`{subject_now.start_time} - {subject_now.end_time}`)",
                          description=f"🔔 {notify_role}")
    embed.set_author(name=day_today, icon_url=HEDCEN_LOGO)

    if subject_next:
        next_subject_strp = datetime.strptime(subject_next.start_time, "%I:%M %p")
        next_subject_repl = now.replace(hour=next_subject_strp.hour, minute=next_subject_strp.minute)
        next_subject_unix = int(next_subject_repl.timestamp())
        # Add it to the embed
        embed.add_field(
            name="Next subject:",
            value=f"{subject_next.name} ({subject_next.start_time}, <t:{next_subject_unix}:R>)"
        )
    else:
        embed.add_field(name="Next subject:", value=f"Dismissal! 🥳 ({subject_now.end_time})")

    return embed, subject_now.gmeet_link


def get_schedule() -> dict:
    with open('jsons/schedules.json', 'r') as f:
        return json.load(f)


def get_schedule_assignments() -> dict:
    with open('jsons/guild_assignments.json', 'r') as f:
        return json.load(f)


def write_schedule(new_sched: dict) -> None:
    with open('jsons/schedules.json', 'w') as f:
        json.dump(new_sched, f, indent=4)


def write_schedule_assignments(new_assign: dict) -> None:
    with open('jsons/guild_assignments.json', 'w') as f:
        json.dump(new_assign, f, indent=4)


def get_attendance() -> dict:
    with open('jsons/attendance.json', 'r') as f:
        return json.load(f)


def write_attendance(new_assign: dict) -> None:
    with open('jsons/attendance.json', 'w') as f:
        json.dump(new_assign, f, indent=4)


def make_schedule_embed(schedule_name: str, day: str) -> discord.Embed:
    schedule_dict = get_schedule()
    schedule = schedule_dict[schedule_name]
    desc = int(list(map(lambda x: x[1][0], schedule[day].items())).count("Independent Study")/len(schedule[day].keys()) * 100)
    emb = discord.Embed(title=f"Schedule for {day}", color=EMBED_COLOR, description=f'{desc}% Independent Study')
    emb.set_author(name=schedule_name, icon_url=HEDCEN_LOGO)
    # Add each subject to the embed

    for _class in schedule[day]:
        # Uncomment for Discord unix timestamps
        # Get unix of the start time
        # unix_start_time = datetime.strptime(_class, "%I:%M %p")
        # unix_start = datetime.now().replace(hour=unix_start_time.hour, minute=unix_start_time.minute)
        # Get unix of the end_time
        # unix_end_time = datetime.strptime(schedule[day][_class][1], "%I:%M %p")
        # unix_end = datetime.now().replace(hour=unix_end_time.hour, minute=unix_end_time.minute)
        emb.add_field(
            name=schedule[day][_class][0],
            value=f"{_class} - {schedule[day][_class][1]}",
            inline=False
        )
    emb.set_footer(text="Allow me to ping you by doing /notifyme")

    return emb


if __name__ == "__main__":
    # Just some testing
    with open('../jsons/schedules.json', 'r') as f:
        schedules = json.load(f)
    class_now = ScheduledClass(schedules, datetime.now(), "HEDCen G12 1st Trim").check_classes(parse_type=0)
    print(class_now)
    pass
