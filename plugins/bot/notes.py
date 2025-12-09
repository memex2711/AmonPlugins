from AmonMusic import app
from config import BOT_USERNAME
from pyrogram import filters
from AmonMusic.utils.admin_filters import admin_filter

from AmonMusic.database import dB 

from AmonMusic.utils.notes_func import GetNoteMessage, exceNoteMessageSender, privateNote_and_admin_checker, SendNoteMessage
from AmonMusic.utils.permissions import user_admin
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup , Message , CallbackQuery
from pyrogram.enums import ChatMemberStatus


NOTE_CATEGORY = "NOTE"
PRIVATE_NOTE_KEY = "PRIVATE_NOTES_STATUS" 


async def SaveNote(chat_id, note_name, content, text, data_type):
    # Mengubah note_name ke huruf kecil (lowercase) agar konsisten saat dipanggil
    note_name = note_name.lower()
    value = {
        "content": content,
        "text": text,
        "data_type": data_type
    }
    await dB.set_var(chat_id, note_name, value, NOTE_CATEGORY)

async def isNoteExist(chat_id, note_name):
    # Mengubah note_name ke huruf kecil saat pengecekan
    note_name = note_name.lower()
    data = await dB.get_var(chat_id, note_name, NOTE_CATEGORY)
    return bool(data)

async def GetNote(chat_id, note_name):
    # Mengubah note_name ke huruf kecil saat mengambil
    note_name = note_name.lower()
    data = await dB.get_var(chat_id, note_name, NOTE_CATEGORY)
    if data and isinstance(data, dict):
        return (
            data.get("content"), 
            data.get("text"), 
            data.get("data_type")
        )
    return (None, None, None)

async def set_private_note(chat_id, status: bool):
    await dB.set_var(chat_id, PRIVATE_NOTE_KEY, status, NOTE_CATEGORY)

async def is_pnote_on(chat_id):
    status = await dB.get_var(chat_id, PRIVATE_NOTE_KEY, NOTE_CATEGORY)
    return status if isinstance(status, bool) else False

async def ClearNote(chat_id, note_name):
    # Mengubah note_name ke huruf kecil saat menghapus
    note_name = note_name.lower()
    await dB.remove_var(chat_id, note_name, NOTE_CATEGORY)

async def ClearAllNotes(chat_id):
    all_notes = await dB.all_var(chat_id, NOTE_CATEGORY)
    if all_notes:
        for note_name in all_notes.keys():
             if note_name != PRIVATE_NOTE_KEY:
                await dB.remove_var(chat_id, note_name, NOTE_CATEGORY)

async def NoteList(chat_id):
    all_notes = await dB.all_var(chat_id, NOTE_CATEGORY)
    if not all_notes:
        return []
    
    notes_list = [name for name in all_notes.keys() if name != PRIVATE_NOTE_KEY]
    return notes_list


@app.on_message(filters.command("save") & admin_filter)
@user_admin
async def _save(client, message):
    chat_id = message.chat.id
    chat_title = message.chat.title
    
    # Memastikan perintah memiliki nama note (index 1)
    if len(message.command) < 2:
        return await message.reply_text("you need to give the note a name!")

    NoteName = message.command[1]

    # Memastikan ada konten yang disimpan (reply atau teks langsung)
    if not message.reply_to_message and len(message.command) < 3:
        return await message.reply_text("You need to give the note some content or reply to a message!")
    
    
    Content, Text, DataType = GetNoteMessage(message)
    await SaveNote(chat_id, NoteName, Content, Text, DataType)

    await message.reply_text(f"I've saved note `{NoteName}` in {chat_title}.")
    

