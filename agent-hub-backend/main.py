import os
import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
import PyPDF2
import docx
from dotenv import load_dotenv

# 加载 .env 文件
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

app = FastAPI(title="Agent Hub Backend")

# 从环境变量读取 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
if not DASHSCOPE_API_KEY:
    print("警告: 未设置 DASHSCOPE_API_KEY 环境变量，请在 .env 文件中配置")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    prompt: str

async def call_llm_gateway(prompt: str, system_prompt: str = "", image_base64: str = None) -> str:
    """统一向 通义千问 发起请求"""
    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    api_key = "sk-99af2b42d32a48a6a3ccaa1718f8279b" 
    
    model_name = "qwen-vl-plus" if image_base64 else "qwen-plus"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
        
    if image_base64:
        messages.append({
            "role": "user", 
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        })
    else:
        messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(api_url, json=payload, headers=headers, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            err_text = e.response.text
            try:
                err_msg = e.response.json().get("error", {}).get("message", err_text)
            except:
                err_msg = err_text
            raise HTTPException(status_code=e.response.status_code, detail=f"大模型报错: {err_msg}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"模型请求失败: {str(e)}")

async def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> str:
    """调用通义千问 Qwen3-ASR-Flash 识别真实语音（OpenAI 兼容模式）"""
    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    api_key = DASHSCOPE_API_KEY
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 将音频文件转为 base64
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    audio_data_uri = f"data:{content_type};base64,{audio_base64}"
    
    payload = {
        "model": "qwen3-asr-flash",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_data_uri}
                    }
                ]
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(api_url, json=payload, headers=headers, timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            err_text = e.response.text
            try:
                err_msg = e.response.json().get("error", {}).get("message", err_text)
            except:
                err_msg = err_text
            raise HTTPException(status_code=e.response.status_code, detail=err_msg)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ================= 业务接口路由 =================

@app.post("/api/chat")
async def api_chat(req: AgentRequest):
    """新增：标准综合聊天接口"""
    sys_prompt = "你是一个智能、友善、全能的AI助手。请自然、准确地回答用户的问题，并提供有帮助的信息。"
    result = await call_llm_gateway(req.prompt, sys_prompt)
    return {"status": "success", "data": result}

@app.post("/api/coder")
async def api_auto_coder(req: AgentRequest):
    sys_prompt = "你是一个顶尖的全栈软件架构师。请根据用户需求输出高质量代码。务必在回答最后使用 Markdown 代码块包裹代码，并准确标注编程语言（如 ```javascript, ```python 等）。"
    result = await call_llm_gateway(req.prompt, sys_prompt)
    return {"status": "success", "data": result}

@app.post("/api/research")
async def api_deep_research(req: AgentRequest):
    sys_prompt = "你是一个严谨的资深行业研究员。请对给定主题进行深度剖析。直接输出排版干净、优雅的自然语言或Markdown排版。绝对不要包含任何JSON格式、特殊符号或复杂的代码包裹。"
    result = await call_llm_gateway(req.prompt, sys_prompt)
    return {"status": "success", "data": result}

@app.post("/api/ocr")
async def api_ocr(file: UploadFile = File(...), prompt: str = Form(None)):
    """真实接收前端传来的图片/文档并解析（支持附加文字要求）"""
    content = await file.read()
    filename = file.filename.lower()
    extracted_text = ""
    image_base64 = None
    
    try:
        # 1. 解析真实 PDF 内容
        if filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            if not extracted_text.strip():
                return {"status": "error", "data": "未能从 PDF 中提取到文本。若是纯图片扫描件，请尝试上传图片格式。"}
        
        # 2. 解析 Word 文档
        elif filename.endswith('.docx'):
            try:
                doc = docx.Document(io.BytesIO(content))
                extracted_text = "\n".join([para.text for para in doc.paragraphs if para.text])
                if not extracted_text.strip():
                    return {"status": "error", "data": "未能从 Word 文档中提取到文字，可能是纯图片Word。"}
            except Exception as e:
                return {"status": "error", "data": f"Word 文档解析异常: {str(e)}"}
                
        # 3. 解析真实图片内容
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            image_base64 = base64.b64encode(content).decode('utf-8')
            extracted_text = "请详细阅读这张图片中的所有文本，并理解其内容结构。"
            
        # 4. 解析真实文本内容
        elif filename.endswith(('.txt', '.md', '.csv')):
            extracted_text = content.decode('utf-8', errors='ignore')
        else:
            return {"status": "error", "data": f"暂不支持解析该文件格式: {filename}"}
    except Exception as e:
        return {"status": "error", "data": f"文件解析失败: {str(e)}"}
    
    # 如果用户输入了附加的问题，将其拼接到提问中
    if prompt:
        extracted_text += f"\n\n--- 用户的具体问题/要求 ---\n{prompt}"
        
    sys_prompt = """你是一个高级多模态文档分析专家。
请对提取出的文档文本或图片内容进行自然语言总结和重组。
要求：
1. 绝对不要输出 JSON 格式。
2. 用流畅的自然语言、清晰的段落结构来汇报。
3. 如果用户有具体的附加问题，请优先解答用户的问题。"""
    
    try:
        result = await call_llm_gateway(extracted_text, sys_prompt, image_base64)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "data": f"提取失败: {str(e)}"}

@app.post("/api/speech")
async def api_speech_analysis(file: UploadFile = File(...), prompt: str = Form(None)):
    """真实处理录音文件（支持附加文字要求）"""
    content = await file.read()
    
    filename = file.filename or "audio_record.webm"
    content_type = file.content_type or "audio/webm"
    
    if "." not in filename:
        if "wav" in content_type:
            filename += ".wav"
        elif "mp3" in content_type:
            filename += ".mp3"
        else:
            filename += ".webm"
            
    try:
        # 第一阶段：语音转文字
        transcript = await transcribe_audio(content, filename, content_type)
        if not transcript:
            return {"status": "error", "data": "未能识别出语音内容，音频可能为空或全为噪音。"}
    except HTTPException as he:
        return {"status": "error", "data": f"阿里云语音接口报错: {he.detail}"}
    except Exception as e:
        return {"status": "error", "data": f"音频发送异常: {str(e)}"}
        
    # 第二阶段：大模型语义分析
    sys_prompt = """你是一个全能的智能语音语义分析专家。
请对用户的语音转写文本进行深度理解。
请输出排版优雅的自然语言，包含：
1. 语音转写原文（引用格式）。
2. 如果用户有附加提问，请优先解答提问。
3. 分析说话者的深层语义与意图。"""
    
    prompt_text = f"以下是真实语音转写结果：\n\n{transcript}"
    if prompt:
        prompt_text += f"\n\n--- 用户的附加问题/要求 ---\n{prompt}"
    
    try:
        result = await call_llm_gateway(prompt_text, sys_prompt)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "data": f"语义模型报错: {str(e)}"}