# https://ro.py.jmksite.dev/index.html
# https://discordpy.readthedocs.io/en/latest/api.html
# omg why did I put this all in one file

import discord
from discord.ext import commands
import time
from ro_py import Client
import requests
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
from datetime import timedelta
from datetime import date

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
spreadClient = gspread.authorize(creds)

employeeSheet = spreadClient.open("Robine Air Employee Database").worksheet("Employee Roster")

prefix = "."
intents = discord.Intents.all()
discordClient = commands.Bot(command_prefix=prefix, intents=intents)

roToken = "REDACTED"
roClient = Client(roToken)


async def infLoop():
    while True:
        values = employeeSheet.col_values(7)
        for i in range(len(values)):
            await asyncio.sleep(5)
            note = employeeSheet.get_note(f"G{i + 1}")
            if not note:
                continue
            if note.find("Suspended") != -1 and note[16].isnumeric():
                unsuspendDate = note[16:26]
                dateList = unsuspendDate.rsplit("/")
                newDate = f"{dateList[2]}-{dateList[0]}-{dateList[1]}"
                print(f"{newDate} | {str(date.today())}")
                if str(newDate) == str(date.today()):
                    employeeSheet.clear_note(f"G{i + 1}")
                    group = await roClient.get_group(5491535)
                    sheetRow = employeeSheet.row_values(i + 1)
                    rUser = sheetRow[3]
                    try:
                        member = await group.get_member_by_username(rUser)
                    except:
                        continue
                    formerPosition = sheetRow[5]
                    robloxRoles = await group.get_roles()
                    for gRole in robloxRoles:
                        if gRole.name == formerPosition:
                            print(gRole.rank)
                            await member.setrole(gRole.rank)
                    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
                    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
                    await airlineLogsChannel1.send(
                        f"**{formerPosition}** {sheetRow[4]} has been **unsuspended** automatically.")
                    await airlineLogsChannel2.send(
                        f"**{formerPosition}** {sheetRow[4]} has been **unsuspended** automatically.")
            elif note.find("Absence") != -1 and note[23].isnumeric():
                removeDate = note[23:33]
                dateList = removeDate.rsplit("/")
                newDate = f"{dateList[2]}-{dateList[0]}-{dateList[1]}"
                print(f"{newDate} | {str(date.today())}")
                if str(newDate) == str(date.today()):
                    employeeSheet.clear_note(f"G{i + 1}")
                    sheetRow = employeeSheet.row_values(i + 1)
                    rUser = sheetRow[3]
                    group = await roClient.get_group(5491535)
                    discMember = None
                    guild = discordClient.get_guild(665574330012401665)
                    for account in guild.members:
                        try:
                            roverUser = None
                            while True:
                                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                                roverParse = json.loads(roverR.text)
                                roverStatus = roverParse["status"]
                                if roverStatus == "error":
                                    roverErrorCode = roverParse["errorCode"]
                                    if roverErrorCode == "429":
                                        await asyncio.sleep(62)
                                        continue
                                    else:
                                        raise KeyError
                                elif roverStatus == "ok":
                                    roverUser = roverParse["robloxUsername"]
                                    break
                            newRoverUser = await group.get_member_by_username(roverUser)
                            if newRoverUser.name == rUser:
                                discMember = account
                                break
                        except:
                            continue
                    if not discMember:
                        continue
                    roles = discMember.roles
                    for role in roles:
                        if role.name == "Leave of Absence":
                            await discMember.remove_roles([role])
                    formerPosition = sheetRow[5]
                    dm = await discMember.create_dm()
                    await dm.send("**Your Robine Air Leave of Absence has expired. Please message somebody within your department’s command or in the Air Command if you need an extension or believe this is a mistake.**")
                    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
                    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
                    await airlineLogsChannel1.send(
                        f"**{formerPosition}** {sheetRow[4]} has been **removed** from **Leave of Absence**.")
                    await airlineLogsChannel2.send(
                        f"**{formerPosition}** {sheetRow[4]} has been **removed** from **Leave of Absence**.")

asyncio.ensure_future(infLoop())


@discordClient.event
async def on_ready():
    print("Bot is ready.")


@discordClient.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("There is still a delay in place. Please try again in a few minutes after the 6 hour delay.")


spamming = False


@discordClient.command()
async def spamping(ctx):
    roles = ctx.message.author.roles
    roleFound = None
    for role in roles:
        if role.name == "Board of Directors":
            roleFound = role
    if not roleFound:
        await ctx.send("This command can only be used by ``Board of Directors``.")
        return

    try:
        user = ctx.message.mentions[0]
        userid = user.id
    except:
        await ctx.send("Please mention a valid user!")
        return

    await ctx.send(f"``Initiating Spam Ping on {user.name}``")

    global spamming
    spamming = True

    while True:
        if not spamming:
            break
        time.sleep(0.5)
        await ctx.send(f"<@!{userid}>")


@discordClient.command()
async def stoppings(ctx):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Board of Directors":
            roleFound = True
    if not roleFound:
        await ctx.send("This command can only be used by ``Board of Directors``.")
        return

    await ctx.send("``Ending Spam Ping...``")
    global spamming
    spamming = False


panelCount = 0
panelMembers = []
panelPercent = 0
positiveVotes = []

voteActive = False


