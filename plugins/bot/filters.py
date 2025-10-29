import re
from AmonMusic import app

from AmonMusic.database import dB 

from config import BOT_USERNAME
from AmonMusic.utils.admin_filters import admin_filter
from AmonMusic.utils.filters_func import GetFIlterMessage, get_text_reason, SendFilterMessage
from AmonMusic.utils.permissions import user_admin
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup


async def add_filter_db(chat_id, filter_name, content, text, data_type):
    value = {
        "content": content,
        "text": text,
        "data_type": data_type
    }
    await dB.set_var(chat_id, filter_name, value, "FILTER")

async def get_filters_list(chat_id):
    all_filters = await dB.all_var(chat_id, "FILTER")
    if not all_filters:
        return []
    return list(all_filters.keys())

async def get_filter(chat_id, filter_name):
    data = await dB.get_var(chat_id, filter_name, "FILTER")
    if data and isinstance(data, dict):
        return (
            filter_name, 
            data.get("content"), 
            data.get("text"), 
            data.get("data_type")
        )
    return (None, None, None, None)

async def stop_all_db(chat_id):
    all_filters = await dB.all_var(chat_id, "FILTER")
    if all_filters:
        for filter_name in all_filters.keys():
            await dB.remove_var(chat_id, filter_name, "FILTER")

async def stop_db(chat_id, filter_name):
    await dB.remove_var(chat_id, filter_name, "FILTER")



@app.on_message(filters.command("filter") & admin_filter)
@user_admin
async def _filter(client, message):
    
    chat_id = message.chat.id 
    if (
        message.reply_to_message
        and not len(message.command) == 2
    ):
        await message.reply("You need to give the filter a name!")  
        return 
    
    filter_name, filter_reason = get_text_reason(message)
    if (
        message.reply_to_message
        and not len(message.command) >=2
    ):
        await message.reply("You need to give the filter some content!")
        return

    content, text, data_type = await GetFIlterMessage(message)
    await add_filter_db(chat_id, filter_name=filter_name, content=content, text=text, data_type=data_type)
    await message.reply(
        f"Saved filter '`{filter_name}`'."
    )


@app.on_message(~filters.bot & filters.group, group=1) 
async def FilterCheckker(client, message):
    if not message.text:
        return
    text = message.text
    chat_id = message.chat.id
    
    ALL_FILTERS = await get_filters_list(chat_id)
    if len(ALL_FILTERS) == 0:
        return

    for filter_ in ALL_FILTERS:
        
        if (
            message.command
            and message.command[0] == 'filter'
            and len(message.command) >= 2
            and message.command[1] ==  filter_
        ):
            return
            
        pattern = r"( |^|[^\w])" + re.escape(filter_) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            filter_name_db, content, text, data_type = await get_filter(chat_id, filter_)
            
            if not content:
                continue

            await SendFilterMessage(
                message=message,
                filter_name=filter_,
                content=content,
                text=text,
                data_type=data_type
            )
            return

@app.on_message(filters.command('filters') & filters.group)
async def _filters(client, message):
    chat_id = message.chat.id
    chat_title = message.chat.title 
    if message.chat.type == 'private':
        chat_title = 'local'
    FILTERS = await get_filters_list(chat_id)
    
    if len(FILTERS) == 0:
        await message.reply(
            f'No filters in {chat_title}.'
        )
        return

    filters_list = f'List of filters in {chat_title}:\n'
    
    for filter_ in FILTERS:
        filters_list += f'- `{filter_}`\n'
    
    await message.reply(
        filters_list
    )


@app.on_message(filters.command('stopall') & admin_filter)
async def stopall(client, message):
    chat_id = message.chat.id
    chat_title = message.chat.title 
    user = await client.get_chat_member(chat_id,message.from_user.id)
    if not user.status == ChatMemberStatus.OWNER :
        return await message.reply_text("Only Owner Can Use This!!") 

    KEYBOARD = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='Delete all filters', callback_data='custfilters_stopall')],
        [InlineKeyboardButton(text='Cancel', callback_data='custfilters_cancel')]]
    )

    await message.reply(
        text=(f'Are you sure you want to stop **ALL** filters in {chat_title}? This action is irreversible.'),
        reply_markup=KEYBOARD
    )


@app.on_callback_query(filters.regex("^custfilters_"))
async def stopall_callback(client, callback_query: CallbackQuery):  
    chat_id = callback_query.message.chat.id 
    query_data = callback_query.data.split('_')[1]  

    user = await client.get_chat_member(chat_id, callback_query.from_user.id)

    if not user.status == ChatMemberStatus.OWNER :
        return await callback_query.answer("Only Owner Can Use This!!") 
    
    if query_data == 'stopall':
        await stop_all_db(chat_id)
        await callback_query.edit_message_text(text="I've deleted all chat filters.")
    
    elif query_data == 'cancel':
        await callback_query.edit_message_text(text='Cancelled.')



@app.on_message(filters.command('stopfilter') & admin_filter)
@user_admin
async def stop(client, message):
    chat_id = message.chat.id
    if not (len(message.command) >= 2):
        await message.reply('Use Help To Know The Command Usage')
        return
    
    filter_name = message.command[1]
    if (filter_name not in await get_filters_list(chat_id)):
        await message.reply("You haven't saved any filters on this word yet!")
        return
    
    await stop_db(chat_id, filter_name)
    await message.reply(f"I've stopped `{filter_name}`.")
    
    
    
__MODULE__ = "Filters"
__HELP__ = """
<blockquote expandable>📬 <b>Filters Commands</b>

• <b>/filter</b> (keyword) (reply message) – Save a filter.
• <b>/filters</b> – View all active filters.
• <b>/stopfilter</b> (name) – Remove a specific filter.
• <b>/stopall</b> – Delete all filters in this chat.

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""    