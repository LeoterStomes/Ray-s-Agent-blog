"""MCP Client — 连接外部 MCP Server，合并工具到 Agent"""
import json, os, time, subprocess, threading, httpx
from typing import Optional


class MCPHttpServer:
    """MCP Server 连接（HTTP/SSE 传输）"""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self._request_id = 0
        self._session_id: Optional[str] = None
        self._connected = False

    def start(self) -> bool:
        """发送 initialize 请求建立连接"""
        try:
            resp = self._post("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "blog-agent", "version": "1.0"},
            })
            if "error" in resp:
                print(f"[MCP:{self.name}] Init failed: {resp['error']}")
                return False
            result = resp.get("result", {})
            self._session_id = result.get("sessionId") or resp.get("sessionId")
            self._connected = True
            # Send initialized notification
            self._notify("notifications/initialized", {})
            tools = self.list_tools()
            print(f"[MCP:{self.name}] Connected (HTTP) — {len(tools)} tools")
            return True
        except Exception as e:
            print(f"[MCP:{self.name}] HTTP Start failed: {e}")
            return False

    def stop(self):
        self._connected = False

    def list_tools(self) -> list[dict]:
        resp = self._post("tools/list", {})
        tools = resp.get("result", {}).get("tools", [])
        converted = []
        for t in tools:
            schema = t.get("inputSchema", {})
            converted.append({
                "type": "function",
                "function": {
                    "name": f"mcp_{self.name}__{t['name']}",
                    "description": f"[{self.name}] {t.get('description', '')}",
                    "parameters": {
                        "type": schema.get("type", "object"),
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", []),
                    },
                },
            })
        return converted

    def call_tool(self, full_name: str, args: dict) -> str:
        real_name = full_name.split("__", 1)[1] if "__" in full_name else full_name
        resp = self._post("tools/call", {"name": real_name, "arguments": args})
        if "error" in resp:
            return json.dumps({"error": resp["error"]}, ensure_ascii=False)
        result_data = resp.get("result", {})
        content = result_data.get("content", [])
        texts = []
        for item in content:
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
        return json.dumps({"result": "\n".join(texts)}, ensure_ascii=False)

    def _post(self, method: str, params: dict) -> dict:
        self._request_id += 1
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        try:
            r = httpx.post(
                self.url,
                json={"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params},
                headers=headers,
                timeout=20.0,
            )
            if r.status_code in (200, 202):
                ct = r.headers.get("content-type", "")
                # Check for session ID in response headers
                sid = r.headers.get("mcp-session-id")
                if sid:
                    self._session_id = sid
                if "text/event-stream" in ct:
                    return self._parse_sse(r.text)
                return r.json()
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def _notify(self, method: str, params: dict):
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        try:
            httpx.post(
                self.url,
                json={"jsonrpc": "2.0", "method": method, "params": params},
                headers=headers,
                timeout=10.0,
            )
        except: pass

    def _parse_sse(self, text: str) -> dict:
        """解析 SSE 响应中的 JSON 数据"""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                data = line[5:].strip()
                if data and data != "[DONE]":
                    try:
                        return json.loads(data)
                    except: pass
        return {"error": "no valid SSE data"}


class MCPServer:
    """单个 MCP Server 连接（stdio）"""

    def __init__(self, name: str, command: str, args: list[str] = None, env: dict = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = {**os.environ, **(env or {})}
        self.process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._request_id = 0

    def start(self) -> bool:
        """启动 MCP Server 子进程"""
        try:
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # 忽略 stderr
                env=self.env, text=True, encoding='utf-8', errors='replace', bufsize=1,
            )
            time.sleep(0.3)  # 等 server 启动
            # Initialize
            result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "blog-agent", "version": "1.0"},
            })
            if "error" in result:
                print(f"[MCP:{self.name}] Init failed: {result['error']}")
                return False
            # Send initialized notification
            self._send_notification("notifications/initialized", {})
            time.sleep(0.1)
            print(f"[MCP:{self.name}] Connected — {len(self.list_tools())} tools")
            return True
        except Exception as e:
            print(f"[MCP:{self.name}] Start failed: {e}")
            return False

    def stop(self):
        if self.process:
            try: self.process.terminate()
            except: pass

    def list_tools(self) -> list[dict]:
        """获取工具列表 → OpenAI function calling 格式"""
        resp = self._send_request("tools/list", {})
        tools = resp.get("result", {}).get("tools", [])
        converted = []
        for t in tools:
            schema = t.get("inputSchema", {})
            converted.append({
                "type": "function",
                "function": {
                    "name": f"mcp_{self.name}__{t['name']}",
                    "description": f"[{self.name}] {t.get('description', '')}",
                    "parameters": {
                        "type": schema.get("type", "object"),
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", []),
                    },
                },
            })
        return converted

    def call_tool(self, full_name: str, args: dict) -> str:
        """执行工具 → 返回 JSON 字符串结果"""
        real_name = full_name.split("__", 1)[1] if "__" in full_name else full_name
        resp = self._send_request("tools/call", {"name": real_name, "arguments": args})
        if "error" in resp:
            return json.dumps({"error": resp["error"]}, ensure_ascii=False)
        result_data = resp.get("result", {})
        content = result_data.get("content", [])
        texts = []
        for item in content:
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
        return json.dumps({"result": "\n".join(texts)}, ensure_ascii=False)

    def _send_request(self, method: str, params: dict) -> dict:
        """同步发送 JSON-RPC 请求，跳过非 JSON 行"""
        with self._lock:
            self._request_id += 1
            req = json.dumps({
                "jsonrpc": "2.0", "id": self._request_id,
                "method": method, "params": params,
            })
            try:
                self.process.stdin.write(req + "\n")
                self.process.stdin.flush()
                # 跳过非 JSON 行（如服务器启动横幅）
                for _ in range(20):
                    line = self.process.stdout.readline()
                    if not line or not line.strip():
                        continue
                    try:
                        return json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue  # 跳过非 JSON 行
                return {"error": "no valid JSON response after 20 lines"}
            except Exception as e:
                return {"error": str(e)}

    def _send_notification(self, method: str, params: dict):
        with self._lock:
            notif = json.dumps({"jsonrpc": "2.0", "method": method, "params": params})
            try:
                self.process.stdin.write(notif + "\n")
                self.process.stdin.flush()
            except: pass


