import config
import traceback

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from AmonMusic import app
from AmonMusic.utils.tools import Tools


@app.on_message(filters.command(["pinterest", "pint"]) & ~config.BANNED_USERS)
async def pinterest_cmd(client, message):
    try:
        proses = await message.reply("> **Memproses permintaanmu...**")

        try:
            prompt = message.text.split(None, 1)[1].strip()
        except IndexError:
            return await proses.edit("**Mohon berikan kata kunci.\nContoh:** `/pinterest kucing lucu`")

        if not prompt:
            return await proses.edit(">**Kata kunci tidak boleh kosong.**")

        url = f"https://api.botcahx.eu.org/api/search/pinterest?text1={prompt}&apikey={config.API_BOTCHAX}"
        response = await Tools.fetch.get(url)

        if response.status_code != 200:
            return await proses.edit(">**Gagal mengambil data. Silakan coba lagi nanti.**")

        data = response.json()
        results = data.get("result", [])
        if not results:
            return await proses.edit(
                f"**Tidak ditemukan hasil untuk:** `{prompt}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Tutup", callback_data="close")]
                ])
            )

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next", callback_data=f"nextpinterest_1_{prompt}")]
        ])

        await proses.delete()
        return await message.reply_photo(results[0], caption=f"📌 Hasil pencarian: `{prompt}`", reply_markup=buttons)

    except Exception:
        return await message.reply(f"❌ Terjadi kesalahan:\n<code>{traceback.format_exc()}</code>")


@app.on_callback_query(filters.regex(r"^nextpinterest_(\d+)_(.+)"))
async def pinterest_next_cb(client, callback_query):
    try:
        index, prompt = callback_query.data.split("_", 2)[1:]
        index = int(index)

        url = f"https://api.botcahx.eu.org/api/search/pinterest?text1={prompt}&apikey={config.API_BOTCHAX}"
        response = await Tools.fetch.get(url)

        if response.status_code != 200:
            return await callback_query.answer("Gagal ambil data", show_alert=True)

        data = response.json()
        results = data.get("result", [])
        if not results or index >= len(results):
            return await callback_query.answer("Sudah sampai akhir!", show_alert=True)

        buttons = []
        row = []

        if index > 0:
            row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"nextpinterest_{index - 1}_{prompt}"))
        if index + 1 < len(results):
            row.append(InlineKeyboardButton("➡️ Next", callback_data=f"nextpinterest_{index + 1}_{prompt}"))
        if row:
            buttons.append(row)

        buttons.append([InlineKeyboardButton("❌ Tutup", callback_data="close")])

        await callback_query.message.edit_media(
            media=InputMediaPhoto(media=results[index]),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception:
        await callback_query.answer("❌ Gagal menampilkan gambar.", show_alert=True)



__MODULE__ = "Pinterest"
__HELP__ = """
<blockquote expandable>📋 <b>Pinterest Commands</b>

• <b>/pinterest [query]</b> – Can search images from pinterest with button scroll.

</blockquote>
"""        