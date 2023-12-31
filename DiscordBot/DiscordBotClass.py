import discord
from discord.ext import commands
from discord.voice_client import VoiceClient
from discord import FFmpegOpusAudio
from langchain.llms import OpenAI
from .BotDatabase import *
from .TextToSpeech import *
import random
import re
import asyncio

async def speak_message(message, voice_channel):
    if voice_channel is None:
        return
    speech_file = "latest_message.mp3"
    create_sound_file(message, speech_file)
    audio_source = FFmpegOpusAudio(speech_file)
    voice_channel.play(audio_source, after=lambda e: print('Player error: %s' % e) if e else None)
    while voice_channel.is_playing():
        await asyncio.sleep(0.1)


async def send_message(message, channel, voice_channel=None):
    await speak_message(message, voice_channel)
    messages = split_string_into_chunks(message)
    for msg in messages:
        await channel.send(msg)

class MySelect(discord.ui.Select):
    def __init__(self, channel_id, user_id, item_type, my_options, db, bot):
        self.channel_id = channel_id
        self.user_id = user_id
        self.item_type = item_type
        self.null_option = "None"
        self.my_options = [discord.SelectOption(label=x) for x in my_options]
        self.my_options.append(discord.SelectOption(label=self.null_option))
        self.db = db
        self.bot = bot
        super().__init__(placeholder="Which one?", max_values=1, min_values=1, options=self.my_options)

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        session = self.db.get_session(self.channel_id)
        if self.values[0] == self.null_option:
            action_resp = DataResponse(False, "Okay! Nothing happened.")
        elif self.item_type == "territories":
            action_resp = session.lose_territory(self.user_id, self.values[0])
        elif self.item_type == "specialResources":
            action_resp = session.lose_special_resource(self.user_id, self.values[0])
        else:
            action_resp = DataResponse(False, "Error processing dropdown entry type")
        self.db.save_session(self.channel_id)
        await interaction.response.send_message(action_resp.get_message())

class MyView(discord.ui.View):
    def __init__(self, channel_id, user_id, item_type, my_options, db, bot):
        super().__init__(timeout=5)
        self.my_select = MySelect(channel_id, user_id, item_type, my_options, db, bot)
        self.add_item(self.my_select)

    async def on_timeout(self) -> None:
        self.remove_item(self.my_select)
        self.my_select.disabled = True

