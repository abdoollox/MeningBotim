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

# Rasmlar va Videolar ID lari (Bularni botga rasm tashlab, ID sini olib o'zgartirasiz)
LOCKED_IMG_ID = "AgACAgIAAxkBA..." # Qulflangan chemodan ID si
OPENED_IMG_ID = "AgACAgIAAxkBA..." # Ochilgan chemodan ID si
RAD_ETISH_VIDEO_ID = "BAACAgIAAxkBAAPWaYGoqNqa7MS-YUfD1yKe0phpSfEAAoaTAALSnxBI0F8_tFFIS9U4BA"

# Botni sozlash
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- HOZIRCHA XOTIRA (DATABASE O'RNIGA) ---
# Foydalanuvchi ismini saqlab turish uchun
USER_NAMES = {} 

# --- STATES (HOLATLAR) ---
class UserState(StatesGroup):
    waiting_for_name = State() # Ism yozishini kutish

# --- FUNKSIYA: RASM CHIZISH (Universal) ---
def rasm_yaratish(ism, shablon_turi="invite"):
    """
    shablon_turi: 
    'invite' -> Taklifnoma (Xat)
    'ticket' -> Chipta
    """
    try:
        if shablon_turi == "invite":
            img_path = "assets/invite.jpg" # Taklifnoma foni
            font_size = 60
            y_offset = -200 # Matnni tepa-past qilish uchun
        else:
            img_path = "assets/ticket.jpg" # Chipta foni
            font_size = 45
            y_offset = 50 # Chiptada ism qayerda turishi kerakligi
            
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

# --- 1-QADAM: SEARCH QILIB KIRGANDA (/start) ---
@dp.message(Command("start"))
async def cmd_muggle_start(message: types.Message):
    # Banner: Qulflangan chemodan
    caption_text = (
        "🚫 **Diqqat, Magllar (Muggles)!**\n\n"
        "Siz oddiy odamlar ko'rishi mumkin bo'lmagan sehrli chemodan qarshisidasiz.\n\n"
        "🔒 Bu chemodan ichida **«Hogwarts Cinema»** ning eng nodir to'plamlari saqlanmoqda.\n"
        "Uni faqat haqiqiy sehrgarlargina ochish afsuni orqali ocha oladilar.\n\n"
        "Agar sehrgar bo'lsangiz, tayoqchangizni ishlating: /alohomora"
    )
    
    # Agar LOCKED_IMG_ID noto'g'ri bo'lsa, xato bermasligi uchun try-except
    try:
        await message.answer_photo(LOCKED_IMG_ID, caption=caption_text)
    except:
        await message.answer(caption_text) # Rasm yo'q bo'lsa matnni o'zi boradi

# --- 2-QADAM: ALOHOMORA (Chemodanni ochish) ---
@dp.message(Command("alohomora"))
async def cmd_open_suitcase(message: types.Message):
    # Banner: Ochilgan chemodan (Xat va Broshura ko'rinadi)
    
    caption_text = (
        "✨ **CLICK! Qulf ochildi!**\n\n"
        "Tabriklaymiz! Siz sehrli chemodanni ochdingiz.\n"
        "Ichida siz uchun atalgan **Muhrlangan Xat** va **Hogwarts Cinema** haqida ma'lumotlar bor.\n\n"
        "Xatda kimning ismi bo'lishini xohlaysiz?"
    )
    
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Xatni (Taklifnoma) olish", callback_data="get_invite_letter")]
    ])
    
    try:
        await message.answer_photo(OPENED_IMG_ID, caption=caption_text, reply_markup=tugma)
    except:
        await message.answer(caption_text, reply_markup=tugma)

# --- 3-QADAM: ISMNI SO'RASH ---
@dp.callback_query(F.data == "get_invite_letter")
async def ask_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete() # Eski xabarni o'chiramiz
    await callback.message.answer(
        "🖋 **Hogwarts taklifnomasiga kimning ismini yozamiz?**\n\n"
        "Iltimos, Ism va Familiyangizni yozib yuboring.\n"
        "_(Misol: Abdulloh Karimberdiyev)_"
    )
    await state.set_state(UserState.waiting_for_name)

