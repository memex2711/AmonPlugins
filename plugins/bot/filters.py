import re
import json
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from AmonMusic import app
from AmonMusic.database import dB 
from AmonMusic.utils.admin_filters import admin_filter
from AmonMusic.utils.filters_func import GetFIlterMessage, get_text_reason, SendFilterMessage
from AmonMusic.utils.permissions import user_admin

# Kategori di tabel variabel
TAG = "FILTER"

@app.on_message(filters.command("filter") & admin_filter & filters.group)
@user_admin
async def add_new_filter(client, message):
    chat_id = message.chat.id 
    
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("❌ **Gagal!** Berikan nama filternya.\nContoh: `/filter halo halo juga` atau reply ke media.")

    # Ambil nama filter
    filter_name, _ = get_text_reason(message)
    if not filter_name:
        return await message.reply("❌ Nama filter tidak valid.")
    
    name = filter_name.lower().strip()
    
    # Ambil konten (teks/media)
    content, text, data_type = await GetFIlterMessage(message)
    
    if not data_type:
        return await message.reply("❌ Konten tidak ditemukan. Sertakan teks atau reply ke media.")

    # Simpan sebagai dict
    value = {
        "content": content,
        "text": text,
        "data_type": data_type
    }
    
    await dB.set_var(chat_id, name, value, TAG)
    await message.reply(f"✅ Filter **`{name}`** berhasil disimpan!")


@app.on_message(filters.group & ~filters.bot, group=10) 
async def check_filters_in_message(client, message):
    text = message.text or message.caption
    if not text or text.startswith(("/", "!", ".")):
        return

    chat_id = message.chat.id
    all_filters = await dB.all_var(chat_id, TAG)
    
    # Validasi jika data kosong atau bukan dictionary
    if not all_filters or not isinstance(all_filters, dict):
        return

    for name, data in all_filters.items():
        if not data: continue
        
        # Parsing jika data tersimpan sebagai string JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                continue
        
        # Regex Case Insensitive untuk kata utuh
        pattern = rf"(?i)\b{re.escape(str(name))}\b"
        
        if re.search(pattern, text):
            await SendFilterMessage(
                message=message,
                filter_name=name,
                content=data.get("content"),
                text=data.get("text"),
                data_type=data.get("data_type")
            )
            return # Berhenti setelah satu filter ketemu


@app.on_message(filters.command('filters') & filters.group)
async def list_active_filters(client, message):
    chat_id = message.chat.id
    all_f = await dB.all_var(chat_id, TAG)
    
    if not all_f or not isinstance(all_f, dict) or len(all_f) == 0:
        return await message.reply(f"❌ Tidak ada filter aktif di **{message.chat.title}**.")

    out = f"📂 **Daftar Filter - {message.chat.title}:**\n\n"
    for name in sorted(all_f.keys()):
        out += f"• `{name}`\n"
    
    await message.reply(out)


@app.on_message(filters.command('stopfilter') & admin_filter & filters.group)
@user_admin
async def delete_filter(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ Gunaka: `/stopfilter [nama_filter]`")
    
    chat_id = message.chat.id
    name = message.command[1].lower().strip()
    
    all_f = await dB.all_var(chat_id, TAG)
    if not all_f or name not in all_f:
        return await message.reply(f"❌ Filter `{name}` tidak ditemukan.")
    
    # Memanggil remove_var yang sudah diperbaiki dengan json_remove
    await dB.remove_var(chat_id, name, TAG)
    await message.reply(f"🗑️ Filter `{name}` telah dihapus.")


@app.on_message(filters.command('stopall') & admin_filter & filters.group)
async def confirm_stop_all(client, message):
    chat_id = message.chat.id
    # Cek izin: Hanya Owner atau Admin dengan hak tertentu
    user = await client.get_chat_member(chat_id, message.from_user.id)
    if user.status != ChatMemberStatus.OWNER:
        return await message.reply("⚠️ Hanya **Pemilik Grup** yang bisa menghapus semua filter.") 

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Ya, Hapus Semua', callback_data='sf_stopall')],
        [InlineKeyboardButton('❌ Batal', callback_data='sf_cancel')]
    ])

    await message.reply(
        f"❓ Hapus **SEMUA** filter di {message.chat.title}?\nTindakan ini tidak bisa dibatalkan.",
        reply_markup=kb
    )


@app.on_callback_query(filters.regex("^sf_"))
async def stopall_callback_handler(client, cb: CallbackQuery):  
    chat_id = cb.message.chat.id 
    cmd = cb.data.split('_')[1]  
    
    user = await client.get_chat_member(chat_id, cb.from_user.id)
    if user.status != ChatMemberStatus.OWNER:
        return await cb.answer("Hanya Owner yang bisa melakukan ini!", show_alert=True) 
    
    if cmd == 'stopall':
        # Gunakan fungsi clear_vars_category untuk menghapus seluruh objek FILTER
        await dB.clear_vars_category(chat_id, TAG)
        await cb.edit_message_text("✅ Semua filter chat berhasil dibersihkan total!")
    else:
        await cb.edit_message_text("❌ Aksi penghapusan dibatalkan.")

__MODULE__ = "Filters"
__HELP__ = """
📬 **Fitur Filter**

• `/filter [keyword]` - Simpan filter.
• `/filters` - Lihat daftar filter.
• `/stopfilter [keyword]` - Hapus satu filter.
• `/stopall` - Hapus semua filter (Owner Only).
"""
