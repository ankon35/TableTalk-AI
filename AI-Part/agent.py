# from dotenv import load_dotenv

# from livekit import agents
# from livekit.agents import AgentSession, Agent, RoomInputOptions
# from livekit.plugins import (
#     noise_cancellation,
# )

# from livekit.plugins import google
# from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
# load_dotenv(".env")


# class Assistant(Agent):
#     def __init__(self) -> None:
#         super().__init__(instructions=AGENT_INSTRUCTION)


# async def entrypoint(ctx: agents.JobContext):
#     session = AgentSession(
#         llm=google.beta.realtime.RealtimeModel(
#             voice="Zephyr"
#         )
#     )

#     await session.start(
#         room=ctx.room,
#         agent=Assistant(),
#         room_input_options=RoomInputOptions(
#             # For telephony applications, use `BVCTelephony` instead for best results
#             noise_cancellation=noise_cancellation.BVC(),
#         ),
#     )

#     await ctx.connect()

#     await session.generate_reply(
#         instructions=SESSION_INSTRUCTION
#     )


# if __name__ == "__main__":
#     agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))







# # sania_agent.py
# """
# Friendly, natural-sounding LiveKit Agent for Pizza Burg Bangladesh (prompt-based follow-up).
# This version uses prompt instructions only to enforce the 5-second follow-up behavior
# (e.g., "Hello? Can you hear me okay?") — no runtime timers are added.
# """

# from dotenv import load_dotenv
# import os
# import time

# from supabase import create_client, Client
# from livekit import agents
# from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
# from livekit.plugins import noise_cancellation
# from livekit.plugins import google

# load_dotenv(".env")

# # ---------- CONFIG ----------
# PRODUCT_TABLE = "product"
# PRODUCT_COLUMNS = ["p.name", "p.price", "p.size", "p.description", "p.image"]

# # ---------- AGENT PERSONALITY ----------
# AGENT_INSTRUCTION = """
# You are Sania — a warm, friendly, and enthusiastic order taker for Pizza Burg Bangladesh.
# Your goal is to make the customer feel welcomed and valued. Sound natural, smile in your voice,
# and be conversational — like a real person who loves their job.

# ABSOLUTE RULES:
# 1.  You DO NOT know product names until you call the tools.
# 2.  NEVER invent product names or details. If a customer asks for something you don't have,
#     politely say, "Currently, we don't have this in our menu," and then suggest available
#     items by name (e.g., "but we do have Chicken Supreme, Beef Lover's, and Cheesy Delight").
# 3.  USE product names and details exactly as returned from tool responses.
# 4.  Always confirm the full order details with the customer before finalizing.
# 5.  After confirming an order, politely collect the customer's name, delivery address, and phone number.
# 6.  If the customer is silent for more than 5 seconds, give a gentle follow-up like
#     "Are you still there?" or "Can you hear me okay?" to re-engage them.

# TOOL USAGE:
# - fetch_all_products: Returns the full menu. Use this before suggesting any pizza.
# - fetch_product_info: Returns info for a single product. Use the exact returned values in your replies.

# SPEAKING STYLE:
# -   Friendly, casual, and natural. Use small talk and short, engaging phrases.
# -   Prefer phrases like: "Hey there!", "Awesome choice!", "Gotcha — one sec while I check.", "Perfect!"
# -   Keep replies short and human. Use contractions ("I'm", "we've", "that's") and an occasional emoji if it feels natural. 🍕
# """

# # ---------- CONVERSATION FLOW (natural tone, prompt-based follow-ups) ----------
# SESSION_INSTRUCTION = """
# You are Sania from Pizza Burg Bangladesh. Follow this natural conversation flow, but be flexible
# and respond to the customer's queries. Your primary goal is a warm, human-like interaction.

# Important rule for silence:
# If the customer doesn’t respond for about 5 seconds, prompt gently with a friendly,
# context-aware follow-up like: "Hey, can you hear me?" or "Are you still with me?"

# --- DEMO CONVERSATION ---

