from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from AmonMusic import app
from AmonMusic.utils.admin_filters import admin_filter


def is_group(message: Message) -> bool:
    return message.chat.type not in [ChatType.PRIVATE, ChatType.BOT]

async def has_permission(user_id: int, chat_id: int, permission: str) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return getattr(member.privileges, permission, False)
    except Exception:
        return False


@app.on_message(filters.command("pin") & admin_filter)
async def pin(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs!**")

    if not message.reply_to_message:
        return await message.reply_text("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴘɪɴ ɪᴛ!**")

    if not await has_permission(message.from_user.id, message.chat.id, "can_pin_messages"):
        return await message.reply_text("**ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴘɪɴ ᴍᴇssᴀɢᴇs.**")

    try:
        await message.reply_to_message.pin()
        await message.reply_text(
            f"**sᴜᴄᴄᴇssғᴜʟʟʏ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ!**\n\n**ᴄʜᴀᴛ:** {message.chat.title}\n**ᴀᴅᴍɪɴ:** {message.from_user.mention}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📝 ᴠɪᴇᴡ ᴍᴇssᴀɢᴇ", url=message.reply_to_message.link)]]
            )
        )
    except Exception as e:
        await message.reply_text(f"**ғᴀɪʟᴇᴅ ᴛᴏ ᴘɪɴ ᴍᴇssᴀɢᴇ:**\n`{str(e)}`")


@app.on_message(filters.command("unpin") & admin_filter)
async def unpin(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs!**")

    if not message.reply_to_message:
        return await message.reply_text("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴜɴᴘɪɴ ɪᴛ!**")

    if not await has_permission(message.from_user.id, message.chat.id, "can_pin_messages"):
        return await message.reply_text("**ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴜɴᴘɪɴ ᴍᴇssᴀɢᴇs.**")

    try:
        await message.reply_to_message.unpin()
        await message.reply_text(
            f"**sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ!**\n\n**ᴄʜᴀᴛ:** {message.chat.title}\n**ᴀᴅᴍɪɴ:** {message.from_user.mention}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📝 ᴠɪᴇᴡ ᴍᴇssᴀɢᴇ", url=message.reply_to_message.link)]]
            )
        )
    except Exception as e:
        await message.reply_text(f"**ғᴀɪʟᴇᴅ ᴛᴏ ᴜɴᴘɪɴ ᴍᴇssᴀɢᴇ:**\n`{str(e)}`")
        

@app.on_message(filters.command("setphoto") & admin_filter)
async def set_photo(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs!**")
    if not message.reply_to_message:
        return await message.reply_text("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ.**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**ʏᴏᴜ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɪɴғᴏ.**")
    try:
        photo = await message.reply_to_message.download()
        await message.chat.set_photo(photo=photo)
        await message.reply_text(f"**ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**\nʙʏ {message.from_user.mention}")
    except Exception as e:
        await message.reply_text(f"**ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴛ ᴘʜᴏᴛᴏ:**\n`{str(e)}`")


@app.on_message(filters.command("removephoto") & admin_filter)
async def remove_photo(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs!**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**ʏᴏᴜ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɪɴғᴏ.**")
    try:
        await app.delete_chat_photo(message.chat.id)
        await message.reply_text(f"**ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ ʀᴇᴍᴏᴠᴇᴅ!**\nʙʏ {message.from_user.mention}")
    except Exception as e:
        await message.reply_text(f"**ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴘʜᴏᴛᴏ:**\n`{str(e)}`")


@app.on_message(filters.command("settitle") & admin_filter)
async def set_title(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs!**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**ʏᴏᴜ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɪɴғᴏ.**")

    title = message.text.split(None, 1)[1] if len(message.command) > 1 else (message.reply_to_message.text if message.reply_to_message else None)
    if not title:
        return await message.reply_text("**ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴇᴡ ᴛɪᴛʟᴇ.**")

    try:
        await message.chat.set_title(title)
        await message.reply_text(f"**ɢʀᴏᴜᴘ ɴᴀᴍᴇ ᴄʜᴀɴɢᴇᴅ ᴛᴏ:** {title}\nʙʏ {message.from_user.mention}")
    except Exception as e:
        await message.reply_text(f"**ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴛ ᴛɪᴛʟᴇ:**\n`{str(e)}`")


@app.on_message(filters.command("setdiscription") & admin_filter)
async def set_description(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs!**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**ʏᴏᴜ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɪɴғᴏ.**")

    desc = message.text.split(None, 1)[1] if len(message.command) > 1 else (message.reply_to_message.text if message.reply_to_message else None)
    if not desc:
        return await message.reply_text("**ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴇᴡ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ.**")

    try:
        await message.chat.set_description(desc)
        await message.reply_text(f"**ɢʀᴏᴜᴘ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!**\nʙʏ {message.from_user.mention}")
    except Exception as e:
        await message.reply_text(f"**ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴛ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:**\n`{str(e)}`")


__MODULE__ = "Group"
__HELP__ = """
<blockquote expandable>📋 <b>Groups Menage Commands</b>

• /pin - Pins a message in the group.
• /unpin - Unpins the currently pinned message.
• /staff - Displays the list of staff members.
• /bots - Displays the list of bots in the group.
• /react - To give random reaction.
• /settitle : Sets the title of the group.
• /setdescription - Sets the description of the group.
• /setphoto - Sets the group photo.
• /removephoto - Removes the group photo
• /zombies - Removes deleted accounts from the group.
• /groupdata - To get group info.

</blockquote>
"""        