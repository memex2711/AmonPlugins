import re
import html
import requests
from io import BytesIO

from pyrogram import filters
from pyrogram.types import Message

from config import API_BOTCHAX
from AmonMusic import app
from AmonMusic.utils.decorators.language import language



__MODULE__ = "Lyrics"
__HELP__ = """
<blockquote expandable>📋 <b>Lyrics Commands</b>

• <b>/lyrics</b> – To search lyrics with tittle songs.

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""  



@app.on_message(filters.command("lyrics"))
@language
async def lyrics_handler(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text("**❌ Berikan judul lagu yang ingin dicari liriknya.**")

    query = message.text.split(None, 1)[1]
    m = await message.reply_text("**🔍 Sedang mencari lirik...**")

    try:
        response = requests.get(
            "https://api.botcahx.eu.org/api/search/lirik",
            params={"lirik": query, "apikey": API_BOTCHAX}
        )

        if response.status_code != 200:
            return await m.edit(f"**❌ Gagal mencari lirik untuk lagu:** <b>{html.escape(query)}</b>")

        result = response.json().get("result", {})
        lyrics_raw = result.get("lyrics", "")
        image_url = result.get("image")

        if not lyrics_raw or len(lyrics_raw.strip()) < 10:
            return await m.edit(f"**❌ Lirik untuk lagu:** <b>{html.escape(query)}</b> tidak ditemukan.")

        match = re.search(r"\[(Intro|Verse|Chorus|Outro|Bridge)", lyrics_raw, re.IGNORECASE)
        lyrics = lyrics_raw[match.start():].strip() if match else lyrics_raw.strip()
        lyrics = html.escape(lyrics)

        caption = f"<blockquote expandable><b>🎵 Lirik untuk:</b> <code>{html.escape(query)}</code>\n{lyrics}</blockquote>"

        if len(caption) > 1024:
            file_data = BytesIO(lyrics.encode("utf-8"))
            file_data.name = f"Lirik - {query}.txt"
            await m.delete()
            return await message.reply_document(
                file_data,
                caption=f"📄 <b>Lirik lengkap untuk:</b> <code>{html.escape(query)}</code>",
            )

        if image_url:
            img = requests.get(image_url)
            img_bytes = BytesIO(img.content)
            img_bytes.name = "cover.jpg"
            await m.delete()
            return await message.reply_photo(
                photo=img_bytes,
                caption=caption
            )

        await m.edit(caption)

    except Exception as e:
        return await m.edit(f"**❌ Terjadi kesalahan.\n📎 Pesan:** `{e}`")