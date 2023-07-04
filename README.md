# Discord DM Game Bot

The Discord DM Game Bot is a Python-based application utilizing OpenAI language model API for playing text-based games on Discord. This bot provides commands to manage game sessions, player data, response style, territory and resource management, and dice rolling functionality, in addition to leveraging AI for game actions.

## Dependencies

- discord.py
- OpenAI GPT-3 API

## Setup

1. Clone the repository to your local machine.
2. Set your system environment variables to access your resources:

```env
DISCORD_TOKEN=<your-discord-token>
OPENAI_API_KEY=<your-openai-api-key>
```

## Running the Bot

To start the bot, execute:

```bash
python DMBot.py
```

The bot should now be running and ready to join a Discord server.

## Playing a game

1. Send an invitation to all your friends to join your Discord server
2. Run the DMBot.py python script
3. Start a new channel where all your AI thoughts will go and run the command `!setThoughts`
4. Start a new channel for your actual game session and run `!setPrompt <prompt for your game>`
5. (Optional) Run `!setResponseStyle <style>` to set how the AI responds
6. Have every player that wants to join send the command `!addPlayer [<starting territory>] [<starting resource>]`
7. Run the command `!start`
8. Have the first player run the `!turn <action>` command
9. The Bot will roll a D20 and make a call to OpenAI's API to generate a response
10. After the bot responds the everyone makes a judgement call to determine if the player who's turn it was should gain/lose a territory/special resource
11. Have the player who went run the appropriate command based off everyone's judgement
12. Take turns going until someone reaches a target score, 1 point per territory and 1 point per resource 

## Bot Commands

1. `!setPrompt <prompt>`: Set the prompt for the current game session.
   - No default, this is required
   - Some ideas:
      - In a fantastical zoo, filled with hyperintelligent animals of various species, five resourceful visitors try to assert control or forge alliances. Special resources can be gathered to secure points. Who will reign supreme in this intriguing zoological battle?
      - In the midst of the medieval era, three ambitious lords vie for control over Europe. Each starts with control of a few nations and resources, but who will ultimately prevail?
2. `!setResponseStyle <style>`: Set the style of response for the current game session.
   - Default: 'about 1 paragraph'
   - Some ideas: 
      - 2 novel style paragraphs
      - 3 verses from the King James Bible  
3. `!start`: Start the current game session.
4. `!stop`: Stop the current game session.
5. `!addPlayer [territories] [resources]`: Add player that sent the command to the current game session with their territories and special resources.
   - Example: !addPlayer [Texas] [Mind Controlling Cowboy Hats] 
6. `!addT <territory>`: Add a territory to the player that sent the message.
   - Example: !addT Oklahoma  
7. `!addSR <resource>`: Add a special resource to the player that sent the message.
   - Example: !addSR Super Intelligent Cows
8. `!removeT`: Remove a territory from the player that sent the message via a dropdown menu.
9. `!removeSR`: Remove a special resource from the player that sent the message via a dropdown menu.
10. `!score`: Get the current state of the game.
11. `!stats`: Get a histogram of all players' rolls.
12. `!turn <action>`: Make a turn in the main game.
    - Example: !turn I use my super intelligent cow herd equipped with mind controlling cowboy hats to attempt to discretely take over Louisiana.  
13. `!setThoughts`: Set the thoughts channel where the all the raw AI prompts and responses will go. Just call this command in a channel and it will be stored for all game sessions.
