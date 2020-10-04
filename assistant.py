import discord
from discord.ext import commands
import asyncio
import play_scraper
from googlesearch import search
import aiohttp
import re
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TOKEN = os.getenv("DISCORD_TOKEN")


bot = commands.Bot(command_prefix="!",help_command=None)

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
        await ctx.send(f"Couldn't find the specs of the given device. {self.get_emoji('harold')}")
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
        else:
            await ctx.send(f"Couldn't find the specs of the given device. {self.get_emoji('harold')}")

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
    text = message.content
    disallowed_sites = ["twitter","ebay"]
    if "http" in text or "www" in text:
        url = re.search("(?P<url>https?://[^\s]+)", text).group("url")
        if "amp" in text and url.split("//")[1].split(".")[0] not in disallowed_sites:
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
    matches = re.findall(".*(autis|dipshit|dipshit|fag|nigger|overdose|stock).*", member.username.lower())
    if len(matches) > 0:
        print("hhhhhhhhhhhh")

@bot.event
async def on_ready():
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------')
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='!help for info', type=discord.ActivityType.playing))#Sets the bot's status and activity info

bot.run(TOKEN)


