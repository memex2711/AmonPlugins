import aiofiles
import aiohttp
import os
import io
import random
import traceback

from pyrogram import filters
from pyrogram.types import (
    Message, MessageEntity, Chat,
) 
from pyrogram.enums import ChatType

from AmonMusic import app, LOGGER

from config import OWNER_ID 


class QuotlyException(Exception):
    pass


class Quotly:
    colors = [
        "White", "Navy", "DarkBlue", "MediumBlue", "Blue", "DarkGreen", "Green", "Teal", "DarkCyan", 
        "DeepSkyBlue", "DarkTurquoise", "MediumSpringGreen", "Lime", "SpringGreen", "Aqua", "Cyan", 
        "MidnightBlue", "DodgerBlue", "LightSeaGreen", "ForestGreen", "SeaGreen", "DarkSlateGray", 
        "DarkSlateGrey", "LimeGreen", "MediumSeaGreen", "Turquoise", "RoyalBlue", "SteelBlue", 
        "DarkSlateBlue", "MediumTurquoise", "Indigo", "DarkOliveGreen", "CadetBlue", "CornflowerBlue", 
        "RebeccaPurple", "MediumAquaMarine", "DimGray", "DimGrey", "SlateBlue", "OliveDrab", "SlateGray", 
        "SlateGrey", "LightSlateGray", "LightSlateGrey", "MediumSlateBlue", "LawnGreen", "Chartreuse", 
        "Aquamarine", "Maroon", "Purple", "Olive", "Gray", "Grey", "SkyBlue", "LightSkyBlue", 
        "BlueViolet", "DarkRed", "DarkMagenta", "SaddleBrown", "DarkSeaGreen", "LightGreen", 
        "MediumPurple", "DarkViolet", "PaleGreen", "DarkOrchid", "YellowGreen", "Sienna", "Brown", 
        "DarkGray", "DarkGrey", "LightBlue", "GreenYellow", "PaleTurquoise", "LightSteelBlue", 
        "PowderBlue", "FireBrick", "DarkGoldenRod", "MediumOrchid", "RosyBrown", "DarkKhaki", 
        "Silver", "MediumVioletRed", "IndianRed", "Peru", "Chocolate", "Tan", "LightGray", "LightGrey", 
        "Thistle", "Orchid", "GoldenRod", "PaleVioletRed", "Crimson", "Gainsboro", "Plum", "BurlyWood", 
        "LightCyan", "Lavender", "DarkSalmon", "Violet", "PaleGoldenRod", "LightCoral", "Khaki", 
        "AliceBlue", "HoneyDew", "Azure", "SandyBrown", "Wheat", "Beige", "WhiteSmoke", "MintCream", 
        "GhostWhite", "Salmon", "AntiqueWhite", "Linen", "LightGoldenRodYellow", "OldLace", "Red", 
        "Fuchsia", "Magenta", "DeepPink", "OrangeRed", "Tomato", "HotPink", "Coral", "DarkOrange", 
        "LightSalmon", "Orange", "LightPink", "Pink", "Gold", "PeachPuff", "NavajoWhite", "Moccasin", 
        "Bisque", "MistyRose", "BlanchedAlmond", "PapayaWhip", "LavenderBlush", "SeaShell", "Cornsilk", 
        "LemonChiffon", "FloralWhite", "Snow", "Yellow", "LightYellow", "Ivory", "Black",
    ]

    @staticmethod
    async def forward_info(reply: Message):
        sid, title, name = 0, "Unknown User", "Unknown User"

        if reply.forward_from_chat:
            chat: Chat = reply.forward_from_chat
            sid = chat.id
            title = chat.title or chat.type.name
            name = title
        elif reply.forward_from:
            user = reply.forward_from
            sid = user.id
            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"
            title = name
        elif reply.forward_sender_name:
            title = name = reply.forward_sender_name
            sid = 0
        elif reply.from_user:
            user = reply.from_user
            sid = user.id
            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"
            title = name
        
        return sid, title, name
    
    @staticmethod
    async def t_or_c(message: Message):
        return message.text or message.caption or ""
            
    @staticmethod
    async def get_entities(message: Message) -> list[MessageEntity]:
        return message.entities or message.caption_entities or []

    @staticmethod
    async def get_emoji(message: Message):
        if message.from_user and getattr(message.from_user, "emoji_status", None):
            emoji_status = str(message.from_user.emoji_status.custom_emoji_id)
        else:
            emoji_status = ""
        return emoji_status

    @staticmethod
    async def quotly(payload):
        url = "https://bot.lyo.su/quote/generate.png"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    try:
                        error_json = await resp.json()
                        raise QuotlyException(error_json.get("error", "Unknown Quotly API error"))
                    except aiohttp.ContentTypeError:
                        raise QuotlyException(f"Quotly API returned status {resp.status}")


