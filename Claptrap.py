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
class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		bot.dir = "Resource"
		bot.number_of_users_in_voice_channels = {}
		bot.connected = {}
		bot.voice_state = {}

################################################################
###							Events							####
################################################################
bot = commands.Bot(command_prefix="!")
bot.add_cog(Music(bot))
bot.remove_command("help")

@bot.event
async def on_disconnect():
	for guild in bot.guilds:
		bot.number_of_users_in_voice_channels[guild.id] = 0
		bot.connected[guild.id] = False
		bot.voice_state[guild.id].stop()
		await bot.voice_state[guild.id].disconnect()

@bot.event
async def on_ready():
	for guild in bot.guilds:
		bot.number_of_users_in_voice_channels[guild.id] = 0
		bot.connected[guild.id] = False
		bot.voice_state[guild.id] = None
		for member in guild.members:
			if member.voice != None and not member.bot:
				bot.number_of_users_in_voice_channels[guild.id] += 1
		for member in guild.members:
			if member.voice != None and not member.bot:
				bot.connected[guild.id] = True
				bot.voice_state[guild.id] = await member.voice.channel.connect()
				while bot.connected[guild.id] == True:
					source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(bot.dir + '/' + random.choice(os.listdir(bot.dir))))
					bot.voice_state[guild.id].play(source)
					while bot.voice_state[guild.id].is_playing():
						await asyncio.sleep(60)
						
@bot.event
async def on_voice_state_update(member, before, after):
	if after.channel != None and before.channel == None:
		bot.number_of_users_in_voice_channels[member.guild.id] += 1
		if bot.connected[member.guild.id] == False:
			bot.connected[member.guild.id] = True
			bot.voice_state[member.guild.id] = await after.channel.connect()
			while bot.connected[member.guild.id] == True:
				source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(bot.dir + '/' + random.choice(os.listdir(bot.dir))))
				bot.voice_state[member.guild.id].play(source)
				while bot.voice_state[member.guild.id].is_playing():
					await asyncio.sleep(60)

	elif after.channel != None and before.channel != None:
		if len(before.channel.members) == 1:
			if bot.voice_state[member.guild.id].is_playing():
				bot.voice_state[member.guild.id].stop()
			await bot.voice_state[member.guild.id].move_to(after.channel)
			while bot.connected[member.guild.id] == True:
				source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(bot.dir + '/' + random.choice(os.listdir(bot.dir))))
				bot.voice_state[member.guild.id].play(source)
				while bot.voice_state[member.guild.id].is_playing():
					await asyncio.sleep(60)
	else:
		bot.number_of_users_in_voice_channels[member.guild.id] -= 1
		if bot.number_of_users_in_voice_channels[member.guild.id] > 1:
			if bot.voice_state[member.guild.id].is_playing():
				bot.voice_state[member.guild.id].stop()
			if len(before.channel.members) == 1:
				for guild in bot.guilds:
					if guild.id == member.guild.id:
						for member in guild.members:
							if member.voice != None and not member.bot:
								await bot.voice_state[guild.id].move_to(m.voice.channel)
								break 
		else:
			bot.connected[member.guild.id] = False
			bot.voice_state[member.guild.id].stop()
			await bot.voice_state[member.guild.id].disconnect()
		while(bot.connected[member.guild.id] == True):
				source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(bot.dir + '/' + random.choice(os.listdir(bot.dir))))
				bot.voice_state[member.guild.id].play(source)
				while bot.voice_state[member.guild.id].is_playing():
					await asyncio.sleep(60)

################################################################
###							Run								####
################################################################
bot.run(TOKEN)
