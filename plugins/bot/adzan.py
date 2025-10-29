import json
from pyrogram import filters
from pyrogram.types import Message
import requests
from AmonMusic import app
import string

@app.on_message(filters.command("adzan", prefixes="/"))
async def adzan_handler(client, message):
    text_split = message.text.split()
    
    lok = text_split[1] if len(text_split) > 1 else None

    pros = await message.reply("Processing...")

    if not lok:
        return await pros.edit("Please provide a location.")

    url = f"http://muslimsalat.com/{lok}.json?key=bd099c5825cbedb9aa934e255a81a5fc"    
    req = requests.get(url)

    if req.status_code != 200:
        return await pros.edit(f"Could not retrieve prayer times for {lok}. Please check the location and try again.")

    result = json.loads(req.text)
    tanggal = result["items"][0]["date_for"]
    kueri = result["query"]
    negara = result["country"]
    terbit = result["items"][0]["shurooq"]
    pajar = result["items"][0]["fajr"]
    juhur = result["items"][0]["dhuhr"]
    asar = result["items"][0]["asr"]
    magrip = result["items"][0]["maghrib"]
    isa = result["items"][0]["isha"]

    txt = f"<b>👨‍💻 Jᴀᴅᴡᴀʟ sʜᴀʟᴀᴛ ʜᴀʀɪ ɪɴɪ:\n</b>"
    txt += f"<b>📆 ᴛᴀɴɢɢᴀʟ:</b> {tanggal}\n"
    txt += f"<b>📍 ʟᴏᴋᴀsɪ:</b> {kueri}, {negara}\n"
    txt += "------------------------\n"
    txt += f"<blockquote><b>➥ ᴛᴇʀʙɪᴛ:</b> {terbit}\n</blockquote>"
    txt += f"<blockquote><b>➥ sʜᴜʙᴜʜ:</b> {pajar}\n</blockquote>"
    txt += f"<blockquote><b>➥ ᴢᴜʜᴜʀ:</b> {juhur}\n</blockquote>"
    txt += f"<blockquote><b>➥ ᴀsʜᴀʀ:</b> {asar}\n</blockquote>"
    txt += f"<blockquote><b>➥ ᴍᴀɢʜʀɪʙ:</b> {magrip}\n</blockquote>"
    txt += f"<blockquote><b>➥ ɪsʏᴀ:</b> {isa}\n</blockquote>"
    txt += "------------------------"

    await message.reply(txt)

    await pros.delete()


__MODULE__ = "Adzan"
__HELP__ = """
<blockquote expandable>📋 <b>Adzan Commands</b>

• <b>/adzan [name country]</b> – Get info adzan by country.

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)
</blockquote>
"""        