# ── 全局 MCP 管理 ──

_servers: dict[str, MCPServer] = {}


def load_mcp_servers() -> dict:
    """从环境变量加载 MCP Server 配置并启动（支持 stdio 和 HTTP）"""
    global _servers
    config_str = os.getenv("MCP_SERVERS", "")
    if not config_str:
        return {}

    for line in config_str.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            cfg = json.loads(line)
        except json.JSONDecodeError:
            continue

        name = cfg.get("name", "unknown")

        # HTTP/SSE 传输
        if "url" in cfg:
            server = MCPHttpServer(name, cfg["url"])
            if server.start():
                _servers[name] = server

        # Stdio 传输
        elif "command" in cfg:
            command = cfg.get("command", "")
            args = cfg.get("args", "").split() if cfg.get("args") else []
            server = MCPServer(name, command, args)
            if server.start():
                _servers[name] = server

    return _servers


def get_mcp_tools() -> list[dict]:
    """获取所有 MCP Server 的工具列表"""
    tools = []
    for name, server in _servers.items():
        try:
            tools.extend(server.list_tools())
        except Exception as e:
            print(f"[MCP:{name}] list_tools error: {e}")
    return tools


def call_mcp_tool(full_name: str, args: dict) -> Optional[str]:
    """调用 MCP 工具"""
    # full_name: "mcp_servername__toolname"
    parts = full_name.split("__", 1)
    if len(parts) < 2:
        return None
    server_name = parts[0].replace("mcp_", "", 1)
    server = _servers.get(server_name)
    if not server:
        return None
    return server.call_tool(full_name, args)


def shutdown_mcp():
    """关闭所有 MCP Server"""
    for server in _servers.values():
        server.stop()
    _servers.clear()
