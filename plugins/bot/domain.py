from pyrogram import filters
from datetime import datetime
import socket
import requests
import whois

from AmonMusic import app



__MODULE__ = "Domain"
__HELP__ = """
<blockquote expandable>📋 <b>Domain & IP Commands</b>

• <b>/domain</b> – Enter the domain name after the command to find info about the domain.
• <b>/ip</b> – Enter the IP address after the command to get info about that IP.

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""        



IPINFO_TOKEN = '6274faab58da61'
IPQUALITYSCORE_API_KEY = '952ztTq41AxoXam43pStVjVNcEjo1ntQ'


@app.on_message(filters.command(["ip"]))
async def ip_info_and_score(_, message):
    if len(message.command) != 2:
        await message.reply_text(
            "ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ɪᴘ ᴀᴅᴅʀᴇss ᴀғᴛᴇʀ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ. ᴇxᴀᴍᴘʟᴇ**: `/ip 8.8.8.8`"
        )
        return

    ip_address = message.command[1]
    ip_info = get_ip_info(ip_address)
    ip_score, score_description, emoji = get_ip_score(ip_address, IPQUALITYSCORE_API_KEY)

    if ip_info is not None and ip_score is not None:
        response_message = (
            f"{ip_info}\n\n"
            f"**ɪᴘ sᴄᴏʀᴇ ➪ {ip_score} {emoji} ({score_description})"
        )
        await message.reply_text(response_message)
    else:
        await message.reply_text("Unable to fetch information for the provided IP address.")


def get_ip_info(ip_address):
    api_url = f"https://ipinfo.io/{ip_address}?token={IPINFO_TOKEN}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            info = (
                f"•➥**IP** ➪ {data.get('ip', 'N/A')}\n"
                f"•➥**City** ➪ {data.get('city', 'N/A')}\n"
                f"•➥**Region** ➪ {data.get('region', 'N/A')}\n"
                f"•➥**Country** ➪ {data.get('country', 'N/A')}\n"
                f"•➥**Location** ➪ {data.get('loc', 'N/A')}\n"
                f"•➥**Organization** ➪ {data.get('org', 'N/A')}\n"
                f"•➥**Postal Code** ➪ {data.get('postal', 'N/A')}\n"
                f"•➥**Timezone** ➪ {data.get('timezone', 'N/A')}"
            )
            return info
    except Exception as e:
        print(f"Error fetching IP information: {e}")
    return None


def get_ip_score(ip_address, api_key):
    api_url = f"https://ipqualityscore.com/api/json/ip/{api_key}/{ip_address}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            fraud_score = data.get("fraud_score", "N/A")
            if fraud_score != "N/A":
                fraud_score = int(fraud_score)
                if fraud_score <= 20:
                    score_description = "Good"
                    emoji = "✅"
                elif fraud_score <= 60:
                    score_description = "Moderate"
                    emoji = "⚠️"
                else:
                    score_description = "Bad"
                    emoji = "❌"
                return fraud_score, score_description, emoji
    except Exception as e:
        print(f"Error fetching IP score: {e}")
    return None, None, None




def get_domain_info(domain_name):
    try:
        return whois.whois(domain_name)
    except Exception as e:
        print(f"[WHOIS Error] {e}")
        return None

def get_domain_age(creation_date):
    if isinstance(creation_date, list):
        creation_date = creation_date[0]
    return (datetime.now() - creation_date).days // 365 if creation_date else None

def get_ip_location(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        if response.ok:
            data = response.json()
            return data if data.get("status") == "success" else None
    except Exception as e:
        print(f"[IP Geo Error] {e}")
    return None

def format_info(info):
    def clean(item):
        if isinstance(item, list):
            return item[0] if item else None
        return item

    domain = clean(info.domain_name)
    registrar = clean(info.registrar)
    creation = clean(info.creation_date)
    expiry = clean(info.expiration_date)
    nameservers = ', '.join(info.name_servers) if info.name_servers else "N/A"
    age = get_domain_age(creation)

    try:
        ip = socket.gethostbyname(domain)
    except:
        ip = "Unavailable"

    location_data = get_ip_location(ip)
    location = f"{location_data['country']}, {location_data['city']}" if location_data else "Unavailable"

    return (
        f"**ᴅᴏᴍᴀɪɴ ɴᴀᴍᴇ**: {domain}\n"
        f"**ʀᴇɢɪsᴛʀᴀʀ**: {registrar}\n"
        f"**ᴄʀᴇᴀᴛɪᴏɴ ᴅᴀᴛᴇ**: {creation.strftime('%Y-%m-%d') if creation else 'N/A'}\n"
        f"**ᴇxᴘɪʀᴀᴛɪᴏɴ ᴅᴀᴛᴇ**: {expiry.strftime('%Y-%m-%d') if expiry else 'N/A'}\n"
        f"**ᴅᴏᴍᴀɪɴ ᴀɢᴇ**: {age} years\n"
        f"**ɪᴘ ᴀᴅᴅʀᴇss**: `{ip}`\n"
        f"**ʟᴏᴄᴀᴛɪᴏɴ**: {location}\n"
        f"**ɴᴀᴍᴇsᴇʀᴠᴇʀs**: {nameservers}\n"
    )

@app.on_message(filters.command("domain"))
async def domain_lookup(_, message):
    if len(message.command) < 2:
        return await message.reply("Please provide a domain name. Example: `/domain heroku.com`")

    domain_name = message.text.split(maxsplit=1)[1].strip()
    data = get_domain_info(domain_name)

    if not data:
        return await message.reply("⚠️ Failed to retrieve WHOIS data.")

    response = format_info(data)
    await message.reply(response)
