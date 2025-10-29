import aiohttp
import httpx
import git
import shutil
import os

from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from AmonMusic import app




__MODULE__ = "Repo"
__HELP__ = """
<blockquote expandable>📋 <b>Repo Commands</b>

• <b>/allrepo</b> – Enter the GitHub username after the command to get all repositories of that account.
• <b>/github or /git [username]</b> – Get information about a GitHub user.
• <b>/downloadrepo [link]</b> – Enter the repository link after the command to download the repository.

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""        



@app.on_message(filters.command(["downloadrepo"]))
async def download_repo(client: Client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "❌ Please provide a valid GitHub repository URL.\n\n"
            "Example: `/downloadrepo https://github.com/memex2711/plerr.git`",
            parse_mode=ParseMode.MARKDOWN
        )

    repo_url = message.command[1]
    status_msg = await message.reply_text("⏬ Cloning the repository...")

    zip_path = await clone_and_zip_repo(repo_url)

    if zip_path:
        try:
            await message.reply_document(
                zip_path,
                caption="✅ Repository downloaded and zipped."
            )
        except Exception as e:
            await message.reply_text(
                f"❌ Failed to send file: `{e}`",
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            os.remove(zip_path)
    else:
        await message.reply_text(
            "❌ Unable to download the specified GitHub repository.",
            parse_mode=ParseMode.MARKDOWN
        )

    await status_msg.delete()

async def clone_and_zip_repo(repo_url: str) -> str | None:
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = repo_name

    try:
        git.Repo.clone_from(repo_url, repo_path)
        zip_file = shutil.make_archive(repo_path, 'zip', repo_path)
        return zip_file
    except git.exc.GitCommandError as e:
        print(f"Git error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)




@app.on_message(filters.command(["github", "git"]))
async def github(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("**ᴜsᴀɢᴇ:** `/git <username>`")

    username = message.text.split(None, 1)[1]
    url = f"https://api.github.com/users/{username}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 404:
                return await message.reply_text("🚫 **ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!**")
            elif response.status != 200:
                return await message.reply_text("⚠️ **ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴅᴀᴛᴀ!**")

            data = await response.json()

    name = data.get("name", "Not specified")
    bio = data.get("bio", "No bio available.")
    blog = data.get("blog", "N/A")
    location = data.get("location", "Unknown")
    company = data.get("company", "N/A")
    created = data.get("created_at", "N/A")
    url = data.get("html_url", "N/A")
    repos = data.get("public_repos", "0")
    followers = data.get("followers", "0")
    following = data.get("following", "0")
    avatar = data.get("avatar_url", None)

    caption = f"""
✨ **ɢɪᴛʜᴜʙ ᴘʀᴏғɪʟᴇ ɪɴꜰᴏ**

👤 **ɴᴀᴍᴇ:** `{name}`
🔧 **ᴜsᴇʀɴᴀᴍᴇ:** `{username}`
📌 **ʙɪᴏ:** {bio}
🏢 **ᴄᴏᴍᴘᴀɴʏ:** {company}
📍 **ʟᴏᴄᴀᴛɪᴏɴ:** {location}
🌐 **ʙʟᴏɢ:** {blog}
🗓 **ᴄʀᴇᴀᴛᴇᴅ ᴏɴ:** `{created}`
📁 **ᴘᴜʙʟɪᴄ ʀᴇᴘᴏs:** `{repos}`
👥 **ғᴏʟʟᴏᴡᴇʀs:** `{followers}` | **ғᴏʟʟᴏᴡɪɴɢ:** `{following}`
🔗 **ᴘʀᴏғɪʟᴇ:** [ᴠɪᴇᴡ ᴏɴ ɢɪᴛʜᴜʙ]({url})
""".strip()

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close")]]
    )

    if avatar:
        await message.reply_photo(photo=avatar, caption=caption, reply_markup=keyboard)
    else:
        await message.reply_text(caption, reply_markup=keyboard)




def chunk_string(text, chunk_size):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


@app.on_message(filters.command("allrepo"))
async def all_repo_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Please enter a GitHub username.\n\nExample: `/allrepo memex2711`")

    username = message.command[1].strip()

    try:
        repo_info = await get_all_repository_info(username)

        if not repo_info:
            return await message.reply_text("❌ No public repositories found or user does not exist.")

        chunks = chunk_string(repo_info, 4000)

        for chunk in chunks:
            await message.reply_text(chunk, disable_web_page_preview=True)

    except Exception as e:
        print(f"Error in /allrepo: {e}")
        await message.reply_text("⚠️ An error occurred while fetching repositories.")


async def get_all_repository_info(username: str) -> str:
    url = f"https://api.github.com/users/{username}/repos"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    if not data:
        return None

    info_lines = [
        f"🔹 **[{repo['name']}]({repo['html_url']})**\n"
        f"⭐ Stars: `{repo['stargazers_count']}` | 🍴 Forks: `{repo['forks_count']}`\n"
        f"📄 {repo['description'] or 'No description'}"
        for repo in data
    ]

    profile_link = f"👤 [View GitHub Profile](https://github.com/{username})"
    return f"{profile_link}\n\n" + "\n\n".join(info_lines)