class BotHandler:
    def __init__(self, discord_token, openai_api_key, filename):
        self.discord_token = discord_token
        self.openai_api_key = openai_api_key
        self.filename = filename
        self.voice_channel = None

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.register_commands()

        self.db = BotDB(self.filename)
        self.llm = OpenAI(model_name='gpt-3.5-turbo', temperature=0.2)

    async def send_thought(self, msg):
        thoughts_channel = self.bot.get_channel(self.db.get_thoughts_id())
        await send_message(msg, thoughts_channel)

    def register_commands(self):
        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user} has connected to Discord!')

        @self.bot.command(name='setPrompt', help='Set the prompt for the current game session')
        async def set_prompt(ctx, *, prompt: str):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            set_prompt_resp = session.set_prompt(prompt)
            self.db.save_session(channel_id)

            await send_message(set_prompt_resp.get_message(), ctx, self.voice_channel)

        @self.bot.command(name='setResponseStyle', help='Set the style of response for current game session')
        async def set_response_style(ctx, *, prompt: str):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            set_response_style_resp = session.set_response_style(prompt)
            self.db.save_session(channel_id)

            await send_message(set_response_style_resp.get_message(), ctx, self.voice_channel)

        @self.bot.command(name='start', help='Start the current game session')
        async def start(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            set_active_resp = session.set_active()
            self.db.save_session(channel_id)

            await send_message(set_active_resp.get_message(), ctx, self.voice_channel)

        @self.bot.command(name='stop', help='Stop the current game session')
        async def stop(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            set_unactive_resp = session.set_unactive()
            self.db.save_session(channel_id)

            await send_message(set_unactive_resp.get_message(), ctx)

        @self.bot.command(name='addPlayer',
                          help='Add a player to the current game session with their territories and special '
                               'resources. Both arguments should be comma-separated lists enclosed in brackets. E.g., '
                               '"!addPlayer [England, France] [soccer ball, iPhone]"')
        async def add_player(ctx, *, sender_msg: str):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)

            # Split the sender message into territories and resources
            territories_str, special_resources_str = sender_msg.strip().split('] [', 1)

            # Remove the outer brackets from territories_str and special_resources_str and split the strings on commas to get the lists
            territories_list = territories_str[1:].split(', ')
            special_resources_list = special_resources_str[:-1].split(', ')

            add_player_resp = session.add_player(ctx.author, territories_list, special_resources_list)
            self.db.save_session(channel_id)

            await send_message(add_player_resp.get_message(), ctx, self.voice_channel)

        @self.bot.command(name='addT',
                          help='Add a territory to the player that sent the message')
        async def add_territory(ctx, *, territory: str):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            give_territory_resp = session.give_territory(ctx.author, territory)
            self.db.save_session(channel_id)

            await send_message(give_territory_resp.get_message(), ctx, self.voice_channel)

        @self.bot.command(name='addSR',
                          help='Add a special resource to the player that sent the message')
        async def add_special_resource(ctx, *, special_resource: str):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            give_special_resource_resp = session.give_special_resource(ctx.author, special_resource)
            self.db.save_session(channel_id)

            await send_message(give_special_resource_resp.get_message(), ctx, self.voice_channel)

        @self.bot.command(name='removeT',
                          help='Remove a territory to the player that sent the message')
        async def remove_territory(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            player_in_game_resp = session.in_game(ctx.author)
            if not player_in_game_resp.get_success():
                await send_message(player_in_game_resp.get_message(), ctx)
                return
            territories = session.get_territories(ctx.author)
            if len(territories) == 0:
                await send_message("You already have no territories", ctx)
                return
            await ctx.send("Select the territory to remove!", view=MyView(channel_id, ctx.author.id, "territories", territories, self.db, self.bot), ephemeral=True)

        @self.bot.command(name='removeSR',
                          help='Remove a special resource to the player that sent the message')
        async def remove_special_resource(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            player_in_game_resp = session.in_game(ctx.author)
            if not player_in_game_resp.get_success():
                await send_message(player_in_game_resp.get_message(), ctx)
                return
            special_resources = session.get_special_resources(ctx.author)
            if len(special_resources) == 0:
                await send_message("You already have no special resources", ctx)
                return
            await ctx.send("Select the special resource to remove!", view=MyView(channel_id, ctx.author.id, "specialResources", special_resources, self.db, self.bot), ephemeral=True)

        @self.bot.command(name='roll',
                          help='Roll a dice using the format NdM, where N is the number of dice and M is the number of sides.')
        async def user_roll(ctx, dice: str = None):
            print(f'{self.bot.user} Saw a roll command!')

            if dice is None:
                await send_message(f'{ctx.author.mention}, please provide a dice format in addition to the command: "!roll NdM" (e.g., "!roll 2d6")', ctx)
                return

            try:
                num_dice, num_sides = map(int, re.findall(r'\d+', dice))
                if num_dice <= 0 or num_sides <= 0:
                    raise ValueError
            except ValueError:
                await send_message(f'{ctx.author.mention}, please use the correct format: NdM (e.g., 2d6)', ctx)
                return

            rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(rolls)
            rolls_str = ', '.join(map(str, rolls))
            await send_message(f'{ctx.author.mention} rolled {dice}: {rolls_str}. Total: {total}', ctx)

        @self.bot.command(name='score',
                          help='Get the current state of the game')
        async def get_state(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            state_msg = session.get_players_state()

            await send_message(state_msg, ctx)

        @self.bot.command(name='stats',
                          help='Get a histogram of all players rolls')
        async def get_stats(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)
            session = self.db.get_session(channel_id)
            filename = 'roll_histogram.png'
            graph = session.plot_player_rolls(filename)
            await ctx.send(file=discord.File(filename))

        @self.bot.command(name='turn', help='Make a turn in the main game.')
        async def on_turn(ctx, *, sender_msg: str):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)

            session = self.db.get_session(channel_id)

            sender_id = ctx.author.id
            check_ready_resp = session.check_ready_for_turn(sender_id)
            if not check_ready_resp.get_success():
                await send_message(check_ready_resp.get_message(), ctx, self.voice_channel)
                return

            # Check for a roll value in the sender's message
            msg_split = sender_msg.split()
            if msg_split[0].startswith("roll="):
                d20_roll = int(msg_split[0].split("=")[1])  # Extract the specified roll value
                sender_msg = " ".join(msg_split[1:])  # Remove the roll value from the sender's message
            else:
                d20_roll = roll(20)  # generate a random roll

            roll_msg = f"rolled a {d20_roll}."
            await speak_message(f"{ctx.author.nick} said, {sender_msg}........ and {roll_msg}", self.voice_channel)
            await send_message(f"{ctx.author.mention}, you {roll_msg}", ctx)

            # Prepare the input for the LLM
            llm_input = session.generate_full_request(sender_id, sender_msg, d20_roll)
            await self.send_thought(llm_input)

            # Call the LLM
            await ctx.typing()
            ai_response = self.llm(llm_input)
            await self.send_thought(ai_response)

            # Split out response from summary
            thoughts, content, summary = parse_output(ai_response)

            # Add turn to database
            session.add_turn(sender_id, sender_msg, d20_roll, content, summary)
            self.db.save_session(channel_id)

            # Send the response
            await send_message(content, ctx, self.voice_channel)

        @self.bot.command(name='undo',
                          help='Undo the last turn')
        async def undo(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)

            session = self.db.get_session(channel_id)

            sender_id = ctx.author.id
            check_ready_resp = session.check_ready_for_turn(sender_id)
            if not check_ready_resp.get_success():
                await send_message(check_ready_resp.get_message(), ctx, self.voice_channel)
                return

            undo_response = session.undo_turn()
            await send_message(undo_response.get_message(), ctx, self.voice_channel)

        @self.bot.command(name='setThoughts',
                          help='Set the thoughts channel')
        async def set_thoughts(ctx):
            channel_id = ctx.channel.id
            self.db.set_thoughts_id(channel_id)

            await send_message("Thoughts channel set", ctx)

        @self.bot.command(name='joinVoice',
                          help='Join the current voice channel')
        async def join_voice(ctx):
            if ctx.author.voice is None:
                await send_message("You aren't in a voice channel so I don't know where to go", ctx)
            voice_channel_name = ctx.author.voice.channel
            self.voice_channel = await voice_channel_name.connect()
            await speak_message("Hello from your Dungeon Master!", self.voice_channel)
            await send_message(f'Joined the {voice_channel_name.name} voice channel!', ctx)

        @self.bot.command(name='leaveVoice',
                          help='Make the discord bot leave the voice channel')
        async def leave_voice(ctx):
            if self.voice_channel is None:
                await send_message("I'm not in any voice channels", ctx)
            await self.voice_channel.disconnect()
            self.voice_channel = None
            await send_message("Disconnected from the voice channel", ctx)

        @self.bot.command(name='testSpeech', help='Speak whatever was sent')
        async def test_speech(ctx, *, speech: str):
            if self.voice_channel is None:
                await ctx.send("Can't speak because I'm not in a voice channel")
            else:
                speech_file = "test_speech.mp3"
                create_sound_file(speech, speech_file)  # Assumed you have a method to create the sound file
                audio_source = FFmpegOpusAudio(speech_file)
                self.voice_channel.play(audio_source, after=lambda e: print('Player error: %s' % e) if e else None)
                while self.voice_channel.is_playing():
                    await asyncio.sleep(0.1)
                await ctx.send("Done speaking")

        @self.bot.command(name='story', help='Tell the whole story up to this point')
        async def tell_story(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)

            session = self.db.get_session(channel_id)
            story = session.tell_story()
            await send_message(story, ctx)

        @self.bot.command(name='summary', help='Tell the whole story up to this point in summaries')
        async def tell_summary(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)

            session = self.db.get_session(channel_id)
            summary = session.tell_summary()
            await send_message(summary, ctx)

        @self.bot.command(name='finalQuest', help='Get your win condition quest')
        async def get_win_condition(ctx):
            channel_id = ctx.channel.id
            if not self.db.check_session(channel_id):
                self.db.sessions[channel_id] = Channel(channel_id)

            session = self.db.get_session(channel_id)
            sender_id = ctx.author.id
            check_ready_resp = session.check_ready_for_turn(sender_id)
            if not check_ready_resp.get_success():
                await send_message(check_ready_resp.get_message(), ctx, self.voice_channel)
                return

            # Prepare the input for the LLM
            win_condition_prompt = session.get_win_condition_prompt(ctx.author.nick)
            await self.send_thought(win_condition_prompt)

            # Call the LLM
            await ctx.typing()
            ai_response = self.llm(win_condition_prompt)
            await self.send_thought(ai_response)

            await send_message(ai_response, ctx, self.voice_channel)




    def run(self):
        self.bot.run(self.discord_token)
