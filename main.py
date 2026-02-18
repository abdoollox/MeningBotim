import asyncio
import logging
import os
import sys
import io
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from PIL import Image, ImageDraw, ImageFont

# --- SOZLAMALAR ---
API_TOKEN = '8544270521:AAFHqHVqY9ZuhfsdY5vfhVu5DtsP6Pz_MWU'
GURUH_ID = -1003369300068
ADMIN_ID = 7566631808
KARTA_RAQAM = "5614 6814 0351 0260"
KARTA_EGA = "KARIMBERDIYEV ABDULLOH"
MAHSULOT_NARXI = "50 000 so'm"

# Rasmlar va Videolar ID lari
LOCKED_IMG_ID = "AgACAgIAAxkBAAEg3zdpggpLHvTAVachHZH85O40qpW5igAChgxrGxJUEUhwB0RJaTX9PAEAAwIAA3gAAzgE" 
OPENED_IMG_ID = "AgACAgIAAxkBAAIBLWmDZ3Ayni9rRSVEvhjpNzNnMNjxAAK2EGsbElQZSFWpvS_4YYirAQADAgADeQADOAQ"
RAD_ETISH_VIDEO_ID = "BAACAgIAAxkBAAPWaYGoqNqa7MS-YUfD1yKe0phpSfEAAoaTAALSnxBI0F8_tFFIS9U4BA"
GOBLIN_CHECK_ID = "AgACAgIAAxkBAAIBgmmDtnNGAdxQApSRrYFCEKiv2HQYAAJsE2sbElQZSDJ0xk6En6WBAQADAgADeQADOAQ"
RAD_ETISH_IMG_ID = "AgACAgIAAxkBAAIBkGmDvYqpIyW_PMMYejTFW6UuuRdeAAKQE2sbElQZSDEI3IolpDreAQADAgADeQADOAQ"

# Botni sozlash
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- HOZIRCHA XOTIRA ---
USER_NAMES = {} 

# --- STATES (HOLATLAR) ---
class UserState(StatesGroup):
    waiting_for_name = State() 

# --- FUNKSIYA: RASM CHIZISH ---
def rasm_yaratish(ism, shablon_turi="invite"):
    try:
        if shablon_turi == "invite":
            img_path = "assets/invite.jpg" 
            font_size = 60
            y_offset = -50 
        else:
            img_path = "assets/ticket.jpg" 
            font_size = 45
            y_offset = 1000 
            
        img = Image.open(img_path)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("assets/font.TTF", size=font_size)
        
        W, H = img.size
        _, _, w, h = draw.textbbox((0, 0), ism, font=font)
        
        x_joyi = (W - w) / 2
        y_joyi = (H - h) / 2 + y_offset
        
        draw.text((x_joyi, y_joyi), ism, font=font, fill="black")
        
        bio = io.BytesIO()
        bio.name = f'{shablon_turi}.jpg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
    except Exception as e:
        logging.error(f"Rasm chizishda xatolik: {e}")
        return None

# --- 1-QADAM: START ---
@dp.message(Command("start"))
async def cmd_muggle_start(message: types.Message):
    caption_text = (
        "Menimcha siz magl ya'ni oddiy odam bo'lsangiz kerak!\n\n"
        "Sababi, chemodanni magllar ocha olmaydi. Ichida «Hogwarts Cinema» ning yashirin xazinasi bor.\n\n"
        "🗝 Agar siz sehrgar bo‘lsangiz, qulfni ochish uchun nima qilishni bilasiz.\n\n"
    )
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪄 Alohomora", callback_data="alohomora_action")]
    ])
    try:
        await message.answer_photo(LOCKED_IMG_ID, caption=caption_text, reply_markup=tugma, parse_mode="Markdown")
    except:
        await message.answer(caption_text, reply_markup=tugma, parse_mode="Markdown")

@dp.callback_query(F.data == "alohomora_action")
async def alohomora_tugma_bosildi(callback: types.CallbackQuery):
    # 1. "Sehr ishlamoqda..." yozuvi chiqadi
    await callback.answer("Sehr ishlamoqda... ✨", show_alert=False)
    
    # 2. 3 soniya kutib turamiz (Afsun ta'sir qilishi uchun)
    await asyncio.sleep(3) 
    
    # 3. Va nihoyat chemodan ochiladi
    await cmd_open_suitcase(callback.message)

# --- 2-QADAM: ALOHOMORA ---
@dp.message(Command("alohomora"))
async def cmd_open_suitcase(message: types.Message):
    caption_text = (
        "🔓 Qulf ochildi!\n\n"
        "✨ Tabriklaymiz! Siz sehrli chemodanni ochdingiz.\n"
        "Ichida qandaydir narsalar va muhrlangan xat borga o'xshayapti.\n\n"
        "🤔 Xat kim uchun atalgan ekan? Qiziq!"
    )
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Xatni ochish", callback_data="get_invite_letter")]
    ])
    try:
        await message.answer_photo(OPENED_IMG_ID, caption=caption_text, reply_markup=tugma)
    except:
        await message.answer(caption_text, reply_markup=tugma)

