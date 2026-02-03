import asyncio
import logging
import os
import sys
import io  # <--- YANGI: Xotirada ishlash uchun
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from PIL import Image, ImageDraw, ImageFont  # <--- YANGI: Rasm chizish uchun

# --- SOZLAMALAR ---
API_TOKEN = '8544270521:AAFHqHVqY9ZuhfsdY5vfhVu5DtsP6Pz_MWU' 
GURUH_ID = -1003369300068  # Guruh ID
ADMIN_ID = 7566631808      # Admin ID
KARTA_RAQAM = "5614 6814 0351 0260"
KARTA_EGA = "KARIMBERDIYEV ABDULLOH"
MAHSULOT_NARXI = "50 000 so'm"
RAD_ETISH_VIDEO_ID = "AAMCAgADGQEAASDdiWmBouMVnoOXfra0gNWKHPPJemplAAKGkwAC0p8QSNTbYMXeQfaMAQAHbQADOAQ"

# Botni sozlash
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- YANGI QO'SHIMCHA: Ism kutish ro'yxati ---
# Bu yerda to'lovi tasdiqlangan, lekin hali ismini yozmagan odamlar turadi
ISM_KUTISH_ROYXATI = set()

# --- YANGI FUNKSIYA: RASM CHIZISH ---
def rasm_yaratish(ism):
    try:
        # 1. Shablonni ochamiz
        img = Image.open("assets/xat.jpg")
        draw = ImageDraw.Draw(img)
        
        # 2. Shriftni yuklaymiz (O'lchamini rasmga qarab to'g'irlash kerak bo'lishi mumkin)
        # size=60 degan joyini kattaroq yoki kichikroq qilib ko'rasiz
        font = ImageFont.truetype("assets/font.TTF", size=60)
        
        # 3. Matnni o'rtaga joylashtirish hisob-kitobi
        # Rasmning o'lchamlari
        W, H = img.size
        # Matnning o'lchamlari
        _, _, w, h = draw.textbbox((0, 0), ism, font=font)
        
        # Koordinatalar (Matn rasmning qoq o'rtasiga tushadi)
        # Agar teparoqqa yoki pastroqqa surmoqchi bo'lsangiz:
        # (H - h) / 2 + 100  (Masalan, +100 pastga suradi)
        x_joyi = (W - w) / 2
        y_joyi = (H - h) / 2 - 240 
        
        # 4. Ismni yozamiz (Rangi: Qora - "black" yoki To'q yashil - "#0b3d0b")
        draw.text((x_joyi, y_joyi), ism, font=font, fill="black")
        
        # 5. Rasmni kompyuter xotirasiga (fayl qilib emas, bayt qilib) saqlaymiz
        bio = io.BytesIO()
        bio.name = 'hogwarts_letter.jpg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
    except Exception as e:
        logging.error(f"Rasm chizishda xatolik: {e}")
        return None

# --- BOT HANDLERLARI ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Sotib olish ({MAHSULOT_NARXI})", callback_data="karta_bilan_tolash")]
    ])
    try:
        # Agar MEDIA_ID bo'lmasa, oddiy matn chiqaradi
        await message.answer("Mahsulot haqida ma'lumot.", reply_markup=tugma)
    except:
        await message.answer("Xush kelibsiz!", reply_markup=tugma)

@dp.callback_query(F.data == "karta_bilan_tolash")
async def send_card_info(callback: types.CallbackQuery):
    matn = (
        f"💳 **To'lov uchun karta:**\n`{KARTA_RAQAM}`\n{KARTA_EGA}\n\n"
        f"💰 **Narxi:** {MAHSULOT_NARXI}\n\n"
        "❗️ Chekni rasm yoki fayl ko'rinishida yuboring.\n"
    )
    await callback.message.answer(matn, parse_mode="Markdown")
    await callback.answer()

