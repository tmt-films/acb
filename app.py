from database import DataBase
from config import BOT_TOKEN, ADMIN_USER_IDS
from info import *
from telegram.ext import *
from telegram import *
import telegram
import time # Added for broadcast delay

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
                    [InlineKeyboardButton(text="🤴🏻 Gender 👸🏻", callback_data='SetGender')],
                    [InlineKeyboardButton(text="📝 Manage False Name", callback_data='ManageFalseName')]
                ])

                # User info
                update.message.reply_text(text="🛠Settings", reply_markup=reply_markup)

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

        # Determine display info for each user
        user_data = self.record.search(user_id)
        partner_data = self.record.search(partner)

        user_display_for_partner = partner_data.get('false_name') if partner_data.get('false_name') else gender2
        partner_display_for_user = user_data.get('false_name') if user_data.get('false_name') else gender1

        # If false_name is not set, use gender (gender1 for user_id, gender2 for partner)
        # The partner_match function now expects the final display string.

        # For user_id, the partner's display info is partner_display_for_user
        # For partner, the user_id's display info is user_display_for_partner

        # Correction: The partner_match should display the *other* person's info.
        # So, for user_id, we display info about 'partner'.
        # For partner, we display info about 'user_id'.

        # Get partner's false name or gender
        partner_info_for_user = partner_data.get('false_name') or gender2 # gender2 is partner's actual gender string e.g. "Male"
        # Get user's false name or gender
        user_info_for_partner = user_data.get('false_name') or gender1 # gender1 is user's actual gender string e.g. "Female"

        context.bot.send_message(chat_id=user_id, text=partner_match(partner_info_for_user))
        context.bot.send_message(chat_id=partner, text=partner_match(user_info_for_partner))


    def find_partner(self, update, context):
        user_id, name, username = self.common_args(update, context)

        # chat type (group or private)
        chat_type = update.message.chat.type

        if chat_type == "private":
            # Updating name & username
            self.record.update(user_id, {"name": name, "username": username})

            # user preference
            data = self.record.search(user_id)
            my_gender = data.get("gender")
            partner_gender = data.get("partner_gender")

            if my_gender is None or partner_gender is None:
                self.settings(update, context)
            else:
                try:
                    if user_id in self.chat_pair:
                        self.end_conversation(update, context)

                    user_added_to_queue_or_matched = False

                    if my_gender == "🤴🏻 Male":
                        user_added_to_queue_or_matched = True
                        if user_id not in self.boys:
                            self.boys.append(user_id)

                        if partner_gender == "👸🏻 Female":
                            if len(self.girls) >= 1:
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Male", gender2="Female")
                            elif len(self.boys) >= 2:
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Male", gender2="Male")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                        elif partner_gender == "🤴🏻 Male":
                            if len(self.boys) >= 2:
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Male", gender2="Male")
                            elif len(self.girls) >= 1:
                                self.partner_selection(context, gender_list=self.boys, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Female", gender2="Male")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                    elif my_gender == "👸🏻 Female":
                        user_added_to_queue_or_matched = True
                        if user_id not in self.girls:
                            self.girls.append(user_id)

                        if partner_gender == "🤴🏻 Male":
                            if len(self.boys) >= 1:
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Female", gender2="Male")
                            elif len(self.girls) >= 2:
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Female", gender2="Female")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                        elif partner_gender == "👸🏻 Female":
                            if len(self.girls) >= 2:
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.girls,
                                                       user_id=user_id, gender1="Female", gender2="Female")
                            elif len(self.boys) >= 1:
                                self.partner_selection(context, gender_list=self.girls, opp_gender_list=self.boys,
                                                       user_id=user_id, gender1="Male", gender2="Female")
                            else:
                                context.bot.send_message(chat_id=user_id, text=partner_not_found())

                    if not user_added_to_queue_or_matched and user_id not in self.chat_pair:
                        if user_id not in self.boys and user_id not in self.girls:
                             context.bot.send_message(chat_id=user_id, text=partner_not_found())

                except telegram.error.Unauthorized:
                    pass

    def end_conversation(self, update, context):
        user_id, name, username = self.common_args(update, context)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                data = self.record.search(user_id)
                my_gender = data.get("gender")

                if user_id not in self.chat_pair:
                    if my_gender == "🤴🏻 Male" and user_id in self.boys:
                        self.boys.remove(user_id)
                    elif my_gender == "👸🏻 Female" and user_id in self.girls:
                        self.girls.remove(user_id)
                    context.bot.send_message(chat_id=user_id, text=invalid_destroy())
                else:
                    partner_id = self.chat_pair.get(user_id)
                    del self.chat_pair[user_id]
                    del self.chat_pair[partner_id]
                    context.bot.send_message(chat_id=user_id, text=destroy(who="You"))
                    context.bot.send_message(chat_id=partner_id, text=destroy(who="Your"))
            except telegram.error.Unauthorized:
                pass

    def message_handler(self, update, context):
        user_id, name, username = self.common_args(update, context)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                if user_id not in self.chat_pair:
                    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)
                    context.bot.send_message(chat_id=user_id, text=invalid_destroy())
                else:
                    partner_id = self.chat_pair.get(user_id)
                    msg = update.message.text
                    context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.TYPING, timeout=1)
                    context.bot.send_message(chat_id=partner_id, text=msg)
            except telegram.error.Unauthorized:
                self.end_conversation(update, context)

    def media_handler(self, update, context):
        user_id, name, username = self.common_args(update, context)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                if user_id not in self.chat_pair:
                    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)
                    context.bot.send_message(chat_id=user_id, text=invalid_destroy())
                else:
                    partner_id = self.chat_pair.get(user_id)
                    caption = update.message.caption
                    
                    if update.message.text:
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.TYPING, timeout=1)
                        context.bot.send_message(chat_id=partner_id, text=update.message.text)
                    elif update.message.sticker:
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.CHOOSE_STICKER, timeout=1)
                        context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker)
                    elif update.message.photo:
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_PHOTO, timeout=1)
                        if caption:
                            context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1], caption=caption)
                        else:
                            context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1])
                    elif update.message.video:
                        context.bot.send_chat_action(chat_id=partner_id, action=telegram.ChatAction.UPLOAD_VIDEO)
                        if caption:
                            context.bot.send_video(chat_id=partner_id, video=update.message.video, caption=caption)
                        else:
                            context.bot.send_video(chat_id=partner_id, video=update.message.video)
                    elif update.message.video_note:
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.RECORD_VIDEO_NOTE, timeout=1)
                        context.bot.send_video_note(chat_id=partner_id, video_note=update.message.video_note)
                    elif update.message.voice:
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.RECORD_VOICE, timeout=1)
                        context.bot.send_voice(chat_id=partner_id, voice=update.message.voice)
                    elif update.message.audio:
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_AUDIO, timeout=1)
                        context.bot.send_audio(chat_id=partner_id, audio=update.message.audio)
                    elif update.message.document:
                        context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_DOCUMENT, timeout=1)
                        context.bot.send_document(chat_id=partner_id, document=update.message.document)
            except telegram.error.Unauthorized:
                self.end_conversation(update, context)

    def button_handler(self, update, context):
        query = update.callback_query
        query.answer()
        user_id = update.callback_query.message.chat.id
        chat_type = update.callback_query.message.chat.type

        if chat_type == "private":
            data = self.record.search(user_id)

            if "SetGender" in query.data:
                if user_id in self.boys: self.boys.remove(user_id)
                elif user_id in self.girls: self.girls.remove(user_id)

                my_gender = data.get("gender")
                partner_gender = data.get("partner_gender")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="👤 Your Gender", callback_data=f'SetMine')],
                    [InlineKeyboardButton(text="🗣️ Partner's Gender", callback_data=f'SetPartner')],
                ])
                query.edit_message_text(
                    text=f"Edit your gender or your partner's gender\nYou: {my_gender}\nPartner: {partner_gender}",
                    reply_markup=reply_markup)

            elif "ManageFalseName" in query.data:
                current_false_name = data.get('false_name')
                query.edit_message_text(text=manage_false_name_prompt(current_false_name), parse_mode='Markdown')

            elif "SetMine" in query.data:
                my_gender = data.get("gender")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🤴🏻 Male", callback_data=f'SetBoy_M')],
                    [InlineKeyboardButton(text="👸🏻 Female", callback_data=f'SetGirl_M')],
                ])
                query.edit_message_text(text=f"Select your gender\nCurrent: {my_gender}", reply_markup=reply_markup)

            elif "SetPartner" in query.data:
                partner_gender = data.get("partner_gender")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🤴🏻 Male", callback_data=f'SetBoy_P')],
                    [InlineKeyboardButton(text="👸🏻 Female", callback_data=f'SetGirl_P')],
                ])
                query.edit_message_text(text=f"Select partner's gender\nCurrent: {partner_gender}",
                                        reply_markup=reply_markup)

            elif "SetBoy" in query.data or "SetGirl" in query.data:
                new_db_data = {}
                if "SetBoy" in query.data:
                    gender_val = "🤴🏻 Male"
                else:
                    gender_val = "👸🏻 Female"

                if str(query.data).split("_")[1] == "M":
                    new_db_data = {"gender": gender_val}
                else:
                    new_db_data = {"partner_gender": gender_val}

                self.record.update(user_id, new_db_data)

                updated_data = self.record.search(user_id)
                my_gender = updated_data.get("gender")
                partner_gender = updated_data.get("partner_gender")

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="👤 Your Gender", callback_data=f'SetMine')],
                    [InlineKeyboardButton(text="🗣️ Partner's Gender", callback_data=f'SetPartner')],
                ])
                query.edit_message_text(
                    text=f"Edit your gender or your partner's gender\nYou: {my_gender}\nPartner: {partner_gender}",
                    reply_markup=reply_markup)

    def sharelink(self, update, context):
        user_id, name, username = self.common_args(update, context)
        chat_type = update.message.chat.type

        if chat_type == "private":
            try:
                if user_id not in self.chat_pair:
                    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING, timeout=1)
                    context.bot.send_message(chat_id=user_id, text=share_profile_not_connected_error())
                else:
                    partner_id = self.chat_pair.get(user_id)
                    if username is not None:
                        context.bot.send_message(chat_id=user_id, text=f"Profile Shared")
                        context.bot.send_message(chat_id=partner_id, text=f"@{username}")
                    else:
                        context.bot.send_message(chat_id=user_id, text=f"Error: Username not found")
            except telegram.error.Unauthorized:
                self.end_conversation(update, context)

    def broadcast_message(self, update, context):
        issuer_id = update.message.from_user.id

        if issuer_id not in ADMIN_USER_IDS:
            context.bot.send_message(chat_id=issuer_id, text=broadcast_access_denied())
            return

        message_to_broadcast = " ".join(context.args)
        if not message_to_broadcast:
            context.bot.send_message(chat_id=issuer_id, text=broadcast_no_message())
            return

        all_user_ids = self.record.get_all_user_ids()
        if not all_user_ids:
            context.bot.send_message(chat_id=issuer_id, text="No users found to broadcast to.")
            return

        success_count = 0
        failure_count = 0
        for user_id_target in all_user_ids: # Renamed user_id to user_id_target to avoid conflict
            if user_id_target == issuer_id:
                continue
            try:
                context.bot.send_message(chat_id=user_id_target, text=message_to_broadcast)
                success_count += 1
                time.sleep(0.1)
            except (telegram.error.Unauthorized, telegram.error.BadRequest) as e:
                failure_count += 1
                print(f"Failed to send broadcast to {user_id_target}: {e}")
            except Exception as e:
                failure_count += 1
                print(f"Unexpected error sending broadcast to {user_id_target}: {e}")

        context.bot.send_message(chat_id=issuer_id, text=broadcast_summary(success_count, failure_count))

    def set_false_name(self, update, context):
        user_id = update.message.from_user.id
        name_parts = context.args
        if not name_parts:
            context.bot.send_message(chat_id=user_id, text=set_false_name_usage())
            return

        false_name_to_set = " ".join(name_parts)
        self.record.update(user_id, {"false_name": false_name_to_set})
        context.bot.send_message(chat_id=user_id, text=false_name_set(false_name_to_set))

    def clear_false_name(self, update, context):
        user_id = update.message.from_user.id
        self.record.update(user_id, {"false_name": None})
        context.bot.send_message(chat_id=user_id, text=false_name_cleared())

    def manage_false_name_command(self, update, context):
        user_id = update.message.from_user.id
        data = self.record.search(user_id)
        current_false_name = data.get('false_name')
        context.bot.send_message(chat_id=user_id, text=manage_false_name_prompt(current_false_name), parse_mode='Markdown')

    def command_handler(self):
        updater = Updater(self.bot_key, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self.start, run_async=True))
        dp.add_handler(CommandHandler("help", self.help, run_async=True))
        dp.add_handler(CommandHandler("settings", self.settings, run_async=True))
        dp.add_handler(CommandHandler("next", self.find_partner, run_async=True))
        dp.add_handler(CommandHandler("stop", self.end_conversation, run_async=True))
        dp.add_handler(CommandHandler("sharelink", self.sharelink, run_async=True))
        dp.add_handler(CommandHandler("broadcast", self.broadcast_message, run_async=True))
        # Add false name command handlers here
        dp.add_handler(CommandHandler("myname", self.manage_false_name_command, run_async=True))
        dp.add_handler(CommandHandler("setname", self.set_false_name, run_async=True))
        dp.add_handler(CommandHandler("clearname", self.clear_false_name, run_async=True))

        dp.add_handler(MessageHandler(Filters.all, self.media_handler, run_async=True))
        dp.add_handler(CallbackQueryHandler(self.button_handler, run_async=True))

        updater.start_polling()
        updater.idle()

if __name__ == '__main__':
    bot_name = "Bot"
    bot_key = BOT_TOKEN
    print("Starting Anon Bot")
    ChatBot(bot_name, bot_key)
