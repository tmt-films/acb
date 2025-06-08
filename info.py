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
"""


def partner_match(gender):
    if gender == "Male":  # Updated to expect "Male"
        partner_display = "🤴🏻 Male"
    elif gender == "Female":  # Updated to expect "Female"
        partner_display = "👸🏻 Female"
    else:
        partner_display = gender # Fallback if gender is not Male/Female

    return f"""Partner: {partner_display}
/next — find a new partner
/stop — stop this chat"""


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