@app.on_message(filters.command("get") & admin_filter)
async def _getnote(client, message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply_text("You need to give the note a name!")  
    
    note_name = message.command[1]
    
    if not await isNoteExist(chat_id, note_name):
         return await message.reply_text("Note not found")
         
    await send_note(message, note_name)
    

@app.on_message(filters.regex(pattern=(r"^#[^\s]+")) & filters.group)
async def regex_get_note(client, message):
    chat_id = message.chat.id
    
    # 🌟 PERBAIKAN UTAMA: Mencegah AttributeError jika message.text adalah None
    if not message.text:
        return
        
    # Cek jika pengguna ada dan pesan dimulai dengan '#'
    # Karena filter sudah memastikan dimulai dengan #, kita fokus pada message.text
    if message.from_user:
        # Mengambil kata pertama (nama note) dan menghapus '#'
        note_name_with_hash = message.text.split()[0]
        if note_name_with_hash.startswith('#'):
            note_name = note_name_with_hash[1:]
        else:
            # Walaupun filter regex seharusnya mencegah ini, ini untuk keamanan
            return

        # Panggil note_name dengan huruf kecil (sudah diubah di fungsi isNoteExist)
        if await isNoteExist(chat_id, note_name):
            await send_note(message, note_name)


PRIVATE_NOTES_TRUE = ['on', 'true', 'yes', 'y']
PRIVATE_NOTES_FALSE = ['off', 'false', 'no', 'n']

@app.on_message(filters.command("privatenotes") & filters.group)
@user_admin
async def PrivateNote(client, message):
    chat_id = message.chat.id
    if len(message.command) >= 2:
        arg = message.command[1].lower() # Gunakan argumen dengan huruf kecil
        if (
            arg in PRIVATE_NOTES_TRUE
        ):
            await set_private_note(chat_id, True)
            await message.reply(
                "Now i will send a message to your chat with a button redirecting to PM, where the user will receive the note.",
                quote=True
            )

        elif (
            arg in PRIVATE_NOTES_FALSE
        ):
            await set_private_note(chat_id, False)
            await message.reply(
                "I will now send notes straight to the group.",
                quote=True
            )  
        else:
            await message.reply(
                f"failed to get boolean value from input:\n\n expected one of y/yes/on/true or n/no/off/false; got: {message.command[1]}",
                quote=True
            )
    else:
        if await is_pnote_on(chat_id):
            await message.reply(
                "Your notes are currently being sent in private. MEMEXPROJECT will send a small note with a button which redirects to a private chat.",
                quote=True
            )
        else:
            await message.reply(
                "Your notes are currently being sent in the group.",
                quote=True
            )
            
@app.on_message(filters.command("clear") & admin_filter)
@user_admin
async def Clear_Note(client, message):
    chat_id = message.chat.id 
    if len(message.command) < 2:
        await message.reply(
            "You need to give the note a name!",
            quote=True
        )
        return
    
    # Memproses multiple notes yang dipisahkan koma
    note_names = [name.strip().lower() for name in "".join(message.command[1:]).split(',')]

    deleted_count = 0
    not_found = []

    for note_name in note_names:
        if await isNoteExist(chat_id, note_name):
            await ClearNote(chat_id, note_name)
            deleted_count += 1
        else:
            not_found.append(note_name)

    response = []
    if deleted_count > 0:
        response.append(f"I've removed **{deleted_count}** note(s)!")
    
    if not_found:
        response.append(f"Note(s) not found: `{', '.join(not_found)}`")

    if not response:
        response.append("You haven't saved any note with that name yet!")

    await message.reply("\n".join(response), quote=True)


@app.on_message(filters.command("clearall") & admin_filter)
async def ClearAll_Note(client, message):
    # Mengambil ID user yang menjalankan perintah
    sender_id = message.from_user.id
    chat_id = message.chat.id 
    chat_title = message.chat.title
    
    # 🌟 Perbaikan: Cek status member, bukan hanya owner
    # Owner adalah status yang paling tinggi, tapi admin filter sudah mengurus ini di atas, 
    # namun fungsi ini secara khusus membatasi hanya untuk Owner.
    try:
        user = await client.get_chat_member(chat_id, sender_id)
        if user.status != ChatMemberStatus.OWNER:
            return await message.reply_text("Only Owner Can Use This!!") 
    except Exception:
        # Handle jika terjadi error saat get_chat_member (misal bot bukan admin)
        return await message.reply_text("Error: Failed to retrieve user status. Ensure the bot is an admin.")


    note_list = await NoteList(chat_id)
    if not note_list:
        return await message.reply(
            f"No notes in {chat_title}",
            quote=True
        )
        
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(text='Delete all notes', callback_data=f'clearallnotes_clear_{sender_id}_{chat_id}')
        ],
        [
            InlineKeyboardButton(text='Cancel', callback_data=f'clearallnotes_cancel_{sender_id}')
        ]]
    )
    await message.reply(
        f"Are you sure you want to clear **ALL** notes in {chat_title}? This action is irreversible.",
        reply_markup=keyboard,
        quote=True
    )

@app.on_callback_query(filters.regex("^clearallnotes_"))
async def ClearAllCallback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('_')
    query_data = data_parts[1]
    owner_id = int(data_parts[2])
    user_id = callback_query.from_user.id 
    chat_id = int(data_parts[3]) if len(data_parts) > 3 else None

    if owner_id == user_id:
        if query_data == 'clear' and chat_id is not None:
            await ClearAllNotes(chat_id)
            await callback_query.edit_message_text("Deleted all chat notes.") 
            return
            
        elif query_data == 'cancel':
            await callback_query.edit_message_text("Cancelled.")
    else:
        await callback_query.answer("Only the user who initiated the command can execute this!", show_alert=True)
                         
