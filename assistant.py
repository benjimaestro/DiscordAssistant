import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import play_scraper
from googlesearch import search
import aiohttp
import re
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv
import datetime
import time
import pickle
import os.path
import hashlib

load_dotenv(find_dotenv())
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=["!"],help_command=None,intents=intents)

def get_specs_url(device):
    """
    Function to get the devicespecifications URL for the requested model using Google
    """
    try:
        for res in search(f"{device} specifications site:devicespecifications.com", num=3, stop=1, pause=3.5):
            if "/model/" in res:
                return res.split('?')[0]
    except:
        pass
    return None

async def get_url_text(session, url):
    """
    Function to get the text of the requested page
    """
    async with session.get(url) as r:
        if r.status == 200:
            return await r.text()
    return None

async def get_specs(session, url):
    """
    Function to get the specs from the found page's HTML
    """
    text = await get_url_text(session, url)
    if text:
        lines = text.splitlines()
        model = None
        unconfirmed = False
        for i in range(len(lines)):
            if "<title>" in lines[i]:
                model = lines[i][7:].rsplit("-", 1)[0].strip()
            elif '<div class="unconfirmed-specifications">' in lines[i]:
                unconfirmed = True
            elif '<div id="model-brief-specifications">' in lines[i]:
                return (model, lines[i + 1].strip(), unconfirmed)
    return None

@bot.command(pass_context=True)
async def specs(ctx,*,device):
    """
    Function called when the !specs command is run.
    This will try and find the specs of the requested device and post the findings as an embed to the chat wherever the command was called from
    """
    await ctx.trigger_typing()
    url = get_specs_url(device)
    if not url:
        await ctx.send("Couldn't find the specs of the given device.")
        return
    async with aiohttp.ClientSession() as session:
        stuff = await get_specs(session, url)
        if stuff:
            model, specs, unconfirmed = stuff
            embed = discord.Embed(
                color=discord.Colour.orange(), description="\n".join(x.strip() for x in specs.replace("<b>", "**").replace("</b>", "**").split("<br />")))
            if unconfirmed:
                embed.set_author(name=f"{model} (UNCONFIRMED)")
            else:
                embed.set_author(name=model)
            embed.set_footer(text="Source: "+url)
            embed.set_thumbnail(url="https://www.devicespecifications.com/images/model/"+url.split("/")[-1:][0]+"/320/main.jpg")
            await ctx.send(embed=embed)
            if ctx.message.channel.name != "botspam":
                await ctx.send("Please use bot commands in the appropriate \#botspam channel unless relevant to the current discussion, abuse of the bot will result in a mute.")
        else:
            await ctx.send("Couldn't find the specs of the given device.")

@bot.event
async def on_member_update(before, after):
    """
    Function called when a member is updated.
    This is used to automatically remove the regular role from muted users.
    """
    #Checks if role was added
    if len(before.roles) < len(after.roles):
    	#Gets the new role
        newRole = next(role for role in after.roles if role not in before.roles)
        if newRole.name == "Muted":
        	role = get(after.guild.roles, name='Regular')
        	await after.remove_roles(role)

@bot.command(pass_context=True)
async def linkme(ctx,*,appSearch):
    """
    Function called when the !linkme command is run.
    This will try and find the play store listing of the requrested app and display the relevant information using play_scraper
    """
    appDict = play_scraper.search(appSearch, page=0)[0]
    appEmbed = discord.Embed(title=appDict["title"], description=appDict["description"], color=0x00ff00)
    appEmbed.set_thumbnail(url=appDict["icon"])
    appEmbed.add_field(name="URL", value="https://play.google.com"+appDict["url"], inline=False)
    appEmbed.add_field(name="Developer", value=appDict["developer"], inline=False)
    if appDict["free"] == True:
        appEmbed.add_field(name="Price", value="Free", inline=False)
    else:
        appEmbed.add_field(name="Price", value=str(appDict["price"]), inline=False)
    appEmbed.set_footer(text="Bot by Zoemaestra#0119")
    await ctx.send(embed=appEmbed)