@discordClient.command()
async def motion(ctx):
    global voteActive

    if voteActive:
        await ctx.send("A vote is already in motion!")
        return

    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Review Panel Member":
            roleFound = True
    if not roleFound:
        await ctx.send("This command can only be used by Review Panel Members.")
        return

    channel = discordClient.get_channel(883576624673615922)
    if ctx.message.channel != channel:
        await ctx.send("This command can't be used in this channel.")
        return

    motionText = str(ctx.message.content).replace(".motion ", "", 1)

    global panelMembers
    panelMembers = []
    members = ctx.message.guild.members
    for member in members:
        roles = member.roles
        for role in roles:
            if role.name == "Review Panel Member":
                panelMembers.insert(len(panelMembers), member)

    global panelCount
    panelCount = len(panelMembers)
    if panelCount == 0:
        await ctx.send("There is nobody with the 'Review Panel Member' Role.")
        return

    global panelPercent
    panelPercent = 100 # 0
    global positiveVotes
    positiveVotes = []

    motionEmbed = discord.Embed(
        title=str(motionText),
        description="Please respond with ``.Agree``, ``.Disagree``, or ``.Abstain``",
        color=9961637
    )
    motionEmbed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)

    await ctx.send(embed=motionEmbed)
    voteActive = True


@discordClient.command()
async def Agree(ctx):
    channel = discordClient.get_channel(883576624673615922)
    resultsChannel = discordClient.get_channel(897932936681250866)
    if ctx.message.channel != channel:
        await ctx.send("This command can't be used in this channel.")
        return

    global voteActive

    if not voteActive:
        await ctx.send("Vote is no longer active.")
        return

    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Review Panel Member":
            roleFound = True
    if not roleFound:
        await ctx.send("This command can only be used by Review Panel Members.")
        return

    global panelMembers
    global panelPercent

    for i in range(len(panelMembers)):
        if ctx.message.author.id == panelMembers[i - 1].id:
            positiveVotes.insert(len(positiveVotes), panelMembers[i - 1])
            panelMembers.pop(i - 1)

    panelPercent = ((panelCount-len(panelMembers))/panelCount) * 100
    # panelPercent = ((panelCount - len(panelMembers)) * 100) / panelCount
    print(panelPercent)

    if panelPercent >= 50:
        print(f"final -- {len(positiveVotes) / (panelCount/2)}")
        if len(positiveVotes) / (panelCount/2) < 0.5:
            print(len(positiveVotes))
            print(panelCount)
            badEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided negatively",
                color=16711680
            )
            await ctx.send(embed=badEmbed)
            await resultsChannel.send(embed=badEmbed)
            voteActive = False
        elif len(positiveVotes) / (panelCount/2) == 0.5:
            okEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided equally.",
                color=16762368
            )
            await ctx.send(embed=okEmbed)
            await resultsChannel.send(embed=okEmbed)
            voteActive = False
        elif len(positiveVotes) / (panelCount/2) > 0.5:
            goodEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided positively.",
                color=50688
            )
            await ctx.send(embed=goodEmbed)
            await resultsChannel.send(embed=goodEmbed)
            voteActive = False
    elif panelPercent < 50:
        addedEmbed = discord.Embed(
            title="Your vote has been casted.",
            color=255
        )
        await ctx.send(embed=addedEmbed)


@discordClient.command()
async def Disagree(ctx):
    channel = discordClient.get_channel(883576624673615922)
    resultsChannel = discordClient.get_channel(897932936681250866)
    if ctx.message.channel != channel:
        await ctx.send("This command can't be used in this channel.")
        return

    global voteActive

    if not voteActive:
        await ctx.send("Vote is no longer active.")
        return

    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Review Panel Member":
            roleFound = True
    if not roleFound:
        await ctx.send("This command can only be used by Review Panel Members.")
        return

    global panelMembers
    global panelPercent

    for i in range(len(panelMembers)):
        if ctx.message.author.id == panelMembers[i - 1].id:
            panelMembers.pop(i - 1)

    panelPercent = ((panelCount-len(panelMembers))/panelCount) * 100
    # panelPercent = ((panelCount - len(panelMembers)) * 100) / panelCount
    print(panelPercent)

    if panelPercent > 50:
        print(f"final -- {len(positiveVotes) / panelCount}")
        if len(positiveVotes) / (panelCount/2) < 0.5:
            badEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided negatively",
                color=16711680
            )
            await ctx.send(embed=badEmbed)
            await resultsChannel.send(embed=badEmbed)
            voteActive = False
        elif len(positiveVotes) / (panelCount/2) == 0.5:
            okEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided equally.",
                color=16762368
            )
            await ctx.send(embed=okEmbed)
            await resultsChannel.send(embed=okEmbed)
            voteActive = False
        elif len(positiveVotes) / (panelCount/2) > 0.5:
            goodEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided positively.",
                color=50688
            )
            await ctx.send(embed=goodEmbed)
            await resultsChannel.send(embed=goodEmbed)
            voteActive = False
    elif panelPercent <= 50:
        addedEmbed = discord.Embed(
            title="Your vote has been casted.",
            color=255
        )
        await ctx.send(embed=addedEmbed)


@discordClient.command()
async def Abstain(ctx):
    motionChannel = discordClient.get_channel(883576624673615922)
    resultsChannel = discordClient.get_channel(897932936681250866)
    if ctx.message.channel != motionChannel:
        await ctx.send("This command can't be used in this channel.")
        return

    global voteActive

    if not voteActive:
        await ctx.send("Vote is no longer active.")
        return

    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Review Panel Member":
            roleFound = True
    if not roleFound:
        await ctx.send("This command can only be used by Review Panel Members.")
        return

    global panelMembers
    global panelPercent

    for i in range(len(panelMembers)):
        if ctx.message.author.id == panelMembers[i - 1].id:
            print(panelMembers[i - 1])
            panelMembers.pop(i - 1)

    panelPercent = ((panelCount-len(panelMembers))/panelCount) * 100
    # panelPercent = ((panelCount - len(panelMembers)) * 100) / panelCount
    print(panelPercent)

    if panelPercent > 50:
        print(f"final -- {len(positiveVotes) / (panelCount/2)}")
        if len(positiveVotes) / (panelCount/2) < 0.5:
            badEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided negatively",
                color=16711680
            )
            await ctx.send(embed=badEmbed)
            await resultsChannel.send(embed=badEmbed)
            voteActive = False
        elif len(positiveVotes) / (panelCount/2) == 0.5:
            okEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided equally.",
                color=16762368
            )
            await ctx.send(embed=okEmbed)
            await resultsChannel.send(embed=okEmbed)
            voteActive = False
        elif len(positiveVotes) / (panelCount/2) > 0.5:
            goodEmbed = discord.Embed(
                title="Results are FINAL",
                description="The Review Panel Members have decided positively.",
                color=50688
            )
            await ctx.send(embed=goodEmbed)
            await resultsChannel.send(embed=goodEmbed)
            voteActive = False
    elif panelPercent <= 50:
        addedEmbed = discord.Embed(
            title="Your vote has been abstained.",
            color=255
        )
        await ctx.send(embed=addedEmbed)