# Sania: Hey there! Good evening — this is Sania from Pizza Burg Bangladesh! Who am I speaking with today?
# Customer: Hi, this is Mr. Rahim.
# Sania: Oh, hi Mr. Rahim! Nice to talk to you, sir! How’s your day going so far?
# Customer: It’s going well, thanks.
# Sania: That’s awesome to hear, sir. So, craving some pizza tonight? 🍕
# Customer: Yep, I’d like to order some pizza.
# Sania: Wonderful, sir! Which pizza would you like to go for — or may I suggest some of our best ones from the menu?
# Customer: Sure, go ahead.
# Sania: Okay! Our top picks right now are Chicken Supreme, Beef Lover’s, and Cheesy Delight. The Chicken Supreme is super flavorful — loaded with juicy chicken, capsicum, onions, and lots of cheese. It’s a total fan favorite!
# Customer: That sounds good. I’ll take one Chicken Supreme Pizza, large size.
# Sania: Perfect choice, sir! One large Chicken Supreme Pizza coming right up. Anything else you’d like to add?
# Customer: Yes, one medium Beef Lover’s Pizza too.
# Sania: Yumm, great pick! So that’s one large Chicken Supreme and one medium Beef Lover’s.
# Customer: That’s all for now.
# Sania: Awesome! May I please have your delivery address, Mr. Rahim?
# Customer: It’s House 23, Road 4, Uttara Sector 9, Dhaka.
# Sania: Got it — House 23, Road 4, Uttara Sector 9. And your contact number, please?
# Customer: 01712-345678.
# Sania: Let me just repeat that — 01712-345678, right, sir?
# Customer: Yes, correct.
# Sania: Perfect! So, confirming your order — one large Chicken Supreme Pizza and one medium Beef Lover’s Pizza. Delivery to House 23, Road 4, Uttara Sector 9, Dhaka. Your total will be around 1,450 Taka, and it should reach you in about 35 to 40 minutes.
# Customer: Sounds good.
# Sania: Yay! Your order’s all set, Mr. Rahim. 🍕 Thanks a bunch for choosing Pizza Burg Bangladesh! You’re going to love this one.
# Customer: Thank you, Sania.
# Sania: Aww, you’re very welcome, sir! Have a lovely evening — and enjoy your pizza party! 😄

# --- BEHAVIOR NOTES ---
# -   Keep the conversation warm, engaging, and smooth.
# -   Be responsive to the user's specific questions. The demo is a guide, not a fixed script.
# -   Use natural pauses, but if silence lasts more than 5 seconds, use a follow-up.
# -   Repeat the customer's exact words for order and contact detail confirmation.
# -   Always be warm, human, and concise.
# """


# # ---------- ASSISTANT CLASS ----------
# class Assistant(Agent):
#     def __init__(self) -> None:
#         super().__init__(instructions=AGENT_INSTRUCTION)
#         try:
#             supabase_url = os.getenv("SUPABASE_URL")
#             supabase_key = os.getenv("SUPABASE_KEY")
#             print(f"[DEBUG] Initializing Supabase at {time.strftime('%Y-%m-%d %H:%M:%S')}")
#             if not supabase_url or not supabase_key:
#                 print("[WARN] SUPABASE_URL or SUPABASE_KEY not set in environment.")
#             self.supabase: Client = create_client(supabase_url, supabase_key)
#             print("[SUCCESS] Supabase client initialized.")
#         except Exception as e:
#             print(f"[ERROR] Failed to initialize Supabase: {e}")
#             raise

