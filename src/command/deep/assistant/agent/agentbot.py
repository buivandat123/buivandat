from .memories import *
from src.command.deep.assistant.agent.apiModels import *

def agentCore(this, promptToModelsClass, threadId, data, userId):
    cmdList = []
    if hasattr(this, "commands"):
        for name, cmd in this.commands.items():
            if isinstance(cmd, dict):
                desc = cmd.get("description", "")
                cmdList.append(f"Command '{name}': {desc}")

    cmdLists = "\n".join(cmdList)
    memoryText = getMemoryText(this, threadId, data)

    prompt = """
Bạn là trợ lý AI mang tên Agenty BOT, bạn có khả năng suy nghĩ, đưa ra câu trả lời đúng

+ Trả lời ngắn gọn, không quá dài khi đang hội thoại
+ Suy nghĩ, phân tích rồi đưa ra câu trả lời
+ Nếu người dùng hỏi câu hỏi bạn không biết thì bạn sẽ trả lời rằng bạn không biết
+ Suy nghĩ rồi đưa ra câu trả lời

- Nếu có người yêu cầu tạo hình ảnh thì bạn sẽ từ chối và nói rằng bạn không có khả năng tạo hình ảnh trong agent-models

Bạn có thể điều khiển các lệnh trong hệ thống nếu người dùng yêu cầu.
Danh sách các lệnh hiện có:
{cmdLists}

Bộ nhớ gần đây của cuộc trò chuyện (dùng để giữ ngữ cảnh, không được bịa thêm):
{memoryText}

Nếu người dùng yêu cầu thực thi một lệnh nào đó, hãy trả lời với định dạng duy nhất:
CMD: tên_lệnh tham_số 

dưới đây là câu hỏi của người dùng {asker} và nhớ rằng {asker} là tên người dùng: 
{generateContent}
"""
    return prompt.format(
        generateContent=promptToModelsClass,
        cmdLists=cmdLists,
        asker=this.userName(userId),
        memoryText=memoryText or "No memory",
    )

def Agent(this, message, data, userId, threadId, type):
    parts = (getattr(message, "text", "") or "").strip().split()
    if len(parts) < 2:
        this.sendMWarning("Bạn chưa nhập câu hỏi, vui lòng nhập câu hỏi cho AI", userId, threadId, type)
        return

    ask = " ".join(parts[1:]).strip()
    low = ask.lower()

    if "lịch sử" in low or "xem lại" in low or "tất cả" in low:
        items = getMemoryItems(this, threadId, data, limit=30)
        if not items:
            this.sendMSuccess("Chưa có lịch sử trong cuộc trò chuyện này.", userId, threadId, type)
            return
        lines = []
        for it in items:
            q = (it.get("q") or "").strip()
            a = (it.get("a") or "").strip()
            if q or a:
                lines.append(f"- User: {q}\n  Agent: {a}")
        this.sendMSuccess("\n".join(lines) if lines else "Chưa có lịch sử.", userId, threadId, type)
        return

    api = ApiModels()
    m = GeminiContent(api)
    m.prompt = agentCore(this, ask, threadId, data, userId)

    text = m.getText()
    if not text:
        this.sendMWarning("Không có câu trả lời.", userId, threadId, type)
        return

    cmdMatch = re.search(r"CMD:\s*(.+)", text, re.IGNORECASE)
    if cmdMatch:
        cmdContent = cmdMatch.group(1).strip()
        try:
            newData = data.copy() if isinstance(data, dict) else {}
            newData["content"] = f"{getattr(this, 'prefix', '/')}{cmdContent}"
            newData["mentions"] = []
            this.LoadCommands(message, newData, userId, threadId, type)
            return
        except Exception:
            this.sendMWarning("Lỗi thực thi lệnh AI", userId, threadId, type)
            return

    appendAgentMemory(
        this,
        threadId,
        data,
        userId,
        ask,
        text,
        meta={"chat_type": str(type or "")},
    )

    this.sendMSuccess(text, userId, threadId, type)

dependencies = {
    "name": "agent",
    "permission": 2,
    "description": "Agent bot",
    "cooldown": 5,
    "main": Agent
}