@discordClient.command()
async def motionkill(ctx):
    global voteActive
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Board of Directors":
            roleFound = True
    if not roleFound:
        await ctx.send("This command can only be used by ``Board of Directors``.")
        return

    await ctx.send("``Killing motion...``")
    voteActive = False
    time.sleep(1)

    killEmbed = discord.Embed(
        title=":white_check_mark: Successfully killed Motion.",
        color=16711680
    )
    await ctx.send(embed=killEmbed)


@discordClient.command()
@commands.cooldown(1, 21600, commands.BucketType.user)
async def lazyvoters(ctx):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Review Panel Member":
            roleFound = True
    if not roleFound:
        await ctx.send("This command can only be used by Review Panel Members.")
        return

    pingMessage = ""
    global panelMembers
    for member in panelMembers:
        pingMessage = f"{pingMessage} {member.mention}"

    await ctx.send(pingMessage)


@discordClient.command()
async def verify(ctx):
    try:
        roverUser = None
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{ctx.message.author.id}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        findEmbed = discord.Embed(
            title=f"{ctx.message.author.mention}, :exclamation::wave: You must be new!",
            description="Please go to https://rover.link/verify and follow the instructions on the page in order to get verified.",
            color=16717824
        )
        await ctx.send(embed=findEmbed)
        return

    try:
        await ctx.message.author.edit(nick=roverUser)
    except:
        await ctx.send("Bot failed to change nickname.")
        return

    await ctx.send(f"{ctx.message.author.mention}, :white_check_mark: Welcome to Robine Air, {roverUser}!")


@discordClient.command()
async def update(ctx):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    try:
        userid = ctx.message.mentions[0].id
    except:
        await ctx.send("Please mention a valid user!")
        return

    try:
        roverUser = None
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{str(userid)}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        findEmbed = discord.Embed(
            title=f"{ctx.message.author.mention}, :exclamation::wave: You must be new!",
            description="Please go to https://rover.link/verify and follow the instructions on the page in order to get verified.",
            color=16717824
        )
        await ctx.send(embed=findEmbed)
        return

    guild = ctx.message.guild
    member = guild.get_member(userid)

    try:
        await member.edit(nick=roverUser)
    except:
        await ctx.send("Bot failed to change nickname.")
        return

    group = await roClient.get_group(5491535)
    try:
        groupMember = await group.get_member_by_username(roverUser)
    except:
        await ctx.send(
            "We could not find you in the group! Please consider joining:\nhttps://www.roblox.com/groups/5491535")
        return

    robloxRoles = await group.get_roles()
    userRoles = ctx.message.author.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await ctx.message.author.remove_roles(userRole)

    roles = ctx.message.guild.roles
    role = None
    for ding in roles:
        if ding.name == groupMember.role.name:
            role = ding
            break

    try:
        await ctx.message.author.add_roles(role)
    except:
        await ctx.send("Bot does not have permission to edit the user's roles!")
        return

    await ctx.send(
        f"{ctx.message.author.mention}, :white_check_mark: {roverUser} has been verified and given the ``{role.name}`` role.")


@discordClient.command()
async def getroles(ctx):
    try:
        roverUser = None
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{ctx.message.author.id}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        findEmbed = discord.Embed(
            title=f"{ctx.message.author.mention}, :exclamation::wave: You must be new!",
            description="Please go to https://rover.link/verify and follow the instructions on the page in order to get verified.",
            color=16717824
        )
        await ctx.send(embed=findEmbed)
        return

    group = await roClient.get_group(5491535)
    try:
        member = await group.get_member_by_username(roverUser)
        rank = member.role.rank
    except:
        await ctx.send(
            "We could not find you in the group! Please consider joining:\nhttps://www.roblox.com/groups/5491535")
        return

    robloxRoles = await group.get_roles()
    userRoles = ctx.message.author.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await ctx.message.author.remove_roles(userRole)

    guildRoles = ctx.message.guild.roles
    role = None
    for ding in guildRoles:
        if ding.name == member.role.name:
            role = ding
            break

    try:
        await ctx.message.author.add_roles(role)
    except:
        await ctx.send("Failed to add role.")
        return

    await ctx.send(f"{ctx.message.author.mention}, :white_check_mark: Successfully added the ``{role.name}`` role.")