#     @function_tool()
#     async def fetch_all_products(self, context: RunContext) -> str:
#         """
#         Returns a short friendly listing of products — EXACT product names and their details
#         must be used by the LLM when speaking with customers.
#         """
#         try:
#             response = self.supabase.table(PRODUCT_TABLE).select("*").execute()
#             if response.data and len(response.data) > 0:
#                 lines = [f"MENU DATABASE RESULTS - {len(response.data)} PRODUCTS FOUND:\n"]
#                 # Keep entries concise; these strings are what the LLM must use verbatim
#                 for idx, product in enumerate(response.data, 1):
#                     name = product.get("p.name")
#                     price = product.get("p.price")
#                     size = product.get("p.size")
#                     desc = product.get("p.description")
#                     lines.append(f"Product {idx}: NAME='{name}', PRICE=${price}, SIZE={size}, DESCRIPTION={desc}")
#                 lines.append("\nUse these exact product names and details in conversation. Do NOT invent items.")
#                 result = "\n".join(lines)
#                 print(f"[DEBUG] fetch_all_products returning {len(response.data)} products.")
#                 return result
#             else:
#                 print("[WARN] No products found in database.")
#                 return "ERROR: No products found in database. Tell the customer the menu is currently unavailable."
#         except Exception as e:
#             print(f"[ERROR] fetch_all_products exception: {e}")
#             return f"ERROR: Cannot access database. {str(e)}"

#     @function_tool()
#     async def fetch_product_info(self, context: RunContext, product_name: str) -> str:
#         """
#         Return the exact product info string the LLM must use when describing the product.
#         """
#         try:
#             response = self.supabase.table(PRODUCT_TABLE).select("*").eq("p.name", product_name).execute()
#             if response.data and len(response.data) > 0:
#                 product = response.data[0]
#                 name = product.get("p.name")
#                 price = product.get("p.price")
#                 size = product.get("p.size")
#                 desc = product.get("p.description")
#                 result = f"PRODUCT FOUND: Name='{name}', Price=${price}, Size={size}, Description={desc}. USE THESE EXACT VALUES."
#                 print(f"[DEBUG] fetch_product_info found product: {name}")
#                 return result
#             else:
#                 print(f"[WARN] Product not found: {product_name}")
#                 return f"ERROR: Product '{product_name}' does not exist in our database."
#         except Exception as e:
#             print(f"[ERROR] fetch_product_info exception: {e}")
#             return f"ERROR: Cannot access database right now. {str(e)}"

#     def get_all_products_for_entrypoint(self) -> str:
#         """Synchronous helper used before starting the session so initial prompt has the menu."""
#         try:
#             response = self.supabase.table(PRODUCT_TABLE).select("*").execute()
#             if response.data and len(response.data) > 0:
#                 result_lines = [f"MENU DATABASE RESULTS - {len(response.data)} PRODUCTS FOUND:\n"]
#                 for idx, product in enumerate(response.data, 1):
#                     name = product.get("p.name")
#                     price = product.get("p.price")
#                     size = product.get("p.size")
#                     desc = product.get("p.description")
#                     result_lines.append(f"Product {idx}: NAME='{name}', PRICE=${price}, SIZE={size}, DESCRIPTION={desc}")
#                 result_lines.append("\nUse these exact product names and details in conversation.")
#                 return "\n".join(result_lines)
#             else:
#                 return "ERROR: No products found in database."
#         except Exception as e:
#             return f"ERROR: Cannot access database. {str(e)}"

# # ---------- ENTRYPOINT ----------
# async def entrypoint(ctx: agents.JobContext):
#     print(f"[DEBUG] Entrypoint started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
#     session = AgentSession(
#         llm=google.beta.realtime.RealtimeModel(
#             voice="Zephyr"
#         )
#     )

#     assistant = Assistant()

#     print("[DEBUG] Starting agent session...")
#     await session.start(
#         room=ctx.room,
#         agent=assistant,
#         room_input_options=RoomInputOptions(
#             noise_cancellation=noise_cancellation.BVC(),
#         ),
#     )

#     await ctx.connect()
#     print("[DEBUG] Connected to room.")

#     # Fetch menu to include in initial instructions so LLM knows the exact menu
#     try:
#         menu_data = assistant.get_all_products_for_entrypoint()
#         print("[DEBUG] Menu data fetched for initial prompt.")
#     except Exception as e:
#         menu_data = f"ERROR: Could not fetch menu before starting session. {str(e)}"
#         print(f"[ERROR] {menu_data}")