@app.on_message(filters.command("q") & ~filters.private)
async def qoutly_cmd(client, message: Message):
    if not message.reply_to_message:
        return await message.reply(f">**Please reply to a message!**")

    pros = await message.reply(">**Please wait making your quotly...**")
    reply_msg = message.reply_to_message
    cmd = message.command[1:]

    def get_color(index=0):
        if len(cmd) > index and (cmd[index].isdigit() or cmd[index].startswith('-')):
             return random.choice(Quotly.colors)
        return cmd[index] if len(cmd) > index else random.choice(Quotly.colors)

    try:
        
        if not cmd or (cmd[0] not in Quotly.colors and not cmd[0].startswith('@') and not cmd[0].isdigit() and cmd[0] != '-r'):
            payload = {
                "type": "quote", "format": "png",
                "backgroundColor": get_color(), "messages": [],
            }
            sid, title, name = await Quotly.forward_info(reply_msg)
            messages_json = {
                "entities": await Quotly.get_entities(reply_msg), 
                "avatar": True,
                "from": {
                    "id": sid, "title": title, "name": name,
                    "emoji_status": await Quotly.get_emoji(reply_msg),
                },
                "text": await Quotly.t_or_c(reply_msg),
                "replyMessage": {},
            }
            payload["messages"].append(messages_json)
            
        elif cmd[0].startswith("@"):
            color = get_color(1)
            include_reply = len(cmd) > 2 and cmd[2] == "-r"
            payload = {
                "type": "quote", "format": "png", "backgroundColor": color, "messages": [],
            }
            username = cmd[0][1:]
            
            try:
                user = await client.get_users(username)
            except Exception:
                return await pros.edit(f">**Invalid username or user not found.**")

            if user.id in OWNER_ID:
                return await pros.edit(f">**You can't quote this user**")

            fake_msg = user
            name = fake_msg.first_name
            if fake_msg.last_name: name += f" {fake_msg.last_name}"

            emoji_status = str(getattr(fake_msg, "emoji_status", None).custom_emoji_id) if getattr(fake_msg, "emoji_status", None) else None

            reply_message = {}
            if include_reply and reply_msg.reply_to_message and reply_msg.reply_to_message.from_user:
                replied = reply_msg.reply_to_message
                
                replied_name = replied.from_user.first_name
                if replied.from_user.last_name: replied_name += f" {replied.from_user.last_name}"
                
                emoji_status_reply = str(getattr(replied.from_user, "emoji_status", None).custom_emoji_id) if getattr(replied.from_user, "emoji_status", None) else None

                reply_message = {
                    "chatId": replied.from_user.id,
                    "entities": await Quotly.get_entities(replied), 
                    "name": replied_name,
                    "text": await Quotly.t_or_c(replied),
                    "emoji_status": emoji_status_reply,
                }

            messages_json = {
                "entities": await Quotly.get_entities(reply_msg), 
                "avatar": True,
                "from": {
                    "id": fake_msg.id, "title": name, "name": name, "emoji_status": emoji_status,
                },
                "text": await Quotly.t_or_c(reply_msg),
                "replyMessage": reply_message,
            }

            payload["messages"].append(messages_json)
            
        elif cmd[0].startswith("-r"):
            replied = reply_msg.reply_to_message
            if not replied or not replied.from_user:
                 return await pros.edit(f">**Please reply to a message that has a reply.**")
                 
            replied_name = replied.from_user.first_name
            if replied.from_user.last_name: replied_name += f" {replied.from_user.last_name}"
            
            emoji_status_reply = str(getattr(replied.from_user, "emoji_status", None).custom_emoji_id) if getattr(replied.from_user, "emoji_status", None) else None
                
            reply_message = {
                "chatId": replied.from_user.id, "entities": await Quotly.get_entities(replied), 
                "name": replied_name, "text": await Quotly.t_or_c(replied), "emoji_status": emoji_status_reply,
            }
            
            color = get_color(1) 
            
            payload = {
                "type": "quote", "format": "png", "backgroundColor": color, "messages": [],
            }
            sid, title, name = await Quotly.forward_info(reply_msg)
            messages_json = {
                "entities": await Quotly.get_entities(reply_msg), "avatar": True,
                "from": {
                    "id": sid, "title": title, "name": name, "emoji_status": await Quotly.get_emoji(reply_msg),
                },
                "text": await Quotly.t_or_c(reply_msg),
                "replyMessage": reply_message,
            }
            payload["messages"].append(messages_json)

        elif cmd[0].isdigit():
            count = int(cmd[0])
            if count <= 0: return await pros.edit(f">**Number must be greater than 0**")
            if count > 10: return await pros.edit(f">**Max 10 messages**")

            color = get_color(1)
            
            payload = {
                "type": "quote", "format": "png", "backgroundColor": color, "messages": [], "scale": 2,
            }
            
            history_messages = []
            current_id = reply_msg.id
            
            for i in range(count):
                try:
                    msg = await client.get_messages(reply_msg.chat.id, current_id - i)
                    if msg: history_messages.append(msg)
                    else: break 
                except Exception: break
            
            history_messages.reverse() 
            unique_messages = []
            seen_ids = set()
            for msg in history_messages:
                if msg.id not in seen_ids:
                    unique_messages.append(msg)
                    seen_ids.add(msg.id)

            for msg in unique_messages:
                sid, title, name = await Quotly.forward_info(msg)
                messages_json = {
                    "entities": await Quotly.get_entities(msg), "avatar": True,
                    "from": {
                        "id": sid, "title": title, "name": name, "emoji_status": await Quotly.get_emoji(msg),
                    },
                    "text": await Quotly.t_or_c(msg), "replyMessage": {},
                }
                payload["messages"].append(messages_json)
                
            payload["messages"] = payload["messages"][-count:]
            
        elif cmd[0] in Quotly.colors:
            payload = {
                "type": "quote", "format": "png", "backgroundColor": cmd[0], "messages": [],
            }
            sid, title, name = await Quotly.forward_info(reply_msg)
            messages_json = {
                "entities": await Quotly.get_entities(reply_msg), "avatar": True,
                "from": {
                    "id": sid, "title": title, "name": name, "emoji_status": await Quotly.get_emoji(reply_msg),
                },
                "text": await Quotly.t_or_c(reply_msg), "replyMessage": {},
            }
            payload["messages"].append(messages_json)
        
        hasil = await Quotly.quotly(payload)
        bio_sticker = io.BytesIO(hasil)
        bio_sticker.name = "biosticker.webp"
        
        await client.send_sticker(
            message.chat.id, 
            sticker=bio_sticker, 
            reply_to_message_id=message.reply_to_message.id 
        )
        await pros.delete()

    except QuotlyException as e:
        await pros.edit(f">**Quotly API ERROR:** `{e}`")
    except Exception as e:
        LOGGER(__name__).error(f"ERROR: {traceback.format_exc()}")
        await pros.edit(f">**ERROR:** `{str(e)}`")


