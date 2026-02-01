import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
# Tokenni xavfsizlik uchun to'g'ridan-to'g'ri yozish o'rniga Environment dan olamiz
# Yoki shu yerga qo'shtirnoq ichida yozib qo'ying: 'SIZNING_TOKENINGIZ'
API_TOKEN = '8544270521:AAELBt_yuonOegOF-nPl-nI2FH7fQ-JBwQE' 
GURUH_ID = -1003369300068 # O'ZINGIZNING GURUH ID
NARX = 1

# Botni sozlash
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- BOT FUNKSIYALARI ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Rasm yoki Video ID si (O'zingiznikini qo'ying)
    MEDIA_ID = "AgACAgIAAxkBAAIC..." 

    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Sotib olish ({NARX} ⭐️)", callback_data="tulov_qilish")]
    ])
    
    # Agar media bo'lmasa, matn chiqaradi
    try:
        await message.answer_video(video=MEDIA_ID, caption="Mahsulot haqida ma'lumot:", reply_markup=tugma)
    except:
        await message.answer("Mahsulot haqida ma'lumot. Sotib olish uchun bosing:", reply_markup=tugma)

@dp.message(Command("test_link"))
async def test_link_cmd(message: types.Message):
    try:
        link = await bot.create_chat_invite_link(chat_id=GURUH_ID, member_limit=1)
        await message.answer(f"✅ Tizim ishlayapti! Link:\n{link.invite_link}")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@dp.callback_query(F.data == "tulov_qilish")
async def send_invoice(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Garri Potter Cinema",
        description="Garri Potter olamining barcha kolleksiyasi jamlangan guruhga kirish uchun bir martalik to'lovni amalga oshiring!",
        payload="hub_tolov",
        provider_token="", 
        currency="XTR",
        prices=[LabeledPrice(label="Kirish", amount=NARX)]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    try:
        link = await bot.create_chat_invite_link(chat_id=GURUH_ID, member_limit=1)
        await message.answer(f"✅ To'lov qabul qilindi!\nHavola: {link.invite_link}")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

# --- RENDER UCHUN VEB-SERVER QISMI (YANGI) ---
async def health_check(request):
    return web.Response(text="Bot ishlab turibdi!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render avtomatik beradigan PORT ni olamiz yoki 8080 ni ishlatamiz
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Veb-server {port}-portda ishga tushdi")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # 1. Veb-serverni ishga tushiramiz (Render "Port scan timeout" bermasligi uchun)
    await start_web_server()
    
    # 2. Botni ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