#     initial_instructions = SESSION_INSTRUCTION + "\n\nMENU_DATA_FOR_AGENT:\n" + menu_data

#     # Generate the first reply using the natural flow instructions + menu data
#     await session.generate_reply(instructions=initial_instructions)
#     print("[DEBUG] Initial reply generated successfully.")

# # ---------- RUN ----------
# if __name__ == "__main__":
#     print(f"[INFO] Sania Agent starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
#     agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

















"""
Friendly, natural-sounding LiveKit Agent for Pizza Burg Bangladesh (prompt-based follow-up).
This version uses prompt instructions only to enforce the 5-second follow-up behavior
(e.g., "Hello? Can you hear me okay?") — no runtime timers are added.
Includes order storage functionality to save customer orders to the database.
FIXED: Single-row order storage with array-based item fields.
"""

from dotenv import load_dotenv
import os
import time
from typing import List, Dict

from supabase import create_client, Client
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
from livekit.plugins import noise_cancellation
from livekit.plugins import google

load_dotenv(".env")

# ---------- CONFIG ----------
PRODUCT_TABLE = "product"
ORDER_TABLE = "Order"
PRODUCT_COLUMNS = ["p.name", "p.price", "p.size", "p.description", "p.image"]

# ---------- AGENT PERSONALITY ----------
AGENT_INSTRUCTION = """
You are Sania — a warm, friendly, and enthusiastic order taker for Pizza Burg Bangladesh.
Your goal is to make the customer feel welcomed and valued. Sound natural, smile in your voice,
and be conversational — like a real person who loves their job.

ABSOLUTE RULES:
1.  You DO NOT know product names until you call the tools.
2.  NEVER invent product names or details. If a customer asks for something you don't have,
    politely say, "Currently, we don't have this in our menu," and then suggest available
    items by name (e.g., "but we do have Chicken Supreme, Beef Lover's, and Cheesy Delight").
3.  USE product names and details exactly as returned from tool responses.
4.  Always confirm the full order details with the customer before finalizing.
5.  After confirming an order, politely collect the customer's name, delivery address, and phone number.
6.  CRITICAL ORDER SAVING REQUIREMENT:
    - Once you have ALL order details AND customer info (name, address, phone), you MUST call save_order_to_database.
    - Call this function ONLY ONCE per order, passing ALL items together.
    - The function accepts arrays/lists for item_names, item_sizes, and item_prices.
    - WAIT for the function response before continuing.
    - If you receive an ERROR response, inform the customer there was a technical issue and try calling the function again.
    - ONLY after receiving SUCCESS response should you tell the customer their order is confirmed.
    - DO NOT say "order is confirmed" or "order is placed" until you have successfully called save_order_to_database.
7.  If the customer is silent for more than 5 seconds, give a gentle follow-up like
    "Are you still there?" or "Can you hear me okay?" to re-engage them.

TOOL USAGE:
- fetch_all_products: Returns the full menu. Use this before suggesting any pizza.
- fetch_product_info: Returns info for a single product. Use the exact returned values in your replies.
- save_order_to_database: Save the complete order to database in ONE call.
  * Pass ALL items in arrays (item_names, item_sizes, item_prices).
  * ALWAYS wait for the response before proceeding.
  * If you get an ERROR, try again or inform the customer.
  * Example: Customer orders 2 pizzas → call function ONCE with arrays containing both items.

SPEAKING STYLE:
-   Friendly, casual, and natural. Use small talk and short, engaging phrases.
-   Prefer phrases like: "Hey there!", "Awesome choice!", "Gotcha — one sec while I check.", "Perfect!"
-   Keep replies short and human. Use contractions ("I'm", "we've", "that's") and an occasional emoji if it feels natural. 🍕
"""

