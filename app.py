from database import DataBase
from config import BOT_TOKEN
from info import *
from telegram.ext import *
from telegram import *
import telegram

class ChatBot:
    def __init__(self, bot_name, bot_key):
        self.boys = []
        self.girls = []
        self.chat_pair = {}

        self.bot_name, self.bot_key = bot_name, bot_key

        # Calling  database
        self.record = DataBase()

        # Bot command handler
        self.command_handler()

    def common_args(self, update, context):
        if update.message.chat.type != "private":
            user_id = update.message.chat.id
            name = context.bot.get_chat(chat_id=user_id).title
            username = context.bot.get_chat(chat_id=user_id).username

        else:
            user_id = update.message.from_user.id
            name = update.message.from_user.first_name
            username = update.message.from_user.username

        return user_id, name, username

    def start(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                check_user = self.record.search(user_id)
                if not check_user:
                    # record insertion
                    self.record.insert(user_id, name, username)

                # Typing Action
                context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)
                # User welcome
                update.message.reply_text(text=welcome(name), parse_mode='Markdown')

                if check_user and not check_user.get('gender') and not check_user.get('partner_gender'):
                    self.settings(update, context)

            # if user stop the bot
            except telegram.error.Unauthorized:
                pass

    def help(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                # Typing Action
                context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)

                # Help user
                update.message.reply_text(text=user_help(), parse_mode='Markdown')

            # if user stop the bot
            except telegram.error.Unauthorized:
                pass

    def settings(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                # Typing Action
                context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🤴🏻 Gender 👸🏻", callback_data='SetGender')]
                ])

                # User info
                update.message.reply_text(text="🛠Settings", reply_markup=reply_markup) # "Settings" is already English

            # if user stop the bot
            except telegram.error.Unauthorized:
                pass

    def partner_selection(self, context, gender_list, opp_gender_list, user_id, gender1, gender2):

        # precaution for same gender
        if gender1 == gender2:
            if gender_list[0] != user_id:
                partner = gender_list[0]
            else:
                partner = gender_list[1]
        else:
            partner = opp_gender_list[0]

        # updating user list
        gender_list.remove(user_id)
        opp_gender_list.remove(partner)

        # updating chat pairs
        self.chat_pair.update({user_id: partner})
        self.chat_pair.update({partner: user_id})

        # Assuming partner_match from info.py now expects "Male" or "Female"
        # and the my_gender/partner_gender stored in database are also "Male"/"Female" (covered in next steps)
        # For now, this call relies on the updated info.py
        context.bot.send_message(chat_id=user_id, text=partner_match(gender1)) # gender1 will be "Male" or "Female"
        context.bot.send_message(chat_id=partner, text=partner_match(gender2)) # gender2 will be "Male" or "Female"


    def find_partner(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            # Updating name & username
            self.record.update(user_id, {"name": name, "username": username})

            # user preference
            data = self.record.search(user_id)
            my_gender = data.get("gender") # This will be "🤴🏻 Male" or "👸🏻 Female"
            partner_gender = data.get("partner_gender") # This will be "🤴🏻 Male" or "👸🏻 Female"

            if my_gender is None or partner_gender is None:
                self.settings(update, context)
            else:
                try:
                    # ending previous dialog if any
                    if user_id in self.chat_pair:
                        self.end_conversation(update, context)

                    # Use "Male" and "Female" for internal logic consistency with info.py's partner_match
                    # The database stores "🤴🏻 Male" or "👸🏻 Female"

                    # Determine partner's actual gender string for partner_match
                    # And own gender string for partner_match when sent to partner

                    # My gender value from DB: "🤴🏻 Male" or "👸🏻 Female"
                    # Partner gender preference from DB: "🤴🏻 Male" or "👸🏻 Female"

                    user_added_to_queue_or_matched = False

                    if my_gender == "🤴🏻 Male":
                        user_added_to_queue_or_matched = True # User is processed by this block
                        if user_id not in self.boys:
                            self.boys.append(user_id)

                        if partner_gender == "👸🏻 Female":
                            if len(self.girls) >= 1:
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Female", gender2="Male")
                            elif len(self.boys) >= 2: # if NO GIRL is available, try boy-boy
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Male", gender2="Male")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                        elif partner_gender == "🤴🏻 Male":
                            if len(self.boys) >= 2:
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Male", gender2="Male")
                            elif len(self.girls) >= 1: # if NO BOY is available, try boy-girl
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Female", gender2="Male")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                    elif my_gender == "👸🏻 Female":
                        user_added_to_queue_or_matched = True # User is processed by this block
                        if user_id not in self.girls:
                            self.girls.append(user_id)

                        if partner_gender == "🤴🏻 Male":
                            if len(self.boys) >= 1:
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Male", gender2="Female")
                            elif len(self.girls) >= 2: # if NO BOY is available, try girl-girl
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Female", gender2="Female")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                        elif partner_gender == "👸🏻 Female":
                            if len(self.girls) >= 2:
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Female", gender2="Female")
                            elif len(self.boys) >= 1: # if NO GIRL is available, try girl-boy
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Male", gender2="Female")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                    # If user's gender was not "🤴🏻 Male" or "👸🏻 Female" (e.g., legacy "🤴🏻 Cowok")
                    # and they were not matched/queued by the logic above,
                    # and they are not already in a chat (safeguard, end_conversation should handle this)
                    if not user_added_to_queue_or_matched and user_id not in self.chat_pair:
                        # Ensure they are not in a waiting queue before sending partner_not_found
                        # This check is mostly a safeguard as they shouldn't be in queues if not processed.
                        if user_id not in self.boys and user_id not in self.girls:
                             context.bot.send_message(chat_id=user_id, text=partner_not_found())

                except telegram.error.Unauthorized:
                    pass

    def end_conversation(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                # getting user info
                data = self.record.search(user_id)
                my_gender = data.get("gender") # This is "🤴🏻 Male" or "👸🏻 Female"

                if user_id not in self.chat_pair:
                    # remove instance from list
                    if my_gender == "🤴🏻 Male" and user_id in self.boys:
                        self.boys.remove(user_id)
                    elif my_gender == "👸🏻 Female" and user_id in self.girls:
                        self.girls.remove(user_id)

                    # user reply
                    context.bot.send_message(chat_id=user_id, text=invalid_destroy())
                else:
                    partner_id = self.chat_pair.get(user_id)

                    # update chat pair
                    del self.chat_pair[user_id]
                    del self.chat_pair[partner_id]

                    context.bot.send_message(chat_id=user_id, text=destroy(who="You"))
                    context.bot.send_message(chat_id=partner_id, text=destroy(who="Your"))

            # if user stop the bot
            except telegram.error.Unauthorized:
                pass

    def message_handler(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                if user_id not in self.chat_pair:
                    # Typing Action
                    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)
                    # This was changed in a previous step to share_profile_not_connected_error
                    # Reverting to invalid_destroy() as it's more generic for sending a message
                    context.bot.send_message(chat_id=user_id, text=invalid_destroy())
                else:
                    partner_id = self.chat_pair.get(user_id)
                    msg = update.message.text

                    # Typing Action
                    context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.TYPING, timeout=1)
                    context.bot.send_message(chat_id=partner_id, text=msg)

            # if user stop the bot
            except telegram.error.Unauthorized:
                self.end_conversation(update, context)

    def media_handler(self, update, context):
        # print(update)
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                if user_id not in self.chat_pair:
                    # Typing Action
                    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)
                    context.bot.send_message(chat_id=user_id, text=invalid_destroy())
                else:
                    partner_id = self.chat_pair.get(user_id)
                    caption = update.message.caption
                    
                    if update.message.text:
                        # text send action
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.TYPING, timeout=1)
                        context.bot.send_message(chat_id=partner_id, text=update.message.text)

                    elif update.message.sticker:
                        # sticker send action
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.CHOOSE_STICKER, timeout=1)
                        context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker)

                    elif update.message.photo:
                        # image send action
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_PHOTO, timeout=1)
                        if caption:
                            context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1], caption=caption)
                        else:
                            context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1])

                    elif update.message.video:
                        # video send action
                        context.bot.send_chat_action(chat_id=partner_id, action=telegram.ChatAction.UPLOAD_VIDEO)
                        if caption:
                            context.bot.send_video(chat_id=partner_id, video=update.message.video, caption=caption)
                        else:
                            context.bot.send_video(chat_id=partner_id, video=update.message.video)

                    elif update.message.video_note:
                        # video note send action
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.RECORD_VIDEO_NOTE, timeout=1)
                        context.bot.send_video_note(chat_id=partner_id, video_note=update.message.video_note)

                    elif update.message.voice:
                        # voice send action
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.RECORD_VOICE, timeout=1)
                        context.bot.send_voice(chat_id=partner_id, voice=update.message.voice)

                    elif update.message.audio:
                        # audio send action
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_AUDIO, timeout=1)
                        context.bot.send_audio(chat_id=partner_id, audio=update.message.audio)

                    elif update.message.document:
                        # document send action
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_DOCUMENT, timeout=1)
                        context.bot.send_document(chat_id=partner_id, document=update.message.document)

            # if user stop the bot
            except telegram.error.Unauthorized:
                self.end_conversation(update, context)

    def button_handler(self, update, context):
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query
        query.answer()

        # chat info
        user_id = update.callback_query.message.chat.id
        chat_type = update.callback_query.message.chat.type

        if chat_type == "private":
            if "SetGender" in query.data:

                # removing user previous state if present
                if user_id in self.boys:
                    self.boys.remove(user_id)
                elif user_id in self.girls:
                    self.girls.remove(user_id)

                # normal flow
                data = self.record.search(user_id)

                my_gender = data.get("gender")
                partner_gender = data.get("partner_gender")

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="👤 Your Gender", callback_data=f'SetMine')],
                    [InlineKeyboardButton(text="🗣️ Partner's Gender", callback_data=f'SetPartner')],
                ])

                query.edit_message_text(
                    text=f"Edit your gender or your partner's gender\nYou: {my_gender}\nPartner: {partner_gender}",
                    reply_markup=reply_markup)

            elif "SetMine" in query.data:
                data = self.record.search(user_id)

                my_gender = data.get("gender")

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🤴🏻 Male", callback_data=f'SetBoy_M')],
                    [InlineKeyboardButton(text="👸🏻 Female", callback_data=f'SetGirl_M')],
                ])

                query.edit_message_text(text=f"Select your gender\nCurrent: {my_gender}", reply_markup=reply_markup)

            elif "SetPartner" in query.data:
                data = self.record.search(user_id)

                partner_gender = data.get("partner_gender")

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🤴🏻 Male", callback_data=f'SetBoy_P')],
                    [InlineKeyboardButton(text="👸🏻 Female", callback_data=f'SetGirl_P')],
                ])

                query.edit_message_text(text=f"Select partner's gender\nCurrent: {partner_gender}",
                                        reply_markup=reply_markup)

            elif "SetBoy" in query.data:
                # checking request for user or partner
                if str(query.data).split("_")[1] == "M":
                    new_data = {"gender": "🤴🏻 Male"}
                else:
                    new_data = {"partner_gender": "🤴🏻 Male"}

                # update user info
                self.record.update(user_id, new_data)

                data = self.record.search(user_id)
                my_gender = data.get("gender")
                partner_gender = data.get("partner_gender")

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="👤 Your Gender", callback_data=f'SetMine')],
                    [InlineKeyboardButton(text="🗣️ Partner's Gender", callback_data=f'SetPartner')],
                ])

                query.edit_message_text(
                    text=f"Edit your gender or your partner's gender\nYou: {my_gender}\nPartner: {partner_gender}",
                    reply_markup=reply_markup)

            elif "SetGirl" in query.data:
                # checking request for user or partner
                if str(query.data).split("_")[1] == "M":
                    new_data = {"gender": "👸🏻 Female"}
                else:
                    new_data = {"partner_gender": "👸🏻 Female"}

                # update user info
                self.record.update(user_id, new_data)

                data = self.record.search(user_id)
                my_gender = data.get("gender")
                partner_gender = data.get("partner_gender")

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="👤 Your Gender", callback_data=f'SetMine')],
                    [InlineKeyboardButton(text="🗣️ Partner's Gender", callback_data=f'SetPartner')],
                ])

                query.edit_message_text(
                    text=f"Edit your gender or your partner's gender\nYou: {my_gender}\nPartner: {partner_gender}",
                    reply_markup=reply_markup)

    def sharelink(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                if user_id not in self.chat_pair:
                    # Typing Action
                    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)
                    context.bot.send_message(chat_id=user_id, text=share_profile_not_connected_error())
                else:
                    partner_id = self.chat_pair.get(user_id)

                    if username is not None:
                        context.bot.send_message(chat_id=user_id, text=f"Profile Shared")
                        context.bot.send_message(chat_id=partner_id, text=f"@{username}")
                    else:
                        context.bot.send_message(chat_id=user_id, text=f"Error: Username not found")

            # if user stop the bot
            except telegram.error.Unauthorized:
                self.end_conversation(update, context)

    def command_handler(self):
        updater = Updater(self.bot_key, use_context=True)

        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self.start, run_async=True))
        dp.add_handler(CommandHandler("help", self.help, run_async=True))
        dp.add_handler(CommandHandler("settings", self.settings, run_async=True))

        dp.add_handler(CommandHandler("next", self.find_partner, run_async=True))
        dp.add_handler(CommandHandler("stop", self.end_conversation, run_async=True))

        dp.add_handler(CommandHandler("sharelink", self.sharelink, run_async=True))

        dp.add_handler(MessageHandler(Filters.all, self.media_handler, run_async=True)) # Changed from Filters.text to Filters.all
        dp.add_handler(CallbackQueryHandler(self.button_handler, run_async=True))

        updater.start_polling()
        updater.idle()
        


if __name__ == '__main__':
    bot_name = "Bot"
    bot_key = BOT_TOKEN
    print("Starting Anon Bot") # This is a server-side print, not for translation
    ChatBot(bot_name, bot_key)