@discordClient.command()
async def hire(ctx, rUser, roleType):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command" or role.name == "Department Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command`` or ``Department Command``.")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    try:
        roverUser = None
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{ctx.message.author.id}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        findEmbed = discord.Embed(
            title=f"{ctx.message.author.mention}, :exclamation::wave: You must be new!",
            description="Please go to https://rover.link/verify and follow the instructions on the page in order to get verified.",
            color=16717824
        )
        await ctx.send(embed=findEmbed)
        return

    group = await roClient.get_group(5491535)
    try:
        roverMember = await group.get_member_by_username(roverUser)
    except:
        await ctx.send(
            "We could not find you in the group! Please consider joining:\nhttps://www.roblox.com/groups/5491535")
        return

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRank = member.role.name

    try:
        await member.setrole(47)
    except:
        await ctx.send("Failed to update ROBLOX Rank.")

    discMember = None
    newRoverUser = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    insRoleType = None
    if roleType == "Pilots":
        insRoleType = "Pilot Trainee"
    elif roleType == "Security":
        insRoleType = "Security Cadet"
    elif roleType == "CC":
        insRoleType = "Trainee CC"
    elif roleType == "GC":
        insRoleType = "Trainee GC"
    else:
        await ctx.send("Please insert a valid role type:```- Pilots\n- Security\n- CC\n- GC```")
        return

    freeRow = None
    if roleType == "Pilots":
        column = employeeSheet.col_values(4)
        for i in range(len(column)):
            if column[i] == "Pilots":
                freeRow = i + 2
    elif roleType == "Security":
        column = employeeSheet.col_values(4)
        for i in range(len(column)):
            if column[i] == "Security":
                freeRow = i + 2
    elif roleType == "CC":
        column = employeeSheet.col_values(4)
        for i in range(len(column)):
            if column[i] == "Cabin Crew":
                freeRow = i + 2
    elif roleType == "GC":
        column = employeeSheet.col_values(4)
        for i in range(len(column)):
            if column[i] == "Ground Crew":
                freeRow = i + 2

    rowToInsert = [None, None, None, rUser, str(discMember), "Trainee Employee", insRoleType, "NONE", None, None, None,
                   None]

    employeeSheet.add_rows(1)
    employeeSheet.insert_row(rowToInsert, freeRow)

    robloxRoles = await group.get_roles()
    userRoles = discMember.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await discMember.remove_roles(userRole)

    roles = ctx.message.guild.roles
    traineeRole = None
    roleInTraining = None
    for ding in roles:
        if ding.name == member.role.name:
            traineeRole = ding
        elif ding.name == f"{roleType} - In Training":
            roleInTraining = ding

    robineAirRole = ctx.message.guild.get_role(713732253519446076)
    try:
        await discMember.add_roles(traineeRole)
        await discMember.add_roles(roleInTraining)
        await discMember.add_roles(robineAirRole)
    except:
        await ctx.send("Failed to add role.")
        return

    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRank}** {discMember.mention} has been **enrolled** in the **{insRoleType}** entrance program.")
    await airlineLogsChannel2.send(
        f"**{oldRank}** {discMember.mention} has been **enrolled** in the **{insRoleType}** entrance program.")

    dm = await discMember.create_dm()

    dmEmbed = discord.Embed(
        title="**| Congratulations! You have passed Robine Air Department Applications! |**",
        description=f"The next step is to officially be trained for your department, then you're an official Employee!\nYou can find more info on your department's training here:\nhttps://discord.gg/ssmsc8KeDP\nGood luck!\n\n*Sincerely,\n{roverUser}, {roverMember.role.name}*",
        color=8532639
    )
    dmEmbed.set_thumbnail(url="https://t4.rbxcdn.com/ebaea549537861bb3ed2e5b4ebe4c4ff")

    await dm.send(embed=dmEmbed)
    await ctx.send("Hired.")


@discordClient.command()
async def dhfire(ctx, rUser):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    try:
        roverUser = None
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{ctx.message.author.id}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        findEmbed = discord.Embed(
            title=f"{ctx.message.author.mention}, :exclamation::wave: You must be new!",
            description="Please go to https://rover.link/verify and follow the instructions on the page in order to get verified.",
            color=16717824
        )
        await ctx.send(embed=findEmbed)
        return

    group = await roClient.get_group(5491535)
    try:
        roverMember = await group.get_member_by_username(roverUser)
    except:
        await ctx.send(
            "We could not find you in the group! Please consider joining:\nhttps://www.roblox.com/groups/5491535")
        return

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRank = member.role.name

    try:
        await member.setrole(10)
    except:
        await ctx.send("Failed to update ROBLOX Rank.")
        return

    discMember = None
    newRoverUser = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    robloxRoles = await group.get_roles()
    userRoles = discMember.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await discMember.remove_roles(userRole)

    roles = ctx.message.guild.roles
    economyClassRole = None
    for ding in roles:
        if ding.name == member.role.name:
            economyClassRole = ding

    try:
        await discMember.add_roles(economyClassRole)
    except:
        await ctx.send("Failed to add role.")
        return

    usersInSheet = employeeSheet.col_values(4)
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            employeeSheet.delete_row(i + 1)

    RASC = discordClient.get_guild(883160715794448454)
    kicked = False
    for account in RASC.members:
        if account.id == discMember.id:
            kicked = True
            await account.kick()
            break

    if not kicked:
        await ctx.send("Could not kick member from RASC.")


    reason = ctx.message.content[(7 + len(rUser)):]
    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRank}** {discMember.mention} has been **dishonorably discharged** due to: {reason}")
    await airlineLogsChannel2.send(
        f"**{oldRank}** {discMember.mention} has been **dishonorably discharged** due to: {reason}")

    await ctx.send("Fired.")