# ---------- CONVERSATION FLOW (natural tone, prompt-based follow-ups) ----------
SESSION_INSTRUCTION = """
You are Sania from Pizza Burg Bangladesh. Follow this natural conversation flow, but be flexible
and respond to the customer's queries. Your primary goal is a warm, human-like interaction.

Important rule for silence:
If the customer doesn't respond for about 5 seconds, prompt gently with a friendly,
context-aware follow-up like: "Hey, can you hear me?" or "Are you still with me?"

--- DEMO CONVERSATION ---

Sania: Hey there! Good evening — this is Sania from Pizza Burg Bangladesh! Who am I speaking with today?
Customer: Hi, this is Mr. Rahim.
Sania: Oh, hi Mr. Rahim! Nice to talk to you, sir! How's your day going so far?
Customer: It's going well, thanks.
Sania: That's awesome to hear, sir. So, craving some pizza tonight? 🍕
Customer: Yep, I'd like to order some pizza.
Sania: Wonderful, sir! Which pizza would you like to go for — or may I suggest some of our best ones from the menu?
Customer: Sure, go ahead.
Sania: Okay! Our top picks right now are Chicken Supreme, Beef Lover's, and Cheesy Delight. The Chicken Supreme is super flavorful — loaded with juicy chicken, capsicum, onions, and lots of cheese. It's a total fan favorite!
Customer: That sounds good. I'll take one Chicken Supreme Pizza, large size.
Sania: Perfect choice, sir! One large Chicken Supreme Pizza coming right up. Anything else you'd like to add?
Customer: Yes, one medium Beef Lover's Pizza too.
Sania: Yumm, great pick! So that's one large Chicken Supreme and one medium Beef Lover's.
Customer: That's all for now.
Sania: Awesome! May I please have your delivery address, Mr. Rahim?
Customer: It's House 23, Road 4, Uttara Sector 9, Dhaka.
Sania: Got it — House 23, Road 4, Uttara Sector 9. And your contact number, please?
Customer: 01712-345678.
Sania: Let me just repeat that — 01712-345678, right, sir?
Customer: Yes, correct.
Sania: Perfect! Let me just save your order to our system... 
[CALLS save_order_to_database ONCE with all items: item_names=["Chicken Supreme Pizza", "Beef Lover's Pizza"], item_sizes=["large", "medium"], item_prices=["850", "600"]]
[WAITS for response]
Great! Your order's confirmed — one large Chicken Supreme Pizza and one medium Beef Lover's Pizza. Delivery to House 23, Road 4, Uttara Sector 9, Dhaka. Your total will be 1,450 Taka, and it should reach you in about 35 to 40 minutes.
Customer: Sounds good.
Sania: Yay! Thanks a bunch for choosing Pizza Burg Bangladesh! You're going to love this one.
Customer: Thank you, Sania.
Sania: Aww, you're very welcome, sir! Have a lovely evening — and enjoy your pizza party! 😄

--- BEHAVIOR NOTES ---
-   Keep the conversation warm, engaging, and smooth.
-   Be responsive to the user's specific questions. The demo is a guide, not a fixed script.
-   Use natural pauses, but if silence lasts more than 5 seconds, use a follow-up.
-   Repeat the customer's exact words for order and contact detail confirmation.
-   CRITICAL: After confirming all details, you MUST:
    1. Tell customer "Let me save your order to our system..."
    2. Call save_order_to_database ONCE with ALL items in arrays
    3. Wait for the function response
    4. If ERROR occurs, try again or inform customer
    5. ONLY after SUCCESS response, confirm "Your order is confirmed!"
-   Never say "order confirmed" before successfully saving to database.
-   Always be warm, human, and concise.
"""


