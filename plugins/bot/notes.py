import re
import json
from AmonMusic import app
from config import BOT_USERNAME
from pyrogram import filters
from AmonMusic.database import dB 
from AmonMusic.utils.admin_filters import admin_filter
from AmonMusic.utils.notes_func import GetNoteMessage, SendNoteMessage, privateNote_and_admin_checker
from AmonMusic.utils.permissions import user_admin
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from pyrogram.enums import ChatMemberStatus

# Konfigurasi Kategori Database
TAG = "NOTE"
PRIVATE_NOTE_KEY = "PRIVATE_NOTES_STATUS"

# --- DATABASE HELPERS ---

async def SaveNote(chat_id, note_name, content, text, data_type):
    note_name = note_name.lower().strip()
    value = {
        "content": content,
        "text": text,
        "data_type": data_type
    }
    await dB.set_var(chat_id, note_name, value, TAG)

async def GetNote(chat_id, note_name):
    note_name = note_name.lower().strip()
    data = await dB.get_var(chat_id, note_name, TAG)
    if data:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return None, None, None
        return data.get("content"), data.get("text"), data.get("data_type")
    return None, None, None

async def isNoteExist(chat_id, note_name):
    note_name = note_name.lower().strip()
    data = await dB.get_var(chat_id, note_name, TAG)
    return bool(data)

async def NoteList(chat_id):
    all_notes = await dB.all_var(chat_id, TAG)
    if not all_notes or not isinstance(all_notes, dict):
        return []
    return [name for name in all_notes.keys() if name != PRIVATE_NOTE_KEY]

# --- COMMAND HANDLERS ---

@app.on_message(filters.command("save") & admin_filter & filters.group)
@user_admin
async def _save(client, message):
    chat_id = message.chat.id
    
    if len(message.command) < 2:
        return await message.reply_text("❌ **Gagal!** Berikan nama catatan.\nContoh: `/save tes` (sambil reply).")

    note_name = message.command[1].lower().strip()
    
    # PERBAIKAN: Ambil teks manual dengan aman (args[2] jika ada)
    args = message.text.split(None, 2) if message.text else message.caption.split(None, 2)
    manual_text = args[2] if len(args) >= 3 else None

    # 1. Logika Pengambilan Konten
    if message.reply_to_message:
        # Ambil konten dari pesan yang di-reply
        content, text, data_type = GetNoteMessage(message.reply_to_message)
        # Jika admin mengetik teks setelah nama note, gunakan itu sebagai caption baru
        if manual_text:
            text = manual_text
    else:
        # Jika tidak reply, teks manual wajib ada sebagai isi note
        if not manual_text:
            return await message.reply_text("❌ Berikan isi teks atau reply ke media untuk menyimpan note.")
        content = None
        text = manual_text
        data_type = 1 # Type TEXT (NoteTypeMap.text.value)

    if not data_type:
        return await message.reply_text("❌ Konten pesan tidak didukung atau kosong.")

    await SaveNote(chat_id, note_name, content, text, data_type)
    await message.reply_text(f"✅ Berhasil menyimpan catatan: `{note_name}`")

@app.on_message(filters.command("get") & filters.group)
async def _getnote(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Berikan nama catatan.")
    
    note_name = message.command[1]
    await send_note(message, note_name)

@app.on_message(filters.regex(pattern=(r"^#[^\s]+")) & filters.group)
async def regex_get_note(client, message):
    if not message.text:
        return
    # Ambil kata pertama, buang '#', ubah kecil
    note_name = message.text.split()[0][1:].lower()
    if await isNoteExist(message.chat.id, note_name):
        await send_note(message, note_name)

@app.on_message(filters.command("clear") & admin_filter & filters.group)
@user_admin
async def Clear_Note(client, message):
    chat_id = message.chat.id 
    if len(message.command) < 2:
        return await message.reply_text("❌ Berikan nama catatan yang ingin dihapus.")
    
    # Ambil sisa teks setelah command
    raw_input = message.text.split(None, 1)[1]
    note_names = [n.strip().lower() for n in raw_input.split(',')]

    deleted, failed = [], []
    for name in note_names:
        if await isNoteExist(chat_id, name):
            await dB.remove_var(chat_id, name, TAG)
            deleted.append(name)
        else:
            failed.append(name)

    res = ""
    if deleted: res += f"✅ Berhasil menghapus: `{', '.join(deleted)}`"
    if failed: res += f"\n❌ Tidak ditemukan: `{', '.join(failed)}`"
    await message.reply_text(res)

@app.on_message(filters.command("clearall") & admin_filter & filters.group)
async def confirm_clear_all_notes(client, message):
    chat_id = message.chat.id
    user = await client.get_chat_member(chat_id, message.from_user.id)
    if user.status != ChatMemberStatus.OWNER:
        return await message.reply("⚠️ Hanya **Pemilik Grup** yang bisa menghapus semua catatan.") 

    notes = await NoteList(chat_id)
    if not notes:
        return await message.reply(f"❌ Tidak ada catatan di **{message.chat.title}**.")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Ya, Hapus Semua', callback_data='sn_clearall')],
        [InlineKeyboardButton('❌ Batal', callback_data='sn_cancel')]
    ])
    await message.reply(f"❓ Hapus **SEMUA** catatan ({len(notes)}) di {message.chat.title}?", reply_markup=kb)

