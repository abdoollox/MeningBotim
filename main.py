import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
API_TOKEN = '8544270521:AAELBt_yuonOegOF-nPl-nI2FH7fQ-JBwQE' 
GURUH_ID = -1003369300068  # Guruh ID si
ADMIN_ID = 7566631808      # SIZNING ID RAQAMINGIZ (Bot sizga chek yuborishi uchun)
KARTA_RAQAM = "5614 6814 0351 0260"  # Faqat raqamlar
KARTA_EGA = "KARIMBERDIYEV ABDULLOH" # Faqat ism
MAHSULOT_NARXI = "50 000 so'm"

# Botni sozlash
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. Start bosilganda (Video/Rasm va Tugma)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    MEDIA_ID = "AgACAgIAAxkBAAIC..." # O'zingizdagi Rasm yoki Video ID

    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Sotib olish ({MAHSULOT_NARXI})", callback_data="karta_bilan_tolash")]
    ])
    
    try:
        await message.answer_photo(photo=MEDIA_ID, caption="Mahsulot haqida ma'lumot. Sotib olish uchun tugmani bosing:", reply_markup=tugma)
    except:
        await message.answer("Mahsulot haqida ma'lumot. Sotib olish uchun tugmani bosing:", reply_markup=tugma)

# 2. "Sotib olish" bosilganda -> Karta raqam berish
@dp.callback_query(F.data == "karta_bilan_tolash")
async def send_card_info(callback: types.CallbackQuery):
    # E'tibor bering: Karta raqamni ` ` belgilari ichiga oldik. 
    # Bu uni nusxalash uchun qulay qiladi.
    matn = (
        f"💳 **To'lov uchun karta:**\n"
        f"`{KARTA_RAQAM}`\n"
        f"{KARTA_EGA}\n\n"
        f"💰 **Narxi:** {MAHSULOT_NARXI}\n\n"
        "❗️ To'lov qilganingizdan so'ng, chekni (rasm yoki fayl ko'rinishida) shu yerga yuboring.\n\n"
        "⏳ **Diqqat:** To'lovlarni tekshirish navbat bilan amalga oshiriladi. Javob olish **8 soatgacha** vaqt olishi mumkin. Iltimos, sabr qiling.\n\n"
        "💯 Kutganingizdan ortiq qiymat olishingizga ishonamiz!"
    )
    await callback.message.answer(matn, parse_mode="Markdown")
    await callback.answer()

# 3. Foydalanuvchi Rasm YOKI Fayl yuborganda
@dp.message(F.photo | F.document) # <--- O'zgargan joyi: Ikkalasini ham qabul qiladi
async def check_receipt(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Noma'lum"
    
    # Admin uchun tugmalar
    admin_tugma = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
        ]
    ])
    
    caption_text = f"📩 **Yangi to'lov cheki!**\n👤 Kimdan: @{username} (ID: {user_id})\n\nTasdiqlaysizmi?"

    # Agar foydalanuvchi RASM yuborgan bo'lsa:
    if message.photo:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=message.photo[-1].file_id,
            caption=caption_text,
            reply_markup=admin_tugma
        )
    
    # Agar foydalanuvchi FAYL (Document) yuborgan bo'lsa:
    elif message.document:
        await bot.send_document(
            chat_id=ADMIN_ID,
            document=message.document.file_id,
            caption=caption_text,
            reply_markup=admin_tugma
        )
    
    await message.answer("⏳ Chek qabul qilindi! Adminlar tekshirib chiqishgach (8 soat ichida) sizga havola yuboriladi.")

# 4. Admin "✅ Tasdiqlash"ni bosganda
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    # Callbackdan user_id ni ajratib olish (confirm_12345 -> 12345)
    mijoz_id = int(callback.data.split("_")[1])
    
    try:
        # 1. Link yaratish
        link = await bot.create_chat_invite_link(chat_id=GURUH_ID, member_limit=1)
        
        # 2. Mijozga yuborish
        success_text = (
            "✅ **To'lov tasdiqlandi!**\n"
            "Guruhga qo'shilish uchun maxsus havola:\n"
            f"{link.invite_link}\n\n"
            "Eslatma: Bu havola faqat bir marta ishlaydi."
        )
        await bot.send_message(chat_id=mijoz_id, text=success_text)
        
        # 3. Adminga xabar
        await callback.message.edit_caption(caption=f"✅ {callback.message.caption}\n\n**TASDIQLANDI**")
        
    except Exception as e:
        await callback.message.answer(f"Xatolik: {e}")

# 5. Admin "❌ Rad etish"ni bosganda
@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    mijoz_id = int(callback.data.split("_")[1])
    
    await bot.send_message(chat_id=mijoz_id, text="❌ To'lovingiz rad etildi yoki chek noto'g'ri. Iltimos, qayta tekshiring yoki adminga yozing.")
    await callback.message.edit_caption(caption=f"❌ {callback.message.caption}\n\n**RAD ETILDI**")

# --- RENDER UCHUN VEB-SERVER (O'ZGARISHSIZ) ---
async def health_check(request):
    return web.Response(text="Bot ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- ASOSIY ---
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())