# ---------- ASSISTANT CLASS ----------
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=AGENT_INSTRUCTION)
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            print(f"[DEBUG] Initializing Supabase at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            if not supabase_url or not supabase_key:
                print("[WARN] SUPABASE_URL or SUPABASE_KEY not set in environment.")
                raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables")
            self.supabase: Client = create_client(supabase_url, supabase_key)
            print("[SUCCESS] Supabase client initialized.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize Supabase: {e}")
            raise

    @function_tool()
    async def fetch_all_products(self, context: RunContext) -> str:
        """
        Returns a short friendly listing of products — EXACT product names and their details
        must be used by the LLM when speaking with customers.
        """
        try:
            response = self.supabase.table(PRODUCT_TABLE).select("*").execute()
            if response.data and len(response.data) > 0:
                lines = [f"MENU DATABASE RESULTS - {len(response.data)} PRODUCTS FOUND:\n"]
                # Keep entries concise; these strings are what the LLM must use verbatim
                for idx, product in enumerate(response.data, 1):
                    name = product.get("p.name")
                    price = product.get("p.price")
                    size = product.get("p.size")
                    desc = product.get("p.description")
                    lines.append(f"Product {idx}: NAME='{name}', PRICE=${price}, SIZE={size}, DESCRIPTION={desc}")
                lines.append("\nUse these exact product names and details in conversation. Do NOT invent items.")
                result = "\n".join(lines)
                print(f"[DEBUG] fetch_all_products returning {len(response.data)} products.")
                return result
            else:
                print("[WARN] No products found in database.")
                return "ERROR: No products found in database. Tell the customer the menu is currently unavailable."
        except Exception as e:
            print(f"[ERROR] fetch_all_products exception: {e}")
            return f"ERROR: Cannot access database. {str(e)}"

    @function_tool()
    async def fetch_product_info(self, context: RunContext, product_name: str) -> str:
        """
        Return the exact product info string the LLM must use when describing the product.
        """
        try:
            response = self.supabase.table(PRODUCT_TABLE).select("*").eq("p.name", product_name).execute()
            if response.data and len(response.data) > 0:
                product = response.data[0]
                name = product.get("p.name")
                price = product.get("p.price")
                size = product.get("p.size")
                desc = product.get("p.description")
                result = f"PRODUCT FOUND: Name='{name}', Price=${price}, Size={size}, Description={desc}. USE THESE EXACT VALUES."
                print(f"[DEBUG] fetch_product_info found product: {name}")
                return result
            else:
                print(f"[WARN] Product not found: {product_name}")
                return f"ERROR: Product '{product_name}' does not exist in our database."
        except Exception as e:
            print(f"[ERROR] fetch_product_info exception: {e}")
            return f"ERROR: Cannot access database right now. {str(e)}"

    @function_tool()
    async def save_order_to_database(
        self, 
        context: RunContext, 
        customer_name: str,
        customer_address: str,
        customer_number: str,
        item_names: List[str],
        item_sizes: List[str],
        item_prices: List[str]
    ) -> str:
        """
        Save a complete order to the database as a SINGLE record.
        All items from the order are stored in array fields.
        
        IMPORTANT: Call this function ONCE per order with ALL items.
        
        Args:
            customer_name: Customer's name (e.g., "Mr. Rahim")
            customer_address: Customer's delivery address (e.g., "House 23, Road 4, Uttara Sector 9, Dhaka")
            customer_number: Customer's phone number (e.g., "01712-345678")
            item_names: List of all pizza/product names (e.g., ["Chicken Supreme Pizza", "Beef Lover's Pizza"])
            item_sizes: List of all item sizes (e.g., ["large", "medium"])
            item_prices: List of all individual item prices as strings (e.g., ["850", "600"])
        
        Returns:
            SUCCESS message if saved, ERROR message if failed.
            You MUST check the response and only proceed if you receive SUCCESS.
        """
        try:
            print(f"[DEBUG] Attempting to save order for {customer_name}")
            print(f"[DEBUG] Items: {item_names}, Sizes: {item_sizes}, Prices: {item_prices}")
            
            # Validate inputs
            if not all([customer_name, customer_address, customer_number]):
                error_msg = "ERROR: Missing customer information (name, address, or phone number)."
                print(f"[ERROR] {error_msg}")
                return error_msg
            
            if not item_names or not item_sizes or not item_prices:
                error_msg = "ERROR: Missing order items. Must provide item_names, item_sizes, and item_prices."
                print(f"[ERROR] {error_msg}")
                return error_msg
            
            # Validate array lengths match
            if not (len(item_names) == len(item_sizes) == len(item_prices)):
                error_msg = f"ERROR: Array length mismatch. Items: {len(item_names)}, Sizes: {len(item_sizes)}, Prices: {len(item_prices)}"
                print(f"[ERROR] {error_msg}")
                return error_msg
            
            # Calculate total quantity (number of items)
            quantity = len(item_names)
            
            # Calculate total price (sum of all item prices)
            try:
                total_price = sum(float(price) for price in item_prices)
                total_price_str = str(int(total_price))  # Convert to string without decimals
            except ValueError as e:
                error_msg = f"ERROR: Invalid price format. Prices must be numeric strings. {str(e)}"
                print(f"[ERROR] {error_msg}")
                return error_msg
            
            # Prepare order record for database (single row with arrays)
            record = {
                "name": customer_name,
                "address": customer_address,
                "number": customer_number,
                "item_name": item_names,      # Array of item names
                "item_size": item_sizes,      # Array of sizes
                "quantity": quantity,         # Total number of items
                "total_price": total_price_str  # Sum of all prices
            }
            
            print(f"[DEBUG] Inserting single order record: {record}")
            
            # Insert order into database as a SINGLE record
            response = self.supabase.table(ORDER_TABLE).insert([record]).execute()
            
            print(f"[DEBUG] Database response: {response}")
            
            if response.data and len(response.data) > 0:
                items_summary = ", ".join([f"{name} ({size})" for name, size in zip(item_names, item_sizes)])
                success_msg = f"SUCCESS: Order saved! {quantity} items [{items_summary}] recorded for {customer_name}. Total: {total_price_str} Taka."
                print(f"[SUCCESS] {success_msg}")
                return success_msg
            else:
                error_msg = f"ERROR: Failed to save order to database. Response: {response}"
                print(f"[ERROR] {error_msg}")
                return "ERROR: Failed to save order to database. Please try again."
                
        except Exception as e:
            error_msg = f"ERROR: Exception while saving order: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return f"ERROR: Technical issue while saving order - {str(e)}. Please try again or contact support."

    def get_all_products_for_entrypoint(self) -> str:
        """Synchronous helper used before starting the session so initial prompt has the menu."""
        try:
            response = self.supabase.table(PRODUCT_TABLE).select("*").execute()
            if response.data and len(response.data) > 0:
                result_lines = [f"MENU DATABASE RESULTS - {len(response.data)} PRODUCTS FOUND:\n"]
                for idx, product in enumerate(response.data, 1):
                    name = product.get("p.name")
                    price = product.get("p.price")
                    size = product.get("p.size")
                    desc = product.get("p.description")
                    result_lines.append(f"Product {idx}: NAME='{name}', PRICE=${price}, SIZE={size}, DESCRIPTION={desc}")
                result_lines.append("\nUse these exact product names and details in conversation.")
                return "\n".join(result_lines)
            else:
                return "ERROR: No products found in database."
        except Exception as e:
            return f"ERROR: Cannot access database. {str(e)}"

# ---------- ENTRYPOINT ----------
async def entrypoint(ctx: agents.JobContext):
    print(f"[DEBUG] Entrypoint started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Zephyr"
        )
    )

    assistant = Assistant()

    print("[DEBUG] Starting agent session...")
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()
    print("[DEBUG] Connected to room.")

    # Fetch menu to include in initial instructions so LLM knows the exact menu
    try:
        menu_data = assistant.get_all_products_for_entrypoint()
        print("[DEBUG] Menu data fetched for initial prompt.")
    except Exception as e:
        menu_data = f"ERROR: Could not fetch menu before starting session. {str(e)}"
        print(f"[ERROR] {menu_data}")

    initial_instructions = SESSION_INSTRUCTION + "\n\nMENU_DATA_FOR_AGENT:\n" + menu_data

    # Generate the first reply using the natural flow instructions + menu data
    await session.generate_reply(instructions=initial_instructions)
    print("[DEBUG] Initial reply generated successfully.")

# ---------- RUN ----------
if __name__ == "__main__":
    print(f"[INFO] Sania Agent starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))