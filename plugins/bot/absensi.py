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
    bulan = {
        "January": "Januari", "Tuesday": "Februari", "March": "Maret", "April": "April", 
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

    absen_text = f"""**{message.chat.title}
Daftar hadir hari** {date_str}.

<blockquote expandable>
{format_absen_list(data)}
</blockquote>

**Waktu dalam timezone WIB (UTC+7).
Yang telah hadir, silakan klik tombol HADIR di bawah ini.**"""
    
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("☑️  Hadir", callback_data="Hadir")]]
    )
    return await message.reply(absen_text, reply_markup=keyboard)


@app.on_message(filters.command("refresh") & admin_filter &  ~BANNED_USERS)
async def refresh_absen(_, message: Message): 
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_str = format_tanggal_indo(now)
    chat_id = message.chat.id
    data = await dB.get_var(chat_id, "ABSENSI") or []
    data = sorted(data, key=lambda x: x["time"])

    absen_text = f"""**{message.chat.title}
Daftar hadir hari {date_str}.**

<blockquote expandable>
{format_absen_list(data)}
</blockquote>

**Waktu dalam timezone WIB (UTC+7).
Yang telah hadir, silakan klik tombol HADIR di bawah ini.**"""
    
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("☑️  Hadir", callback_data="Hadir")]]
    )
    return await message.reply(absen_text, reply_markup=keyboard)


@app.on_message(filters.command("selesai") & admin_filter &  ~BANNED_USERS)
async def selesai_absen(_, message: Message): 
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_str = format_tanggal_indo(now)
    chat_id = message.chat.id
    data = await dB.get_var(chat_id, "ABSENSI") or []
    data = sorted(data, key=lambda x: x["time"])

    await dB.remove_var(chat_id, "ABSENSI")

    absen_text = f"""**{message.chat.title}
Daftar hadir hari {date_str}.**

<blockquote expandable>
{format_absen_list(data)}
</blockquote>

**Sesi absensi telah diakhiri oleh Admin.**

**Waktu dalam timezone WIB (UTC+7).**"""
    
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
    
    if existing:
        data = [u for u in data if u["user_id"] != user_id]
        status_msg = "Anda membatalkan absensi."
    else:
        now_time = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%H:%M")
        data.append({"user_id": user_id, "name": name, "time": now_time})
        status_msg = "Absensi berhasil dicatat."

    await callback_query.answer(status_msg, show_alert=False)
    data = sorted(data, key=lambda x: x["time"])
    await dB.set_var(chat_id, "ABSENSI", data)

    try:
        now = datetime.now(pytz.timezone("Asia/Jakarta"))
        date_str = format_tanggal_indo(now)
        text = f"""**{callback_query.message.chat.title}
Daftar hadir hari {date_str}.**

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
        print(f"ERROR: {traceback.format_exc()}")
        await callback_query.answer("Gagal memperbarui pesan absensi.", show_alert=True)
        
        
__MODULE__ = "Absensi"
__HELP__ = """
<blockquote expandable>📋 <b>Attendance Commands</b>

• <b>/mulai</b> – Start attendance session.  
• <b>/selesai</b> – End the current attendance session.  
• <b>/refresh</b> – Refresh the attendance message if it's buried.

📌 <i>Use these commands in group chats to track who is present.</i>

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""        