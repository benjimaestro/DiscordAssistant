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
import datetime
import time
import pickle
import os.path
import hashlib

load_dotenv(find_dotenv())

registry = []

class ballot(dict):
    def __init__(self,name):
    	self.name = name
    	if os.path.exists(f"{self.name}.pkl"):
    		loaded_ballot_box = pickle.load(open(f"{self.name}.pkl", "rb" ))
    		for key in loaded_ballot_box:
    			self[key] = loaded_ballot_box[key]
    	else:
    		self.name = name
    		self["1"] = {"voter_id":"1","voter_name":"1","nominee_id":"1","nominee_tag":"1","timestamp":str(time.time())}
    		pickle.dump(self, open(f"{self.name}.pkl", "wb" ))
    
    def vote(self,voter_id,voter_tag,nominee_id,nominee_tag):
        prev_hash = list(self.items())[-1][0]
        prev_results = list(self.items())[-1][1]
        new_hash = hashlib.sha256(str.encode(prev_hash)).hexdigest()
        self[new_hash] = {"voter_id":voter_id,
        				  "voter_name":voter_tag,
        				  "nominee_id":nominee_id,
        				  "nominee_tag":nominee_tag,
        				  "timestamp":str(time.time())}
        print(new_hash, self[new_hash])
    
    def backup(self):
    	print(self)
    	if os.path.exists(f"{self.name}.pkl"):
    		os.rename(f"{self.name}.pkl", f"{self.name} {datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')}.pkl")
    		pickle.dump(self, open(f"{self.name}.pkl", "wb" ))
    	else:
            pickle.dump(self, open(f"{self.name}.pkl", "wb" ))

vote_helpful = ballot("helpful")
vote_funny = ballot("funny")
vote_improved = ballot("improved")
vote_best = ballot("best")

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",help_command=None,intents=intents)

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
async def vote(ctx):
    registry.append(ctx.message.author.id)
    user = bot.get_user(ctx.message.author.id)
    await ctx.send("<@!"+str(ctx.message.author.id)+"> you have been DM'd voting instructions. Make sure you are able to receive DMs from server members.")
    if ctx.message.author.joined_at.timestamp() < 1606780800:
    	await user.send("""Thank you for participating in the Droider Of The Year awards.
The following categories to vote for are:
Funniest droider
Most helpful droider
Most improved droider
Droider of the year

Nominees are submitted by ID - you must have discord developer mode enabled to copy IDs.
A discord ID is a string of numbers, look up how to get user IDs on the internet.

To vote for the funniest droider, run the command in this DM:
`!funniest 349220599152771072`

To vote for the most helpful droider, run the command in this DM:
`!helpful 349220599152771072`

To vote for the most improved droider, run the command in this DM:
`!improved 349220599152771072`

To vote for the droider of the year, run the command in this DM:
`!doty 349220599152771072`

Replace `349220599152771072` with your the ID of your nominee of choice.
""")
    else:
    	await user.send("Sorry but your account did not join early enough to participate.")

@commands.dm_only()
@bot.command(pass_context=True)
async def doty(ctx, arg):
	user = bot.get_user(int(arg))
	await ctx.send(f"You are nominating {user} for the Droider of the Year category. Enter Y to confirm, or anything else to cancel.")
	msg = await bot.wait_for('message')
	if msg.content.lower() == 'y' and msg.author.id in registry and user != None:
		vote = True
		for key in vote_best:
			if vote_best[key]["voter_id"] == msg.author.id:
				await ctx.send("Vote not recorded. You have already voted in this catergory!")
				vote = False
				break
		if vote:
			vote_best.vote(msg.author.id,msg.author.name+"#"+msg.author.discriminator,int(arg),user.name+"#"+user.discriminator)
			await ctx.send(f"You have voted for {user} for the Droider of the Year category. Make sure you vote in the other categories too!")
	else:
		await ctx.send("Vote was not recorded. Either it was cancelled, you weren't registered to vote or the ID was invalid. Register by running `!vote` in #botspam.")

@bot.command(pass_context=True)
async def debug(ctx):
	for key in vote_best:
	    print(vote_best[key]["voter_id"])

@bot.command(pass_context=True)
async def backupvotes(ctx):
	vote_helpful.backup()
	vote_funny.backup()
	vote_improved.backup()
	vote_best.backup()
	await ctx.send("Ballot boxes backed up!")

@bot.command(pass_context=True)
async def specs(ctx,*,device):
    """
    Function called when the !specs command is run.
    This will try and find the specs of the requested device and post the findings as an embed to the chat wherever the command was called from
    """
    await ctx.send("Due to issues with the website providing data for this bot, this command has been disabled until it works again.")
    #await ctx.trigger_typing()
    #url = get_specs_url(device)
    #if not url:
    #    await ctx.send("Couldn't find the specs of the given device.")
    #    return
    #async with aiohttp.ClientSession() as session:
    #    stuff = await get_specs(session, url)
    #    if stuff:
    #        model, specs, unconfirmed = stuff
    #        embed = discord.Embed(
    #            color=discord.Colour.orange(), description="\n".join(x.strip() for x in specs.replace("<b>", "**").replace("</b>", "**").split("<br />")))
    #        if unconfirmed:
    #            embed.set_author(name=f"{model} (UNCONFIRMED)")
    #        else:
    #            embed.set_author(name=model)
    #        embed.set_footer(text="Source: "+url)
    #        embed.set_thumbnail(url="https://www.devicespecifications.com/images/model/"+url.split("/")[-1:][0]+"/320/main.jpg")
    #        await ctx.send(embed=embed)
    #        if ctx.message.channel.name != "botspam":
    #            await ctx.send("Please use bot commands in the appropriate \#botspam channel unless relevant to the current discussion, abuse of the bot will result in a mute.")
    #    else:
    #        await ctx.send("Couldn't find the specs of the given device.")

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
    # Anti panda emote garbage
    if message.author.id == 136636611415900161:
    	if any(str(emoji) in message.content for emoji in message.guild.emojis):
    		await message.delete()

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
    matches = re.findall(".*(autis|dipshit|dipshit|fag|nigger|overdose|stock).*", member.name.lower())
    if len(matches) > 0 and member.guild.id == 114407194971209731:
        embed = discord.Embed(title="Ban", color=0xDD5F53)
        embed.add_field(name="Offender:", value=str(member), inline=False)
        embed.add_field(name="Reason:", value="Bad username", inline=False)
        embed.add_field(name="Responsible moderator:", value=bot.user.name, inline=False)
        await member.guild.get_channel(349220599152771072).send(embed=embed)
        await member.ban(reason="Bad username",delete_message_days=7)

@bot.event
async def on_ready():
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------')
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='!help for info', type=discord.ActivityType.playing))#Sets the bot's status and activity info

bot.run(TOKEN)


