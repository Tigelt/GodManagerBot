import json
from telethon import TelegramClient
from telethon.tl.types import User

async def dump_personals(out_file="personal_dialogs.ndjson"):
    API_ID = 14739654
    API_HASH = '98c13db08224026ed85682c5ed3e1834'   

    async with TelegramClient('aimanager', API_ID, API_HASH) as client:
           with open(out_file, "a", encoding="utf-8") as f:
            async for dialog in client.iter_dialogs():
                if isinstance(dialog.entity, User) and not dialog.entity.bot:
                    entity = dialog.entity
                    async for m in client.iter_messages(entity, reverse=True):
                        rec = {
                            "dialog_id": int(entity.id),
                            "dialog_title": getattr(entity, "username", None) or f"{entity.first_name} {entity.last_name or ''}".strip(),
                            "msg_id": m.id,
                            "from_me": m.out,
                            "text": m.message or "",
                            "date": m.date.isoformat(),
                        }
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"✅ Слил только личные чаты в {out_file}")