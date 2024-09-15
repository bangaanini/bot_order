import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from pymongo import MongoClient
from dotenv import load_dotenv
from telegram.error import TimedOut
from bson import ObjectId

# Memuat variabel dari file .env
load_dotenv()

# Mendapatkan MongoDB URI dan Bot Token dari file .env
MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Konfigurasi koneksi MongoDB
client = MongoClient(MONGO_URI)
db = client["db_price"]
collection = db["db_price"]

# Fungsi untuk memulai bot dan menampilkan kategori
def start(update: Update, context: CallbackContext) -> None:
    produk = collection.find()
    kategori_list = {item['kategori'] for item in produk}  # Set untuk menghilangkan duplikat
    
    # Buat tombol inline untuk kategori
    keyboard = [[InlineKeyboardButton(kategori, callback_data=f"kategori:{kategori}")] for kategori in kategori_list]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text("<b>Selamat datang!</b>\nIni adalah layanan bot order dari @arsylastoree\nJika ada yang ingin ditanyakan bisa langsung hubungi admin.\nAdmin : @aanhendri\n\n<b>Silahkan Pilih Kategori:</b>",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )

# Fungsi untuk menangani pilihan kategori
def kategori_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    kategori_terpilih = query.data.split(":")[1]
    produk = collection.find({"kategori": kategori_terpilih})
    layanan_list = {item['layanan'] for item in produk}  # Menggunakan set untuk menghindari duplikat
    context.user_data['kategori'] = kategori_terpilih

    if layanan_list:
        keyboard = [
            [InlineKeyboardButton(layanan, callback_data=f"layanan:{layanan}")] for layanan in layanan_list
        ]
        keyboard.append([InlineKeyboardButton("Kembali", callback_data="back:start")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=f"<b>LAYANAN DALAM KATEGORI {kategori_terpilih}</b>:", 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.HTML
        )
    else:
        query.edit_message_text(text=f"Tidak ada layanan dalam kategori {kategori_terpilih}.")



# Fungsi untuk menangani pilihan layanan
def layanan_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    layanan_terpilih = query.data.split(":")[1]
    context.user_data['layanan'] = layanan_terpilih  # Simpan layanan terpilih
    kategori_terpilih = context.user_data.get('kategori')
    
    # Ambil paket berdasarkan layanan yang dipilih
    produk = collection.find({"layanan": layanan_terpilih})
    
    # Buat pesan untuk menampilkan paket-paket yang tersedia
    response = f"ʚ ═══･୨ <b>{layanan_terpilih.upper()}</b> ୧･═══ ɞ\n==========================\n\n"
    paket_dict = {}
    
    for item in produk:
        paket = item['paket']
        if paket not in paket_dict:
            paket_dict[paket] = {
                'deskripsi': item['deskripsi'],
                'durasi_harga': []
            }
        paket_dict[paket]['durasi_harga'].append((item['durasi'], item['harga']))
    
    # Format output untuk setiap paket
    for paket, details in paket_dict.items():
        response += f"°࿐ •<b>{paket}</b>:\n"
        response += f"╰►Deskripsi: {details['deskripsi']}\n"
        for durasi, harga in details['durasi_harga']:
            response += f"➥ {durasi} - Rp{harga}\n"
        response += "\n==========================\n\n"
    
    # Tambahkan tombol order di bagian akhir
    keyboard = [
        [InlineKeyboardButton("Order", callback_data=f"order:{layanan_terpilih}")],
        [InlineKeyboardButton("Kembali", callback_data=f"back:category:{kategori_terpilih}")]  # Tambahkan kategori ke callback data
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=response + "Silakan pilih paket yang Anda inginkan dengan menekan tombol di bawah.",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )

# Fungsi untuk menangani pemilihan paket setelah tombol "Order" ditekan
def order_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    layanan_terpilih = query.data.split(":")[1]
    context.user_data['layanan'] = layanan_terpilih  # Simpan layanan terpilih agar bisa kembali ke deskripsi layanan

    produk = collection.find({"layanan": layanan_terpilih})
    paket_list = {item['paket'] for item in produk}

    keyboard = [[InlineKeyboardButton(paket, callback_data=f"paket:{layanan_terpilih}:{paket}")] for paket in paket_list]
    
    # Tambahkan tombol kembali
    keyboard.append([InlineKeyboardButton("Kembali", callback_data=f"back:layanan:{layanan_terpilih}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(f"<b>SILAKAN PILIH PAKET UNTUK {layanan_terpilih.upper()}</b>:",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )

# Fungsi untuk menangani pemilihan durasi setelah paket dipilih
def paket_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data.split(":")
    layanan_terpilih = data[1]
    paket_terpilih = data[2]
    
    context.user_data['paket'] = paket_terpilih  # Simpan paket terpilih

    produk = collection.find({"layanan": layanan_terpilih, "paket": paket_terpilih})

    # Buat tombol untuk setiap durasi dan harga
    keyboard = [[InlineKeyboardButton(f"{item['durasi']} - Rp{item['harga']}", callback_data=f"durasi:{layanan_terpilih}:{paket_terpilih}:{item['durasi']}:{item['harga']}")] for item in produk]
    
    # Tambahkan tombol kembali di bawah tombol durasi
    keyboard.append([InlineKeyboardButton("Kembali", callback_data=f"back:paket:{layanan_terpilih}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(f"KAMU MEMILIH PAKET <b>{paket_terpilih}</b> DALAM LAYANAN <b>{layanan_terpilih.upper()}.</b>\n\n<b>SILAKAN PILIH DURASI:</b>",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )

# Fungsi untuk menangani pemilihan durasi dan harga
def durasi_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data.split(":")
    layanan_terpilih = data[1]
    paket_terpilih = data[2]
    durasi_terpilih = data[3]
    harga_terpilih = data[4]
    
    # Simpan data ke context.user_data
    context.user_data['layanan'] = layanan_terpilih
    context.user_data['paket'] = paket_terpilih
    context.user_data['durasi'] = durasi_terpilih
    context.user_data['harga'] = harga_terpilih

    # Pesan konfirmasi
    message = f"Kamu memilih paket <b>{paket_terpilih}</b> dalam layanan <b>{layanan_terpilih.upper()}</b> untuk durasi <b>{durasi_terpilih}</b> dengan harga <b>Rp {harga_terpilih}</b>.\n\n<b>Silakan pilih metode pembayaran.</b>"
    
    # Tombol metode pembayaran + tombol kembali
    keyboard = [
        [InlineKeyboardButton("Dana", callback_data=f"payment:dana:{harga_terpilih}"),
         InlineKeyboardButton("GoPay", callback_data=f"payment:gopay:{harga_terpilih}")],
        [InlineKeyboardButton("QRIS", callback_data=f"payment:qris:{harga_terpilih}")],
        [InlineKeyboardButton("Kembali", callback_data=f"back:durasi:{layanan_terpilih}:{paket_terpilih}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=message,
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )

# Fungsi untuk menangani pemilihan metode pembayaran
def payment_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data.split(":")
    metode_pembayaran = data[1]
    harga = data[2]

    # Pesan sesuai metode pembayaran
    if metode_pembayaran == "dana":
        rekening = "081228121825 \nAtas nama: <b>Aan Hendri R</b>"
    elif metode_pembayaran == "gopay":
        rekening = "081228121825 \nAtas nama: <b>Aan Hendri R</b>"
    else:
        rekening = "[https://t.me/catatanstore/223]\n\nAtas nama: <b>Kelontong AH Visual</b>"

    message = f"Silakan bayar sejumlah <b>Rp {harga}</b> ke \n\n{rekening}.\n\n<b>Jangan lupa kirim bukti pembayaran di sini</b>"
    
    # Tambahkan tombol kembali di bawah pesan pembayaran
    keyboard = [
        [InlineKeyboardButton("Kembali", callback_data=f"back:payment:{harga}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text=message,
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )

# Mendapatkan Admin Chat ID dari file .env
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Fungsi untuk menangani pengiriman bukti pembayaran oleh pengguna
def payment_confirmation_handler(update: Update, context: CallbackContext) -> None:
    # Pastikan pengguna mengirim foto
    if update.message.photo:
        # Ambil foto bukti pembayaran
        photo_file = update.message.photo[-1].get_file()

        # Buat tombol di bawah pesan
        keyboard = [
            [InlineKeyboardButton("Kembali ke Menu Utama", callback_data="back:start")],
            [InlineKeyboardButton("Join Grup", url="https://t.me/arsylastoree")],
            [InlineKeyboardButton("Hubungi Admin", url="https://t.me/aanhendri")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Pesan konfirmasi untuk pengguna dengan tombol
        update.message.reply_text(
            "Terima kasih, bukti pembayaran sudah diterima. Pesanan Anda sedang diproses.",
            reply_markup=reply_markup
        )

        # Kirim bukti pembayaran dan detail pesanan ke admin
        send_to_admin(update, context, photo_file)
    else:
        # Jika pengguna tidak mengirim foto, beri tahu mereka
        update.message.reply_text("Silakan kirim bukti pembayaran berupa foto.")

# Fungsi untuk mengirim bukti pembayaran dan detail pesanan ke admin
def send_to_admin(update: Update, context: CallbackContext, photo_file) -> None:
    user = update.message.from_user
    # Ambil detail pesanan dari user_data
    layanan = context.user_data.get('layanan')
    paket = context.user_data.get('paket')
    durasi = context.user_data.get('durasi')
    harga = context.user_data.get('harga')
    
    caption = (
        f"Pesanan baru dari {user.first_name} {user.last_name or ''} (@{user.username or 'N/A'}):\n"
        f"Layanan: <b>{layanan}</b>\n"
        f"Paket: <b>{paket}</b>\n"
        f"Durasi: <b>{durasi}</b>\n"
        f"Harga: Rp{harga}\n"
    )
    
    # Kirim foto bukti pembayaran ke admin dengan caption yang benar
    context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo_file.file_id, caption=caption, parse_mode=ParseMode.HTML)

    # Informasikan admin untuk memproses pesanan
    context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Silakan cek dan proses pesanan tersebut.")
    
def error_handler(update, context):
    try:
        raise context.error
    except TimedOut:
        update.message.reply_text("Request timeout. Please try again.")
        
def back_to_start(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    produk = collection.find()
    kategori_list = {item['kategori'] for item in produk}

    keyboard = [[InlineKeyboardButton(kategori, callback_data=f"kategori:{kategori}")] for kategori in kategori_list]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text("<b>Selamat datang!</b>\nIni adalah layanan bot order dari @arsylastoree\nJika ada yang ingin ditanyakan bisa langsung hubungi admin.\nAdmin : @aanhendri\n\n<b>Silahkan Pilih Kategori</b>:",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )

def kembali_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    data = query.data.split(":")
    if len(data) == 3:
        kategori = data[2]  # Ambil kategori dari callback data
        context.user_data['kategori'] = kategori  # Simpan kategori yang dipilih

        produk = collection.find({"kategori": kategori})
        layanan_list = {item['layanan'] for item in produk}

        if layanan_list:
            keyboard = [
                [InlineKeyboardButton(layanan, callback_data=f"layanan:{layanan}")] for layanan in layanan_list
            ]
            keyboard.append([InlineKeyboardButton("•Kembali•", callback_data="back:start")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(text=f"<b>LAYANAN DALAM KATEGORI {kategori}</b>:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
            )
        else:
            query.edit_message_text(text=f"Tidak ada layanan dalam kategori {kategori}.")
    else:
        query.edit_message_text(text="Kategori tidak ditemukan.")
        
def layanan_kembali_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    # Ambil layanan terpilih dari callback data
    layanan_terpilih = query.data.split(":")[2]
    
    # Ambil produk dan format ulang respons
    produk = collection.find({"layanan": layanan_terpilih})
    
    response = f"ʚ ═══･୨ <b>{layanan_terpilih.upper()}</b> ୧･═══ ɞ\n==========================\n\n"
    paket_dict = {}
    
    for item in produk:
        paket = item['paket']
        if paket not in paket_dict:
            paket_dict[paket] = {
                'deskripsi': item['deskripsi'],
                'durasi_harga': []
            }
        paket_dict[paket]['durasi_harga'].append((item['durasi'], item['harga']))
    
    for paket, details in paket_dict.items():
        response += f"°࿐ •<b>{paket}</b>:\n"
        response += f"╰►Deskripsi: {details['deskripsi']}\n"
        for durasi, harga in details['durasi_harga']:
            response += f"➥ {durasi} - Rp{harga}\n"
        response += "\n==========================\n\n"

    # Tambahkan tombol order dan kembali
    keyboard = [
        [InlineKeyboardButton("Order", callback_data=f"order:{layanan_terpilih}")],
        [InlineKeyboardButton("•Kembali•", callback_data=f"back:category:{context.user_data.get('kategori')}")]  # Kembali ke daftar kategori
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=response + "Silakan pilih paket yang Anda inginkan dengan menekan tombol di bawah.",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )        
    
def back_to_paket_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    layanan_terpilih = query.data.split(":")[2]  # Ambil layanan dari callback data
    
    produk = collection.find({"layanan": layanan_terpilih})
    paket_list = {item['paket'] for item in produk}

    keyboard = [[InlineKeyboardButton(paket, callback_data=f"paket:{layanan_terpilih}:{paket}")] for paket in paket_list]
    
    # Tambahkan tombol kembali
    keyboard.append([InlineKeyboardButton("Kembali", callback_data=f"back:layanan:{layanan_terpilih}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(f"<b>SILAKAN PILIH PAKET UNTUK {layanan_terpilih.upper()}</b>:",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )    
    
def back_to_durasi_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data.split(":")
    layanan_terpilih = data[2]
    paket_terpilih = data[3]

    produk = collection.find({"layanan": layanan_terpilih, "paket": paket_terpilih})

    # Buat tombol durasi dan harga kembali
    keyboard = [[InlineKeyboardButton(f"{item['durasi']} - Rp{item['harga']}", callback_data=f"durasi:{layanan_terpilih}:{paket_terpilih}:{item['durasi']}:{item['harga']}")] for item in produk]
    
    # Tambahkan tombol kembali ke pilihan paket
    keyboard.append([InlineKeyboardButton("Kembali", callback_data=f"back:paket:{layanan_terpilih}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(f"KAMU MEMILIH PAKET <b>{paket_terpilih}</b> DI DALAM LAYANAN <b>{layanan_terpilih.upper()}</b>.\n\nSILAKAN PILIH DURASI:",
    reply_markup=reply_markup,
    parse_mode=ParseMode.HTML
    )    
    
def back_to_payment_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    # Cek apakah context.user_data memiliki layanan dan paket
    layanan_terpilih = context.user_data.get('layanan', None)
    paket_terpilih = context.user_data.get('paket', None)
    durasi_terpilih = context.user_data.get('durasi', None)
    harga_terpilih = context.user_data.get('harga', None)

    # Jika salah satu data tidak ada, kirim pesan error
    if not layanan_terpilih or not paket_terpilih or not durasi_terpilih or not harga_terpilih:
        query.edit_message_text("Data tidak lengkap, silakan ulangi dari awal.")
        return

    # Kembali ke pemilihan metode pembayaran
    keyboard = [
        [InlineKeyboardButton("Dana", callback_data=f"payment:dana:{harga_terpilih}"),
         InlineKeyboardButton("GoPay", callback_data=f"payment:gopay:{harga_terpilih}")],
        [InlineKeyboardButton("QRIS", callback_data=f"payment:qris:{harga_terpilih}")],
        [InlineKeyboardButton("Kembali", callback_data=f"back:durasi:{layanan_terpilih}:{paket_terpilih}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        f"Kamu memilih paket <b>{paket_terpilih}</b> dalam layanan <b>{layanan_terpilih.upper()}</b> untuk durasi <b>{durasi_terpilih}</b> dengan harga <b>Rp {harga_terpilih}</b>.\n\n<b>Silakan pilih metode pembayaran.</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
# Fungsi untuk membagi pesan panjang
def split_message(message, max_length=4096):
    """Membagi pesan menjadi beberapa bagian jika terlalu panjang."""
    parts = []
    while len(message) > max_length:
        split_pos = message.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(message[:split_pos])
        message = message[split_pos:].lstrip('\n')
    parts.append(message)
    return parts

# Perintah untuk menambah produk
def tambah_produk(update: Update, context: CallbackContext) -> None:
    try:
        args = ' '.join(context.args)
        lines = args.split('\n')

        for line in lines:
            parts = line.split(',')

            if len(parts) != 6:
                update.message.reply_text("Format input salah di baris: '{}'. Gunakan format: kategori,layanan,paket,\"deskripsi\",\"durasi\",harga".format(line))
                return

            produk_data = {
                "kategori": parts[0].strip(),
                "layanan": parts[1].strip(),
                "paket": parts[2].strip(),
                "deskripsi": parts[3].strip().strip('"'),
                "durasi": parts[4].strip().strip('"'),
                "harga": parts[5].strip(),
            }
            collection.insert_one(produk_data)
        
        update.message.reply_text("Produk telah ditambahkan.")
    except Exception as e:
        update.message.reply_text(f"Terjadi kesalahan: {e}")

# Perintah untuk melihat semua produk
def lihat_produk(update: Update, context: CallbackContext) -> None:
    produk = collection.find()
    response = "Produk yang ada di database:\n\n"
    
    for item in produk:
        response += (f"ID: {str(item.get('_id', 'Tidak tersedia'))}\n"
                     f"Kategori: {item.get('kategori', 'Tidak tersedia')}\n"
                     f"Layanan: {item.get('layanan', 'Tidak tersedia')}\n"
                     f"Paket: {item.get('paket', 'Tidak tersedia')}\n"
                     f"Deskripsi: {item.get('deskripsi', 'Tidak tersedia')}\n"
                     f"Durasi: {item.get('durasi', 'Tidak tersedia')}\n"
                     f"Harga: {item.get('harga', 'Tidak tersedia')}\n\n")
    
    if response.strip() == "Produk yang ada di database:":
        response = "Tidak ada produk yang ditemukan di database."
    
    for part in split_message(response):
        update.message.reply_text(part)

# Perintah untuk menghapus produk berdasarkan ID
def hapus_produk(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("Silakan berikan ID produk yang akan dihapus.")
        return
    
    produk_id = context.args[0]
    
    try:
        result = collection.delete_one({"_id": ObjectId(produk_id)})
        if result.deleted_count > 0:
            update.message.reply_text(f"Produk dengan ID {produk_id} telah dihapus.")
        else:
            update.message.reply_text(f"Tidak ada produk dengan ID {produk_id}.")
    except Exception as e:
        update.message.reply_text(f"Terjadi kesalahan: {e}")

# Perintah untuk mengedit produk berdasarkan ID
def edit_produk(update: Update, context: CallbackContext) -> None:
    try:
        # Menggabungkan semua argumen dan memisahkannya dengan '\n' untuk baris baru
        args = ' '.join(context.args)
        lines = args.split('\n')

        for line in lines:
            # Memisahkan setiap baris berdasarkan ','
            parts = line.split(',')

            if len(parts) != 7:
                update.message.reply_text("Format input salah di baris: '{}'. Gunakan format: id_produk,kategori,layanan,paket,\"deskripsi\",\"durasi\",harga".format(line))
                return

            produk_id = parts[0].strip()
            data_baru = {
                "kategori": parts[1].strip(),
                "layanan": parts[2].strip(),
                "paket": parts[3].strip(),
                "deskripsi": parts[4].strip().strip('"'),
                "durasi": parts[5].strip().strip('"'),
                "harga": parts[6].strip(),
            }

            # Melakukan update produk berdasarkan ID
            result = collection.update_one({"_id": ObjectId(produk_id)}, {"$set": data_baru})
            if result.matched_count > 0:
                update.message.reply_text(f"Produk dengan ID {produk_id} telah diperbarui.")
            else:
                update.message.reply_text(f"Tidak ada produk dengan ID {produk_id}.")
        
    except Exception as e:
        update.message.reply_text(f"Terjadi kesalahan: {e}")
        

# Fungsi utama untuk menjalankan bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(kategori_handler, pattern="^kategori:"))
    dp.add_handler(CallbackQueryHandler(layanan_handler, pattern="^layanan:"))
    dp.add_handler(CallbackQueryHandler(order_handler, pattern="^order:"))
    dp.add_handler(CallbackQueryHandler(paket_handler, pattern="^paket:"))
    dp.add_handler(CallbackQueryHandler(durasi_handler, pattern="^durasi:"))
    dp.add_handler(CallbackQueryHandler(payment_handler, pattern="^payment:"))
    dp.add_handler(MessageHandler(Filters.photo, payment_confirmation_handler))
    dp.add_error_handler(error_handler)
    dp.add_handler(CallbackQueryHandler(back_to_start, pattern='^back:start$'))
    dp.add_handler(CallbackQueryHandler(kembali_handler, pattern='^back:category:'))
    dp.add_handler(CallbackQueryHandler(layanan_kembali_handler, pattern='^back:layanan:'))
    dp.add_handler(CallbackQueryHandler(back_to_paket_handler, pattern='^back:paket:'))
    dp.add_handler(CallbackQueryHandler(back_to_durasi_handler, pattern='^back:durasi:'))
    dp.add_handler(CallbackQueryHandler(back_to_payment_handler, pattern='^back:payment:'))
    dp.add_handler(CommandHandler("tambah_produk", tambah_produk))
    dp.add_handler(CommandHandler("lihat_produk", lihat_produk))
    dp.add_handler(CommandHandler("hapus_produk", hapus_produk))
    dp.add_handler(CommandHandler("edit_produk", edit_produk))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()