@discordClient.command()
async def hfire(ctx, rUser):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    try:
        roverUser = None
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{ctx.message.author.id}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        findEmbed = discord.Embed(
            title=f"{ctx.message.author.mention}, :exclamation::wave: You must be new!",
            description="Please go to https://rover.link/verify and follow the instructions on the page in order to get verified.",
            color=16717824
        )
        await ctx.send(embed=findEmbed)
        return

    group = await roClient.get_group(5491535)
    try:
        roverMember = await group.get_member_by_username(roverUser)
    except:
        await ctx.send(
            "We could not find you in the group! Please consider joining:\nhttps://www.roblox.com/groups/5491535")
        return

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRank = member.role.name

    try:
        await member.setrole(10)
    except:
        await ctx.send("Failed to update ROBLOX Rank.")
        return

    discMember = None
    newRoverUser = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    robloxRoles = await group.get_roles()
    userRoles = discMember.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await discMember.remove_roles(userRole)

    roles = ctx.message.guild.roles
    economyClassRole = None
    for ding in roles:
        if ding.name == member.role.name:
            economyClassRole = ding

    try:
        await discMember.add_roles(economyClassRole)
    except:
        await ctx.send("Failed to add role.")
        return

    usersInSheet = employeeSheet.col_values(4)
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            employeeSheet.delete_row(i + 1)

    RASC = discordClient.get_guild(883160715794448454)
    kicked = False
    for account in RASC.members:
        if account.id == discMember.id:
            kicked = True
            await account.kick()
            break

    if not kicked:
        await ctx.send("Could not kick member from RASC.")

    reason = ctx.message.content[(7 + len(rUser)):]
    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRank}** {discMember.mention} has been **honorably discharged** due to: {reason}")
    await airlineLogsChannel2.send(
        f"**{oldRank}** {discMember.mention} has been **honorably discharged** due to: {reason}")

    await ctx.send("Fired.")


@discordClient.command()
async def genfire(ctx, rUser):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    try:
        roverUser = None
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{ctx.message.author.id}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        findEmbed = discord.Embed(
            title=f"{ctx.message.author.mention}, :exclamation::wave: You must be new!",
            description="Please go to https://rover.link/verify and follow the instructions on the page in order to get verified.",
            color=16717824
        )
        await ctx.send(embed=findEmbed)
        return

    group = await roClient.get_group(5491535)
    try:
        roverMember = await group.get_member_by_username(roverUser)
    except:
        await ctx.send(
            "We could not find you in the group! Please consider joining:\nhttps://www.roblox.com/groups/5491535")
        return

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRank = member.role.name

    try:
        await member.setrole(10)
    except:
        await ctx.send("Failed to update ROBLOX Rank.")
        return

    discMember = None
    newRoverUser = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    robloxRoles = await group.get_roles()
    userRoles = discMember.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await discMember.remove_roles(userRole)

    roles = ctx.message.guild.roles
    economyClassRole = None
    for ding in roles:
        if ding.name == member.role.name:
            economyClassRole = ding

    try:
        await discMember.add_roles(economyClassRole)
    except:
        await ctx.send("Failed to add role.")
        return

    usersInSheet = employeeSheet.col_values(4)
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            employeeSheet.delete_row(i + 1)

    RASC = discordClient.get_guild(883160715794448454)
    kicked = False
    for account in RASC.members:
        if account.id == discMember.id:
            kicked = True
            await account.kick()
            break

    if not kicked:
        await ctx.send("Could not kick member from RASC.")

    reason = ctx.message.content[(11 + len(rUser)):]
    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRank}** {discMember.mention} has been **generally discharged** due to: {reason}")
    await airlineLogsChannel2.send(
        f"**{oldRank}** {discMember.mention} has been **generally discharged** due to: {reason}")

    await ctx.send("Fired.")


@discordClient.command()
async def ticket(ctx):
    ticketsCategoryChannel = 935741705670512640
    user = ctx.message.author
    category = discordClient.get_channel(ticketsCategoryChannel)
    guild = ctx.message.guild

    ticketChannel = await guild.create_text_channel(
        name=f"ticket-{user.name}-{user.id}",
        category=category
    )
    await ticketChannel.set_permissions(user, read_messages=True, send_messages=True, view_channel=True)

    ticketEmbed = discord.Embed(
        title=":tickets: Welcome to your ticket!",
        description="Support Team will be with you shortly.",
        color=6559841
    )

    await ticketChannel.send(f"<@!{user.id}>", embed=ticketEmbed)


@discordClient.command()
async def promote(ctx, *args):
    if len(args) < 3 or not args[1].isnumeric():
        await ctx.send("Please use the following format:\n``.promote (Roblox Username) (New Rank ID) (Reason)``")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    rUser = args[0]
    rankID = args[1]

    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    group = await roClient.get_group(5491535)

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRank = member.role.name

    try:
        await member.setrole(int(rankID))
    except:
        await ctx.send("Failed to update ROBLOX Rank.")

    await asyncio.sleep(3)
    member = await group.get_member_by_username(rUser)

    robloxRoles = await group.get_roles()
    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    roRole = None
    userRoles = discMember.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                roRole = robloxRole
                await discMember.remove_roles(userRole)

    roles = ctx.message.guild.roles
    economyClassRole = None
    for ding in roles:
        if ding.name == member.role.name:
            economyClassRole = ding

    try:
        await discMember.add_roles(economyClassRole)
    except:
        await ctx.send("Failed to add role to discord account.")
        return

    usersInSheet = employeeSheet.col_values(4)
    sheetRow = None
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            sheetRow = i + 1
            break

    if sheetRow:
        print("a")
        employeeSheet.update_cell(sheetRow, 6, economyClassRole.name)
        print("b")
    else:
        print("c")
        pilotRow = None
        for i in range(len(usersInSheet)):
            if usersInSheet[i] == "Pilots":
                pilotRow = i + 1
        rowToInsert = [None, None, None, rUser, str(discMember), roRole.name, "Pilot Trainee", "NONE", None, None,
                       None, None]
        employeeSheet.insert_row(rowToInsert, pilotRow + 1)
    print("what")
    reason = ctx.message.content[(11 + len(rUser) + len(rankID)):]
    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRank}** {discMember.mention} has been **promoted** to **{economyClassRole.name}** due to {reason}")
    await airlineLogsChannel2.send(
        f"**{oldRank}** {discMember.mention} has been **promoted** to **{economyClassRole.name}** due to {reason}")

    await ctx.send("Successfully Promoted User.")


