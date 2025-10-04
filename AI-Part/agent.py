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
Your primary role is to sell restaurant products over calls in a polite, persuasive, and professional manner.

# CRITICAL RULES - FOLLOW EXACTLY
1. When you call fetch_all_products or fetch_product_info, you MUST read and speak the EXACT product information returned in the tool response.
2. DO NOT make up product names, prices, or descriptions. 
3. ONLY mention products that appear in the tool response data.
4. When the tool returns product information, YOU MUST announce those EXACT products to the customer.

# How to Use Tools
- For menu questions: Call `fetch_all_products` then speak about the EXACT products returned in the response.
- For specific products: Call `fetch_product_info` with the exact name, then use the EXACT data returned.
- The tool response will include a "message" field - use this information in your response to the customer.

# Speaking Style
- Natural and conversational
- Professional but friendly
- Always mention the actual product name, price, size, and description from the database
- Example: "We have Meat Machine, which is a small size pizza at $480 - Friday Blast special. We also have Meaty Onion at $300, small size - Customer Choice."
"""

# SESSION_INSTRUCTION
SESSION_INSTRUCTION = """
# Task
You are Sania calling from Ankon Restaurant.

# Step-by-Step Process
1. Greet: "Hello, this is Sania from Ankon Restaurant—how are you today?"
2. IMMEDIATELY call fetch_all_products tool
3. WAIT for the tool response
4. READ the "message" field in the tool response - it contains the full menu details
5. SPEAK those EXACT product details to the customer - mention each product name, size, and price
6. Ask which one they'd like to try

# CRITICAL
- You MUST mention the actual product names from the tool response (like "Meat Machine" and "Meaty Onion")
- You MUST mention the actual prices from the tool response (like $480 and $300)
- DO NOT say generic terms like "chicken" or "pasta" - say the EXACT names returned by the database
- The tool response "message" field contains pre-formatted text you can speak directly

Example after calling fetch_all_products:
"Great! Let me tell you what we have today. We have ABC Machine, which is small size at $480 - it's our Friday Blast special. We also have Meaty Onion at $300, small size - this is a Customer Choice favorite. Which one sounds good to you?"
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
    ) -> dict:
        """
        Fetch product information from the Supabase database by product name.
        
        Args:
            product_name: The name of the product to look up.
        
        Returns:
            A dictionary with product details (name, price, size, description) or an error message.
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] fetch_product_info: Attempt {attempt + 1}/{max_retries}")
                print(f"[DEBUG] Searching for product: '{product_name}'")
                print(f"[DEBUG] Table: {PRODUCT_TABLE}")
                print(f"[DEBUG] Columns to select: {PRODUCT_COLUMNS}")
                
                # Use the actual column names with p. prefix
                response = (
                    self.supabase.table(PRODUCT_TABLE)
                    .select('*')
                    .eq("p.name", product_name)
                    .execute()
                )
                
                print(f"[DEBUG] fetch_product_info response.data type: {type(response.data)}")
                print(f"[DEBUG] fetch_product_info response.data length: {len(response.data) if response.data else 0}")
                print(f"[DEBUG] fetch_product_info full response.data: {response.data}")
                
                if response.data and len(response.data) > 0:
                    product_data = response.data[0]
                    print(f"[SUCCESS] Product found: {product_data}")
                    
                    result = {
                        "status": "success",
                        "product": {
                            "name": product_data.get("p.name"),
                            "price": f"${product_data.get('p.price')}",
                            "size": product_data.get("p.size"),
                            "description": product_data.get("p.description"),
                        },
                        "message": f"Found product: {product_data.get('p.name')} - {product_data.get('p.size')} size at ${product_data.get('p.price')}. {product_data.get('p.description')}"
                    }
                    print(f"[DEBUG] Returning to LLM: {result}")
                    return result
                else:
                    print(f"[WARNING] No data found for product_name='{product_name}'")
                    return {"error": f"Product '{product_name}' not found"}
                    
            except Exception as e:
                print(f"[ERROR] fetch_product_info attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}")
                print(f"[ERROR] Full error details: {repr(e)}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying fetch_product_info in 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"[ERROR] fetch_product_info failed after {max_retries} attempts")
                    return {"error": f"Database query failed after {max_retries} attempts: {str(e)}"}

    @function_tool()
    async def fetch_all_products(
        self,
        context: RunContext,
    ) -> dict:
        """
        Fetch all available products from the Supabase database.
        
        Returns:
            A dictionary with a list of all products (name, price, size, description) or an error message.
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] fetch_all_products: Attempt {attempt + 1}/{max_retries}")
                print(f"[DEBUG] Table: {PRODUCT_TABLE}")
                print(f"[DEBUG] Columns to select: {PRODUCT_COLUMNS}")
                
                # Use select('*') to get all columns
                response = (
                    self.supabase.table(PRODUCT_TABLE)
                    .select('*')
                    .execute()
                )
                
                print(f"[DEBUG] fetch_all_products response.data type: {type(response.data)}")
                print(f"[DEBUG] fetch_all_products response.data length: {len(response.data) if response.data else 0}")
                print(f"[DEBUG] fetch_all_products full response.data: {response.data}")
                
                if response.data and len(response.data) > 0:
                    products_list = [
                        {
                            "name": product.get("p.name"),
                            "price": f"${product.get('p.price')}",
                            "size": product.get("p.size"),
                            "description": product.get("p.description"),
                        }
                        for product in response.data
                    ]
                    print(f"[SUCCESS] Found {len(products_list)} products")
                    print(f"[DEBUG] Products list: {products_list}")
                    
                    # Create a detailed message for the LLM
                    product_details = []
                    for p in products_list:
                        product_details.append(f"{p['name']} ({p['size']} size) - {p['price']}: {p['description']}")
                    
                    result = {
                        "status": "success",
                        "total_products": len(products_list),
                        "products": products_list,
                        "message": f"Current menu has {len(products_list)} items: " + " | ".join(product_details)
                    }
                    print(f"[DEBUG] Returning to LLM: {result}")
                    return result
                else:
                    print("[WARNING] No products found in database")
                    return {"error": "No products found"}
                    
            except Exception as e:
                print(f"[ERROR] fetch_all_products attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}")
                print(f"[ERROR] Full error details: {repr(e)}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying fetch_all_products in 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"[ERROR] fetch_all_products failed after {max_retries} attempts")
                    return {"error": f"Database query failed after {max_retries} attempts: {str(e)}"}

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
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION
    )
    print("[DEBUG] Initial reply generated")

if __name__ == "__main__":
    print(f"[DEBUG] Application starting at {time.strftime('%H:%M:%S %z on %Y-%m-%d')}")
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))