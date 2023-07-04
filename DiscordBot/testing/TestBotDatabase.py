import sys
import os

# Get the directory one level up
parent_dir = os.path.dirname(os.getcwd())

# Add the parent directory to the system path
sys.path.append(parent_dir)

from BotDatabase import *
import random

class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name

# Create a list of fake territories and special resources
territories = ["Territory_" + str(i+1) for i in range(10)]
resources = ["Resource_" + str(i+1) for i in range(10)]

# Create a list of fake users
users = [User(i, "User_" + str(i+1)) for i in range(1235, 1238)]

# Create a BotDB object
db = BotDB('test.yaml')

# Create a channel
channel_id = 123
channel = Channel(channel_id, "Game of Territories", 0.2)

# Add players to the channel
for user in users:
    user_territories = random.sample(territories, 3)  # Assign 3 random territories per user
    user_resources = random.sample(resources, 2)  # Assign 2 random resources per user
    channel.add_player(user, user_territories, user_resources)

# Set channel to active
channel.set_active()

# Simulate turns
for i in range(10):  # Simulate 10 turns
    for user in users:
        roll = random.randint(1, 6)
        sender_msg = f"User {user.name} turn {i+1}"
        ai_resp = f"AI Response turn {i+1}"
        summary = f"{user.name} rolled a {roll}"
        channel.add_turn(user.id, sender_msg, roll, ai_resp, summary)

db.sessions[channel_id] = channel
db.save_session(channel_id)

# Print the game state after every turn
# print(channel.get_game_state())
# print("Intro:")
# print(load_intro())
# print("Example:")
# print(load_example())
my_session = db.get_session(channel_id)
print(my_session.generate_full_request(1236, "I will dominate the world", 17))