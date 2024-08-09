"""
This is a To-do list Slack bot.

It has two slash commands: /add-task and /list-tasks.
The /add-task command adds a task to the to-do list. For example, the user
could enter /add-task "Study for test". The bot would then add "Study for test"
to a list of tasks. The bot would respond with "Task added: Study for test".

The /list-tasks command lists all the tasks in the to-do list. For example, if
the user enters /list-tasks, the bot would list all the tasks that have been
added so far. If no tasks have been added, the bot would respond with "No
tasks added yet". Each task is sent in a separate message with a white_large
square emoji next to the task. If a user reacts with a checkmark to a task,
the bot would mark that task as completed by replacing the white_large_square
emoji with a white_check_mark emoji. The bot will also remove the task from the
to-do list and reply with a confirmation message.

The bot uses the Bolt framework to listen for incoming messages and slash
commands from Slack. The bot also uses the Flask web framework to create a
web server that listens for requests from Slack.

"""

# Import necessary libraries
import os                         # for environment variables
from slack_bolt import App        # for initializing the app
# for handling slash commands
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request  # for creating a Flask app
from dotenv import load_dotenv    # for loading environment variables

# load environment variables from .env file
load_dotenv()

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Create a Flask app
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

# Dictionary to store tasks. The user is the key and the
# value is a list of tasks
tasks = {}


# A slash command called /add-task that adds a task to the to-do list
@app.command("/add-task")
def add_task(ack, say, command):
    ack()                         # acknowledge the command request
    task = command["text"]        # Get the user's input
    user_id = command["user_id"]  # Get the user's ID

    # Print message if the user did not enter a task
    if task == "":
        say("Please enter a task", icon_emoji=":spiral_note_pad:")
        return

    # Add the task to the to-do list
    if user_id in tasks:  # The user has already added tasks

        # list comprehension that converts all tasks to
        # lowercase and removes punctuation
        tasks_lower = [task.lower().strip('.,!?') for task in tasks[user_id]]

        # Check if the task is already in the list before adding it
        if task.lower().strip('.,!?') in tasks_lower:
            say(text=f"Task already added: {task}", 
                icon_emoji=':spiral_note_pad:')
        else:
            tasks[user_id].append(task)
            say(text=f"Task added: {task}", icon_emoji=':spiral_note_pad:')

    else:  # a new user
        tasks[user_id] = [task]
        say(text=f"Task added: {task}", icon_emoji=':spiral_note_pad:')

    # print statement for debugging
    print(tasks)


# A slash command called /list-tasks that lists all the tasks in the to-do list
@app.command("/list-tasks")
def list_tasks(ack, say, command):
    ack()                         # acknowledge the command request
    user_id = command["user_id"]  # Get the user's ID

    # Check if the user has added any tasks
    if user_id not in tasks or len(tasks[user_id]) == 0:
        say("No tasks added yet", icon_emoji=":spiral_note_pad:")
    else:
        # List all the tasks added by the user
        for task in tasks[user_id]:
            say(text=f":white_large_square: {task}", 
                icon_emoji=':spiral_note_pad:')


# Event for when a user reacts to a message
@app.event("reaction_added")
def reaction_added(event, say, client):
    # Get the user ID of the user who reacted
    user_id = event["user"]
    # Get the reaction
    reaction = event["reaction"]
    # Get the message ID of the message that was reacted to
    message_id = event["item"]["ts"]
    # Get the channel ID of the message that was reacted to
    channel_id = event["item"]["channel"]

    # Check if the reaction is a checkmark
    if reaction == "white_check_mark":
        # Get the user's tasks (return an empty list if the user has no tasks)
        user_tasks = tasks.get(user_id, [])

        # Get the message content
        try:
            response = client.conversations_history(
                channel=channel_id,
                latest=message_id,
                limit=1,
                inclusive=True
            )
            message_text = response['messages'][0]['text'].replace(":white_large_square:", "").strip()
        except Exception as e:
            message_text = ""
            print(f"Error fetching message content: {e}")

        # Check if the user has any tasks
        if len(user_tasks) > 0:
            # Check if the message content is in the user's tasks
            if message_text in user_tasks:
                # Remove the task from the to-do list by its content
                user_tasks.remove(message_text)

                # Update the messsage with a checkmark
                try:
                    client.chat_update(
                        channel=channel_id,
                        ts=message_id,
                        icon_emoji=":spiral_note_pad:",
                        text=f":white_check_mark: {message_text}"
                    )

                    # Print confirmation message in thread
                    say(
                        text="Congratulations! :tada: Task marked as completed.",
                        thread_ts=message_id,
                        icon_emoji=":spiral_note_pad:"
                    )

                except Exception as e:
                    print(f"Error updating message: {e}")

    # print tasks for debugging
    print(tasks)


# Route to handle Slack requests
@flask_app.route("/slack/events", methods=["POST"])
@flask_app.route("/slack/add-task", methods=["POST"])
@flask_app.route("/slack/list-tasks", methods=["POST"])
def slack_events():
    return handler.handle(request)


# Start your Flask app
if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 3000)))
