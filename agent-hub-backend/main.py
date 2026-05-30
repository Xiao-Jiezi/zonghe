import os
import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
import PyPDF2
import docx

app = FastAPI(title="Agent Hub Backend")

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
    api_key = "sk-99af2b42d32a48a6a3ccaa1718f8279b" 
    
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
async def api_ocr(file: UploadFile = File(...)):
    """真实接收前端传来的图片/文档并解析"""
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
    
    sys_prompt = """你是一个高级多模态文档分析专家。
请对提取出的文档文本或图片内容进行自然语言总结和重组。
要求：
1. 绝对不要输出 JSON 格式。
2. 用流畅的自然语言、清晰的段落结构来汇报。
3. 一两句话总结核心大意，然后归纳关键信息。
4. 用逻辑清晰的方式将凌乱的信息重新组织排版。"""
    
    try:
        result = await call_llm_gateway(extracted_text, sys_prompt, image_base64)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "data": f"提取失败: {str(e)}"}

@app.post("/api/speech")
async def api_speech_analysis(file: UploadFile = File(...)):
    """真实处理录音文件"""
    content = await file.read()
    
    # 【修复核心点】：处理缺少后缀名、或 Mime Type 丢失导致 API 报错的问题
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
        # 精准抛出 API 错误原文
        return {"status": "error", "data": f"通义千问语音接口报错: {he.detail}"}
    except Exception as e:
        return {"status": "error", "data": f"音频发送异常: {str(e)}"}
        
    # 第二阶段：大模型语义分析
    sys_prompt = """你是一个全能的智能语音语义分析专家。
请对用户的语音转写文本进行深度理解。
请输出排版优雅的自然语言，包含：
1. 语音转写原文（引用格式）。
2. 核心主旨概括。
3. 梳理重要细节与逻辑。
4. 分析说话者的深层语义与意图。
绝对不要输出 JSON 格式！"""
    
    prompt_text = f"以下是真实语音转写结果，请分析：\n\n{transcript}"
    
    try:
        result = await call_llm_gateway(prompt_text, sys_prompt)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "data": f"语义模型报错: {str(e)}"}