# --- 3-QADAM: ISMNI SO'RASH ---
@dp.callback_query(F.data == "get_invite_letter")
async def ask_name(callback: types.CallbackQuery, state: FSMContext):
    # 1. Pop-up xabar chiqaramiz (Xat ochilmoqda)
    await callback.answer("Xat ochilmoqda... 📩", show_alert=False)
    
    # 2. 3 soniya kutamiz (Kutish hissini berish uchun)
    await asyncio.sleep(3)
    
    # 3. Keyingi xabarni yuboramiz va ism so'raymiz
    await callback.message.answer(
        "📜 Xat ochildi!\n\n"
        "🧐 Qiziq, qiziq, juda ham qiziq...\n\n"
        "Sizning ism va familyangiz nima edi?\n\n"
        "🔎 Tekshirib olishimiz uchun ismingizni to'liq holda yoza olasizmi?"
    )
    # Holatni ism kutish rejimiga o'tkazamiz
    await state.set_state(UserState.waiting_for_name)

# --- 4-QADAM: TAKLIFNOMA YARATISH ---
@dp.message(StateFilter(UserState.waiting_for_name))
async def generate_invite(message: types.Message, state: FSMContext):
    ism = message.text
    user_id = message.from_user.id
    USER_NAMES[user_id] = ism
    
    await bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    rasm = rasm_yaratish(ism, "invite")
    
    caption_text = (
        f"🫨 {ism}, xat siz uchun yozilgan ekan!\n\n"
        "Siz rasman «Hogwarts Cinema» yopiq klubiga taklif qilinibsiz. Bu qanchalik baxt!\n\n"
        "«Hogwarts Cinema» klubi haqida eshitganmisiz? Agar yo'q bo'lsa, xatni davomini o'qing!"
    )
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Xatning davomini o'qish", callback_data="show_info")]
    ])
    
    if rasm:
        await message.answer_photo(BufferedInputFile(rasm.read(), filename="invite.jpg"), caption=caption_text, reply_markup=tugma)
    else:
        await message.answer("Rasm yaratishda xatolik, lekin davom eting.", reply_markup=tugma)
    await state.clear()

# --- 5-QADAM: MA'LUMOT ---
@dp.callback_query(F.data == "show_info")
async def show_info_handler(callback: types.CallbackQuery):
    XAT_PAST_ID = "AgACAgIAAxkBAAIBUmmDh7oFbWda6w83ehovduXBLX4OAAL9EWsbElQZSIWIAAGNZ-Sw4QEAAwIAA3gAAzgE" 
    matn = (
        "🏰 «Hogwarts Cinema» — Bu shunchaki guruh emas!\n\n"
        
        "Bu yerda siz:\n"
        "🎬 «Garri Potter» asarining barcha filmlarini 4K formatda\n"
        "🌍 3 xil tilda: ingliz, rus va o'zbek tillarida\n"
        "🎶 8 ta filming soundtrek albomlarini\n"
        "📚 Asarning barcha 8 ta elektron kitoblarini\n"
        "🎧 Kitoblarning audio shakladi audikitoblarini\n"
        "🎨 San'at asari darajasida chizilgan posterlar to'plamini\n"
        "🎮 Sehrli olam uchun ishlab chiqilgan mobil va kompyuter o'yinlarini\n"
        "👥 Siz kabilar jamlangan jamiyat bor\n\n"
        
        "1️⃣ «Hogwarts»ga ketish uchun faqat bir dona qadam qoldi.\n"
        "🚂 Poyezdga chiqish uchun sizda Platform 9¾ chiptasi bo'lishi kerak!"
    )
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎫 Chipta xarid qilish", callback_data="buy_ticket")]
    ])
    try:
        await callback.message.answer_photo(photo=XAT_PAST_ID, caption=matn, reply_markup=tugma, parse_mode="Markdown")
    except:
        await callback.message.answer(matn, reply_markup=tugma, parse_mode="Markdown")

# --- 6-QADAM: TO'LOV MA'LUMOTLARI ---
@dp.callback_query(F.data == "buy_ticket")
async def payment_info(callback: types.CallbackQuery):
    TO_LOV_RASMI_ID = "AgACAgIAAxkBAAIBdGmDsD9t3C-hmRVIRIxfWtO-Wu_9AAJLE2sbElQZSP4w9uywRSKdAQADAgADeQADOAQ" 
    matn = (
        f"💳 **Gringotts Banki hisob raqami:**\n`{KARTA_RAQAM}`\n{KARTA_EGA}\n\n"
        
        f"💰 **To'lov miqdori:** {MAHSULOT_NARXI}\n\n"
        
        "❗️ To'lov qilganingizdan so'ng, **chek rasmini** (skrinshot) shu yerga yuboring.\n\n"
        
        "🔎 Bizning goblinlar tekshirib, sizga Chipta yuborishadi."
    )
    try:
        await callback.message.answer_photo(photo=TO_LOV_RASMI_ID, caption=matn, parse_mode="Markdown")
    except:
        await callback.message.answer(matn, parse_mode="Markdown")