@discordClient.command()
async def demote(ctx, *args):
    if len(args) < 2 or not args[1].isnumeric():
        await ctx.send("Please use the following format:\n``.demote (Roblox Username) (New Rank ID) (Reason)``")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    rUser = args[0]
    rankID = args[1]

    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    group = await roClient.get_group(5491535)

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRank = member.role.name

    try:
        await member.setrole(int(rankID))
    except:
        await ctx.send("Failed to update ROBLOX Rank.")

    await asyncio.sleep(3)
    print(member.role.name)
    await asyncio.sleep(3)
    member = await group.get_member_by_username(rUser)
    print(member.role.name)

    robloxRoles = await group.get_roles()
    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    roRole = None
    userRoles = discMember.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await discMember.remove_roles(userRole)
                roRole = robloxRole

    roles = ctx.message.guild.roles
    economyClassRole = None
    for ding in roles:
        if ding.name == member.role.name:
            economyClassRole = ding

    try:
        await discMember.add_roles(economyClassRole)
    except:
        await ctx.send("Failed to add role to discord account.")
        return

    usersInSheet = employeeSheet.col_values(4)
    sheetRow = None
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            sheetRow = i + 1
            break

    if sheetRow:
        print("a")
        employeeSheet.update_cell(sheetRow, 6, economyClassRole.name)
        print("b")
    else:
        print("c")
        pilotRow = None
        for i in range(len(usersInSheet)):
            if usersInSheet[i] == "Pilots":
                pilotRow = i + 1
        rowToInsert = [None, None, None, rUser, str(discMember), roRole.name, "Pilot Trainee", "NONE", None, None,
                       None, None]
        employeeSheet.insert_row(rowToInsert, pilotRow + 1)
    print("what")
    reason = ctx.message.content[(11 + len(rUser) + len(rankID)):]
    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRank}** {discMember.mention} has been **demoted** to **{economyClassRole.name}** due to {reason}")
    await airlineLogsChannel2.send(
        f"**{oldRank}** {discMember.mention} has been **demoted** to **{economyClassRole.name}** due to {reason}")

    await ctx.send("Successfully Demoted User.")


@discordClient.command()
async def suspend(ctx, *args):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command" or role.name == "Human Resources Officer":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command`` or ``Human Resources Officer``.")
        return

    if len(args) < 2:
        await ctx.send(
            "Please use the following format:\n``(Roblox username) (Unsuspension date // MM/DD/YYY) (Reason)``")
        return

    rUser = args[0]
    unsuspendDate = args[1]
    reasonStart = len(rUser) + len(unsuspendDate) + 11
    reason = ctx.message.content[reasonStart:]

    newDate = unsuspendDate.rsplit("/")
    if len(newDate) < 3 or len(newDate[0]) != 2 or len(newDate[1]) != 2 or len(newDate[2]) != 4:
        await ctx.send(
            "Please follow the following format for Unsuspension Date: MM/DD/YYYY\nExample: 04/15/2021 (April 15th, 2021)")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    usersInSheet = employeeSheet.col_values(4)
    userFound = False
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            note = f"Suspended until {unsuspendDate} by {ctx.message.author.name}"
            employeeSheet.clear_note(f"G{i + 1}")
            employeeSheet.insert_note(f"G{i + 1}", note)
            userFound = True
    if not userFound:
        await ctx.send("User is not in sheet.")
        return

    group = await roClient.get_group(5491535)

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRole = member.role

    try:
        await member.setrole(40)  # 40
    except:
        await ctx.send("Failed to update ROBLOX Rank.")

    member = await group.get_member_by_username(rUser)

    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    robloxRoles = await group.get_roles()
    userRoles = discMember.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await discMember.remove_roles(userRole)

    roles = ctx.message.guild.roles
    economyClassRole = None
    suspendRole = None
    for ding in roles:
        if ding.name == member.role.name:
            economyClassRole = ding
        elif ding.name == "Suspended":
            suspendRole = ding

    try:
        await discMember.add_roles(economyClassRole)
        await discMember.add_roles(suspendRole)
    except:
        await ctx.send("Failed to add role to discord account.")

    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRole.name}** {discMember.mention} has been **suspended** until {unsuspendDate} due to {reason}")
    await airlineLogsChannel2.send(
        f"**{oldRole.name}** {discMember.mention} has been **suspended** until {unsuspendDate} due to {reason}")

    await ctx.send("Successfully Suspended User.")


@discordClient.command()
async def unsuspend(ctx, *args):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Board of Directors":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Board of Directors``.")
        return

    if len(args) < 2:
        await ctx.send("Please use the following format: ``.unsuspend (Roblox username) (Reason)``")
        return

    rUser = args[0]
    group = await roClient.get_group(5491535)

    await ctx.send("Working (Could take 5-10 minutes)...")

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    roles = ctx.message.guild.roles
    economyClassRole = None
    suspendRole = None
    for ding in roles:
        if ding.name == member.role.name:
            economyClassRole = ding
        elif ding.name == "Suspended":
            suspendRole = ding

    try:
        await discMember.add_roles(economyClassRole)
        await discMember.remove_roles(suspendRole)
    except:
        await ctx.send("Failed to add role to discord account.")
        return

    employees = employeeSheet.col_values(4)
    employeeFound = False
    formerPosition = None
    for i in range(len(employees)):
        if employees[i] == rUser:
            formerPosition = employeeSheet.cell(i + 1, 7).value
            employeeSheet.clear_note(f"G{i + 1}")
            employeeFound = True

    if not employeeFound:
        await ctx.send("User is not in the database.")
        return

    robloxRoles = await group.get_roles()
    userRoles = discMember.roles
    formerRole = None
    for robloxRole in robloxRoles:
        if robloxRole.name == formerPosition:
            formerRole = robloxRole
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await discMember.remove_roles(userRole)

    try:
        await member.setrole(formerRole.rank)
    except:
        await ctx.send("Failed to update ROBLOX Rank.")

    reason = ctx.message.content[(10 + len(rUser)):]
    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{formerPosition}** {discMember.mention} has been **unsuspended** due to {reason}")
    await airlineLogsChannel2.send(
        f"**{formerPosition}** {discMember.mention} has been **unsuspended** due to {reason}")

    await ctx.send("Successfully Suspended User.")