@bot.command(pass_context=True)
async def help(ctx):
    """
    Function called when the !help command is run.
    This will post information about the bot as a discord embed
    """
    embed = discord.Embed(title=bot.user.name+" Help", description="This bot is written and maintained by Zoemaestra#0119", color=0x00ff00)
    embed.add_field(name="!specs Device Name", value="Fetches the specs for the given device", inline=False)
    embed.add_field(name="!linkme App Title", value="Fetches app info for the given app", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    """
    Function called whenever a message is posted in the server.
    This will try and see if a message is a link, and then check if it's an AMP link, then try to de-AMPify the link, then post the de-AMPified link to the chat.
    """
    try:
	    if time.time() - 86400 < int(message.author.joined_at.strftime('%s')):
	    	matches = re.findall(".*(dipshit|pome|overdose).*", message.content.lower())
	    	if len(matches) > 0 and message.author.guild.id == 114407194971209731:
	    		embed = discord.Embed(title="Ban", color=0xDD5F53)
	    		embed.add_field(name="Offender:", value=str(message.author), inline=False)
	    		embed.add_field(name="Reason:", value="Angry pome guy", inline=False)
	    		embed.add_field(name="Responsible moderator:", value=bot.user.name, inline=False)
	    		await message.author.guild.get_channel(349220599152771072).send(embed=embed)
	    		await message.author.ban(reason="Angry pome guy",delete_message_days=7)
    except AttributeError: #Not happy when bots post messages
    	pass

    text = message.content
    disallowed_sites = ["twitter","ebay"]
    if "http" in text or "www" in text:
        url = re.search("(?P<url>https?://[^\s]+)", text).group("url")
        if "amp" in text and url.split("//")[1].split(".")[0] not in disallowed_sites and message.author.id != 597372169269542913:
            try:
                html_text = requests.get(url).text
                soup = BeautifulSoup(html_text, 'html.parser')
                for link in soup.find_all('link'):
                    if link.get('rel')[0] == "canonical":
                        if link.get('href') != url:
                            deamped = "Non-AMP link: <" + link.get('href') + ">"
                            await message.channel.send(deamped)
                        break
            except:
                pass
    await bot.process_commands(message)#This is necessary to keep the commands working, else the bot will ignore them

@bot.event
async def on_member_join(member):
    matches = re.findall(".*(autis|dipshit|dipshit|fag|nigger|overdose|UTTP|THDTC).*", member.name.lower())
    if len(matches) > 0 and member.guild.id == 114407194971209731:
        embed = discord.Embed(title="Ban", color=0xDD5F53)
        embed.add_field(name="Offender:", value=str(member), inline=False)
        embed.add_field(name="Reason:", value="Bad username", inline=False)
        embed.add_field(name="Responsible moderator:", value=bot.user.name, inline=False)
        await member.guild.get_channel(349220599152771072).send(embed=embed)
        await member.ban(reason="Known troll alt",delete_message_days=7)

@bot.command(pass_context=True)
@commands.has_any_role("Giant Nerd","Mod","Admin")
async def tsban(ctx, member: discord.Member):
    role = get(member.guild.roles, name='ts-muted')
    await member.add_roles(role)
    await ctx.send(f"{member.name}#{member.discriminator} has been banned from support channels")
    embed = discord.Embed(title="Support Channel Ban", color=0xF48942)
    embed.add_field(name="Offender:", value=f"{member.name}#{member.discriminator}", inline=False)
    embed.add_field(name="Reason:", value="Support channel ban", inline=False)
    embed.add_field(name="Responsible moderator:", value=f"{ctx.message.author.name}#{ctx.message.author.discriminator}", inline=False)
    await member.guild.get_channel(349220599152771072).send(embed=embed)

@bot.command(pass_context=True)
@commands.has_any_role("Giant Nerd","Mod","Admin")
async def tsunban(ctx, member: discord.Member):
    role = get(member.guild.roles, name='ts-muted')
    await member.remove_roles(role)
    await ctx.send(f"{member.name}#{member.discriminator} has now been unbanned from support channels")
    embed = discord.Embed(title="Support Channel Unban", color=0x42F4A7)
    embed.add_field(name="User:", value=f"{member.name}#{member.discriminator}", inline=False)
    embed.add_field(name="Responsible moderator:", value=f"{ctx.message.author.name}#{ctx.message.author.discriminator}", inline=False)
    await member.guild.get_channel(349220599152771072).send(embed=embed)

@bot.event
async def on_ready():
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------')
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='!help for info', type=discord.ActivityType.playing))#Sets the bot's status and activity info

bot.run(TOKEN)


