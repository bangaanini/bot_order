from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
from bson import ObjectId

# Konfigurasi koneksi MongoDB
client = MongoClient("mongodb+srv://rokeroke41:beVBSN5LlKVJHjK2@pricelist.2pwko.mongodb.net/?retryWrites=true&w=majority&appName=pricelist")
db = client["db_price"]
collection = db["db_sosmed"]

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

# Perintah untuk menambah produk (kategori, layanan, harga)
def tambah_produk(update: Update, context: CallbackContext) -> None:
    try:
        args = ' '.join(context.args)
        parts = args.split(',')

        if len(parts) != 3:
            update.message.reply_text("Format input salah. Gunakan format: kategori,layanan,harga")
            return

        produk_data = {
            "kategori": parts[0].strip(),
            "layanan": parts[1].strip(),
            "harga": parts[2].strip(),
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
        # Menggabungkan semua argumen dan memisahkannya dengan ','
        args = ' '.join(context.args)
        parts = args.split(',')

        if len(parts) != 4:
            update.message.reply_text("Format input salah. Gunakan format: id_produk,kategori,layanan,harga")
            return

        produk_id = parts[0].strip()
        data_baru = {
            "kategori": parts[1].strip(),
            "layanan": parts[2].strip(),
            "harga": parts[3].strip(),
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
    updater = Updater("7360636044:AAGwM_nsIQ1lKO5Zm-2xphDQyI-Rb8vSRes", use_context=True)
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("tambah_produk", tambah_produk))
    dp.add_handler(CommandHandler("lihat_produk", lihat_produk))
    dp.add_handler(CommandHandler("hapus_produk", hapus_produk))
    dp.add_handler(CommandHandler("edit_produk", edit_produk))  # Menambahkan handler edit_produk
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()