@app.on_message(filters.command(['notes', 'saved']) & filters.group)
async def Notes(client, message):
    
    chat_id = message.chat.id
    chat_title = message.chat.title

    Notes_list = await NoteList(chat_id)
    
    NoteHeader = f"List of notes in {chat_title}:\n"
    if (
        len(Notes_list) != 0
    ): 
        for notes in Notes_list:
            NoteName = f" • `#{notes}`\n"
            NoteHeader += NoteName
        await message.reply(
            (
                f"{NoteHeader}\n"
                "You can retrieve these notes by using `/get notename`, or `#notename`"
            ),
            quote=True
        )
        
    else:
        await message.reply(
            f"No notes in {chat_title}.",
            quote=True
        )        

async def exceNoteMessageSender_wrapper(message, note_name, content, text, data_type, from_chat_id=None):
    try:
        await SendNoteMessage(message, note_name, content, text, data_type, from_chat_id)
    except Exception as e:
        await message.reply(
            (
                "The notedata was incorrect, please update it. The buttons are most likely to be broken. If you are sure you aren't doing anything wrong and this was unexpected - please report it in my support chat.\n"
                f"**Error:** `{e}`"
            ),
            quote=True
        )

async def send_note(message: Message, note_name: str):
    chat_id = message.chat.id  
    # 🌟 Pastikan note_name dipanggil dalam huruf kecil di sini juga
    content, text, data_type = await GetNote(chat_id, note_name.lower()) 
    
    if not content and not text:
        return await message.reply("Note not found or empty.")

    privateNote, allow = await privateNote_and_admin_checker(message, text)   
    
    if allow:
        pnote_status_db = await is_pnote_on(chat_id)
        
        if privateNote is None:
            if pnote_status_db:
                await PrivateNoteButton(message, chat_id, note_name)
            else:
                await exceNoteMessageSender_wrapper(message, note_name, content, text, data_type)
        elif privateNote is not None:
            if privateNote:
                await PrivateNoteButton(message, chat_id, note_name)
            else:
                await exceNoteMessageSender_wrapper(message, note_name, content, text, data_type)
                    
async def note_redirect(message):
    # Memeriksa panjang command
    if len(message.command) < 2:
        return await message.reply("Invalid note redirect command format.")
        
    # Mengambil bagian setelah '/start note_'
    start_payload = message.command[1] 
    
    # Memastikan format payload benar: 'note_chatid_notename'
    if not start_payload.startswith('note_'):
         return await message.reply("Invalid note redirect command format.")

    try:
        # note_redirect dipanggil di PM, command[0] = /start, command[1] = note_12345_tes
        parts = start_payload.split('_')
        if len(parts) != 3:
            raise ValueError("Incorrect number of parts in payload.")
            
        # parts[0] = 'note', parts[1] = chat_id, parts[2] = note_name
        chat_id = int(parts[1])
        note_name = parts[2]
    except (ValueError, IndexError):
        return await message.reply("Error parsing note redirect data.")

    
    content, text, data_type = await GetNote(chat_id, note_name)
    if not content and not text:
        return await message.reply("Note not found or empty.")
        
    await exceNoteMessageSender_wrapper(message, note_name, content, text, data_type, from_chat_id=chat_id) 

async def PrivateNoteButton(message, chat_id, NoteName):
    PrivateNoteButton = InlineKeyboardMarkup(
        [
            [
                # NoteName harus di-encode jika mengandung karakter khusus, tapi untuk amannya kita anggap NoteName adalah string sederhana
                InlineKeyboardButton(text='Click me!', url=f'http://t.me/{BOT_USERNAME}?start=note_{chat_id}_{NoteName}')
            ]
        ]
    )
    await message.reply(
        text=f"Tap here to view '{NoteName}' in your private chat.",
        reply_markup=PrivateNoteButton
    )
    
    
    
__MODULE__ = "Notes"
__HELP__ = """
<blockquote expandable>📋 <b>Notes Commands</b>

<b>/save [name]</b> - Save replied message as a note.  
<b>/get [name]</b> - Get note by name.
<b>/clear [name1,name2,...]</b> - Delete specific notes (comma separated).  
<b>/clearall</b> - Delete all notes in group.

✧ These modules by ➪ [fr rasta](https://t.me/root404byte)

</blockquote>
"""
