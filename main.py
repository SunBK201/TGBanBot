import os
from typing import Optional, Tuple

from telegram import Chat, ChatMember, ChatMemberUpdated, ChatPermissions, Update
from telegram.constants import ParseMode
from telegram.ext import (Application, ChatMemberHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)


async def show_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(str(uid) for uid in context.bot_data.setdefault("user_ids", set()))
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    channel_ids = ", ".join(str(cid) for cid in context.bot_data.setdefault("channel_ids", set()))
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    if update.effective_message is None:
        return
    await update.effective_message.reply_text(text)


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def guarddog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member is None:
        return
    result = extract_status_change(update.chat_member)
    if result is None:
        return
    was_member, is_member = result
    if was_member and not is_member:
        return
    member_name = update.chat_member.new_chat_member.user.name
    chat_id = update.chat_member.chat.id
    user = update.chat_member.new_chat_member.user
    user_id = user.id
    user_is_premium = user.is_premium
    print(f'chat_id: {chat_id}, user_id: {user_id}, member_name: {member_name}, user_is_premium: {user_is_premium}')
    if not was_member and is_member:
        if user_is_premium:
            await context.bot.restrict_chat_member("@crack_campus_network", user_id, ChatPermissions(
                can_send_messages=False,
            ))
            text = f'Premium user not aproved, {member_name}'
        else:
            # await context.bot.approve_chat_join_request(chat_id, user_id)
            text = f'User approved, {member_name}'
        await context.bot.send_message(chat_id=chat_id, text=text)


def main():
    token = os.getenv("TGBANBOT_TOKEN")
    if token is None:
        raise ValueError("Please provide a valid token in the TGBANBOT_TOKEN environment variable")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("show_chats", show_chats))
    application.add_handler(ChatMemberHandler(guarddog, ChatMemberHandler.CHAT_MEMBER))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
