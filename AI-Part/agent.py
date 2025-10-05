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





from dotenv import load_dotenv
import os
from supabase import create_client, Client
import time

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
from livekit.plugins import noise_cancellation
from livekit.plugins import google

load_dotenv(".env")

# Constants for Supabase product table
PRODUCT_TABLE = "product"
# Column names match your actual Supabase table structure
PRODUCT_COLUMNS = ["p.name", "p.price", "p.size", "p.description", "p.image"]

# AGENT_INSTRUCTION
AGENT_INSTRUCTION = """
# Persona
You are Sania, a professional Salesperson for Ankon Restaurant.

# ABSOLUTE RULES - NEVER BREAK THESE
1. You do NOT know what products exist until you call the tools
2. NEVER invent, guess, or make up product names
3. NEVER mention any specific product name unless it came from a tool response
4. If you haven't called fetch_all_products yet, DO NOT talk about specific menu items
5. Only speak about products that are explicitly listed in the tool response you just received

# Tool Usage
- fetch_all_products: Returns actual products from database. Use the returned data ONLY.
- fetch_product_info: Returns specific product details. Use the returned data ONLY.

# Speaking Style
- Friendly and professional
- Only discuss products after receiving tool data
- If you don't have data yet, say you're checking the menu
"""

# SESSION_INSTRUCTION
SESSION_INSTRUCTION = """
# Your Task
Call a customer from Ankon Restaurant to offer menu items.

# STRICT PROCESS - FOLLOW IN ORDER

Step 1: Greet
Say: "Hello, this is Sania from Ankon Restaurant—how are you today?"

Step 2: After greeting, IMMEDIATELY SAY:
"Let me check what we have available for you today."

Step 3: IMMEDIATELY call fetch_all_products (DO NOT skip this step)

Step 4: WAIT for the tool response

Step 5: The tool will return a JSON with:
{
  "products": [
    {"name": "...", "price": "...", "size": "...", "description": "..."},
    ...
  ],
  "message": "..."
}

Step 6: Read the "products" array. For EACH product in the array, you MUST:
- Take the exact "name" value
- Take the exact "price" value  
- Take the exact "size" value
- Take the exact "description" value

Step 7: Speak to customer using ONLY those exact values. Example format:
"We have [exact name from product[0]], which is [exact size from product[0]] size at [exact price from product[0]] - [exact description from product[0]]. We also have [exact name from product[1]] at [exact price from product[1]], [exact size from product[1]] size - [exact description from product[1]]."

# CRITICAL
- Do NOT say product names before Step 6
- Do NOT invent any product information
- Use ONLY the exact strings from the tool response
- If tool returns empty, say "We don't have items available right now"
"""

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=AGENT_INSTRUCTION)
        # Initialize Supabase client
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            print(f"[DEBUG] Initializing Supabase at {time.strftime('%H:%M:%S %z on %Y-%m-%d')}")
            print(f"[DEBUG] SUPABASE_URL: {supabase_url[:30]}..." if supabase_url else "[DEBUG] SUPABASE_URL is None")
            print(f"[DEBUG] SUPABASE_KEY exists: {bool(supabase_key)}")
            
            self.supabase: Client = create_client(supabase_url, supabase_key)
            print(f"[SUCCESS] Supabase initialized successfully at {time.strftime('%H:%M:%S %z on %Y-%m-%d')}")
        except Exception as e:
            print(f"[ERROR] Supabase initialization failed at {time.strftime('%H:%M:%S %z on %Y-%m-%d')}: {str(e)}")
            raise Exception(f"Failed to initialize Supabase client: {str(e)}")

    @function_tool()
    async def fetch_product_info(
        self,
        context: RunContext,
        product_name: str,
    ) -> str:
        """
        Fetch specific product information from database.
        
        Args:
            product_name: Exact product name to search for
        
        Returns:
            String with product details you MUST use in your response
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] fetch_product_info: Attempt {attempt + 1}/{max_retries}")
                print(f"[DEBUG] Searching for product: '{product_name}'")
                
                response = (
                    self.supabase.table(PRODUCT_TABLE)
                    .select('*')
                    .eq("p.name", product_name)
                    .execute()
                )
                
                print(f"[DEBUG] fetch_product_info response.data: {response.data}")
                
                if response.data and len(response.data) > 0:
                    product_data = response.data[0]
                    name = product_data.get("p.name")
                    price = product_data.get('p.price')
                    size = product_data.get("p.size")
                    desc = product_data.get("p.description")
                    
                    result = f"PRODUCT FOUND: Name='{name}', Price=${price}, Size={size}, Description={desc}. YOU MUST use these exact values when talking to the customer."
                    
                    print(f"[SUCCESS] Returning to LLM: {result}")
                    return result
                else:
                    print(f"[WARNING] No data found for product_name='{product_name}'")
                    return f"ERROR: Product '{product_name}' does not exist in our database."
                    
            except Exception as e:
                print(f"[ERROR] fetch_product_info failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return f"ERROR: Cannot access database right now. {str(e)}"

    @function_tool()
    async def fetch_all_products(
        self,
        context: RunContext,
    ) -> str:
        """
        Fetch ALL products from database. This returns the complete menu.
        You MUST call this before talking about any specific products.
        
        Returns:
            String listing all products with their details that you MUST use exactly as provided
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] fetch_all_products: Attempt {attempt + 1}/{max_retries}")
                
                response = (
                    self.supabase.table(PRODUCT_TABLE)
                    .select('*')
                    .execute()
                )
                
                print(f"[DEBUG] fetch_all_products response.data: {response.data}")
                
                if response.data and len(response.data) > 0:
                    # Build a very explicit string format
                    result_lines = [f"MENU DATABASE RESULTS - {len(response.data)} PRODUCTS FOUND:\n"]
                    
                    for idx, product in enumerate(response.data, 1):
                        name = product.get("p.name")
                        price = product.get('p.price')
                        size = product.get("p.size")
                        desc = product.get("p.description")
                        
                        result_lines.append(
                            f"Product {idx}: NAME='{name}', PRICE=${price}, SIZE={size}, DESCRIPTION={desc}"
                        )
                    
                    result_lines.append("\nYOU MUST mention these EXACT product names and details to the customer. Do NOT make up any other products.")
                    
                    result = "\n".join(result_lines)
                    print(f"[SUCCESS] Returning to LLM:\n{result}")
                    return result
                else:
                    print("[WARNING] No products found in database")
                    return "ERROR: No products found in database. Tell customer menu is currently unavailable."
                    
            except Exception as e:
                print(f"[ERROR] fetch_all_products failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return f"ERROR: Cannot access database. {str(e)}"

    # Helper used from entrypoint (synchronous-friendly)
    def get_all_products_for_entrypoint(self) -> str:
        """
        Synchronously fetch all products and return the same formatted string
        used by the async tool. This lets entrypoint obtain product data
        before calling `session.generate_reply` so the LLM has the menu.
        """
        try:
            print(f"[DEBUG] get_all_products_for_entrypoint: querying database")
            response = (
                self.supabase.table(PRODUCT_TABLE)
                .select('*')
                .execute()
            )

            print(f"[DEBUG] get_all_products_for_entrypoint response.data: {response.data}")

            if response.data and len(response.data) > 0:
                result_lines = [f"MENU DATABASE RESULTS - {len(response.data)} PRODUCTS FOUND:\n"]
                for idx, product in enumerate(response.data, 1):
                    name = product.get("p.name")
                    price = product.get('p.price')
                    size = product.get("p.size")
                    desc = product.get("p.description")

                    result_lines.append(
                        f"Product {idx}: NAME='{name}', PRICE=${price}, SIZE={size}, DESCRIPTION={desc}"
                    )

                result_lines.append("\nYOU MUST mention these EXACT product names and details to the customer. Do NOT make up any other products.")
                result = "\n".join(result_lines)
                return result
            else:
                return "ERROR: No products found in database. Tell customer menu is currently unavailable."
        except Exception as e:
            print(f"[ERROR] get_all_products_for_entrypoint failed: {str(e)}")
            return f"ERROR: Cannot access database. {str(e)}"

async def entrypoint(ctx: agents.JobContext):
    print(f"[DEBUG] Entrypoint started at {time.strftime('%H:%M:%S %z on %Y-%m-%d')}")
    
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Zephyr"
        )
    )
    
    print("[DEBUG] Creating Assistant instance...")
    assistant = Assistant()
    print("[DEBUG] Assistant created successfully")

    print("[DEBUG] Starting session...")
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    print("[DEBUG] Session started")

    print("[DEBUG] Connecting to room...")
    await ctx.connect()
    print("[DEBUG] Connected to room")

    print("[DEBUG] Generating initial reply...")
    # Fetch products synchronously and include them in the initial instructions
    print("[DEBUG] Fetching products for entrypoint before generating reply...")
    try:
        menu_data = assistant.get_all_products_for_entrypoint()
        print(f"[DEBUG] Menu data fetched for entrypoint: {menu_data[:200]}...")
    except Exception as e:
        menu_data = f"ERROR: Could not fetch menu before starting session. {str(e)}"
        print(f"[ERROR] {menu_data}")

    # Append the menu data to the session instructions so the realtime LLM voice
    # has the product information available immediately when producing speech.
    initial_instructions = SESSION_INSTRUCTION + "\n\n" + "MENU_DATA_FOR_AGENT:\n" + menu_data

    await session.generate_reply(
        instructions=initial_instructions
    )
    print("[DEBUG] Initial reply generated")

if __name__ == "__main__":
    print(f"[DEBUG] Application starting at {time.strftime('%H:%M:%S %z on %Y-%m-%d')}")
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))