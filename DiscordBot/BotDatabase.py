import yaml
import os
import random
import re
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

def split_string_into_chunks(text):
    MAX_CHUNK_SIZE = 2000
    chunks = []
    current_chunk = ""

    for line in text.splitlines():
        if len(current_chunk) + len(line) + 1 <= MAX_CHUNK_SIZE:
            current_chunk += line + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def load_txt_file(filename):
    example_file = open(filename)
    return ''.join(example_file)

def load_prompt_file(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    intro_file_path = os.path.join(current_dir, 'prompt_texts', filename)
    return load_txt_file(intro_file_path)

def load_intro(prompt_num):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    intro_file_path = os.path.join(current_dir, 'prompt_texts', f"PromptIntro{prompt_num}.txt")
    return load_txt_file(intro_file_path)


def load_example(ex_num):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    example_file_path = os.path.join(current_dir, 'prompt_texts', f"Example{ex_num}.txt")
    return load_txt_file(example_file_path)


def roll(num_sides):
    return random.randint(1, num_sides)


def parse_output(input_string):
    thoughts_match = re.search(r'THOUGHTS:(.*?)RESPONSE:', input_string, re.DOTALL)
    if thoughts_match:
        thoughts = thoughts_match.group(1).strip()
    else:
        thoughts = None

    response_match = re.search(r'RESPONSE:(.*?)SUMMARY:', input_string, re.DOTALL)
    if response_match:
        response = response_match.group(1).strip()
    else:
        response = None

    summary_match = re.search(r'SUMMARY:(.*)', input_string, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()
    else:
        summary = None

    return thoughts, response, summary


def plot_histogram(players, filename=None):
    plt.figure(figsize=[12, 8])
    sns.set()  # set aesthetic parameters in one step

    # Prepare data
    dice_numbers = np.arange(1, 21)
    frequencies = {player: [rolls.count(i) for i in dice_numbers] for player, rolls in players.items()}

    # Create bottom padding for stacked bar chart
    bottoms = np.array([0] * 20)

    for player, freq in frequencies.items():
        plt.bar(dice_numbers, freq, bottom=bottoms, label=player)
        bottoms += np.array(freq)

    plt.title('Histogram of Dice Rolls')
    plt.xlabel('Dice Number')
    plt.ylabel('Frequency')
    plt.xticks(dice_numbers)
    plt.legend()
    plt.grid(True)

    fig = plt.gcf()

    if filename:
        fig.savefig(filename)

    return fig

class DataResponse:
    def __init__(self, success, msg):
        self.success = success
        self.msg = msg

    def get_success(self):
        return self.success

    def get_message(self):
        return self.msg


class Turn:
    def __init__(self, turn_num=None, sender_id=None, sender_msg=None, roll=None, ai_resp=None, summary=None,
                 config=None):
        if config is not None:
            self.turn_num = config["turn_num"]
            self.sender_id = config["sender_id"]
            self.sender_msg = config["sender_msg"]
            self.roll = config["roll"]
            self.ai_response = config["ai_response"]
            self.summary = config["summary"]
        else:
            self.turn_num = turn_num
            self.sender_id = sender_id
            self.sender_msg = sender_msg
            self.roll = roll
            self.ai_response = ai_resp
            self.summary = summary

    def get_roll(self):
        return self.roll

    def export(self):
        config = {
            'turn_num': self.turn_num,
            'sender_id': self.sender_id,
            'sender_msg': self.sender_msg,
            'roll': self.roll,
            'ai_response': self.ai_response,
            'summary': self.summary
        }
        return config


class Player:
    def __init__(self, id=None, name=None, territories=None, special_resources=None, config=None):
        if config is not None:
            self.id = config["id"]
            self.name = config["name"]
            self.territories = config["territories"]
            self.special_resources = config["special_resources"]
            self.last_move_summary = config["last_move_summary"]
            self.turn_numbers = config["turn_numbers"]
        else:
            self.id = id
            self.name = name
            self.territories = territories
            self.special_resources = special_resources
            self.last_move_summary = f"{self.name} has not made any actions yet."
            self.turn_numbers = []

    def has_territory(self, territory):
        return territory in self.territories

    def add_territory(self, territory):
        if not self.has_territory(territory):
            self.territories.append(territory)
            return DataResponse(True, f"{self.name} now has {territory}")
        else:
            return DataResponse(False, f"{self.name} already has the territory {territory}")

    def remove_territory(self, territory):
        if self.has_territory(territory):
            self.territories.remove(territory)
            return DataResponse(True, f"{self.name} lost {territory}")
        else:
            return DataResponse(False, f"{self.name} does not have {territory}")

    def get_territories(self):
        return self.territories

    def has_special_resource(self, special_resource):
        return special_resource in self.special_resources

    def add_special_resource(self, special_resource):
        if not self.has_special_resource(special_resource):
            self.special_resources.append(special_resource)
            return DataResponse(True, f"{self.name} now has {special_resource}")
        else:
            return DataResponse(False, f"{self.name} already has the special resource {special_resource}")

    def remove_special_resource(self, special_resource):
        if self.has_special_resource(special_resource):
            self.special_resources.remove(special_resource)
            return DataResponse(True, f"{self.name} lost {special_resource}")
        else:
            return DataResponse(False, f"{self.name} does not have {special_resource}")

    def get_special_resources(self):
        return self.special_resources

    def add_turn_number(self, turn_number):
        if turn_number not in self.turn_numbers:
            self.turn_numbers.append(turn_number)
            return DataResponse(True, f"{self.name} added {turn_number} to their turns")
        else:
            return DataResponse(False, f"{self.name} already has a turn {turn_number} listed")

    def update_name(self, name):
        self.name = name

    def set_last_move_summary(self, summary):
        self.last_move_summary = summary

    def add_turn(self, turn):
        self.set_last_move_summary(turn.summary)
        self.add_turn_number(turn.turn_num)

    def export(self):
        config = {
            'id': self.id,
            'name': self.name,
            'territories': self.territories,
            'special_resources': self.special_resources,
            'last_move_summary': self.last_move_summary,
            'turn_numbers': self.turn_numbers
        }
        return config

    def get_score(self):
        score = len(self.territories) + len(self.special_resources)
        return DataResponse(True, f"{self.name} has a score of:  {score}")

    def score(self):
        return len(self.territories) + len(self.special_resources)

    def get_state_summary(self):
        territories = ', '.join(self.territories)
        resources = ', '.join(self.special_resources)
        player_state = f"{self.name}: {self.score()} pts, controls {territories}; special resources: {resources}."
        return DataResponse(True, player_state)

    def get_latest_move(self):
        return DataResponse(True, f"{self.name}: {self.last_move_summary}")

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_turns(self):
        return self.turn_numbers


class Channel:
    def __init__(self, id=None, prompt=None, temperature=None, config=None):
        if config is not None:
            self.id = config["id"]
            self.prompt = config["prompt"]
            self.active = config["active"]
            self.temperature = config["temperature"]
            self.players = {}
            self.turns = []
            if "response_style" in config:
                self.response_style = config["response_style"]
            else:
                self.response_style = "about 1 paragraph"
            players = config["players"]
            for player, player_data in players.items():
                self.players[player] = Player(config=player_data)
            turns = config["turns"]
            for turn_data in turns:
                self.turns.append(Turn(config=turn_data))
            self.current_turn = len(self.turns) + 1
        else:
            self.id = id
            self.prompt = prompt
            if temperature is not None:
                self.temperature = temperature
            else:
                self.temperature = 0.2
            self.players = {}
            self.turns = []
            self.active = False
            self.current_turn = 1
            self.response_style = "About 1 paragraph"

    def set_prompt(self, prompt):
        self.prompt = prompt
        return DataResponse(True, f"Prompt set to: {self.prompt}")

    def get_prompt(self):
        return DataResponse(True, f"Prompt: {self.prompt}")

    def set_active(self):
        if self.prompt is None:
            return DataResponse(False, "Session does not have a prompt therefore it cannot be set to active")
        elif len(self.players) == 0:
            return DataResponse(False, "Session has no players, therefore it cannot be set to active")
        else:
            self.active = True
            return DataResponse(True, "Session was set to active")

    def set_unactive(self):
        self.active = False
        return DataResponse(True, "Session was deactivated")

    def get_active(self):
        if self.active:
            return DataResponse(True, "This channel currently has an active session")
        else:
            return DataResponse(True, "This channel does not have an active session")

    def set_temperature(self, temp):
        self.temperature = temp
        return DataResponse(True, f"The LLM temperature was set to {temp}")

    def get_temperature(self):
        return self.temperature

    def set_response_style(self, response_style):
        self.response_style = response_style
        return DataResponse(True, f"Response style was set to {response_style}")

    def add_player(self, user, territories, special_resources):
        self.players[user.id] = Player(user.id, user.display_name, territories, special_resources)
        return DataResponse(True, f"Player {user.display_name} was added to the conquest!")

    def add_turn(self, sender_id, sender_msg, d20_roll, ai_resp, summary):
        current_turn = len(self.turns) + 1
        turn = Turn(current_turn, sender_id, sender_msg, d20_roll, ai_resp, summary)
        self.turns.append(turn)
        self.players[sender_id].add_turn(turn)

    def undo_turn(self):
        if len(self.turns) > 0:
            last_turn = self.turns.pop()
            player = self.players[last_turn.sender_id]
            player.turn_numbers.pop()
            if len(player.turn_numbers) > 0:
                player.last_move_summary = self.turns[player.turn_numbers[-1] - 1].summary
            else:
                player.last_move_summary = f"{player.name} has not made any actions yet."
            return DataResponse(True, "Last turn undone successfully")
        else:
            return DataResponse(False, "No turns to undo")

    def get_turn(self, idx):
        return self.turns[idx]

    def in_game(self, user):
        if user.id not in self.players:
            return DataResponse(False, "This player is not actively in the game, use `!addPlyaer`")
        else:
            return DataResponse(True, "Player in game")

    def give_territory(self, user, territory):
        if user.id not in self.players:
            return DataResponse(False, "This player is not actively in the game, use `!addPlyaer`")
        player = self.players[user.id]
        player.add_territory(territory)
        return DataResponse(True, f"You now have control of {territory}")

    def give_special_resource(self, user, special_resource):
        if user.id not in self.players:
            return DataResponse(False, "This player is not actively in the game, use `!addPlyaer`")
        player = self.players[user.id]
        player.add_special_resource(special_resource)
        return DataResponse(True, f"You now own {special_resource}")

    def get_territories(self, user):
        if user.id not in self.players:
            return DataResponse(False, "This player is not actively in the game, use `!addPlyaer`")
        player = self.players[user.id]
        return player.get_territories()

    def get_special_resources(self, user):
        if user.id not in self.players:
            return DataResponse(False, "This player is not actively in the game, use `!addPlyaer`")
        player = self.players[user.id]
        return player.get_special_resources()

    def lose_territory(self, user_id, territory):
        if user_id not in self.players:
            return DataResponse(False, "This player is not actively in the game")
        player = self.players[user_id]
        player.remove_territory(territory)
        return DataResponse(True, f"{territory} removed")

    def lose_special_resource(self, user_id, special_resource):
        if user_id not in self.players:
            return DataResponse(False, "This player is not actively in the game")
        player = self.players[user_id]
        player.remove_special_resource(special_resource)
        return DataResponse(True, f"{special_resource} removed")

    def get_game_state(self):
        player_states = []
        for player, player_state in self.players.items():
            resp = player_state.get_state_summary()
            player_states.append(resp.msg)
        return '\n'.join(player_states)

    def get_latest_moves(self):
        latest_moves = []
        for player, player_state in self.players.items():
            resp = player_state.get_latest_move()
            latest_moves.append(resp.msg)
        return '\n'.join(latest_moves)

    def check_ready_for_turn(self, sender_id):
        if self.prompt is None:
            return DataResponse(False, "Session does not have a prompt, call !setprompt")
        elif len(self.players) == 0:
            return DataResponse(False, "Session has no players, call !addplayer")
        elif not self.active:
            return DataResponse(False, "Session is not active, call !start")
        elif sender_id not in self.players:
            return DataResponse(False, "Do not recognize player that sent the message, please add them")
        else:
            return DataResponse(True, "Ready")


    def generate_turn_request(self, sender_id, msg, d20_roll):
        game_session_intro = f"Game Session: {self.prompt}\n\n"

        other_parameters = "Settings:\n"
        other_parameters += f"Response Style: {self.response_style}\n"
        other_parameters += "\n\n"

        last_turn_summaries = "Last Turn Summaries:\n"
        last_turn_summaries += "\n".join([player.get_latest_move().get_message() for player in self.players.values()])
        last_turn_summaries += "\n\n"

        current_game_state = "Current Game State:\n"
        current_game_state += "\n".join([player.get_state_summary().get_message() for player in self.players.values()])
        current_game_state += "\n\n"

        incoming_turn = "Incoming Turn\n"
        incoming_turn += f"From: {self.players[sender_id].get_name()}\n"
        incoming_turn += f"Message: {msg}\n"
        incoming_turn += f"D20 roll: {d20_roll}\n"

        return game_session_intro + other_parameters + last_turn_summaries + current_game_state + incoming_turn

    def generate_full_request(self, sender_id, msg, d20_roll):
        full_request = load_intro(2)
        full_request += "\nEXAMPLE 1:"
        full_request += "\n" + load_example(1)
        full_request += "\nEXAMPLE 2:"
        full_request += "\n" + load_example(2)
        full_request += "\nEXAMPLE 3:"
        full_request += "\n" + load_example(3)
        full_request += "\n---------"
        full_request += "\nNow for your real input, remember to follow the example structures and provide a clear " \
                        "success or failure of the action "
        full_request += "\n" + self.generate_turn_request(sender_id, msg, d20_roll)
        return full_request

    def get_players_ranking(self):
        # First we'll create a list of players along with their scores, territories, and special resources
        # Each element in the list is a tuple with format: (score, player_name, territories, special_resources)
        player_rankings = [
            (player.score(), player.get_name(), player.territories, player.special_resources)
            for player in self.players.values()]

        # Now we sort the list in descending order of score (which is the first element of each tuple)
        # Python's sort function will automatically sort tuples by their first element first, then second, and so on
        player_rankings.sort(reverse=True)

        # Now we'll create a string representation of the sorted list
        player_rankings_str_list = []
        for score, player_name, territories, special_resources in player_rankings:
            territories_str = ', '.join(territories)
            special_resources_str = ', '.join(special_resources)
            player_rankings_str_list.append(
                f"{player_name} with a score of {score}, controls territories: {territories_str} and owns resources: {special_resources_str}"
            )

        # Finally, join the string representations of the player rankings into one string separated by newlines
        return '\n'.join(player_rankings_str_list)

    def get_players_rankingV2(self):
        # First we'll create a list of players along with their scores, territories, and special resources
        player_rankings = [(player.get_name(), player.score(), len(player.territories),
                            len(player.special_resources))
                           for player in self.players.values()]

        # Sort the list in descending order of score
        player_rankings.sort(key=lambda x: x[1], reverse=True)

        # Now we'll create the table using the tabulate module.
        headers = ["Player Name", "Score", "Territories", "Resources"]
        table = tabulate(player_rankings, headers, tablefmt="simple")
        table = "```\n" + table + "\n```"

        return table

    def get_players_state(self):
        player_rankings = [(player.get_name(), player.score(), player.territories,
                            player.special_resources)
                           for player in self.players.values()]

        # Sort the list in descending order of score
        player_rankings.sort(key=lambda x: x[1], reverse=True)

        # Start the formatted output
        formatted_output = ""
        for rank in player_rankings:
            # Add player name and score
            formatted_output += "Player Name: " + str(rank[0]) + "\nScore: " + str(rank[1]) + "\n"

            # Add territories
            formatted_output += "Territories:\n"
            for territory in rank[2]:
                formatted_output += "- " + str(territory) + "\n"

            # Add special resources
            formatted_output += "Resources:\n"
            for resource in rank[3]:
                formatted_output += "- " + str(resource) + "\n"

            # Add a separator for clarity
            formatted_output += "-----------------------------\n"

        formatted_output = "```\n" + formatted_output + "\n```"
        return formatted_output

    def get_players_rolls(self):
        player_rolls = {}
        for player in self.players.values():
            player_turns = player.get_turns()
            rolls = []
            for pt in player_turns:
                rolls.append(self.turns[pt - 1].get_roll())
            player_rolls[player.get_name()] = rolls
        return player_rolls

    def plot_player_rolls(self, filename=None):
        player_rolls = self.get_players_rolls()
        return plot_histogram(player_rolls, filename)

    def get_story(self):
        responses = [turn.ai_response for turn in self.turns]
        story = '\n---\n'.join(responses)
        return story

    def get_summary(self):
        summaries = [turn.summary for turn in self.turns]
        summary = '\n---\n'.join(summaries)
        return summary

    def tell_story(self):
        story = f"Prompt: {self.prompt}\nStory:\n"
        story += self.get_story()
        return story

    def tell_summary(self):
        summary = f"Prompt: {self.prompt}\nSummary of events:\n"
        summary += self.get_summary()
        return summary

    def get_win_condition_prompt(self, player_name):
        win_condition_prompt = load_prompt_file("WinConditionIntro.txt")
        win_condition_prompt += f"\n{load_prompt_file('WinConditionRules.txt')}"
        win_condition_prompt += f"\nGive me a winning goal for {player_name}"
        win_condition_prompt += f"\nPrompt: {self.prompt}"
        win_condition_prompt += f"\nGame State\n{self.get_players_state()}"
        win_condition_prompt += f"\nSummary of events:\n{self.tell_summary()}"
        win_condition_prompt += f"\n----------\n"
        win_condition_prompt += f'\nBased on the game up to this point and the rules described above, the final goal ' \
                                f'for {player_name} that does not involve convincing any other players in the game to do anything is: '
        return win_condition_prompt

    def export(self):
        players = {player_id: player.export() for player_id, player in self.players.items()}
        turns = [turn.export() for turn in self.turns]
        config = {
            'id': self.id,
            'prompt': self.prompt,
            'active': self.active,
            'temperature': self.temperature,
            'players': players,
            'turns': turns,
            'response_style': self.response_style
        }
        return config


class BotDB:
    def __init__(self, filepath):
        self.filepath = filepath
        self.sessions = {}
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                self.session_configs = yaml.safe_load(f)
            if not self.session_configs:
                self.session_configs = {}
        else:
            with open(self.filepath, 'w') as f:
                yaml.safe_dump({}, f)
            self.session_configs = {}
        for session, session_data in self.session_configs.items():
            if session != "thoughts":
                self.sessions[session] = Channel(config=session_data)

        self.thoughts_channel_name = "thoughts"

    def check_session(self, session_id):
        if session_id in self.sessions:
            return True
        else:
            return False

    def get_session(self, session_id):
        return self.sessions[session_id]

    def save_session(self, session_id):
        self.session_configs[session_id] = self.sessions[session_id].export()
        with open(self.filepath, 'w') as f:
            yaml.safe_dump(self.session_configs, f)

    def set_thoughts_id(self, channel_id):
        c_id_config = {"channel_id": channel_id}
        self.session_configs[self.thoughts_channel_name] = c_id_config
        with open(self.filepath, 'w') as f:
            yaml.safe_dump(self.session_configs, f)

    def get_thoughts_id(self):
        if self.thoughts_channel_name in self.session_configs:
            return self.session_configs[self.thoughts_channel_name]["channel_id"]
