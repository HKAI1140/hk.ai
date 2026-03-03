#!/usr/bin/env python3
"""
港股模拟炒股大赛 MCP API 封装脚本

提供命令行接口调用 MCP 服务的所有工具

授权方式: ApiKey
凭证Key: COZE_HK_TRADING_TOKEN_<skill_id>
"""

import argparse
import json
import os
import sys

try:
    from coze_workload_identity import requests
except ImportError:
    import requests


# Skill ID (构建时已确定)
SKILL_ID = "7612169344646119458"

# MCP 服务基础端点
MCP_BASE_URL = "https://www.mcp.zjk.site/mcp/http"

# 请求 ID 计数器
_request_id = 0


def get_mcp_endpoint() -> str:
    """
    获取 MCP 服务端点（包含用户 Token）
    
    Returns:
        完整的 MCP 端点 URL
    """
    # 从环境变量获取用户的 Token
    credential_key = f"COZE_HK_TRADING_TOKEN_{SKILL_ID}"
    token = os.getenv(credential_key)
    
    if not token:
        raise ValueError(
            f"缺少必要的凭证配置。请设置环境变量 {credential_key}，"
            "或通过 Skill 凭证管理配置您的 MCP Token。"
        )
    
    return f"{MCP_BASE_URL}?token={token}"


def call_mcp_tool(tool_name: str, arguments: dict = None) -> dict:
    """
    调用 MCP 工具
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        API 响应结果
    """
    global _request_id
    _request_id += 1
    
    try:
        endpoint = get_mcp_endpoint()
    except ValueError as e:
        return {"success": False, "error": str(e)}
    
    payload = {
        "jsonrpc": "2.0",
        "id": _request_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # 检查 JSON-RPC 错误
        if "error" in result:
            return {"success": False, "error": result["error"]}
        
        # 提取工具返回内容
        content = result.get("result", {}).get("content", [])
        if content and len(content) > 0:
            text_content = content[0].get("text", "{}")
            try:
                return {"success": True, "data": json.loads(text_content)}
            except json.JSONDecodeError:
                return {"success": True, "data": text_content}
        
        return {"success": True, "data": result.get("result", {})}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"网络请求失败: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"未知错误: {str(e)}"}


# ==================== 行情查询 ====================

def list_selectable_stocks():
    """查询可选股票列表及最新行情"""
    return call_mcp_tool("list_selectable_stocks")


def get_quote_by_symbols(symbols):
    """
    批量查询指定股票代码的最新行情
    
    Args:
        symbols: 股票代码数组或逗号分隔的字符串
    """
    # 处理输入格式
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(",")]
    return call_mcp_tool("get_quote_by_symbols", {"symbols": symbols})


def get_market_status():
    """获取市场状态"""
    return call_mcp_tool("get_market_status")


# ==================== 账户查询 ====================

def get_account_snapshot():
    """获取账户快照"""
    return call_mcp_tool("get_account_snapshot")


def get_positions():
    """查询当前持仓列表及浮动盈亏"""
    return call_mcp_tool("get_positions")


def get_holdings():
    """持股明细"""
    return call_mcp_tool("get_holdings")


# ==================== 交易操作 ====================

def buy_stock(stock_code: str, quantity: int):
    """
    买入股票
    
    Args:
        stock_code: 股票代码，如 00700.HK
        quantity: 买入数量（股），最小 10 股
    """
    return call_mcp_tool("buy_stock", {"stock_code": stock_code, "quantity": quantity})


def sell_stock(stock_code: str, quantity: int):
    """
    卖出股票
    
    Args:
        stock_code: 股票代码，如 00700.HK
        quantity: 卖出数量（股），最小 10 股
    """
    return call_mcp_tool("sell_stock", {"stock_code": stock_code, "quantity": quantity})


# ==================== 历史记录 ====================

def get_orders_history(limit: int = 50):
    """查询买卖交易历史记录"""
    return call_mcp_tool("get_orders_history", {"limit": min(limit, 200)})


def get_buy_list(page: int = 1, limit: int = 50):
    """查询买入历史"""
    return call_mcp_tool("get_buy_list", {"page": page, "limit": min(limit, 200)})


