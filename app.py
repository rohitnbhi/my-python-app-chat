from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Simple in-memory store for demo (you can replace with DB)
user_sessions = {}

# Example products
PRODUCTS = {
    "Electronics": ["iPhone 15", "Samsung Galaxy S24", "Sony Headphones"],
    "Clothing": ["T-shirt", "Jeans", "Sneakers"],
    "Home": ["Smart Bulb", "Vacuum Cleaner", "Air Purifier"]
}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip().lower()
    sender = request.values.get("From")

    resp = MessagingResponse()
    msg = resp.message()

    # Initialize session
    if sender not in user_sessions:
        user_sessions[sender] = {"step": "start"}

    step = user_sessions[sender]["step"]

    # Start conversation
    if "hi" in incoming_msg or step == "start":
        reply = (
            "👋 *Welcome to ShopEasy!*\n"
            "How can I help you today?\n\n"
            "1️⃣ Browse Products\n"
            "2️⃣ Track Order\n"
            "3️⃣ Contact Support"
        )
        user_sessions[sender]["step"] = "main_menu"
        msg.body(reply)
        return str(resp)

    # Main menu options
    if step == "main_menu":
        if incoming_msg == "1":
            categories = "\n".join([f"- {cat}" for cat in PRODUCTS.keys()])
            reply = f"🛍️ Choose a category:\n\n{categories}\n\n(Type category name)"
            user_sessions[sender]["step"] = "category"
        elif incoming_msg == "2":
            reply = "🔍 Please enter your order ID to track:"
            user_sessions[sender]["step"] = "track_order"
        elif incoming_msg == "3":
            reply = "📞 Our support team will contact you shortly.\nYou can also email: support@shopeasy.com"
            user_sessions[sender]["step"] = "start"
        else:
            reply = "❌ Invalid choice. Please enter 1, 2, or 3."
        msg.body(reply)
        return str(resp)

    # Product browsing
    if step == "category":
        category = incoming_msg.title()
        if category in PRODUCTS:
            items = "\n".join([f"- {item}" for item in PRODUCTS[category]])
            reply = f"🛒 *{category}*:\n\n{items}\n\n(Type product name to order)"
            user_sessions[sender]["step"] = "product"
            user_sessions[sender]["category"] = category
        else:
            reply = "⚠️ Category not found. Please type a valid category name."
        msg.body(reply)
        return str(resp)

    # Product selection
    if step == "product":
        product_name = incoming_msg.title()
        category = user_sessions[sender].get("category")
        if product_name in PRODUCTS.get(category, []):
            reply = (
                f"✅ You selected *{product_name}*.\n"
                "Please enter quantity:"
            )
            user_sessions[sender]["product"] = product_name
            user_sessions[sender]["step"] = "quantity"
        else:
            reply = "⚠️ Product not found. Please type one from the list."
        msg.body(reply)
        return str(resp)

    # Quantity input
    if step == "quantity":
        if incoming_msg.isdigit():
            quantity = int(incoming_msg)
            product = user_sessions[sender]["product"]
            reply = (
                f"🧾 Order Summary:\n"
                f"Product: {product}\n"
                f"Quantity: {quantity}\n\n"
                "Type *confirm* to place order or *cancel* to go back."
            )
            user_sessions[sender]["quantity"] = quantity
            user_sessions[sender]["step"] = "confirm_order"
        else:
            reply = "Please enter a valid number for quantity."
        msg.body(reply)
        return str(resp)

    # Order confirmation
    if step == "confirm_order":
        if "confirm" in incoming_msg:
            product = user_sessions[sender]["product"]
            quantity = user_sessions[sender]["quantity"]
            reply = (
                f"🎉 Order confirmed!\n"
                f"{quantity} × {product} will be processed soon.\n\n"
                "Thank you for shopping with ShopEasy! 💚"
            )
            user_sessions[sender]["step"] = "start"
        elif "cancel" in incoming_msg:
            reply = "❌ Order canceled. Returning to main menu."
            user_sessions[sender]["step"] = "start"
        else:
            reply = "Please type *confirm* or *cancel*."
        msg.body(reply)
        return str(resp)

    msg.body("⚙️ Sorry, I didn’t understand that. Type 'hi' to start again.")
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
