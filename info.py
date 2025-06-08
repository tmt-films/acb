def welcome(name):
    return f"""Hi {name}🖐\n
Send me text, links, gifs, stickers, photos, videos, or voice messages and I will forward them anonymously to your partner.

Commands
/start - start the bot
/help - display help guide
/next — find a new partner
/stop — stop the dialog
/settings - settings menu
"""


def user_help():
    return """With this bot, you can chat anonymously with Males and Females based on gender.
    
Commands
/start - start the bot
/help - display help guide
/next — find a new partner
/stop — stop the dialog
/sharelink - share profile with partner
/settings - settings menu
/myname - manage your false name
""" # Added /myname to help

# Modified partner_match function
def partner_match(display_info):
    return f"You are now chatting with {display_info}.\nType /next to find a new partner or /stop to end this chat."


def partner_not_found():
    return """🔎 Looking for a partner"""


def destroy(who=None):
    if who == "You":
        return """You stopped this chat 🙄
Type /next to find a new partner
"""
    elif who == "Your":
        return """Your partner stopped this chat 🙄
Type /next to find a new partner
"""


def invalid_destroy():
    return """You don't have a chat partner 🤔
Type /next to find a new partner"""


def share_profile_not_connected_error():
    return """Error: You must be connected to a partner to share your profile."""


def broadcast_access_denied():
    return "Sorry, you are not authorized to use this command."


def broadcast_no_message():
    return "Please provide a message to broadcast. Usage: /broadcast <your message>"


def broadcast_summary(success_count, failure_count):
    return f"Broadcast attempt finished.\nSuccessfully sent to: {success_count} users.\nFailed to send to: {failure_count} users."


# New functions for false name management
def manage_false_name_prompt(current_false_name):
    if not current_false_name: # Handles None or empty string
        display_name = "Not set"
    else:
        display_name = current_false_name

    return (f"Your current false name is: {display_name}\n\n"
            "You can set or change your false name using:\n"
            "/setname <your_desired_name>\n\n"
            "To remove your false name, use:\n"
            "/clearname")


def set_false_name_usage():
    return "Usage: /setname <your desired name>"


def false_name_set(name):
    return f"Your false name has been set to: {name}"


def false_name_cleared():
    return "Your false name has been cleared."