@discordClient.command()
async def al(ctx, *args):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command" or role.name == "Human Resources Officer":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command`` or ``Human Resources Officer``.")
        return

    if len(args) < 2:
        await ctx.send("Please use the correct format: ``.al (Roblox username) (Reason)``")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    rUser = args[0]
    reason = ctx.message.content[(5 + len(rUser)):]
    group = await roClient.get_group(5491535)

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRole = member.role.name

    try:
        await member.setrole(40)  # 40
    except:
        await ctx.send("Failed to update ROBLOX Rank.")

    member = await group.get_member_by_username(rUser)

    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    usersInSheet = employeeSheet.col_values(4)
    userFound = False
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            note = f"Administrative Leave: {oldRole}"
            employeeSheet.clear_note(f"G{i + 1}")
            employeeSheet.insert_note(f"G{i + 1}", note)
            userFound = True
    if not userFound:
        await ctx.send("User is not in sheet.")
        return

    roles = ctx.message.guild.roles
    aLeaveRole = None
    for ding in roles:
        if ding.name == "Administrative Leave":
            aLeaveRole = ding

    try:
        await discMember.add_roles(aLeaveRole)
    except:
        await ctx.send("Failed to add role to discord account.")
        return

    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRole}** {discMember.mention} has been **placed** on **Administrative Leave** due to {reason}")
    await airlineLogsChannel2.send(
        f"**{oldRole}** {discMember.mention} has been **placed** on **Administrative Leave** due to {reason}")

    await ctx.send("Placed user on *Administrative Leave*.")


@discordClient.command()
async def remAL(ctx, *args):
    if len(args) < 1:
        await ctx.send("Please use the correct format: ``.remAL (Roblox username)``")
        return

    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command" or role.name == "Human Resources Officer":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command`` or ``Human Resources Officer``.")
        return

    rUser = args[0]
    group = await roClient.get_group(5491535)

    await ctx.send("Working (Could take 5-10 minutes)...")

    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    usersInSheet = employeeSheet.col_values(4)
    newRole = None
    for i in range(len(usersInSheet)):
        if usersInSheet[i] == rUser:
            note = employeeSheet.get_note(f"G{i + 1}")
            if note.find("Administrative Leave") == -1:
                continue
            newRole = note[22:]
            employeeSheet.clear_note(f"G{i + 1}")
            break
    if not newRole:
        await ctx.send("User is either not on Administrative Leave or not in the sheet.")
        return

    try:
        member = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find the inserted user in group.")
        return

    oldRole = member.role.name

    robloxRoles = await group.get_roles()
    roleRank = None
    for role in robloxRoles:
        if role.name == newRole:
            roleRank = role.rank

    try:
        await member.setrole(roleRank)
    except:
        await ctx.send("Failed to update ROBLOX Rank.")

    member = await group.get_member_by_username(rUser)

    discRoles = discMember.roles
    for role in discRoles:
        if role.name == "Administrative Leave":
            discMember.remove_role(role)
            break

    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{oldRole}** {discMember.mention} has been **removed** from **Administrative Leave**")
    await airlineLogsChannel2.send(
        f"**{oldRole}** {discMember.mention} has been **removed** from **Administrative Leave**")


@discordClient.command()
async def strike(ctx, *args):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command" or role.name == "Human Resources Officer":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command`` or ``Human Resources Officer``.")
        return

    if len(args) < 2:
        await ctx.send("Please use the following format: ``.strike (Roblox Username) (Reason)``")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    rUser = args[0]
    reason = ctx.message.content[(9 + len(rUser)):]

    group = await roClient.get_group(5491535)

    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    employees = employeeSheet.col_values(4)
    row = None
    for i in range(len(employees)):
        if employees[i] == rUser:
            row = i + 1
            break
    if not row:
        await ctx.send("User is not in sheet!")
        return

    if employeeSheet.cell(row, 8).value == "NONE":
        employeeSheet.update_cell(row, 8, "1")
    elif employeeSheet.cell(row, 8).value == "1":
        employeeSheet.update_cell(row, 8, "2")
        delta = timedelta(days=3)
        date1 = date.today() + delta
        dateList = str(date1).split("-")
        date2 = f"{dateList[1]}/{dateList[2]}/{dateList[0]}"
        await suspend(ctx, rUser, date2)
    elif employeeSheet.cell(row, 8).value == "2":
        employeeSheet.update_cell(row, 8, "3")
        delta = timedelta(days=7)
        date1 = date.today() + delta
        dateList = str(date1).split("-")
        date2 = f"{dateList[1]}/{dateList[2]}/{dateList[0]}"
        await suspend(ctx, rUser, date2)
    elif employeeSheet.cell(row, 8).value == "3":
        employeeSheet.update_cell(row, 8, "4")
        await demote(ctx, rUser, "10")
    elif employeeSheet.cell(row, 8).value == "4":
        await dhfire(ctx, rUser)

    dm = await discMember.create_dm()
    await dm.send(
        f"**You have received a strike within Robine Air due to {reason}. Please contact somebody within the Human Resources or in the Air Command if you believe this is a mistake.**")

    await ctx.send("Successfully Striked user.")


