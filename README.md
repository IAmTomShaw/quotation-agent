# AI Quotation Agent

A WebSocket-powered AI agent that provides accurate and competitive pricing quotes based on data from a Notion pricing database. This agent leverages OpenAI's GPT-4o model and integrates with external APIs to deliver real-time pricing information.

## 🚀 Features

- **Real-time WebSocket Communication**: Interactive chat interface with instant responses
- **Notion Integration**: Fetches pricing data from Notion database
- **Currency Conversion**: Supports multi-currency quotes using live exchange rates
- **Web Search Capabilities**: Can research market rates and industry standards
- **Session Management**: Maintains conversation context across multiple interactions
- **API Security**: Protected endpoints with API key authentication

## 🏗️ Architecture

The system consists of two main components:

1. **WebSocket Agent** ([main.py](main.py)): Core AI agent with FastAPI WebSocket server
2. **Streamlit Frontend** ([frontend.py](frontend.py)): Optional web interface for testing

### WebSocket Agent

The agent is built using the `openai-agents` library and provides:

- **Intelligent Pricing**: Analyzes client requirements and suggests appropriate rates
- **Tool Integration**: Uses function tools for external data fetching
- **Conversation Memory**: Maintains context throughout the chat session
- **Error Handling**: Robust error management and user feedback

## 🛠️ Setup

### Prerequisites

- Python 3.13+
- OpenAI API key
- Notion API access (optional)
- Exchange rate API key (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd quotation-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in [.env](.env):
```env
OPENAI_API_KEY=your_openai_api_key
API_KEY=your_api_security_key
NOTION_API_KEY=your_notion_api_key
NOTION_PAGE_ID=your_notion_page_id
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key
```

4. Run the WebSocket server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔌 WebSocket API

### Connection

Connect to the WebSocket endpoint:
```
ws://localhost:8000/ws/chat
```

### Message Format

Send messages as JSON with the following structure:

```json
{
  "session_id": "unique-session-id",
  "message": "I need a quote for my project requirements",
  "user_id": "user123",
  "timestamp": "2024-01-01T10:00:00Z",
  "message_type": "chat"
}
```

### Response Format

Receive responses in the following format:

```json
{
  "session_id": "unique-session-id",
  "message": "Based on your requirements...",
  "sender": "agent",
  "timestamp": "2024-01-01T10:00:01Z",
  "message_type": "response",
  "success": true,
  "error": null
}
```

### Special Commands

- Send `"/clear"` or set `message_type: "clear"` to reset conversation history

## 🛠️ Available Tools

The agent has access to several function tools:

### 1. Notion Pricing Data
- **Function**: [`get_pricing_from_notion`](main.py)
- **Purpose**: Fetches current pricing information from Notion database
- **Integration**: Uses Notion API to retrieve structured pricing data

### 2. Currency Conversion
- **Function**: [`currency_conversion`](main.py)
- **Purpose**: Converts prices between different currencies
- **API**: Uses exchangerate-api.com for live exchange rates

### 3. Web Search
- **Tool**: `WebSearchTool()`
- **Purpose**: Researches market rates and industry standards
- **Usage**: Helps provide competitive pricing context

## 📋 REST API Endpoints

### Health Check
```
GET /
```
Returns API status (requires API key authentication)

### Clear Chat History
```
POST /clear-chat
```
Clears the global conversation history

## 🐳 Docker Deployment

The project includes a [Dockerfile](Dockerfile) for containerized deployment:

```bash
# Build the image
docker build -t quotation-agent .

# Run the container
docker run -p 8000:8000 --env-file .env quotation-agent
```

## 💡 Usage Examples

### Basic Quote Request
```json
{
  "session_id": "session123",
  "message": "I need a quote for my project requirements",
  "message_type": "chat"
}
```

### Currency-Specific Quote
```json
{
  "session_id": "session123",
  "message": "What would this cost in USD?",
  "message_type": "chat"
}
```

### Follow-up Questions
```json
{
  "session_id": "session123",
  "message": "Can you break down the pricing for each deliverable?",
  "message_type": "chat"
}
```

## 🧪 Testing with Frontend

An optional Streamlit frontend is provided for testing:

```bash
streamlit run frontend.py
```

Access the web interface at `http://localhost:8501`

## 📊 Pricing Data Structure

The agent works with pricing data from [pricing.txt](pricing.txt) as its source of information. This document contains structured pricing information that the agent uses to generate accurate quotes.

## 🔧 Configuration

Key configuration options in [main.py](main.py):

- **Model**: GPT-4o for optimal reasoning
- **Session Management**: UUID-based session tracking
- **Error Handling**: Comprehensive exception management
- **API Security**: Header-based authentication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the WebSocket API
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

---

Built with ❤️ by [Tom Shaw](https://tomshaw.dev)