@dp.message(F.photo | F.document)
async def check_receipt(message: types.Message):
    user_id = message.from_user.id
    # Mijoz ismini olib qolamiz (keyinroq xatga yozish uchun)
    first_name = message.from_user.first_name
    username = message.from_user.username or "Noma'lum"
    
    # Callback data ichiga ismni ham yashirib ketamiz (faqat qisqa ism)
    # Ehtiyot bo'lish kerak: Telegram callback data 64 baytdan oshmasligi kerak.
    # Shuning uchun ismni kesib olmaymiz, uni keyin foydalanuvchi IDsi orqali olamiz.
    
    admin_tugma = InlineKeyboardMarkup(inline_keyboard=[
        [
            # confirm_USERID_ISM deb yuboramiz (faqat birinchi so'zini)
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
        ]
    ])
    
    caption_text = f"📩 **Yangi chek!**\n👤: {first_name} (@{username})\nID: {user_id}"

    if message.photo:
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption_text, reply_markup=admin_tugma)
    elif message.document:
        await bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption=caption_text, reply_markup=admin_tugma)
    
    await message.answer("⏳ Chek qabul qilindi! Tez orada javob olasiz.\n"
                        "⏳ Tekshirish vaqti uzog'i 8 soatgacha davom etadi.\n"
                         "💯 Kutganingizdan ortiq qiymat olishingizga ishonamiz!")

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[1])
        
        # 1. Mijozni "Ism kutish" ro'yxatiga qo'shamiz
        ISM_KUTISH_ROYXATI.add(user_id)
        
        # 2. Mijozga xabar yuboramiz
        await bot.send_message(
            chat_id=user_id,
            text="✅ **To'lov tasdiqlandi!**\n\nIltimos, Hogwarts xatiga yozishimiz uchun **Ism va Familiyangizni** yozib yuboring.\n\n*Misol: Abdulloh Karimberdiyev*",
            parse_mode="Markdown"
        )
        
        # 3. Adminga xabar (O'zgardi)
        await callback.message.edit_caption(
            caption=f"✅ {callback.message.caption}\n\n<b>TASDIQLANDI. Mijozdan ism kutilmoqda...</b>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.answer(f"Xatolik: {e}")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    rad_etish_matni = (
        "🏦 Gringotts Banki xabarnomasi\n\n"
        
        "Afsuski, bu chek qalbakiga o'xshaydi yoki unda xatolik bor. "
        "Goblinlar uni qabul qilishmadi. 🙅‍♂️\n\n"
        
        "Iltimos, qaytadan tekshirib, to'g'ri chekni yuboring."
    )
    
    # VIDEO YUBORISH
    await bot.send_video(
        chat_id=user_id,
        video=RAD_ETISH_VIDEO_ID,
        caption=rad_etish_matni,
        parse_mode="Markdown"
    )
    
    await callback.message.edit_caption(caption=f"❌ {callback.message.caption}\n\n**RAD ETILDI (Video yuborildi)**")

# --- YANGI FUNKSIYA: Ismni qabul qilish va Tugma bilan yuborish ---
@dp.message(F.text)
async def ism_qabul_qilish(message: types.Message):
    user_id = message.from_user.id
    
    # Agar bu odam to'lov qilganlar ro'yxatida bo'lsa:
    if user_id in ISM_KUTISH_ROYXATI:
        
        haqiqiy_ism = message.text
        
        # Ism uzunligini tekshirish
        if len(haqiqiy_ism) > 30:
            await message.answer("Ism juda uzun! Iltimos, qisqaroq qilib (Masalan: Ism Familiya) qayta yuboring.")
            return

        await message.answer("⏳ Ism qabul qilindi. Sehrli xat va chipta tayyorlanmoqda...")

        try:
            # 1. RASM CHIZAMIZ
            xat_rasmi = rasm_yaratish(haqiqiy_ism)
            
            # 2. Link yaratish
            link = await bot.create_chat_invite_link(chat_id=GURUH_ID, member_limit=1)
            
            # 3. LINKNI TUGMAGA JOYLASH (YANGI QISM)
            # url=link.invite_link -> Bu tugmani bosganda guruhga olib o'tadi
            stansiya_tugmasi = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚂 Platforma 9 ¾ (Kirish)", url=link.invite_link)]
            ])
            
            # 4. Javob matni (Linkni olib tashladik, o'rniga ko'rsatma yozdik)
            success_caption = (
                f"🦉 ✉️\n\n"
                
                f"<b>{haqiqiy_ism}, «Garri Potter Cinema» guruhiga qabul qilindingiz!</b>\n\n"

                f"🎫 Bu chipta faqat siz uchun!\n\n"
                
                f"🕰 Poyezd jo'nashiga oz qoldi!\n\n"
                
                f"👇 Guruhga qo'shilish uchun pastdagi <b>Platforma 9 ¾</b> tugmasini bosing!"
            )
            
            # 5. Yuborish (reply_markup=stansiya_tugmasi qo'shildi)
            if xat_rasmi:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=BufferedInputFile(xat_rasmi.read(), filename="xat.jpg"),
                    caption=success_caption,
                    reply_markup=stansiya_tugmasi, # <--- Tugma shu yerda
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=user_id, 
                    text=success_caption, 
                    reply_markup=stansiya_tugmasi,
                    parse_mode="HTML"
                )
            
            # 6. Ro'yxatdan o'chiramiz
            ISM_KUTISH_ROYXATI.discard(user_id)
            
        except Exception as e:
            await message.answer(f"Xatolik yuz berdi: {e}")

# --- VEB SERVER ---
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

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())













