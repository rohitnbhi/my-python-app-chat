from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Store sessions (replace with DB later)
sessions = {}

# Sample product data
PRODUCTS = {
    "Electronics": ["iPhone 15", "Samsung Galaxy S24", "Sony Headphones"],
    "Clothing": ["T-shirt", "Jeans", "Sneakers"],
    "Home": ["Smart Bulb", "Vacuum Cleaner", "Air Purifier"]
}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("WhatsApp Orders").sheet1
    sheet.append_row(["Test", "✅ Bot Connected Successfully!"])
    print("✅ Test row added successfully!")
    
    sender = request.values.get("From", "")
    body = request.values.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    if sender not in sessions:
        sessions[sender] = {"step": "start"}

    step = sessions[sender]["step"]

    # Start conversation
    if body in ["hi", "hello", "menu", "start", "hey"] or step == "start":
        msg.body(
            "👋 Welcome to *ShopEasy!*\n\n"
            "Please choose:\n"
            "1️⃣ Browse Products\n"
            "2️⃣ Track Order\n"
            "3️⃣ Contact Support"
        )
        sessions[sender]["step"] = "main_menu"
        return str(resp)

    # Main menu
    if step == "main_menu":
        if body == "1":
            cats = "\n".join([f"- {c}" for c in PRODUCTS.keys()])
            msg.body(f"🛍️ Choose category:\n\n{cats}\n\n(Type category name)")
            sessions[sender]["step"] = "category"
        elif body == "2":
            msg.body("🔍 Enter your Order ID:")
            sessions[sender]["step"] = "track"
        elif body == "3":
            msg.body("💬 Support: Please email support@shopeasy.com")
            sessions[sender]["step"] = "start"
        else:
            msg.body("❌ Invalid option. Type 1, 2, or 3.")
        return str(resp)

    # Category handling
    if step == "category":
        cat = body.title()
        if cat in PRODUCTS:
            items = "\n".join([f"- {p}" for p in PRODUCTS[cat]])
            msg.body(f"🛒 *{cat}* items:\n\n{items}\n\nType product name to order")
            sessions[sender]["category"] = cat
            sessions[sender]["step"] = "product"
        else:
            msg.body("⚠️ Unknown category. Try again.")
        return str(resp)

    # Product handling
    if step == "product":
        cat = sessions[sender]["category"]
        if body.title() in PRODUCTS[cat]:
            sessions[sender]["product"] = body.title()
            msg.body(f"How many *{body.title()}* would you like?")
            sessions[sender]["step"] = "quantity"
        else:
            msg.body("❌ Invalid product. Please type one from the list.")
        return str(resp)

    # Quantity
    if step == "quantity":
        if body.isdigit():
            qty = int(body)
            sessions[sender]["quantity"] = qty
            product = sessions[sender]["product"]
            msg.body(
                f"🧾 Confirm your order:\n"
                f"Product: {product}\n"
                f"Quantity: {qty}\n\n"
                f"Type *confirm* to place or *cancel* to abort."
            )
            sessions[sender]["step"] = "confirm"
        else:
            msg.body("Please enter a valid quantity number.")
        return str(resp)

    # Confirmation
    if step == "confirm":
        if body == "confirm":
            prod = sessions[sender]["product"]
            qty = sessions[sender]["quantity"]
            msg.body(
                f"✅ Order confirmed!\n"
                f"{qty} x {prod} will be delivered soon.\n\n"
                f"Thank you for shopping with ShopEasy! 💚"
            )
            sessions[sender]["step"] = "start"
        elif body == "cancel":
            msg.body("❌ Order canceled. Type 'hi' to start again.")
            sessions[sender]["step"] = "start"
        else:
            msg.body("Type *confirm* or *cancel*.")
        return str(resp)

    msg.body("⚙️ Sorry, I didn't understand. Type 'hi' to start again.")
    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
