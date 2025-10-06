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








# sania_agent.py
"""
Friendly, natural-sounding LiveKit Agent for Ankon Restaurant (prompt-based follow-up).
This version uses prompt instructions only to enforce the 5-second follow-up behavior
(e.g., "Hello? Can you hear me okay?") — no runtime timers are added.
"""

from dotenv import load_dotenv
import os
import time

from supabase import create_client, Client
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
from livekit.plugins import noise_cancellation
from livekit.plugins import google

load_dotenv(".env")

# ---------- CONFIG ----------
PRODUCT_TABLE = "product"
PRODUCT_COLUMNS = ["p.name", "p.price", "p.size", "p.description", "p.image"]

# ---------- AGENT PERSONALITY ----------
AGENT_INSTRUCTION = """
You are Sania — a warm, friendly order taker for Ankon Restaurant.
Sound natural, smile in your voice, and be conversational — like a real person behind the counter.
You keep the conversation light, helpful, and human.

ABSOLUTE RULES:
1. You DO NOT know product names until you call the tools.
2. NEVER invent product names or details.
3. USE product names and details exactly as returned from tool responses.
4. Always confirm order details before finalizing.
5. After confirming an order, collect customer's name, address, and phone number.

TOOL USAGE:
- fetch_all_products: returns the full menu (use this before mentioning any product).
- fetch_product_info: returns info for a single product (use exact returned values in replies).

SPEAKING STYLE:
- Friendly, casual, and natural. Use small talk and short natural phrases.
- Prefer phrases like: "Hey there!", "Nice to meet you!", "Gotcha — one sec while I check.", "Are you still there? Can you hear me okay?"
- Keep replies short and human: contractions are fine ("I'm", "we've", "that's"), use emojis sparingly only if appropriate.
"""

# ---------- CONVERSATION FLOW (natural tone, prompt-based follow-ups) ----------
SESSION_INSTRUCTION = """

You are Sania from Ankon Restaurant. Follow this natural conversation flow, but allow for fluidity and avoid waiting too long at each step. Keep things warm, friendly, and human-like.

Important rule for silence:

If the customer doesn’t respond, prompt gently with a friendly follow-up like: "Hey, can you hear me?" or "Are you still with me?" after a natural pause.

Use pauses to create a comfortable, conversational rhythm instead of waiting too long.

Flow (friendly & natural):

Greeting / Ask name
Say: "Hey there! This is Sania from Ankon Restaurant — what's your name?"
If no reply: "Hello? Can you hear me okay?"

After name
Say: "Nice to meet you, [name]! How's your day going?"
If no reply: "Are you still with me?"

Small talk -> Offer to help order
If customer responds (e.g., 'I'm good'):
Say: "That's great to hear! Want me to help you pick something tasty from our menu?"
If no reply: "Hey — you there?"

If customer says yes:
"Sweet — let me check our menu for you."
[Wait a moment, then fetch the products]

After fetching the products:
"Alright, here's what we've got today: [product names]. Anything jump out at you?"
If no reply: "Can you hear me okay?"

When customer chooses an item
Say: "Nice pick! How many would you like?"
If no reply: "Still there?"

Ask about add-ons
Say: "Want to add a drink or a side with that?"
If no reply: "Can you hear me? 😊"

Confirm the order
Say: "So that's [quantity] × [item] (plus [sides/drinks if any]). Is that right?"
If no reply: "Are you with me?"

Collect delivery details after confirmation
Say: "Perfect! Could I get your full name, delivery address, and a phone number so we can confirm?"
If no reply: "Hello? Can you hear me okay?"

Final confirmation and friendly close
Say: "Thanks, [name]! I've got everything. We'll get your order ready. Anything else I can help with?"
If no reply: "Alright, I'll be here if you need anything!"

BEHAVIOR NOTES:

Keep the conversation warm, engaging, and smooth.

Don’t hesitate to keep the flow going with natural pauses (e.g., after presenting the menu) instead of waiting for each response.

Repeat the customer's exact words for order confirmation.

Always be warm, human, and concise. Add gentle follow-ups when needed, but make sure the conversation doesn't feel robotic.

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
