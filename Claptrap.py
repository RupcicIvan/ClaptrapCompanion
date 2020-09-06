#Claptrap.py
import os
import logging
import random

from discord.ext import commands
import discord
import asyncio
from dotenv import load_dotenv


################################################################
###						Logging								####
################################################################
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

################################################################
###						Environment							####
################################################################
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

################################################################
###							Class							####
################################################################
class States(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		bot.dir = "Resource"

		#dictionaries where key=guild.id and values are:

		#number of users connected to voice chat (for that guild)
		bot.number_of_users_in_voice_channels = {}
		#True if bot is connected already to voice channel (for that guild), false otherwise
		bot.connected = {}
		#discord.VoiceClient (for that guild)
		bot.voice_state = {}
		#True if bot is preparing to move to (other) channel, false otherwise
		bot.moving = {}

################################################################
###							Events							####
################################################################
bot = commands.Bot(command_prefix="!")
#adding class 
bot.add_cog(States(bot))
#disable any kind of text communication
bot.remove_command("help")

@bot.event
async def on_disconnect():
	#whenever bot lose communication with guild, he reset his states, stop playing and disconnect from guild
	for guild in bot.guilds:
		bot.number_of_users_in_voice_channels[guild.id] = 0
		bot.connected[guild.id] = False
		bot.moving[guild.id] = False
		bot.voice_state[guild.id].stop()
		await bot.voice_state[guild.id].disconnect()

@bot.event
async def on_ready():
	for guild in bot.guilds:
		#initialize states and counter for users in voice chats
		bot.number_of_users_in_voice_channels[guild.id] = 0
		bot.connected[guild.id] = False
		bot.voice_state[guild.id] = None
		bot.moving[guild.id] = False
		for member in guild.members:
			if member.voice != None and not member.bot:
				bot.number_of_users_in_voice_channels[guild.id] += 1

		#connect to random member of guild if there is at least 1 user in voice chat
		if bot.number_of_users_in_voice_channels[guild.id] > 0:
			#if random function find bot, we have to randomize again
			while bot.voice_state[guild.id] == None:
				member = random.choice(guild.members)
				if not member.bot:
					bot.connected[guild.id] = True
					bot.moving[guild.id] = True
					bot.voice_state[guild.id] = await member.voice.channel.connect()
					bot.moving[guild.id] = False
						
@bot.event
async def on_voice_state_update(member, before, after):
	#when user (not bot) connect to voice chat
	#and only if bot wasn't disconnected to any voice channel, connect him to same channel as this user
	if after.channel != None and before.channel == None and not member.bot:
		bot.number_of_users_in_voice_channels[member.guild.id] += 1
		if bot.connected[member.guild.id] == False:
			bot.connected[member.guild.id] = True
			bot.moving[member.guild.id] = True
			bot.voice_state[member.guild.id] = await after.channel.connect()
			bot.moving[member.guild.id] = False

	#when user (not bot) moves to other voice chat
	#and only if there is no other user in current bot's channel, connect bot to same channel user has moved to
	elif after.channel != None and before.channel != None and not member.bot:
		users_in_channel = 0
		for user in before.channel.members:
			if not user.bot:
				users_in_channel += 1
		if users_in_channel == 0:
			bot.moving[member.guild.id] == True
			if bot.voice_state[member.guild.id].is_playing():
				bot.voice_state[member.guild.id].stop()
			await bot.voice_state[member.guild.id].move_to(after.channel)
			bot.moving[member.guild.id] == False

	#when user (not bot) disconnect from voice chat
	#either find other member and connect to his voice channel
	#or disconenct from voice channels if there is no other user connected to voice channel
	elif after.channel == None and before.channel != None and not member.bot:
		bot.number_of_users_in_voice_channels[member.guild.id] -= 1
		if bot.number_of_users_in_voice_channels[member.guild.id] > 0:
			bot.moving[member.guild.id] == True
			if bot.voice_state[member.guild.id].is_playing():
				bot.voice_state[member.guild.id].stop()
			users_in_channel = 0
			for user in before.channel.members:
				if not user.bot:
					users_in_channel += 1
			if users_in_channel == 0:
				#connect to random member of guild if there is at least 1 user in voice chat
				#if random function find bot, we have to randomize again
				while bot.moving[member.guild.id] == True:
					user = random.choice(member.guild.members)
					if not user.bot:
						bot.connected[user.guild.id] = True
						bot.voice_state[user.guild.id] = await bot.voice_state[user.guild.id].move_to(user.voice.channel)
						bot.moving[member.guild.id] == False
		else:
			bot.connected[member.guild.id] = False
			bot.voice_state[member.guild.id].stop()
			await bot.voice_state[member.guild.id].disconnect()

	#when this bot connects to channel, check if all states are ready (has bot moved) before loop
	elif member == bot.user:
		while bot.moving[member.guild.id] == True:
			await asyncio.sleep(0.1)
		#every 60 seconds play random audio. Stop it once bot disconnect or moves to other channel
		#there are issues when switching channels - previous loops are not lost
		while bot.connected[member.guild.id] == True and bot.moving[member.guild.id] == False and bot.voice_state[member.guild.id] != None:
			source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(bot.dir + '/' + random.choice(os.listdir(bot.dir))))
			bot.voice_state[member.guild.id].play(source)
			while bot.voice_state[member.guild.id].is_playing():
				await asyncio.sleep(60)

	#all other cases (other bot connecting/moving/disconnecting)
	else:
		pass

################################################################
###							Run								####
################################################################
bot.run(TOKEN)
