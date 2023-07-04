import os
from DiscordBot import DiscordBotClass

bot_handler = DiscordBotClass.BotHandler(os.environ["DISCORD_TOKEN"],
                                         os.environ["OPENAI_API_KEY"],
                                         'sessions.yaml')
bot_handler.run()