def get_sell_list(page: int = 1, limit: int = 50):
    """查询卖出历史"""
    return call_mcp_tool("get_sell_list", {"page": page, "limit": min(limit, 200)})


def get_settlement_list(page: int = 1, limit: int = 50):
    """查询结算记录"""
    return call_mcp_tool("get_settlement_list", {"page": page, "limit": min(limit, 200)})


def get_balance_log(page: int = 1, limit: int = 50):
    """查询余额变动流水"""
    return call_mcp_tool("get_balance_log", {"page": page, "limit": min(limit, 200)})


def get_fee_log(page: int = 1, limit: int = 50):
    """查询手续费记录"""
    return call_mcp_tool("get_fee_log", {"page": page, "limit": min(limit, 200)})


# ==================== 规则查询 ====================

def get_competition_rules():
    """获取比赛规则"""
    return call_mcp_tool("get_competition_rules")


# ==================== 命令行接口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="港股模拟炒股大赛 MCP API 客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 行情查询
  python trading_api.py --action list_stocks
  python trading_api.py --action get_quote --symbols "00700.HK,00388.HK"
  python trading_api.py --action market_status

  # 账户查询
  python trading_api.py --action account
  python trading_api.py --action positions
  python trading_api.py --action holdings

  # 交易操作
  python trading_api.py --action buy --stock-code 00700.HK --quantity 100
  python trading_api.py --action sell --stock-code 00700.HK --quantity 100

  # 历史记录
  python trading_api.py --action orders_history --limit 50
  python trading_api.py --action buy_list --page 1 --limit 50
  python trading_api.py --action sell_list --page 1 --limit 50

  # 规则查询
  python trading_api.py --action rules

注意:
  需要先配置 MCP Token 凭证，通过环境变量 COZE_HK_TRADING_TOKEN_7612169344646119458 设置
        """
    )
    
    parser.add_argument(
        "--action",
        required=True,
        choices=[
            # 行情
            "list_stocks", "get_quote", "market_status",
            # 账户
            "account", "positions", "holdings",
            # 交易
            "buy", "sell",
            # 历史
            "orders_history", "buy_list", "sell_list",
            "settlement_list", "balance_log", "fee_log",
            # 规则
            "rules"
        ],
        help="操作类型"
    )
    
    parser.add_argument("--symbols", help="股票代码，逗号分隔")
    parser.add_argument("--stock-code", help="股票代码")
    parser.add_argument("--quantity", type=int, help="交易数量")
    parser.add_argument("--page", type=int, default=1, help="页码")
    parser.add_argument("--limit", type=int, default=50, help="返回条数")
    
    args = parser.parse_args()
    
    # 执行对应操作
    result = None
    
    if args.action == "list_stocks":
        result = list_selectable_stocks()
    elif args.action == "get_quote":
        if not args.symbols:
            result = {"success": False, "error": "缺少 --symbols 参数"}
        else:
            result = get_quote_by_symbols(args.symbols)
    elif args.action == "market_status":
        result = get_market_status()
    elif args.action == "account":
        result = get_account_snapshot()
    elif args.action == "positions":
        result = get_positions()
    elif args.action == "holdings":
        result = get_holdings()
    elif args.action == "buy":
        if not args.stock_code or not args.quantity:
            result = {"success": False, "error": "缺少 --stock-code 或 --quantity 参数"}
        else:
            result = buy_stock(args.stock_code, args.quantity)
    elif args.action == "sell":
        if not args.stock_code or not args.quantity:
            result = {"success": False, "error": "缺少 --stock-code 或 --quantity 参数"}
        else:
            result = sell_stock(args.stock_code, args.quantity)
    elif args.action == "orders_history":
        result = get_orders_history(args.limit)
    elif args.action == "buy_list":
        result = get_buy_list(args.page, args.limit)
    elif args.action == "sell_list":
        result = get_sell_list(args.page, args.limit)
    elif args.action == "settlement_list":
        result = get_settlement_list(args.page, args.limit)
    elif args.action == "balance_log":
        result = get_balance_log(args.page, args.limit)
    elif args.action == "fee_log":
        result = get_fee_log(args.page, args.limit)
    elif args.action == "rules":
        result = get_competition_rules()
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 返回状态码
    sys.exit(0 if result and result.get("success") else 1)


if __name__ == "__main__":
    main()
