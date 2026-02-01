import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
API_TOKEN = '8544270521:AAELBt_yuonOegOF-nPl-nI2FH7fQ-JBwQE'  # BotFather bergan token
ADMIN_ID = 12345678  # O'zingizning ID raqamingiz (botga /start bosib bilib olasiz)
GURUH_ID = -1003369300068  # Guruh ID si
NARX = 1  # 1 Yulduz (Stars)

# Botni ishga tushirish
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. /start bosilganda video va tugma chiqarish
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Bu yerga videoning File ID sini qo'yasiz.
    # Agar File ID yo'q bo'lsa, pastdagi video_id o'rniga video fayl yo'lini (masalan: FSInputFile("video.mp4")) ishlating
    VIDEO_ID = "BAACAgIAAxkBAAIC..." # <-- Videoni botga tashlab ID sini oling

    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Sotib olish ({NARX} ⭐️)", callback_data="tulov_qilish")]
    ])
    
    # Agar VIDEO_ID bo'lmasa, vaqtincha oddiy xabar yuborib turadi:
    await message.answer("Mahsulot haqida ma'lumot. Sotib olish uchun tugmani bosing:", reply_markup=tugma)
    # Video bilan yuborish uchun bu qatorni oching:
    # await message.answer_video(video=VIDEO_ID, caption="Mahsulot haqida video", reply_markup=tugma)

# 2. To'lov schetini (Invoice) yuborish
@dp.callback_query(F.data == "tulov_qilish")
async def send_invoice(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Guruhga kirish",
        description="Hub guruhiga bir martalik havola",
        payload="hub_tolov_payload",
        provider_token="",  # Stars uchun bo'sh qoldiriladi
        currency="XTR",     # XTR - Telegram Stars valyutasi
        prices=[LabeledPrice(label="Kirish", amount=NARX)]
    )
    await callback.answer()

# 3. To'lovni tasdiqlash (Pre-checkout)
@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# 4. To'lov muvaffaqiyatli bo'lganda -> Link berish
@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    try:
        link = await bot.create_chat_invite_link(
            chat_id=GURUH_ID,
            member_limit=1,
            name=f"User {message.from_user.id}"
        )
        await message.answer(f"✅ To'lov qabul qilindi!\n\nSizning shaxsiy havolangiz:\n{link.invite_link}")
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")

# Video ID sini olish uchun yordamchi (Video tashlasangiz ID beradi)
@dp.message(F.video)
async def get_video_id(message: types.Message):
    await message.reply(f"Video ID: `{message.video.file_id}`", parse_mode="Markdown")

# Asosiy ishga tushirish qismi
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())