# --- 4-QADAM: TAKLIFNOMA YARATISH VA INFO ---
@dp.message(StateFilter(UserState.waiting_for_name))
async def generate_invite(message: types.Message, state: FSMContext):
    ism = message.text
    user_id = message.from_user.id
    
    # Ismni xotiraga saqlab qo'yamiz (Keyinchalik Chipta uchun kerak bo'ladi)
    USER_NAMES[user_id] = ism
    
    await message.answer("⏳ Boyqushlar taklifnomangizni yozishmoqda...")
    
    # Taklifnoma (Invite) yaratish
    rasm = rasm_yaratish(ism, "invite")
    
    caption_text = (
        f"📩 **Sizga xat keldi, {ism}!**\n\n"
        "Siz rasman **«Hogwarts Cinema»** yopiq klubiga taklif qilindingiz.\n\n"
        "Lekin poyezdga chiqish uchun sizga **Platforma 9 ¾ Chiptasi** kerak bo'ladi.\n"
        "Guruh haqida to'liq ma'lumotni o'qib chiqing."
    )
    
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Guruh haqida ma'lumot", callback_data="show_info")]
    ])
    
    if rasm:
        await message.answer_photo(BufferedInputFile(rasm.read(), filename="invite.jpg"), caption=caption_text, reply_markup=tugma)
    else:
        await message.answer("Rasm yaratishda xatolik bo'ldi, lekin davom etishingiz mumkin.", reply_markup=tugma)
        
    await state.clear() # State dan chiqamiz

# --- 5-QADAM: MA'LUMOT VA CHIPTA SHARTI ---
@dp.callback_query(F.data == "show_info")
async def show_info_handler(callback: types.CallbackQuery):
    matn = (
        "🏰 **Hogwarts Cinema — Bu shunchaki kanal emas!**\n\n"
        "Bu yerda siz:\n"
        "🎬 Barcha 8 qism filmlarni 4K formatda;\n"
        "🎞 Kesilgan va rejissyorlik sahnalarini;\n"
        "🎧 O'zbek tilidagi professional audiokitoblarni topasiz.\n\n"
        "⚠️ **Kirish sharti:**\n"
        "Guruh yopiq va unga kirish uchun **Bir martalik Chipta** xarid qilishingiz kerak.\n"
        "Chipta narxi: **50 000 so'm** (Umrbod kirish)."
    )
    
    tugma = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎫 Chipta xarid qilish", callback_data="buy_ticket")]
    ])
    
    await callback.message.answer(matn, reply_markup=tugma, parse_mode="Markdown")

# --- 6-QADAM: TO'LOV MA'LUMOTLARI ---
@dp.callback_query(F.data == "buy_ticket")
async def payment_info(callback: types.CallbackQuery):
    matn = (
        f"💳 **Gringotts Banki hisob raqami:**\n`{KARTA_RAQAM}`\n{KARTA_EGA}\n\n"
        f"💰 **To'lov miqdori:** {MAHSULOT_NARXI}\n\n"
        "❗️ To'lov qilganingizdan so'ng, **chek rasmini** (skrinshot) shu yerga yuboring.\n"
        "Bizning goblinlar tekshirib, sizga **Chipta** yuborishadi."
    )
    await callback.message.answer(matn, parse_mode="Markdown")

