from agents import Agent, Runner, TResponseInputItem, function_tool, WebSearchTool
import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")



# Agent Tools

@function_tool
async def get_pricing_from_notion():
 
  # API Request to Notion to get pricing data

  api_url = f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children"

  headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
  }

  response = requests.get(api_url, headers=headers)

  print(f"Fetching pricing data from Notion: {response.status_code} - {response.text}")

  if response.status_code != 200:
    print(f"Failed to fetch pricing data: {response.status_code} - {response.text}")
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Failed to fetch pricing data from Notion")
  
  data = response.json()

  return f"The pricing data from Notion is: {json.dumps(data, indent=2)}"

@function_tool
async def currency_conversion(amount: float, from_currency: str, to_currency: str):
  """Convert currency using an external API"""

  print(f"Converting {amount} from {from_currency} to {to_currency}")

  api_url = f"https://v6.exchangerate-api.com/v6/7446b91e600ea91f9238c885/latest/{from_currency}"
  
  response = requests.get(api_url)
  
  if response.status_code != 200:
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Failed to fetch exchange rates")
  
  rates = response.json().get("rates", {})
  
  if to_currency not in rates:
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"Currency {to_currency} not supported")
  
  converted_amount = amount * rates[to_currency]
  
  return f"{converted_amount:.2f} {to_currency}"

# Agent Function

conversation: list[TResponseInputItem] = []

async def run_quotation_agent(message: str, page_id: str = None):

  # You should customise this agent's prompt to suit your needs and your business.

  agent = Agent(
    name="Quotation Agent",
    instructions=f"""
    <background>
    You are a pricing and quotation agent that provides accurate and competitive pricing quotes based on user requests. You are an expert in the influencer marketing industry so you know how to price campaigns effectively.
    You are pricing campaigns for Tom Shaw, a programming and tech content creator with a focus on software development, AI, and technology trends.
    </background>
    <goal>
    Provide accurate and competitive pricing quotes that are beneficial for the influencer to ensure that they are paid a fair rate for their services. If you do not have enough information, or need any details specified (for example, the type of content, duration, on or off site production, etc), ask the user for more information.
    </goal>
    <tools>
    You have access to tools that can fetch information on the influencer's pricing list. You have the ability to search the web for additional information if needed. Make sure to specify when you have used a tool so that the user knows where the information came from. You can also convert currencies using the exchange rate API.
    </tools>
    <output>
    Provide a clear and concise quote based on the user's request. The quote should be broken down into its component parts so that the user can understand how you have reached the final amount. If the user asks for more information, provide relevant details about the influencer's previous deals and pricing. The quote should be in the GBP currency format unless otherwise specified. If so, you should convert the quote to the specified currency. If you do swap currencies, make sure you do the pricing in GBP first, then convert to the specified currency using the exchange rate API.
    </output>
    """,
    tools=[get_pricing_from_notion, WebSearchTool(), currency_conversion],
    model="gpt-4o",
  )

  # Add the message to the conversation
  conversation.append({
    "role": "user",
    "content": message
  })

  result = await Runner.run(agent, conversation)

  if result and result.final_output:
    conversation.append({
      "role": "assistant",
      "content": result.final_output
    })
  else:
    conversation.append({
      "role": "assistant",
      "content": "No response from agent."
    })

  return result




# FastAPI Setup

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()

def verify_api_key(api_key: str = Depends(api_key_header)):
  if api_key != API_KEY:
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key")
  return api_key

@app.get("/")
def read_root(api_key: str = Depends(verify_api_key)):
  return {"message": "API is working"}

@app.post("/clear-chat")
def clear_chat(api_key: str = Depends(verify_api_key)):
  """Clear the conversation history"""
  global conversation
  conversation.clear()
  return {"message": "Chat history cleared successfully", "success": True}

class ConnectionManager:
  def __init__(self):
    self.active_connections: list[WebSocket] = []

  async def connect(self, websocket: WebSocket):
    await websocket.accept()
    self.active_connections.append(websocket)

  def disconnect(self, websocket: WebSocket):
    self.active_connections.remove(websocket)

  async def send_message(self, message: str, websocket: WebSocket):
    await websocket.send_text(message)

  async def broadcast(self, message: str):
    for connection in self.active_connections:
      await self.send_message(message, connection)

manager = ConnectionManager()

class ChatMessage(BaseModel):
  session_id: str
  message: str
  user_id: str = "user"
  timestamp: str | None = None
  message_type: str = "chat"

class ChatResponse(BaseModel):
  session_id: str
  message: str
  sender: str = "agent"
  timestamp: str
  message_type: str = "response"
  success: bool = True
  error: str | None = None

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
  await manager.connect(websocket)
  session_id = str(uuid.uuid4())
  print(f"New WebSocket connection established with session ID: {session_id}")
  
  try:
    while True:
      # Receive message from client
      data = await websocket.receive_text()
      
      try:
        # Parse incoming JSON message
        message_data = json.loads(data)
        chat_message = ChatMessage(**message_data)
        
        # Check if this is a clear command
        if chat_message.message_type == "clear" or chat_message.message.lower().strip() == "/clear":
          global conversation
          conversation.clear()
          response = ChatResponse(
            session_id=chat_message.session_id,
            message="Chat history has been cleared.",
            timestamp=datetime.now().isoformat()
          )
        else:
          # Process the message with the agent
          agent_response = await process_chat_message(chat_message.message)
          
          # Create response
          response = ChatResponse(
            session_id=chat_message.session_id,
            message=agent_response,
            timestamp=datetime.now().isoformat()
          )
        
        # Send response back to client
        await manager.send_message(response.model_dump_json(), websocket)
          
      except json.JSONDecodeError:
        # Handle plain text messages for backward compatibility
        agent_response = await process_chat_message(data)
        response = ChatResponse(
          session_id=session_id,
          message=agent_response,
          timestamp=datetime.now().isoformat()
        )
        await manager.send_message(response.model_dump_json(), websocket)
          
      except Exception as e:
        # Handle errors
        error_response = ChatResponse(
          session_id=session_id,
          message="Sorry, I encountered an error processing your message.",
          timestamp=datetime.now().isoformat(),
          success=False,
          error=str(e)
        )
        await manager.send_message(error_response.model_dump_json(), websocket)
                
  except WebSocketDisconnect:
    manager.disconnect(websocket)
    print(f"WebSocket connection closed for session: {session_id}")

async def process_chat_message(message: str) -> str:
  """Process chat message with the quotation agent"""
  try:
    # Run the quotation agent with the user's message
    result = await run_quotation_agent(message)
    
    # Return the agent's final output
    if result and result.final_output:
      return result.final_output
    else:
      return "I couldn't process your request at the moment. Please try again."
          
  except Exception as e:
    print(f"Error processing message: {e}")
    return "I encountered an error while processing your message. Please try again."