# --- 7-QADAM: CHEK QABUL QILISH (Guruhda ishlamaydi) ---
@dp.message((F.photo | F.document) & (F.chat.type == "private"))
async def handle_receipt(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        file_id = message.photo[-1].file_id if message.photo else message.document.file_id
        await message.reply(f"🔑 <b>Fayl ID:</b>\n<code>{file_id}</code>", parse_mode="HTML")
        return 

    first_name = message.from_user.first_name
    admin_tugma = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
        ]
    ])
    caption_text = f"📩 **Yangi to'lov!**\n👤: {first_name}\nID: {user_id}"
    
    try:
        if message.photo:
            await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption_text, reply_markup=admin_tugma)
        elif message.document:
            await bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption=caption_text, reply_markup=admin_tugma)
            
        kutish_matni = (
            "🦉 Chek ukkilar tomonidan bankka yuborildi!\n\n"
            
            "🧐 Gringotts goblinlari to'lovni tekshirishni boshlashdi. Agar hammasi joyida bo'lsa, tez orada sizga Platforma 9¾ chiptasi yuboriladi.\n\n"
            
            "⏳ Tekshirish vaqti: 10 daqiqadan 8 soatgacha.\n"
            "💯 Kutganingizdan ortiq qiymat olishingizga ishonamiz!"
                       )
        try:
            await message.answer_photo(photo=GOBLIN_CHECK_ID, caption=kutish_matni, parse_mode="Markdown")
        except:
            await message.answer(kutish_matni, parse_mode="Markdown")
    except Exception as e:
        await message.answer("Xatolik: Adminga yuborib bo'lmadi.")

# --- 8-QADAM: RAD ETISH ---
@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    rad_matni = (
        "🚫 To'lov rad etildi!\n\n"
        
        "🧐 Gringotts goblinlari ushbu chekni haqiqiy emas deb topishdi yoki to'lov summasi noto'g'ri.\n\n"
        
        "Iltimos, qayta tekshirib, haqiqiy chekni yuboring!\n\n"
        
        "🚂 Aks holda poyezdga chiqishga kech qolishingiz mumkin."
                )
    try:
        await bot.send_photo(chat_id=user_id, photo=RAD_ETISH_IMG_ID, caption=rad_matni, parse_mode="Markdown")
        await callback.message.edit_caption(caption=f"❌ {callback.message.caption}\n\n<b>RAD ETILDI 🚫</b>", parse_mode="HTML")
    except Exception as e:
        await callback.message.answer(f"Xatolik: {e}")
        
# --- 9-QADAM: ADMIN JAVOBI ---
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[1])
        mijoz_ismi = USER_NAMES.get(user_id, "Talaba")
        chipta_rasmi = rasm_yaratish(mijoz_ismi, "ticket")
        link = await bot.create_chat_invite_link(chat_id=GURUH_ID, member_limit=1)
        stansiya_tugmasi = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚂 Platforma 9 ¾ (Guruhga kirish)", url=link.invite_link)]])
        
        caption_text = (
            "🎫 Mana sizning chiptangiz!\n\n"
            
            "🚂 Xogvarts Ekspress jo'nashga tayyor.\n\n"

            "👇 Quyidagi tugmani bosib, sehrli olamga kiring!"
                       )
        
        if chipta_rasmi:
            await bot.send_photo(chat_id=user_id, photo=BufferedInputFile(chipta_rasmi.read(), filename="chipta.jpg"), caption=caption_text, reply_markup=stansiya_tugmasi, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=user_id, text=caption_text, reply_markup=stansiya_tugmasi)
        await callback.message.edit_caption(caption=f"✅ {callback.message.caption}\n\n<b>TASDIQLANDI (Chipta berildi)</b>", parse_mode="HTML")
    except Exception as e:
        await callback.message.answer(f"Xatolik: {e}")

# --- RENDER UCHUN SERVER SOZLAMALARI ---
# Siz mana shu funksiyani o'chirib yuborgansiz. Uni qaytardim:
async def start_web_server():
    async def health_check(request):
        return web.Response(text="Bot is live!")
    
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")

# --- ASOSIY MAIN FUNKSIYASI ---
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # 1. Serverni fonda ishga tushiramiz
    asyncio.create_task(start_web_server())
    
    # 2. Botni ishga tushiramiz
    print("🚀 Bot va Server ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot to'xtatildi!")




