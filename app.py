import random

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

GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxkKNVC-XVGpQwoJliNcURwvVPFC1WLQiklWq53lWk4tiOKWkdS7Gi0Z5Q9OVx8bYVsew/exec"

AMOUNTS = {
    "iPhone 15": 200,
    "Samsung Galaxy S24": 200,
    "Sony Headphones": 200
}

import requests
from datetime import datetime

def store_order_secure(orderid, customer_name, phone, product, quantity, amount, address):
    payload = {
        "orderid": orderid,
        "customer_name": customer_name,
        "phone": phone,
        "product": product,
        "quantity": quantity,
        "amount": amount,
        "address": address
    }

    res = requests.post(GOOGLE_WEBHOOK_URL, json=payload)

    if res.status_code == 200:
        print("✅ Order stored successfully in Google Sheet")
    else:
        print("❌ Failed to store order:", res.text)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():

    '''import gspread
    from google.oauth2.service_account import Credentials

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
    client = gspread.authorize(creds)

    sheet = client.open("Whatsapp Orders").sheet1
    sheet.append_row(["✅ Connection OK"])
    print("✅ Added row successfully!")'''

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
            msg.media("1.jpg")
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
            amount = AMOUNTS[product]*qty
            sessions[sender]["amount"] = amount
            msg.body(
                f"🧾 Provide your address:\n"
            )
            sessions[sender]["step"] = "awaiting_address"
        else:
            msg.body("Please enter a valid quantity number.")
        return str(resp)

    #Address
    if step == "awaiting_address":
        sessions[sender]["address"] = body
        qty= sessions[sender]["quantity"]
        product = sessions[sender]["product"]
        amount = sessions[sender]["amount"]
        msg.body(
            f"🧾 Confirm your order:\n"
            f"Product: {product}\n"
            f"Quantity: {qty}\n\n"
            f"Amount: {amount}\n\n"
            f"Address: {sessions[sender]["address"]}\n\n"
            f"Type *confirm* to place or *cancel* to abort."
        )
        sessions[sender]["step"] = "confirm"
        return str(resp)
    # Confirmation
    if step == "confirm":
        if body == "confirm":
            address = sessions[sender]["address"]
            prod = sessions[sender]["product"]
            qty = sessions[sender]["quantity"]
            amount = sessions[sender]["amount"]
            orderid = random.randint(100000 , 900000)
            store_order_secure(orderid,"Rohit", sender, prod, qty, amount, address)
            msg.body(
                f"✅ Order {orderid} confirmed!\n"
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

    def get_order_by_id(orderid):
        params = {"orderid": orderid}
        res = requests.get(GOOGLE_WEBHOOK_URL, params=params)
        if res.status_code == 200:
            data = res.json()
            return data[0] if data else None
        return None

    #Tracking
    if step == "track":
        orderid = request.values.get("Body", "").strip()
        order = get_order_by_id(orderid)
        if order:
            msg.body(
                f"📦 *Order ID:* {orderid}\n🛍 Product: {order['Product']}\n🔢 Quantity: {order['Quantity']}\n💰 Amount: ₹{order['Amount']}\n📅 Status: {order['Status']}")
        else:
            msg.body("❌ Order not found. Please check your Order ID.")

    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