@app.on_message(filters.command("qcolor") & ~filters.private)
async def qcolor_cmd(client, message: Message):
    iymek = f"\n•".join(Quotly.colors)
    jadi = f">**Color for quotly**\n•"
    if len(iymek) > 4096:
        async with aiofiles.open("qcolor.txt", "w") as file:
            await file.write(iymek)
        
        await client.send_document(
            message.chat.id,
            "qcolor.txt", 
            caption=f">**Color for quotly**",
            reply_to_message_id=message.id
        )
        os.remove("qcolor.txt")
        return
    else:
        return await message.reply(jadi + iymek)
        
        
        
__MODULE__ = "Quotly"
__HELP__ = """
<blockquote expandable>
<b>📝 Quote Generator</b>

<b>/q</b> [reply] – Quote message with random color.  
<b>/q pink</b> [reply] – Quote message with custom color.  
<b>/q</b> @username [reply] – Fake quote for a specific user.  
<b>/q</b> @username pink -r [reply] – Fake quote with reply & color.  
<b>/q</b> -r [reply] – Quote with replies.  
<b>/q</b> -r pink [reply] – Quote with replies & color.  
<b>/q</b> 5 [reply] – Quote multiple messages.  
<b>/q</b> 5 pink [reply] – Multiple quotes with custom color.

<b>/qcolor</b> – Show all available quote colors.


✧ These modules by ➪ [fr rasta](https://t.me/root404byte)
</blockquote>
"""
