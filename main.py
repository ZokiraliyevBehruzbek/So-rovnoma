import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
import asyncio
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

API_TOKEN = '8142576403:AAE-WVpabtixSvM3oQiIukIryefNNu2SObI'
CHANNEL_ID = '@dium_15'  # Majburiy obuna bo'lish kerak bo'lgan kanal

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# SQLAlchemy ma'lumotlar bazasi
DATABASE_URL = "sqlite:///vote.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Ovozlar va foydalanuvchilarni saqlash uchun model
class Vote(Base):
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)
    teacher_name = Column(String)

# Jadvalni yaratish
Base.metadata.create_all(engine)

# Ustozlar ro'yxati va ovozlarni saqlash
ustozlar = [
    "Abdulhakimova Surayyo 1-A",
    "Rahmonova Barno 1-B",
    "Tur'gunboyeva Latofat 1-D",
    "Ergasheva Shoira 2-A",
    "Egamqulova Kimyo 2-B",
    "Sulaymonova Nazokat 2-D",
    "Madaliyeva Tabassum 3-A",
    "To'xtanova Gulbahor 3-B",
    "Mamatqulova Zamira 4-A",
    "Madaliyeva Munisa 4-B",
    "Zokirova Dilobar 5-A",
    "Abdurahimova Hilola 5-B",
    "Sayfullayeva Fotima 6-A",
    "Abdulhakimova Mashhura 6-B",
    "Ismoilova Nargiza 6-D",
    "Mamatqulova Shaxzoda 7-A",
    "Yunusaliyeva Mashhura 7-B",
    "Kimsanova Dilnura 8-A",
    "Madg'oziyeva Gulsara 8-B",
    "Pozilova Feruza 9-A",
    "Sharofiddinova Muxlisa 9-B",
    "Hushnazarova Dilfuza 10",
    "Mamatova Zarifa 11"
]
ovozlar = {ustoz: 0 for ustoz in ustozlar}
all_ovozlar = 0  # Umumiy ovoz berganlar soni

# Start komandasi
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

    if chat_member.status != "left":
        markup = InlineKeyboardBuilder()
        for i, ustoz in enumerate(ustozlar, start=1):
            markup.button(text=f"{i}. {ustoz}", callback_data=str(i))
        markup.adjust(1)
        await message.answer("Quyidagi ustozlardan biriga ovoz bering:", reply_markup=markup.as_markup())
    else:
        # Foydalanuvchi obuna bo'lmagan bo'lsa
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Obuna bo'lish 📢", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_subscription")]
        ])
        await message.answer("Siz kanalga obuna bo'lishingiz kerak!", reply_markup=markup)

# Obunani tekshirish tugmasi
@dp.callback_query(F.data == "check_subscription")
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    if chat_member.status != "left":
        markup = InlineKeyboardBuilder()
        for i, ustoz in enumerate(ustozlar, start=1):
            markup.button(text=f"{i}. {ustoz}", callback_data=str(i))
        markup.adjust(1)
        await callback_query.message.answer("Rahmat! Endi ustozga ovoz bering:", reply_markup=markup.as_markup())
    else:
        await callback_query.answer("Hali ham obuna bo'lmadingiz!", show_alert=True)

# Ovoz berish jarayoni
@dp.callback_query(F.data.isdigit())
async def vote(callback_query: types.CallbackQuery):
    ustoz_index = int(callback_query.data) - 1
    selected_ustoz = ustozlar[ustoz_index]
    await callback_query.message.answer(f"Siz {selected_ustoz}ga ovoz berishga. Rozimisiz?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ha", callback_data=f"confirm_{ustoz_index}")],
        [InlineKeyboardButton(text="Yo'q", callback_data="retry_vote")]
    ]))

# Ovoz berishni tasdiqlash
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_vote(callback_query: types.CallbackQuery):
    ustoz_index = int(callback_query.data.split("_")[1])
    selected_ustoz = ustozlar[ustoz_index]

    # Eski xabarni o'chirish
    await callback_query.message.delete()

    # SQL ma'lumotlar bazasiga ovoz qo'shish
    user_id = callback_query.from_user.id
    session = Session()
    existing_vote = session.query(Vote).filter(Vote.user_id == str(user_id)).first()
    
    if existing_vote is None:
        new_vote = Vote(user_id=str(user_id), teacher_name=selected_ustoz)
        session.add(new_vote)
        session.commit()
        
        ovozlar[selected_ustoz] += 1
        global all_ovozlar
        all_ovozlar += 1
        await callback_query.message.answer(f"Rahmat! Siz {selected_ustoz} ga ovoz berdingiz.")
    else:
        await callback_query.message.answer("Siz allaqachon ovoz bergansiz!")
    
    session.close()

# Ovoz berishni qayta boshlash
@dp.callback_query(F.data == "retry_vote")
async def retry_vote(callback_query: types.CallbackQuery):
    markup = InlineKeyboardBuilder()
    for i, ustoz in enumerate(ustozlar, start=1):
        markup.button(text=f"{i}. {ustoz}", callback_data=str(i))
    markup.adjust(1)
    await callback_query.message.answer("Qaytadan ustozga ovoz bering:", reply_markup=markup.as_markup())

# Admin panel
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Reyting", callback_data="show_ratings")],
        [InlineKeyboardButton(text="Barcha ovozlar", callback_data="show_all_votes")],
        [InlineKeyboardButton(text="Ovozlarni 0ga tushirish", callback_data="reset_votes")]
    ])
    await message.answer("Admin panel:", reply_markup=markup)

# Reytingni ko'rsatish
@dp.callback_query(F.data == "show_ratings")
async def show_ratings(callback_query: types.CallbackQuery):
    text = "\n".join([f"{ustoz}: {ovoz} ta ovoz" for ustoz, ovoz in ovozlar.items()])
    await callback_query.message.answer(text)

# Barcha ovozlarni ko'rsatish
@dp.callback_query(F.data == "show_all_votes")
async def show_all_votes(callback_query: types.CallbackQuery):
    await callback_query.message.answer(f"Umumiy ovoz berganlar soni: {all_ovozlar}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())