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

# --- DATABASE FUNCTIONS ---

async def add_filter_db(chat_id, filter_name, content, text, data_type):
    # Gunakan .lower() agar pencarian tidak sensitif huruf besar/kecil
    value = {
        "content": content,
        "text": text,
        "data_type": data_type
    }
    await dB.set_var(chat_id, filter_name.lower(), value, "FILTER")

async def get_filters_list(chat_id):
    all_filters = await dB.all_var(chat_id, "FILTER")
    if not all_filters:
        return []
    return list(all_filters.keys())

async def get_filter(chat_id, filter_name):
    data = await dB.get_var(chat_id, filter_name.lower(), "FILTER")
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
    await dB.remove_var(chat_id, filter_name.lower(), "FILTER")

# --- HANDLERS ---

@app.on_message(filters.command("filter") & admin_filter & filters.group)
@user_admin
async def _filter(client, message):
    chat_id = message.chat.id 
    
    # Validasi input
    if len(message.command) < 2:
        return await message.reply("❌ **Format Salah.**\nGunakannya: `/filter [nama] [balasan]` atau reply ke pesan.")
    
    # Ambil nama filter dan cek apakah ada konten
    filter_name, _ = get_text_reason(message)
    content, text, data_type = await GetFIlterMessage(message)
    
    if not content and not text:
        return await message.reply("❌ **Error:** Saya tidak bisa menemukan konten untuk disimpan.")

    await add_filter_db(chat_id, filter_name, content, text, data_type)
    await message.reply(f"✅ Filter **`{filter_name}`** berhasil disimpan!")


@app.on_message(filters.group & ~filters.bot, group=1) 
async def FilterCheckker(client, message):
    # Ambil teks dari pesan atau caption (jika kirim gambar/file)
    text = message.text or message.caption
    if not text or text.startswith(("/", "!", ".")):
        return

    chat_id = message.chat.id
    ALL_FILTERS = await get_filters_list(chat_id)
    
    if not ALL_FILTERS:
        return

    for name in ALL_FILTERS:
        # Regex \b memastikan kata kunci berdiri sendiri (bukan bagian dari kata lain)
        # Contoh: filter 'halo' tidak akan terpicu oleh kata 'haloha'
        pattern = rf"\b{re.escape(name)}\b"
        
        if re.search(pattern, text, flags=re.IGNORECASE):
            _, content, f_text, data_type = await get_filter(chat_id, name)
            
            if not content and not f_text:
                continue

            await SendFilterMessage(
                message=message,
                filter_name=name,
                content=content,
                text=f_text,
                data_type=data_type
            )
            break # Hentikan agar tidak memicu filter lain dalam satu pesan


@app.on_message(filters.command('filters') & filters.group)
async def _filters(client, message):
    chat_id = message.chat.id
    chat_title = message.chat.title 
    
    FILTERS = await get_filters_list(chat_id)
    if not FILTERS:
        return await message.reply(f"❌ Tidak ada filter aktif di **{chat_title}**.")

    filters_list = f"📂 **Filter Aktif di {chat_title}:**\n"
    for filter_ in sorted(FILTERS):
        filters_list += f"• `{filter_}`\n"
    
    await message.reply(filters_list)


@app.on_message(filters.command('stopfilter') & admin_filter & filters.group)
@user_admin
async def stop(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ Gunakan: `/stopfilter [nama_filter]`")
    
    chat_id = message.chat.id
    filter_name = message.command[1].lower()
    
    if filter_name not in await get_filters_list(chat_id):
        return await message.reply("❌ Filter tersebut tidak ditemukan.")
    
    await stop_db(chat_id, filter_name)
    await message.reply(f"🗑️ Filter `{filter_name}` telah dihapus.")


@app.on_message(filters.command('stopall') & admin_filter & filters.group)
async def stopall(client, message):
    chat_id = message.chat.id
    user = await client.get_chat_member(chat_id, message.from_user.id)
    
    if user.status != ChatMemberStatus.OWNER:
        return await message.reply("⚠️ Hanya **Pemilik Grup** yang bisa menghapus semua filter.") 

    KEYBOARD = InlineKeyboardMarkup([
        [InlineKeyboardButton('Hapus Semua', callback_data='custfilters_stopall')],
        [InlineKeyboardButton('Batal', callback_data='custfilters_cancel')]
    ])

    await message.reply(
        f"⚠️ **Konfirmasi:** Apakah Anda yakin ingin menghapus **SEMUA** filter di {message.chat.title}?",
        reply_markup=KEYBOARD
    )


@app.on_callback_query(filters.regex("^custfilters_"))
async def stopall_callback(client, callback_query: CallbackQuery):  
    chat_id = callback_query.message.chat.id 
    data = callback_query.data.split('_')[1]  
    user = await client.get_chat_member(chat_id, callback_query.from_user.id)

    if user.status != ChatMemberStatus.OWNER:
        return await callback_query.answer("Hanya pemilik grup yang bisa menekan tombol ini!", show_alert=True) 
    
    if data == 'stopall':
        await stop_all_db(chat_id)
        await callback_query.edit_message_text("✅ Semua filter chat telah dibersihkan.")
    elif data == 'cancel':
        await callback_query.edit_message_text("❌ Aksi dibatalkan.")

__MODULE__ = "Filters"
__HELP__ = """
📬 **Fitur Filter**

• `/filter [keyword]` - Simpan filter (balas ke pesan/media).
• `/filters` - Lihat daftar filter aktif.
• `/stopfilter [keyword]` - Hapus filter tertentu.
• `/stopall` - Hapus semua filter (Hanya Owner).
"""
