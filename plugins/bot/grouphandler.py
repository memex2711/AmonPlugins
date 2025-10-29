import time
from asyncio import sleep

from pyrogram import filters, enums
from pyrogram.enums import ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from AmonMusic import app, LOGGER
from AmonMusic.utils.admin_filters import admin_filter



async def get_photo(chat_id: int):
    try:
        chat = await app.get_chat(chat_id)
        if chat.photo:
            file_path = await app.download_media(chat.photo.big_file_id)
            return file_path
    except Exception as e:
        LOGGER("AmonMusic").warning(f"Failed to get photo for {chat_id}: {e}")
    return None  

@app.on_message(~filters.private & filters.command(["groupdata"]), group=2)
async def instatus(app, message):
    start_time = time.perf_counter()
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    count = await app.get_chat_members_count(message.chat.id)

    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        sent_message = await message.reply_text("🚫 ONLY ADMINS CAN USE THIS!")
        await sleep(5)
        return await sent_message.delete()

    sent_message = await message.reply_text("🔍 Gathering group stats...")

    stats = {
        "banned": 0,
        "deleted": 0,
        "bots": 0,
        "premium": 0,
        "restricted": 0,
        "fake": 0,
        "admins": 0,
        "uncached": 0,
    }

    async for member in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.BANNED):
        stats["banned"] += 1

    async for member in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        stats["admins"] += 1

    async for member in app.get_chat_members(message.chat.id):
        u = member.user
        if u.is_deleted:
            stats["deleted"] += 1
        elif u.is_bot:
            stats["bots"] += 1
        elif u.is_premium:
            stats["premium"] += 1
        elif getattr(member, "status", None) == enums.ChatMemberStatus.RESTRICTED:
            stats["restricted"] += 1
        elif u.username is None and u.first_name is not None and len(u.first_name) <= 2:
            stats["fake"] += 1
        else:
            stats["uncached"] += 1

    end_time = time.perf_counter()
    timelog = "{:.2f}".format(end_time - start_time)

    caption = f"""
<blockquote expandable>**▰▰▰ GROUP DATA REPORT ▰▰▰
➲ NAME : {message.chat.title} ✅
➲ TOTAL MEMBERS : {count} 🫂
➖➖➖➖➖➖➖
➲ ADMINS : {stats['admins']} 👮‍♂️
➲ BOTS : {stats['bots']} 🤖
➲ ZOMBIES : {stats['deleted']} 🧟
➲ BANNED : {stats['banned']} 🚫
➲ PREMIUM USERS : {stats['premium']} 🎁
➲ RESTRICTED USERS : {stats['restricted']} 🔒
➲ FAKE USERS : {stats['fake']} 👻
➖➖➖➖➖➖➖
⏱ TIME TAKEN : {timelog} sec**</blockquote>
"""

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 CLOSE", callback_data=f"close_groupdata_{message.chat.id}")]
    ])

    await sent_message.delete()

    photo = await get_photo(message.chat.id)

    if photo:
        await message.reply_photo(photo=photo, caption=caption, reply_markup=buttons)
    else:
        await message.reply_text(text=caption, reply_markup=buttons)


@app.on_callback_query(filters.regex(r"^close_groupdata_"))
async def close_groupdata_cb(_, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        await query.answer("❌ Failed to delete message", show_alert=True)



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
• /settitle : Sets the title of the group.
• /setdescription - Sets the description of the group.
• /setphoto - Sets the group photo.
• /removephoto - Removes the group photo
• /groupdata - To get group info.

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""        