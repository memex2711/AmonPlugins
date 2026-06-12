import pytz
import traceback
import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardMarkup, InlineKeyboardButton
)

from config import BANNED_USERS
from AmonMusic import app
from AmonMusic.database import dB
from AmonMusic.utils.admin_filters import admin_filter


def format_absen_list(data):
    if not data:
        return "**Belum ada yang absen.**"
    return "\n".join([
        f"{i+1}. {u['name']}  ({u['time']})." for i, u in enumerate(data)
    ])


def format_tanggal_indo(dt: datetime) -> str:
    hari = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", 
        "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu",
    }
    # Perbaikan bug typo: "Tuesday" -> "February"
    bulan = {
        "January": "Januari", "February": "Februari", "March": "Maret", "April": "April", 
        "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus",
        "September": "September", "October": "Oktober", "November": "November", "December": "Desember",
    }

    nama_hari = hari[dt.strftime("%A")]
    nama_bulan = bulan[dt.strftime("%B")]
    return f"{nama_hari}, tanggal {dt.day} {nama_bulan} {dt.year}"


@app.on_message(filters.command("mulai") & admin_filter & ~BANNED_USERS)
async def mulai_absen(_, message: Message): 
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_str = format_tanggal_indo(now)
    
    chat_id = message.chat.id
    await dB.set_var(chat_id, "ABSENSI", [])
    data = [] 

    absen_text = f"""**{message.chat.title}**
**Daftar hadir hari** {date_str}.

<blockquote expandable>
{format_absen_list(data)}
</blockquote>

**Waktu dalam timezone WIB (UTC+7).
Yang telah hadir, silakan klik tombol HADIR di bawah ini.**"""
    
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("☑️  Hadir", callback_data="Hadir")]]
    )
    return await message.reply(absen_text, reply_markup=keyboard)


@app.on_message(filters.command("refreshabsen") & admin_filter & ~BANNED_USERS)
async def refresh_absen(_, message: Message): 
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_str = format_tanggal_indo(now)
    chat_id = message.chat.id
    data = await dB.get_var(chat_id, "ABSENSI") or []

    absen_text = f"""**{message.chat.title}**
**Daftar hadir hari** {date_str}.

<blockquote expandable>
{format_absen_list(data)}
</blockquote>

**Waktu dalam timezone WIB (UTC+7).
Yang telah hadir, silakan klik tombol HADIR di bawah ini.**"""
    
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("☑️  Hadir", callback_data="Hadir")]]
    )
    return await message.reply(absen_text, reply_markup=keyboard)


@app.on_message(filters.command("rekap") & admin_filter & ~BANNED_USERS)
async def rekap_absen(_, message: Message):
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_str = format_tanggal_indo(now)
    chat_id = message.chat.id
    
    data = await dB.get_var(chat_id, "ABSENSI")
    
    if data is None:
        return await message.reply("❌ **Tidak ada sesi absensi yang aktif atau data kosong.**")
    if not data:
        return await message.reply("⚠️ **Sesi absensi aktif, tetapi belum ada anggota yang mengisi daftar hadir.**")

    total_hadir = len(data)
    rekap_text = f"""📌 **BACKUP REKAP ABSENSI**
🏢 **Grup:** {message.chat.title}
📅 **Hari/Tanggal:** {date_str}
🔢 **Total Hadir:** {total_hadir} orang

======= **DAFTAR HADIR** =======
{format_absen_list(data)}
==============================

**Silakan salin atau teruskan (forward) pesan ini untuk arsip.**"""

    return await message.reply(rekap_text)


@app.on_message(filters.command("selesai") & admin_filter & ~BANNED_USERS)
async def selesai_absen(_, message: Message): 
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_str = format_tanggal_indo(now)
    chat_id = message.chat.id
    data = await dB.get_var(chat_id, "ABSENSI") or []

    # Hapus data dari database agar sesi selesai
    await dB.remove_var(chat_id, "ABSENSI")

    absen_text = f"""🏁 **SESI ABSENSI DITUTUP**
**{message.chat.title}** - {date_str}

======= **REKAP AKHIR** =======
{format_absen_list(data)}
==============================
Total: {len(data)} orang hadir.

**Sesi absensi telah diakhiri oleh Admin. Data di bot telah dibersihkan. Silakan gunakan `/mulai` kembali di hari berikutnya.**"""
    
    return await message.reply(absen_text)


@app.on_callback_query(filters.regex(r"^Hadir"))
async def hadir_callback(_, callback_query: CallbackQuery): 
    user = callback_query.from_user
    user_id = user.id
    name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name 
    chat_id = callback_query.message.chat.id

    data = await dB.get_var(chat_id, "ABSENSI")
    if data is None:
        return await callback_query.answer("Sesi absensi belum dimulai! Silakan gunakan /mulai.", show_alert=True)
        
    data = data or []
    existing = next((u for u in data if u["user_id"] == user_id), None)
    
    # Perbaikan logika toggle: Jika sudah absen, tampilkan alert teks, jangan dihapus
    if existing:
        return await callback_query.answer("Kamu sudah melakukan absensi sebelumnya! ✨", show_alert=True)
    
    # Jika belum absen, masukkan ke list berdasarkan waktu kedatangan asli
    now_time = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%H:%M")
    data.append({"user_id": user_id, "name": name, "time": now_time})
    status_msg = "Absensi berhasil dicatat! ✅"

    await callback_query.answer(status_msg, show_alert=False)
    await dB.set_var(chat_id, "ABSENSI", data)

    try:
        now = datetime.now(pytz.timezone("Asia/Jakarta"))
        date_str = format_tanggal_indo(now)
        text = f"""**{callback_query.message.chat.title}**
**Daftar hadir hari** {date_str}.

<blockquote expandable>
{format_absen_list(data)}
</blockquote>

**Waktu dalam timezone WIB (UTC+7).
Yang telah hadir, silakan klik tombol HADIR di bawah ini.**"""
        
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("☑️  Hadir", callback_data="Hadir")]]
        )
            
        await callback_query.edit_message_text(text, reply_markup=keyboard)
    except Exception:
        pass
        
        
__MODULE__ = "Absensi"
__HELP__ = """
<blockquote expandable>📋 <b>Attendance Commands</b>

• <b>/mulai</b> – Start attendance session.  
• <b>/selesai</b> – End session & clear database (Auto-rekap).  
• <b>/refreshabsen</b> – Refresh the attendance message if it's buried.
• <b>/rekap</b> – Backup/rekap current attendance anytime.

📌 <i>Use these commands in group chats to track who is present.</i>

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""
