from telethon.sync import TelegramClient

api_id = 27867189
api_hash = 'aae51a8a046989834c4c50e1188e8dc6'

with TelegramClient('monitor', api_id, api_hash) as client:
    for dialog in client.iter_dialogs():
        print(f"{dialog.name} - {dialog.id}")