@app.on_callback_query(filters.regex("^sn_"))
async def clearall_notes_callback(client, cb: CallbackQuery):  
    chat_id = cb.message.chat.id 
    cmd = cb.data.split('_')[1]  
    user = await client.get_chat_member(chat_id, cb.from_user.id)
    
    if user.status != ChatMemberStatus.OWNER:
        return await cb.answer("Hanya Owner yang bisa melakukan ini!", show_alert=True) 
    
    if cmd == 'clearall':
        await dB.clear_vars_category(chat_id, TAG)
        await cb.edit_message_text(f"✅ Semua catatan di **{cb.message.chat.title}** telah dihapus.")
    else:
        await cb.edit_message_text("❌ Aksi penghapusan dibatalkan.")

@app.on_message(filters.command(['notes', 'saved']) & filters.group)
async def Notes(client, message):
    notes = await NoteList(message.chat.id)
    if not notes:
        return await message.reply_text(f"❌ Tidak ada catatan di **{message.chat.title}**.")

    out = f"📂 **Daftar Catatan - {message.chat.title}:**\n"
    for n in sorted(notes):
        out += f" • `#{n}`\n"
    await message.reply_text(out + "\n💡 Panggil dengan `#nama_catatan`")

# --- CORE LOGIC SEND NOTE ---

async def send_note(message: Message, note_name: str):
    chat_id = message.chat.id
    content, text, data_type = await GetNote(chat_id, note_name)
    
    if not data_type:
        return

    # Pengecekan izin & status private
    p_note, allow = await privateNote_and_admin_checker(message, text or "")
    if not allow: return

    is_p_global = await dB.get_var(chat_id, PRIVATE_NOTE_KEY, TAG)
    should_private = p_note if p_note is not None else is_p_global

    if should_private:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("Klik untuk Lihat", url=f"t.me/{BOT_USERNAME}?start=note_{chat_id}_{note_name}")
        ]])
        await message.reply_text(f"📩 Catatan `{note_name}` dikirim ke Private Chat.", reply_markup=kb)
    else:
        await SendNoteMessage(message, note_name, content, text, data_type, from_chat_id=None)

@app.on_message(filters.command("start") & filters.private)
async def start_pm_notes(client, message):
    if len(message.command) > 1 and message.command[1].startswith("note_"):
        parts = message.command[1].split("_")
        if len(parts) == 3:
            target_chat = int(parts[1])
            note_name = parts[2]
            content, text, data_type = await GetNote(target_chat, note_name)
            if data_type:
                return await SendNoteMessage(message, note_name, content, text, data_type, from_chat_id=target_chat)
    
    await message.reply_text("Halo! Saya bot asisten grup Anda.")

__MODULE__ = "Notes"
__HELP__ = """
📋 **Fitur Catatan (Notes)**

• `/save [nama]` - Simpan catatan (bisa reply media).
• `/get [nama]` - Ambil catatan.
• `#nama` - Shortcut panggil catatan.
• `/notes` - Lihat daftar catatan.
• `/clear [nama]` - Hapus catatan tertentu.
• `/clearall` - Hapus semua catatan (Owner).
"""