@discordClient.command()
async def loa(ctx, *args):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    if len(args) < 3:
        await ctx.send(
            "Please use the following format:\n ``.loa (Roblox username) (Removal date // MM/DD/YYYY) (Reason)``")
        return

    unsuspendDate = args[1]
    newDate = unsuspendDate.rsplit("/")
    if len(newDate) < 3 or len(newDate[0]) != 2 or len(newDate[1]) != 2 or len(newDate[2]) != 4:
        await ctx.send("Please follow the following format for Unsuspension Date: MM/DD/YYYY\nExample: 04/15/2021 (April 15th, 2021)")
        return

    await ctx.send("Working (Could take 5-10 minutes)...")

    rUser = args[0]
    reason = ctx.message.content[(7 + len(rUser) + len(unsuspendDate)):]
    print(reason)

    group = await roClient.get_group(5491535)
    try:
        robloxUser = await group.get_member_by_username(rUser)
    except:
        await ctx.send("Could not find roblox user.")
        return

    rank = robloxUser.role.name

    rUsers = employeeSheet.col_values(4)
    userRow = None
    for i in range(len(rUsers)):
        if rUsers[i] == rUser:
            userRow = i + 1
            break
    if not userRow:
        await ctx.send(f"Could not find user ``{rUser}`` in database.")
        return

    discMember = None
    newRoverUser = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                if account.id == ctx.message.author.id:
                    await ctx.send("You cannot use this command on yourself.")
                    return
                else:
                    discMember = account
                    break
        except:
            continue

    if not discMember:
        await ctx.send(f"Roblox user is not in the discord!")
        return

    guild = ctx.message.guild
    guildRoles = guild.roles
    for role in guildRoles:
        if role.name == "Leave of Absence":
            try:
                await discMember.add_roles([role])
            except:
                await ctx.send("Failed to add Leave of Absence role")

    note = f"Leave of Absence until {unsuspendDate}"
    employeeSheet.clear_note(f"G{userRow}")
    employeeSheet.insert_note(f"G{userRow}", note)

    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{rank}** {discMember.mention} has been **placed** on **Leave of Absence** until {unsuspendDate} due to {reason}")
    await airlineLogsChannel2.send(
        f"**{rank}** {discMember.mention} has been **placed** on **Leave of Absence** until {unsuspendDate} due to {reason}")


@discordClient.command()
async def remLOA(ctx, rUser):
    roles = ctx.message.author.roles
    roleFound = False
    for role in roles:
        if role.name == "Air Command":
            roleFound = True
            break
    if not roleFound:
        await ctx.send("This command can only be used by ``Air Command``.")
        return

    row = None
    people = employeeSheet.col_values(4)
    for i in range(len(people)):
        if people[i] == rUser:
            employeeSheet.clear_note(f"G{i+1}")
            row = i+1
            break
    if not row:
        await ctx.send("User not found in database")
        return

    sheetRow = employeeSheet.row_values[row]

    group = await roClient.get_group(5491535)

    discMember = None
    for account in ctx.message.guild.members:
        try:
            roverUser = None
            while True:
                roverR = requests.get(f"https://verify.eryn.io/api/user/{str(account.id)}")
                roverParse = json.loads(roverR.text)
                roverStatus = roverParse["status"]
                if roverStatus == "error":
                    roverErrorCode = roverParse["errorCode"]
                    if roverErrorCode == "429":
                        await asyncio.sleep(62)
                        continue
                    else:
                        raise KeyError
                elif roverStatus == "ok":
                    roverUser = roverParse["robloxUsername"]
                    break
            newRoverUser = await group.get_member_by_username(roverUser)
            if newRoverUser.name == rUser:
                discMember = account
                break
        except:
            continue
    if not discMember:
        return

    roles = discMember.roles
    for role in roles:
        if role.name == "Leave of Absence":
            await discMember.remove_roles([role])
    formerPosition = sheetRow[5]
    dm = await discMember.create_dm()
    await dm.send(
        "**Your Robine Air Leave of Absence has expired. Please message somebody within your department’s command or in the Air Command if you need an extension or believe this is a mistake.**")
    airlineLogsChannel1 = discordClient.get_channel(719170431227265034)
    airlineLogsChannel2 = discordClient.get_channel(883558456353763358)
    await airlineLogsChannel1.send(
        f"**{formerPosition}** {sheetRow[4]} has been **removed** from **Leave of Absence**.")
    await airlineLogsChannel2.send(
        f"**{formerPosition}** {sheetRow[4]} has been **removed** from **Leave of Absence**.")


@discordClient.event
async def on_member_join(member):
    if member.guild.id != 883160715794448454:
        return

    userid = member.id

    roverUser = None
    try:
        while True:
            roverR = requests.get(f"https://verify.eryn.io/api/user/{str(userid)}")
            roverParse = json.loads(roverR.text)
            roverStatus = roverParse["status"]
            if roverStatus == "error":
                roverErrorCode = roverParse["errorCode"]
                if roverErrorCode == "429":
                    await asyncio.sleep(62)
                    continue
                else:
                    raise KeyError
            elif roverStatus == "ok":
                roverUser = roverParse["robloxUsername"]
                break
    except:
        print("nothing")

    guild = discordClient.get_guild(211228845771063296)
    member = guild.get_member(userid)

    try:
        await member.edit(nick=roverUser)
    except:
        print("nothing")

    group = await roClient.get_group(5491535)
    try:
        groupMember = await group.get_member_by_username(roverUser)
    except:
        return

    robloxRoles = await group.get_roles()
    userRoles = member.roles
    for robloxRole in robloxRoles:
        for userRole in userRoles:
            if robloxRole.name == userRole.name:
                await member.remove_roles(userRole)

    roles = guild.roles
    role = None
    for ding in roles:
        if ding.name == groupMember.role.name:
            role = ding
            break

    try:
        await member.add_roles(role)
    except:
        return


discordClient.run("REDACTED")
