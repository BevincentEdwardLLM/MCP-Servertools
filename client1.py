import os, re, json, ast, asyncio
import pandas as pd
import streamlit as st
import base64
from io import BytesIO
from PIL import Image
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import streamlit.components.v1 as components
import re
import json
from anthropic import Anthropic
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import requests


# Load environment variables
load_dotenv()

# Initialize OpenAI client with environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("🔐 OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")
    st.stop()


llm_client = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    model=os.environ.get("OPENAI_MODEL", "gpt-4o") # Using gpt-4o as a modern default
)


# initialising anthropic client
ANTHROPIC_API_KEY=os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    st.error("🔐 ANTHROPIC_API_KEY environment variable is not set. Please add it to your environment.")
    st.stop()
else:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="MCP CRUD Chat", layout="wide")

# ========== GLOBAL CSS ==========
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4286f4 0%, #397dd2 100%);
        color: #fff !important;
        min-width: 330px !important;
        padding: 0 0 0 0 !important;
    }
    [data-testid="stSidebar"] .sidebar-title {
        color: #fff !important;
        font-weight: bold;
        font-size: 2.2rem;
        letter-spacing: -1px;
        text-align: center;
        margin-top: 28px;
        margin-bottom: 18px;
    }
    .sidebar-block {
        width: 94%;
        margin: 0 auto 18px auto;
    }
    .sidebar-block label {
        color: #fff !important;
        font-weight: 500;
        font-size: 1.07rem;
        margin-bottom: 4px;
        margin-left: 2px;
        display: block;
        text-align: left;
    }
    .sidebar-block .stSelectbox>div {
        background: #fff !important;
        color: #222 !important;
        border-radius: 13px !important;
        font-size: 1.13rem !important;
        min-height: 49px !important;
        box-shadow: 0 3px 14px #0002 !important;
        padding: 3px 10px !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
    }
    .stButton>button {
            width: 100%;
            height: 3rem;
            background: #39e639;
            color: #222;
            font-size: 1.1rem;
            font-weight: bold;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
    /* Small refresh button styling */
    .small-refresh-button button {
        width: auto !important;
        height: 2rem !important;
        background: #4286f4 !important;
        color: #fff !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        margin-bottom: 0.5rem !important;
        padding: 0.25rem 0.75rem !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    .small-refresh-button button:hover {
        background: #397dd2 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    .sidebar-logo-label {
        margin-top: 30px !important;
        margin-bottom: 10px;
        font-size: 1.13rem !important;
        font-weight: 600;
        text-align: center;
        color: #fff !important;
        letter-spacing: 0.1px;
    }
    .sidebar-logo-row {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .sidebar-logo-row img {
        width: 42px;
        height: 42px;
        border-radius: 9px;
        background: #fff;
        padding: 6px 8px;
        object-fit: contain;
        box-shadow: 0 2px 8px #0002;
    }
    /* Chat area needs bottom padding so sticky bar does not overlap */
    .stChatPaddingBottom { padding-bottom: 98px; }
    /* Responsive sticky chatbar */
    .sticky-chatbar {
        position: fixed;
        left: 330px;
        right: 0;
        bottom: 0;
        z-index: 100;
        background: #f8fafc;
        padding: 0.6rem 2rem 0.8rem 2rem;
        box-shadow: 0 -2px 24px #0001;
    }
    @media (max-width: 800px) {
        .sticky-chatbar { left: 0; right: 0; padding: 0.6rem 0.5rem 0.8rem 0.5rem; }
        [data-testid="stSidebar"] { display: none !important; }
    }
    .chat-bubble {
        padding: 13px 20px;
        margin: 8px 0;
        border-radius: 18px;
        max-width: 75%;
        font-size: 1.09rem;
        line-height: 1.45;
        box-shadow: 0 1px 4px #0001;
        display: inline-block;
        word-break: break-word;
    }
    .user-msg {
        background: #e6f0ff;
        color: #222;
        margin-left: 24%;
        text-align: right;
        border-bottom-right-radius: 6px;
        border-top-right-radius: 24px;
    }
    .agent-msg {
        background: #f5f5f5;
        color: #222;
        margin-right: 24%;
        text-align: left;
        border-bottom-left-radius: 6px;
        border-top-left-radius: 24px;
    }
    .chat-row {
        display: flex;
        align-items: flex-end;
        margin-bottom: 0.6rem;
    }
    .avatar {
        height: 36px;
        width: 36px;
        border-radius: 50%;
        margin: 0 8px;
        object-fit: cover;
        box-shadow: 0 1px 4px #0002;
    }
    .user-avatar { order: 2; }
    .agent-avatar { order: 0; }
    .user-bubble { order: 1; }
    .agent-bubble { order: 1; }
    .right { justify-content: flex-end; }
    .left { justify-content: flex-start; }
    .chatbar-claude {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        max-width: 850px;
        margin: 0 auto;
        border-radius: 20px;
        background: #fff;
        box-shadow: 0 2px 8px #0002;
        padding: 8px 14px;
        margin-bottom: 0;
    }
    .claude-hamburger {
        background: #f2f4f9;
        border: none;
        border-radius: 11px;
        font-size: 1.35rem;
        font-weight: bold;
        width: 38px; height: 38px;
        cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.13s;
    }
    .claude-hamburger:hover { background: #e6f0ff; }
    .claude-input {
        flex: 1;
        border: none;
        outline: none;
        font-size: 1.12rem;
        padding: 0.45rem 0.5rem;
        background: #f5f7fa;
        border-radius: 8px;
        min-width: 60px;
    }
    .claude-send {
        background: #fe3044 !important;
        color: #fff !important;
        border: none;
        border-radius: 50%;
        width: 40px; height: 40px;
        font-size: 1.4rem !important;
        cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.17s;
    }
    .claude-send:hover { background: #d91d32 !important; }
    .tool-menu {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        min-width: 200px;
    }
    .server-title {
        font-weight: bold;
        margin-bottom: 10px;
        color: #333;
    }
    .expandable {
        margin-top: 8px;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: #fff !important;
        font-weight: 500;
        font-size: 1.07rem;
    }
    /* Visualization styles */
    .visualization-container {
        margin: 20px 0;
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #f9f9f9;
    }
    .visualization-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

# ========== NEW HELPER FUNCTION: DETECT VISUALIZATION INTENT ==========
def detect_visualization_intent(query: str) -> str:
    """
    Analyzes the user's query to detect if a visualization is requested.
    This simulates a more complex semantic search.
    """
    visualization_keywords = [
        "visualize", "chart", "graph", "plot", "dashboard","trend","trends",
        "distribution", "breakdown", "pie chart", "bar graph", "line chart",
        "show me a report", "analytics for", "visual", "visuals","Illustrate"
    ]
    query_lower = query.lower()
    for keyword in visualization_keywords:
        if keyword in query_lower:
            return "Yes"
    return "No"


# ========== DYNAMIC TOOL DISCOVERY FUNCTIONS ==========
async def _discover_tools() -> dict:
    """Discover available tools from the MCP server"""
    try:
        # ✅ Ensure base host only, no trailing /mcp
        server_url = st.session_state.get("MCP_SERVER_URL", "http://localhost:8000")
        
        # ✅ Append /mcp only once here
        transport = StreamableHttpTransport(f"{server_url}/mcp")
        
        async with Client(transport) as client:
            tools = await client.list_tools()
            return {tool.name: tool.description for tool in tools}
    except Exception as e:
        st.error(f"Failed to discover tools: {e}")
        return {}


def discover_tools() -> dict:
    """Synchronous wrapper for tool discovery"""
    return asyncio.run(_discover_tools())


def generate_tool_descriptions(tools_dict: dict) -> str:
    """Generate tool descriptions string from discovered tools"""
    if not tools_dict:
        return "No tools available"

    descriptions = ["Available tools:"]
    for i, (tool_name, tool_desc) in enumerate(tools_dict.items(), 1):
        descriptions.append(f"{i}. {tool_name}: {tool_desc}")

    return "\n".join(descriptions)

def get_image_base64(img_path):
    img = Image.open(img_path)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode()
    return img_base64

# ========== SIDEBAR NAVIGATION ==========
with st.sidebar:
    st.markdown("<div class='sidebar-title'>Solutions Scope</div>", unsafe_allow_html=True)
    with st.container():
        # Application selectbox (with key)
        application = st.selectbox(
            "Select Application",
            ["Select Application", "MCP Application"],
            key="app_select"
        )

        # Dynamically choose default options for other selects
        # Option lists
        protocol_options = ["", "MCP Protocol", "A2A Protocol"]
        llm_options = ["", "OpenAI gpt-4o", "OpenAI gpt-4-turbo", "Anthropic claude-3-5-sonnet-20240620"]

        # Logic to auto-select defaults if MCP Application is chosen
        protocol_index = protocol_options.index(
            "MCP Protocol") if application == "MCP Application" else protocol_options.index(
            st.session_state.get("protocol_select", ""))
        llm_index = llm_options.index("OpenAI gpt-4o") if application == "MCP Application" else llm_options.index(
            st.session_state.get("llm_select", ""))

        protocol = st.selectbox(
            "Protocol",
            protocol_options,
            key="protocol_select",
            index=protocol_index
        )

        llm_model = st.selectbox(
            "LLM Models",
            llm_options,
            key="llm_select",
            index=llm_index
        )

        # Dynamic server tools selection based on discovered tools
        if application == "MCP Application" and "available_tools" in st.session_state and st.session_state.available_tools:
            server_tools_options = [""] + list(st.session_state.available_tools.keys())
            default_tool = list(st.session_state.available_tools.keys())[0] if st.session_state.available_tools else ""
            server_tools_index = server_tools_options.index(default_tool) if default_tool else 0
        else:
            server_tools_options = ["", "sqlserver_crud", "postgresql_crud"]  # Fallback
            server_tools_index = 0

        server_tools = st.selectbox(
            "Server Tools",
            server_tools_options,
            key="server_tools",
            index=server_tools_index
        )

        st.button("Clear/Reset", key="clear_button")

    st.markdown('<div class="sidebar-logo-label">Build & Deployed on</div>', unsafe_allow_html=True)
    logo_base64 = get_image_base64("llm.png")
    st.markdown(
    f"""
    <div class="sidebar-logo-row">
        <img src="https://media.licdn.com/dms/image/v2/D560BAQFIon13R1UG4g/company-logo_200_200/company-logo_200_200/0/1733990910443/llm_at_scale_logo?e=2147483647&v=beta&t=WtAgFOcGQuTS0aEIqZhNMzWraHwL6FU0z5EPyPrty04" title="Logo" style="width: 50px; height: 50px;">
        <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/googlecloud/googlecloud-original.svg" title="Google Cloud" style="width: 50px; height: 50px;">
        <img src="https://a0.awsstatic.com/libra-css/images/logos/aws_logo_smile_1200x630.png" title="AWS" style="width: 50px; height: 50px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/a/a8/Microsoft_Azure_Logo.svg" title="Azure Cloud" style="width: 50px; height: 50px;">
    </div>
    """,
    unsafe_allow_html=True
)


# ========== LOGO/HEADER FOR MAIN AREA ==========
logo_path = "servicenow.png"
logo_base64 = get_image_base64(logo_path) if os.path.exists(logo_path) else ""
if logo_base64:
    st.markdown(
        f"""
        <div style='display: flex; flex-direction: column; align-items: center; margin-bottom:20px;'>
            <img src='data:image/png;base64,{logo_base64}' width='400'>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 18px;
        padding: 10px 0 10px 0;
    ">
        <span style="
            font-size: 2.5rem;
            font-weight: bold;
            letter-spacing: -2px;
            color: #222;
        ">
            Agentic AI Orchestration
        </span>
        <span style="
            font-size: 1.15rem;
            color: #555;
            margin-top: 0.35rem;
        ">
            Voice Agents Simplify User Interaction and Improve
User Experience with ServiceNow 
        </span>
        <hr style="
        width: 80%;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #4286f4, transparent);
        margin: 20px auto;
        ">
    </div>

    """,
    unsafe_allow_html=True
)

# ========== SESSION STATE INIT ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize available_tools if not exists
if "available_tools" not in st.session_state:
    st.session_state.available_tools = {}

# Initialize MCP_SERVER_URL in session state
if "MCP_SERVER_URL" not in st.session_state:
    st.session_state["MCP_SERVER_URL"] = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

# Initialize tool_states dynamically based on discovered tools
if "tool_states" not in st.session_state:
    st.session_state.tool_states = {}

if "show_menu" not in st.session_state:
    st.session_state["show_menu"] = False
if "menu_expanded" not in st.session_state:
    st.session_state["menu_expanded"] = True
if "chat_input_box" not in st.session_state:
    st.session_state["chat_input_box"] = ""

# Initialize visualization state
if "visualizations" not in st.session_state:
    st.session_state.visualizations = []


# ========== HELPER FUNCTIONS ==========
def _clean_json(raw: str) -> str:
    fences = re.findall(r"``````", raw, re.DOTALL)
    if fences:
        return fences[0].strip()
    # If no JSON code fence, try to find JSON-like content
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    return json_match.group(0).strip() if json_match else raw.strip()


def call_mcp_tool(tool_name: str, operation: str, args: dict) -> dict:
    """
    Synchronous helper that calls the MCP server REST endpoint for a tool.
    Adjust URL/path depending on your FastMCP HTTP transport.
    """
    base_url = st.session_state.get("MCP_SERVER_URL", "http://localhost:8000") + f"/call_tool"
    url=f"{base_url}/tools/{tool_name}/invoke"
    payload = {"tool": tool_name, "operation": operation, "args": args}
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"sql": None, "result": f"❌ error calling MCP tool: {e}"}


# ========== PARAMETER VALIDATION FUNCTION ==========
def validate_and_clean_parameters(tool_name: str, args: dict) -> dict:
    """Validate and clean parameters for specific tools"""

    if tool_name == "sales_crud":
        # Define allowed parameters for sales_crud (with WHERE clause support)
        allowed_params = {
            'operation', 'customer_id', 'product_id', 'quantity',
            'unit_price', 'total_amount', 'sale_id', 'new_quantity',
            'table_name', 'display_format', 'customer_name',
            'product_name', 'email', 'total_price',
            'columns',  # Column selection
            'where_clause',  # WHERE conditions
            'filter_conditions',  # Structured filters
            'limit'  # Row limit
        }

        # Clean args to only include allowed parameters
        cleaned_args = {k: v for k, v in args.items() if k in allowed_params}

        # Validate display_format values
        if 'display_format' in cleaned_args:
            valid_formats = [
                'Data Format Conversion',
                'Decimal Value Formatting',
                'String Concatenation',
                'Null Value Removal/Handling'
            ]
            if cleaned_args['display_format'] not in valid_formats:
                cleaned_args.pop('display_format', None)

        # Clean up columns parameter
        if 'columns' in cleaned_args:
            if isinstance(cleaned_args['columns'], str) and cleaned_args['columns'].strip():
                columns_str = cleaned_args['columns'].strip()
                columns_list = [col.strip() for col in columns_str.split(',') if col.strip()]
                cleaned_args['columns'] = ','.join(columns_list)
            else:
                cleaned_args.pop('columns', None)

        # Validate WHERE clause
        if 'where_clause' in cleaned_args:
            if not isinstance(cleaned_args['where_clause'], str) or not cleaned_args['where_clause'].strip():
                cleaned_args.pop('where_clause', None)

        # Validate limit
        if 'limit' in cleaned_args:
            try:
                limit_val = int(cleaned_args['limit'])
                if limit_val <= 0 or limit_val > 1000:  # Reasonable limits
                    cleaned_args.pop('limit', None)
                else:
                    cleaned_args['limit'] = limit_val
            except (ValueError, TypeError):
                cleaned_args.pop('limit', None)

        return cleaned_args

    elif tool_name == "sqlserver_crud":
        allowed_params = {
            'operation', 'name', 'email', 'limit', 'customer_id',
            'new_email', 'table_name'
        }
        return {k: v for k, v in args.items() if k in allowed_params}

    elif tool_name == "postgresql_crud":
        allowed_params = {
            'operation', 'name', 'price', 'description', 'limit',
            'product_id', 'new_price', 'table_name'
        }
        return {k: v for k, v in args.items() if k in allowed_params}

    return args


# ========== NEW LLM RESPONSE GENERATOR ==========
def generate_llm_response(operation_result: dict, action: str, tool: str, user_query: str, history_limit: int = 10) -> str:
    """Generate LLM response based on operation result with context (includes chat history)."""

    # collect last N messages from session (if available)
    messages_for_llm = []
    history = st.session_state.get("messages", [])[-history_limit:]
    for m in history:
        role = m.get("role", "user")
        content = m.get("content", "")
        # convert to System/Human/Assistant roles for your LLM client
        if role == "assistant":
            messages_for_llm.append(HumanMessage(content=f"(assistant) {content}"))
        else:
            messages_for_llm.append(HumanMessage(content=f"(user) {content}"))

    system_prompt = (
        "You are a helpful database assistant. Generate a brief, natural response "
        "explaining what operation was performed and its result. Be conversational "
        "and informative. Focus on the business context and user-friendly explanation."
    )

    user_prompt = f"""
User asked: "{user_query}"
Operation: {action}
Tool used: {tool}
Result: {json.dumps(operation_result, indent=2)}
Please respond naturally and reference prior conversation context where helpful.
"""

    try:
        messages = [SystemMessage(content=system_prompt)] + messages_for_llm + [HumanMessage(content=user_prompt)]
        response = llm_client.invoke(messages)
        return response.content.strip()
    except Exception as e:
        # Fallback response if LLM call fails
        if action == "read":
            return f"Successfully retrieved data from {tool}."
        elif action == "create":
            return f"Successfully created new record in {tool}."
        elif action == "update":
            return f"Successfully updated record in {tool}."
        elif action == "delete":
            return f"Successfully deleted record from {tool}."
        elif action == "describe":
            return f"Successfully retrieved table schema from {tool}."
        else:
            return f"Operation completed successfully using {tool}."


# ========== VISUALIZATION GENERATOR ==========
def generate_visualization(data: any, user_query: str, tool: str) -> tuple:
    """
    Generate JavaScript visualization code based on data and query.
    Streams code live while generating, then renders.
    Returns tuple of (HTML/JS code for the visualization, raw code).
    """
    # Prepare context for the LLM
    context = {
        "user_query": user_query,
        "tool": tool,
        "data_type": type(data).__name__,
        "data_sample": data[:5] if isinstance(data, list) and len(data) > 0 else data
    }

    system_prompt = """
    You are a JavaScript dashboard designer and visualization expert.

⚡ ALWAYS!!! generate a FULL, self-contained HTML document with:
- <!DOCTYPE html>, <html>, <head>, <body>, and </html> tags included.
- <style> for modern responsive CSS (gradient backgrounds, glassmorphism cards, shadows, rounded corners).
- <script> with all JavaScript logic inline (no external JS files except Chart.js).
- At least two charts (bar, pie, or line) using Chart.js (CDN: https://cdn.jsdelivr.net/npm/chart.js).
- Summary stat cards (totals, averages, trends).
- Optional dynamic lists or tables derived from the data.
- Smooth animations, styled tooltips, and responsive resizing.

📌 RULES:
1. Output ONLY raw HTML, CSS, and JS (no markdown, no explanations).
2. Charts must have fixed max height (350–400px).
3. The document is INVALID unless it ends with </html>. Do not stop early.
4. Always close all opened tags and brackets in HTML, CSS, and JS.
5. The final deliverable must run directly in a browser without edits.

🎨 Design:
- Use a clean dashboard layout with cards, charts, and tables.
- Gradient backgrounds, glassmorphism effects, shadows, rounded corners.
- Gradient or neon text for headings and KPI values.
- Responsive layout for both desktop and mobile.

❌ Never truncate output.
✅ Always finish the document properly with </html>.
"""
    

    user_prompt = f"""
    Create an interactive visualization for this data:
    
    User Query: "{user_query}"
    Tool Used: {tool}
    Data Type: {context['data_type']}
    Data Sample: {json.dumps(context['data_sample'], indent=2)}
    
    📌 Requirements:
- Return a COMPLETE, browser-ready HTML document.
- Include <style> and <script> inline.
- Close all tags properly.
- End ONLY with </html>.
    Generate a comprehensive visualization that helps understand the data.
    Focus on the most important insights from the query.
    Make sure charts have fixed heights and don't overflow .
    """

    try:
        # Placeholder to show live code generation
        placeholder = st.empty()
        code_accum = ""

        # Stream response tokens from Anthropic
        with anthropic_client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            for event in stream:
                if event.type == "content.delta":
                    token = event.delta
                    code_accum += token
                    
            final_message = stream.get_final_message()
            visualization_code = "".join(
                block.text for block in final_message.content if block.type == "text"
            ).strip()

        # Return both the code and the rendered HTML
        st.code(visualization_code, language="html")
        return visualization_code, visualization_code

    except Exception as e:
        
        # Fallback to a simple table if visualization generation fails
        if isinstance(data, list) and len(data) > 0:
            fallback_code = f"""
            <div class="visualization-container" style="height: 400px; overflow: auto;">
                <div class="visualization-title">Data Table</div>
                <div id="table-container"></div>
            </div>
            <script>
                const data = {json.dumps(data)};
                let tableHtml = '<table border="1" style="width:100%; border-collapse: collapse;">';
                
                // Add headers
                tableHtml += '<tr>';
                Object.keys(data[0]).forEach(key => {{
                    tableHtml += `<th style="padding: 8px; background: #f2f2f2;">${{key}}</th>`;
                }});
                tableHtml += '</tr>';
                
                // Add rows
                data.forEach(row => {{
                    tableHtml += '<tr>';
                    Object.values(row).forEach(value => {{
                        tableHtml += `<td style="padding: 8px;">${{value}}</td>`;
                    }});
                    tableHtml += '</tr>';
                }});
                
                tableHtml += '</table>';
                document.getElementById('table-container').innerHTML = tableHtml;
            </script>
            """
        else:
            fallback_code = f"""
            <div class="visualization-container" style="height: 200px; overflow: auto;">
                <div class="visualization-title">Result</div>
                <p>{str(data)}</p>
            </div>
            """
        return fallback_code, fallback_code

# Add this CSS for the split layout
st.markdown("""
    <style>
    .split-container {
        display: flex;
        width: 100%;
        gap: 20px;
        margin: 20px 0;
    }
    .code-panel {
        flex: 1;
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #e9ecef;
        max-height: 500px;
        overflow-y: auto;
    }
    .viz-panel {
        flex: 1;
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #e9ecef;
        max-height: 500px;
        overflow-y: auto;
    }
    .code-header, .viz-header {
        font-weight: bold;
        margin-bottom: 10px;
        color: #333;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .copy-button {
        background: #4286f4;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.8rem;
    }
    .copy-button:hover {
        background: #397dd2;
    }
    .chart-container {
        height: 350px !important;
        margin-bottom: 20px;
    }
    .visualization-container {
        height: 400px;
        overflow: auto;
        max-width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)


def parse_user_query(query: str, available_tools: dict) -> dict:
    """
    Takes a natural language query and uses an LLM to generate a JSON object
    containing the appropriate tool and a valid BigQuery SQL query.
    """
    if not available_tools:
        return {"error": "No tools available to query."}

    # Build a detailed description of all available tools for the LLM prompt.
    tool_descriptions = "\n".join(
        [f"- **{name}**: {desc}" for name, desc in available_tools.items()]
    )

    # --- UPDATED PROMPT FOR OPENAI CONSISTENCY ---
    # New System Prompt
    # New System Prompt with Updated Examples
    system_prompt = f"""
You are an expert Google BigQuery SQL writer. Your sole function is to act as a deterministic translator.
Your task is to convert a user's natural language request into a single, valid JSON object.
This JSON object MUST contain two keys:
1.  **"tool"**: The exact name of the tool from the list below.
2.  **"sql"**: A valid, complete, and syntactically correct BigQuery SQL query.

**STRICT RULES:**
* **DO NOT** generate any prose, explanations, or text outside the JSON object. Your entire response must be the JSON.
* The `sql` query MUST use the full, exact table names as specified in the tool descriptions (e.g., `genai-poc-424806.MCP_demo.CarData`).
* The `tool` value MUST be one of the exact tool names provided.

**AVAILABLE TOOLS AND THEIR DESCRIPTIONS:**
{tool_descriptions}

**EXAMPLES:**
1.  User Query: "Show me all records from the BigQuery CarData table."
    JSON Output:
    {{
      "tool": "BigQuery_CarData",
      "sql": "SELECT * FROM `genai-poc-424806.MCP_demo.CarData`"
    }}
2.  User Query: "Find all customer feedback records for product 101."
    JSON Output:
    {{
      "tool": "Oracle_CustomerFeedback",
      "sql": "SELECT * FROM `genai-poc-424806.MCP_demo.CustomerFeedback` WHERE product_id = '101'"
    }}
3.  User Query: "How many users are registered?"
    JSON Output:
    {{
      "tool": "tool_Users",
      "sql": "SELECT COUNT(*) FROM `genai-poc-424806.MCP_demo.Users`"
    }}
4.  User Query: "List the top 5 highest-priced cars."
    JSON Output:
    {{
      "tool": "BigQuery_CarData",
      "sql": "SELECT * FROM `genai-poc-424806.MCP_demo.CarData` ORDER BY price DESC LIMIT 5"
    }}
5.  User Query: "Give me the first 20 records from the Youth Health Records."
    JSON Output:
    {{
      "tool": "Bigquery_YouthHealthRecords",
      "sql": "SELECT * FROM `genai-poc-424806.MCP_demo.YouthHealthRecords` LIMIT 20"
    }}

Now, for the user's query, generate ONLY the JSON response. """
    # --- END OF UPDATED PROMPT ---

    user_prompt = f'User query: "{query}"'

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Call the LLM to generate the tool and SQL
        resp = llm_client.invoke(messages)
        raw_json = _clean_json(resp.content)

        # Parse the cleaned JSON response
        try:
            result = json.loads(raw_json)
        except json.JSONDecodeError:
            result = ast.literal_eval(raw_json)
        
        # Return the parsed result directly. All old logic is removed.
        return result

    except Exception as e:
        # If any part of the process fails, return a structured error.
        return {
            "tool": None,
            "sql": None,
            "error": f"Failed to parse query: {str(e)}"
        }


async def _invoke_tool(tool: str, sql: str) -> any: # <-- Changed parameters
    transport = StreamableHttpTransport(f"{st.session_state['MCP_SERVER_URL']}/mcp")
    async with Client(transport) as client:
        # The payload now only needs the sql parameter, as the tool functions in main.py expect it.
        payload = {"sql": sql} 
        res_obj = await client.call_tool(tool, payload)
    if res_obj.structured_content is not None:
        return res_obj.structured_content
    text = "".join(b.text for b in res_obj.content).strip()
    if text.startswith("{") and "}{" in text:
        text = "[" + text.replace("}{", "},{") + "]"
    try:
        return json.loads(text)
    except:
        return text


# In client.py, find the call_mcp_tool function

def call_mcp_tool(tool: str, sql: str) -> any: # <-- Changed parameters
    return asyncio.run(_invoke_tool(tool, sql))


def format_natural(data) -> str:
    if isinstance(data, list):
        lines = []
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                parts = [f"{k} {v}" for k, v in item.items()]
                lines.append(f"Record {i}: " + ", ".join(parts) + ".")
            else:
                lines.append(f"{i}. {item}")
        return "\n".join(lines)
    if isinstance(data, dict):
        parts = [f"{k} {v}" for k, v in data.items()]
        return ", ".join(parts) + "."
    return str(data)


def normalize_args(args):
    mapping = {
        "product_name": "name",
        "customer_name": "name",
        "item": "name"
    }
    for old_key, new_key in mapping.items():
        if old_key in args:
            args[new_key] = args.pop(old_key)
    return args


def extract_name_from_query(text: str) -> str:
    """Enhanced name extraction that handles various patterns"""
    # Patterns for customer operations
    customer_patterns = [
        r'delete\s+customer\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'remove\s+customer\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'update\s+customer\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'delete\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'remove\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)'
    ]
    
    # Patterns for product operations
    product_patterns = [
        r'delete\s+product\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'remove\s+product\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'update\s+(?:price\s+of\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'change\s+price\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'(?:price\s+of\s+)([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:to|=)'
    ]
    
    all_patterns = customer_patterns + product_patterns
    
    for pattern in all_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group(0) if match else None


def extract_price(text):
    # Look for price patterns like "to 25", "= 30.50", "$15.99"
    price_patterns = [
        r'to\s+\$?(\d+(?:\.\d+)?)',
        r'=\s+\$?(\d+(?:\.\d+)?)',
        r'\$(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*dollars?'
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None


# Updated generate_table_description function
def generate_table_description(df: pd.DataFrame, content: dict, action: str, tool: str, user_query: str) -> str:
    """Generate a simple, direct confirmation message for a successful query."""

    # Get the number of records from the DataFrame
    record_count = len(df)

    # --- REVISED SYSTEM PROMPT ---
    system_prompt = (
        "You are a helpful and efficient database assistant. Your sole purpose is "
        "to confirm a user's request in a single, friendly sentence. "
        "The response must include the number of records retrieved and confirm that the data has been provided. "
        "Do not provide any analysis, insights, or technical details."
    )
    # --- END REVISED SYSTEM PROMPT ---

    user_prompt = f"""
    The user asked: "{user_query}"
    The query successfully retrieved {record_count} records.
    The data is from the "{tool}" tool.

    Please generate a single, friendly, and simple confirmation message.

    Example: "Sure, here is the car data you requested. It contains 321 records."
    Example: "The records for user 'chen.wei' are here. We found 25 matching entries for you."
    """

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = llm_client.invoke(messages)
        return response.content.strip()
    except Exception as e:
        # Fallback to a simple message if the LLM call fails
        return f"Successfully retrieved {record_count} records from the database."


# ========== NEW HELPER FUNCTION: RENDER ASSISTANT MESSAGE CONTENT ==========
# ========== REPLACEMENT FUNCTION ==========
def render_assistant_message_content(msg: dict):
    """
    Renders the assistant's message, now updated for the new SQL-based server response.
    """
    agent_avatar_url = "https://cdn-icons-png.flaticon.com/512/4712/4712039.png"
    
    # Check if the message is for displaying results from a tool call
    if msg.get("format") == "sql_crud" and isinstance(msg["content"], dict):
        content = msg.get("content", {})
        request = msg.get("request", {})
        user_query = msg.get("user_query", "")
        
        # Extract the generated SQL query from the request
        sql_query = request.get("sql", "No SQL query was generated.")
        
        # Extract results from the server's response
        result_rows = content.get("rows", [])
        row_count = content.get("row_count", 0)
        table_name = content.get("table", "an unknown table")
        error = content.get("error")

        # Display a conversational summary message
        summary_message = msg.get("description", f"I ran the query against the **{table_name}** table and found **{row_count}** results for you.")
        if error:
            summary_message = f"I encountered an error trying to query the **{table_name}** table."

        st.markdown(
            f"""
            <div class="chat-row left">
                <img src="{agent_avatar_url}" class="avatar agent-avatar" alt="Agent">
                <div class="chat-bubble agent-msg agent-bubble">{summary_message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Use an expander to show the technical details
        with st.expander("Show Details"):
            st.markdown("##### 💬 User Query")
            st.text(user_query)
            st.markdown("##### ⚙️ Generated SQL")
            st.code(sql_query, language="sql")
            st.markdown("##### 📥 Raw Server Response")
            st.json(content)

        # If there was an error, display it clearly
        if error:
            st.error(f"🚨 **Error:** {error}")
        # If we have data, display it in a table
        elif result_rows and isinstance(result_rows, list):
            st.markdown("#### Query Results")
            df = pd.DataFrame(result_rows)
            st.dataframe(df)

    else:
        # Fallback for simple text messages (like errors from the client)
        st.markdown(
            f"""
            <div class="chat-row left">
                <img src="{agent_avatar_url}" class="avatar agent-avatar" alt="Agent">
                <div class="chat-bubble agent-msg agent-bubble">{msg['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ========== MAIN ==========
if application == "MCP Application":
    
    user_avatar_url = "https://cdn-icons-png.flaticon.com/512/1946/1946429.png"
    agent_avatar_url = "https://cdn-icons-png.flaticon.com/512/4712/4712039.png"

    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    st.session_state["MCP_SERVER_URL"] = MCP_SERVER_URL

    # Discover tools dynamically if not already done
    if not st.session_state.available_tools:
        with st.spinner("Discovering available tools..."):
            discovered_tools = discover_tools()
        st.session_state.available_tools = discovered_tools
        st.session_state.tool_states = {tool: True for tool in discovered_tools.keys()}

    # Generate dynamic tool descriptions
    TOOL_DESCRIPTIONS = generate_tool_descriptions(st.session_state.available_tools)

    # ========== 1. REFACTORED CHAT MESSAGE RENDERING LOOP ==========
    st.markdown('<div class="stChatPaddingBottom">', unsafe_allow_html=True)
    for msg_index, msg in enumerate(st.session_state.messages):
        # --- Render User Messages ---
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="chat-row right">
                    <div class="chat-bubble user-msg user-bubble">{msg['content']}</div>
                    <img src="{user_avatar_url}" class="avatar user-avatar" alt="User">
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # --- Render Assistant Messages ---
        elif msg["role"] == "assistant":
            # Check if this message has a linked visualization
            viz_index = msg.get("visualization_index")

            if viz_index is not None and viz_index < len(st.session_state.visualizations):
                # --- Create Split-Screen Layout for Chat + Visualization ---
                chat_col, viz_col = st.columns(2)

                with chat_col:
                    render_assistant_message_content(msg)

                with viz_col:
                    cola,colb=st.columns([0.05,0.95])
                    with colb:
                        viz_html, viz_code, viz_query = st.session_state.visualizations[viz_index]
                        with st.expander(
                            f"Visualization: {viz_query[:50]}..." if len(viz_query) > 50 else f"Visualization: {viz_query}",
                            expanded=False):
                            # Create tabs with Code first, then Visualization
                            tab1, tab2 = st.tabs(["Generated Code", "Visualization"])
                            with tab1:
                                st.markdown("**Generated Code**")
                                with st.container(height=800):
                                # Initialize streaming state for this visualization if not exists
                                    stream_key = f"stream_complete_{msg_index}"
                                    if stream_key not in st.session_state:
                                        st.session_state[stream_key] = False
                                    # Create placeholder for streaming effect
                                    code_placeholder = st.empty()
                                    if not st.session_state[stream_key]:
                                    # Streaming effect - show code character by character
                                        import time
                                    # Show streaming indicator first
                                        with code_placeholder.container():
                                            st.info("🔄 Generating code...")
                                        # Small delay to show the loading message
                                        time.sleep(0.5)
                                    # Stream the code
                                        streamed_code = ""
                                        for j, char in enumerate(viz_code):
                                            streamed_code += char
                                        # Update every 5-10 characters for better performance
                                            if j % 8 == 0 or j == len(viz_code) - 1:
                                                code_placeholder.code(streamed_code, language="html")
                                                time.sleep(0.03)  # Adjust speed as needed
                                    # Mark streaming as complete
                                        st.session_state[stream_key] = True
                                    # Force a rerun to show the complete state
                                        st.rerun()
                                    else:
                                    # Show complete code immediately
                                        code_placeholder.code(viz_code, language="html")
                                    # Adding copy button (only show when streaming is complete)
                                    if st.session_state[stream_key]:
                                        if st.button("Copy Code", key=f"copy_{msg_index}"):
                                            st.session_state.copied_code = viz_code
                                            st.success("Code copied to clipboard!")
                                        if st.button("Replay Generation", key=f"replay_{msg_index}"):
                                            st.session_state[stream_key] = False
                                            st.rerun()
                            with tab2:
                                st.markdown("**Interactive Visualization**")
                                # Use a container with fixed height
                                with st.container():
                                    components.html(viz_code, height=800, scrolling=True)
                                if st.session_state.visualizations:
                                    if st.button("Clear Visualizations", key=f"clear_viz_{msg_index}"):
                                        st.session_state.visualizations = []
                                        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("stream_complete_")]
                                        for key in keys_to_remove:
                                            del st.session_state[key]
                                        st.rerun()
                                
                                    
            else:
                # --- Render a normal, full-width assistant message ---
                render_assistant_message_content(msg)


    st.markdown('</div>', unsafe_allow_html=True)
   
    
    

    # ========== 3. CLAUDE-STYLE STICKY CHAT BAR ==========
    
    st.markdown('<div class="sticky-chatbar"><div class="chatbar-claude">', unsafe_allow_html=True)
    with st.form("chatbar_form", clear_on_submit=True):
        chatbar_cols = st.columns([1, 16, 1])  # Left: hamburger, Middle: input, Right: send

        # --- LEFT: Hamburger (Tools) ---
        with chatbar_cols[0]:
            hamburger_clicked = st.form_submit_button("≡", use_container_width=True)

        # --- MIDDLE: Input Box ---
        with chatbar_cols[1]:
            user_query_input = st.text_input(
            "Chat Input",  # Provide a label
            placeholder="How can I help you today?",
            label_visibility="collapsed",  # Hide the label visually
            key="chat_input_box"
            )

        # --- RIGHT: Send Button ---
        with chatbar_cols[2]:
            send_clicked = st.form_submit_button("➤", use_container_width=True)
    
    
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # if st.session_state.available_tools:
    #     st.info(
    #         f"🔧 Discovered {len(st.session_state.available_tools)} tools: {', '.join(st.session_state.available_tools.keys())}")
    # else:
    #     st.warning("⚠️ No tools discovered. Please check your MCP server connection.")
    
    # ========== HANDLE HAMBURGER ==========
    if hamburger_clicked:
        st.session_state["show_menu"] = not st.session_state.get("show_menu", False)
        st.rerun()

    # ========== PROCESS CHAT INPUT ==========
    
    if user_query_input and send_clicked:
        user_query = user_query_input

        # --- NEW LOGIC: DIRECTLY HANDLE META-QUERIES ABOUT TOOLS ---
        if "list" in user_query.lower() and "tools" in user_query.lower():
            st.session_state.messages.append({"role": "user", "content": user_query, "format": "text"})
            
            tools_list = st.session_state.get("available_tools")
            if tools_list:
                formatted_list = "Here are the available tools:\n\n"
                for name, desc in tools_list.items():
                    formatted_list += f"- **{name}**\n"
                assistant_response = formatted_list
            else:
                assistant_response = "I'm sorry, no tools are currently available. Please check the MCP server connection."
            
            st.session_state.messages.append({"role": "assistant", "content": assistant_response, "format": "text"})
            st.rerun()

        # The 'try' block starts here and wraps all operations
        try:
            enabled_tools = [k for k, v in st.session_state.tool_states.items() if v]
            if not enabled_tools:
                raise Exception("No tools are enabled. Please enable at least one tool in the menu.")

            # 1. Parse the user's query to get the tool and SQL
            p = parse_user_query(user_query, st.session_state.available_tools)
            tool = p.get("tool")
            sql_query = p.get("sql")

            if not tool or not sql_query:
                raise Exception("LLM failed to generate a valid tool or SQL query.")
            
            if tool not in enabled_tools:
                raise Exception(f"Tool '{tool}' is disabled. Please enable it in the menu.")
            if tool not in st.session_state.available_tools:
                raise Exception(
                    f"Tool '{tool}' is not available. Available tools: {', '.join(st.session_state.available_tools.keys())}")

            # 2. Call the tool with the generated SQL
            raw = call_mcp_tool(tool, sql_query)

            # 3. Prepare the response message for the chat history
            
            assistant_message = {
                "role": "assistant",
                "content": raw,
                "format": "sql_crud",
                "request": p,
                "tool": tool,
                "user_query": user_query,
            }

            # --- NEW LOGIC: Dynamically generate a table description ---
            if p.get("sql", "").lower().strip().startswith("select") and raw.get("rows", []):
                df = pd.DataFrame(raw["rows"])
                try:
                    # Check this line carefully!
                    table_description = generate_table_description(df, raw, "read", tool, user_query)
                    assistant_message["description"] = table_description
                except Exception as e:
                    assistant_message["description"] = f"Retrieved {len(df)} records from the database."

            # 4. Check for and generate visualization if needed
            visualization_intent = detect_visualization_intent(user_query)
            should_generate_viz = (visualization_intent == "Yes" )
            
            viz_data = raw.get("rows", raw) if isinstance(raw, dict) else raw

            if viz_data and isinstance(viz_data, list) and len(viz_data) > 0 and should_generate_viz:
                with st.spinner("🎨 Generating visualization..."):
                    viz_code, viz_html = generate_visualization(viz_data, user_query, tool)
                    
                    if "visualizations" not in st.session_state:
                        st.session_state.visualizations = []
                    
                    st.session_state.visualizations.append((viz_html, viz_code, user_query))
                    assistant_message["visualization_index"] = len(st.session_state.visualizations) - 1
                    st.success("Visualization generated successfully!")

        # The 'except' block correctly catches any failure from the 'try' block
        except Exception as e:
            # Append user query and the error message to chat
            st.session_state.messages.append({"role": "user", "content": user_query, "format": "text"})
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}", "format": "text"})
        
        # The 'else' block runs ONLY if the 'try' block was successful
        else:
            # Append user query and the successful assistant message to chat
            st.session_state.messages.append({"role": "user", "content": user_query, "format": "text"})
            st.session_state.messages.append(assistant_message)
        
        # Rerun the app to display the new messages
        st.rerun()

    # ========== 4. AUTO-SCROLL TO BOTTOM ==========
    components.html("""
        <script>
            setTimeout(() => { window.scrollTo(0, document.body.scrollHeight); }, 80);
        </script>
    """)