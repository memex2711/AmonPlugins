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

TAG = "FILTER"

@app.on_message(filters.command("filter") & admin_filter & filters.group)
@user_admin
async def add_new_filter(client, message):
    chat_id = message.chat.id 
    
    # 1. Ambil nama filter dan sisa teks manual
    filter_name, manual_text = get_text_reason(message)
    
    if not filter_name:
        return await message.reply("❌ **Gagal!** Berikan nama filternya.\nContoh: `/filter halo teks_balasan` atau reply media.")

    name = filter_name.lower().strip()
    
    # 2. Ambil konten (Reply vs Manual)
    if message.reply_to_message:
        # Jika reply, ambil media/teks dari pesan yang di-reply
        content, text, data_type = await GetFIlterMessage(message.reply_to_message)
        # Jika admin menulis teks tambahan di /filter, gunakan teks itu daripada teks reply
        if manual_text:
            text = manual_text
    else:
        # Jika tidak reply, anggap teks manual sebagai konten
        if not manual_text:
            return await message.reply("❌ Masukkan pesan balasan untuk filter tersebut.")
        content = None
        text = manual_text
        data_type = 1 # TEXT

    if not data_type:
        return await message.reply("❌ Konten tidak dikenali atau tidak didukung.")

    # 3. Simpan sebagai dict
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
    
    if not all_filters or not isinstance(all_filters, dict):
        return

    for name, data in all_filters.items():
        if not data: continue
        
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                continue
        
        # Pengecekan kata utuh (Exact Match)
        pattern = rf"(?i)\b{re.escape(str(name))}\b"
        
        if re.search(pattern, text):
            await SendFilterMessage(
                message=message,
                filter_name=name,
                content=data.get("content"),
                text=data.get("text"),
                data_type=data.get("data_type")
            )
            return


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
        return await message.reply("❌ Gunakan: `/stopfilter [nama_filter]`")
    
    chat_id = message.chat.id
    # Ambil nama filter menggunakan helper agar support tanda kutip jika perlu
    name, _ = get_text_reason(message)
    if not name:
        name = message.command[1].lower().strip()
    
    all_f = await dB.all_var(chat_id, TAG)
    if not all_f or name not in all_f:
        return await message.reply(f"❌ Filter `{name}` tidak ditemukan.")
    
    await dB.remove_var(chat_id, name, TAG)
    await message.reply(f"🗑️ Filter `{name}` telah dihapus.")


@app.on_message(filters.command('stopall') & admin_filter & filters.group)
async def confirm_stop_all(client, message):
    chat_id = message.chat.id
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
        await dB.clear_vars_category(chat_id, TAG)
        await cb.edit_message_text("✅ Semua filter chat berhasil dibersihkan total!")
    else:
        await cb.edit_message_text("❌ Aksi penghapusan dibatalkan.")

__MODULE__ = "Filters"
__HELP__ = """
📬 **Fitur Filter**

• `/filter [keyword] [pesan]` - Simpan filter teks.
• `/filter [keyword]` (Reply media) - Simpan filter media.
• `/filters` - Lihat daftar filter.
• `/stopfilter [keyword]` - Hapus satu filter.
• `/stopall` - Hapus semua filter (Owner Only).
"""