# --- 7-QADAM: CHEKNI QABUL QILISH ---
@dp.message(F.photo | F.document)
async def handle_receipt(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or "nomalum"
    
    # Admin uchun tugmalar
    admin_tugma = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
        ]
    ])
    
    caption_text = f"📩 **Yangi to'lov!**\n👤: {first_name} (@{username})\nID: {user_id}"
    
    # Adminga yuborish
    try:
        if message.photo:
            await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption_text, reply_markup=admin_tugma)
        elif message.document:
            await bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption=caption_text, reply_markup=admin_tugma)
            
        # Mijozga javob (Gringotts uslubida)
        kutish_matni = (
            "🦉 **Chek qabul qilindi!**\n\n"
            "Gringotts goblinlari 🧐 to'lovni tekshirishni boshlashdi.\n"
            "Agar hammasi joyida bo'lsa, tez orada sizga **Platforma 9 ¾ Chiptasi** yuboriladi.\n\n"
            "_Tekshirish vaqti: 10 daqiqadan 8 soatgacha._"
        )
        await message.answer(kutish_matni, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer("Xatolik: Adminga yuborib bo'lmadi.")

# --- 8-QADAM: ADMIN JAVOBI (RAD ETISH) ---
@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    rad_matni = (
        "🏦 **Gringotts Banki xabarnomasi**\n\n"
        "Goblinlar chekni haqiqiy emas deb topishdi. 🙅‍♂️\n"
        "Iltimos, to'lovni qayta tekshirib, haqiqiy chekni yuboring."
    )
    
    try:
        await bot.send_video(chat_id=user_id, video=RAD_ETISH_VIDEO_ID, caption=rad_matni)
        await callback.message.edit_caption(caption=f"❌ {callback.message.caption}\n\n<b>RAD ETILDI</b>", parse_mode="HTML")
    except Exception as e:
        await callback.message.answer(f"Xatolik: {e}")

# --- 9-QADAM: ADMIN JAVOBI (TASDIQLASH VA CHIPTA BERISH) ---
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[1])
        
        # Ismni xotiradan olamiz. Agar topilmasa "Talaba" deb yozamiz
        mijoz_ismi = USER_NAMES.get(user_id, "Talaba")
        
        await bot.send_message(user_id, "✅ To'lov tasdiqlandi! Chiptangiz bosilmoqda...")
        
        # 1. CHIPTA YARATISH (Ticket)
        chipta_rasmi = rasm_yaratish(mijoz_ismi, "ticket")
        
        # 2. Link yaratish
        link = await bot.create_chat_invite_link(chat_id=GURUH_ID, member_limit=1)
        
        # 3. Tugma
        stansiya_tugmasi = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚂 Platforma 9 ¾ (Guruhga kirish)", url=link.invite_link)]
        ])
        
        caption_text = (
            f"🎫 **CHIPTANGIZ TAYYOR, {mijoz_ismi}!**\n\n"
            "Xogvarts Ekspressi jo'nashga tayyor. 🚂\n"
            "Quyidagi tugmani bosib, sehrli olamga kiring!\n\n"
            "👋 **Xush kelibsiz!**"
        )
        
        if chipta_rasmi:
            await bot.send_photo(
                chat_id=user_id,
                photo=BufferedInputFile(chipta_rasmi.read(), filename="chipta.jpg"),
                caption=caption_text,
                reply_markup=stansiya_tugmasi,
                parse_mode="Markdown"
            )
        else:
            await bot.send_message(chat_id=user_id, text=caption_text, reply_markup=stansiya_tugmasi)
            
        # Adminga o'zgarish
        await callback.message.edit_caption(caption=f"✅ {callback.message.caption}\n\n<b>TASDIQLANDI (Chipta berildi)</b>", parse_mode="HTML")
        
    except Exception as e:
        await callback.message.answer(f"Xatolik: {e}")


# --- SERVER SOZLAMALARI ---
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

# --- VIDEO ID OLSISH (Yordamchi) ---
@dp.message(F.video)
async def video_id_olish(message: types.Message):
    await message.reply(f"`{message.video.file_id}`", parse_mode="Markdown")

# --- RASM ID OLSISH (Yordamchi) ---
@dp.message(F.photo)
async def photo_id_olish(message: types.Message):
    await message.reply(f"`{message.photo[-1].file_id}`", parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
