import argparse
import sys
import json
import os
from tabulate import tabulate
from datetime import datetime
from .services import TextToSQLService, conversation_manager, visualization_service
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 初始化 Rich Console
console = Console()


def format_execution_result(result):
    """格式化執行結果為表格"""
    if not result or not result.get("columns") or not result.get("rows"):
        return "無結果或空表"
    
    headers = result.get("columns", [])
    rows = result.get("rows", [])
    
    # 檢查是否有視覺化數據
    viz_info = ""
    if result.get("visualization"):
        viz_type = result["visualization"].get("type", "")
        img_path = result["visualization"].get("file_path", "")
        
        if viz_type and img_path:
            viz_info = f"\n\n視覺化: {viz_type.upper()} 圖表\n"
            viz_info += f"圖像保存至: {img_path}\n"
    
    # 使用 tabulate 格式化表格
    table = tabulate(rows, headers=headers, tablefmt="grid")
    
    # 如果有視覺化數據，添加到輸出中
    if viz_info:
        return table + viz_info
    else:
        return table


def print_query_history(service, limit=10):
    """打印查詢歷史"""
    history = service.get_history(limit=limit)
    
    if not history:
        console.print("[yellow]沒有查詢歷史記錄[/yellow]")
        return
    
    # 創建 Rich 表格
    table = Table(title="查詢歷史")
    table.add_column("ID", style="dim")
    table.add_column("查詢", style="cyan")
    table.add_column("狀態", style="green")
    table.add_column("標記", style="yellow")
    table.add_column("時間", style="magenta")
    
    for entry in history:
        # 處理日期格式
        created_at = entry.created_at
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # 格式化日期
        date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created_at, datetime) else str(created_at)
        
        # 狀態
        status = "[green]成功[/green]"
        if entry.error_message:
            status = f"[red]錯誤: {entry.error_message}[/red]"
        elif entry.executed:
            status = "[blue]已執行[/blue]"
            
        # 標記
        flags = []
        if entry.is_favorite:
            flags.append("⭐收藏")
        if entry.is_template:
            flags.append("📋模板")
        flags_str = ", ".join(flags) if flags else ""
        
        # 添加行
        table.add_row(
            str(entry.id),
            entry.user_query[:50] + ("..." if len(entry.user_query) > 50 else ""),
            status,
            flags_str,
            date_str
        )
    
    console.print(table)


def main():
    # 解析命令列參數
    parser = argparse.ArgumentParser(description='將自然語言查詢轉換為 SQL')
    subparsers = parser.add_subparsers(dest='command', help='指令')
    
    # 轉換命令
    convert_parser = subparsers.add_parser('convert', help='將自然語言轉換為 SQL')
    convert_parser.add_argument('query', type=str, nargs='?', help='要轉換的查詢文字')
    convert_parser.add_argument('-f', '--file', type=str, help='包含查詢的檔案')
    convert_parser.add_argument('-o', '--output', type=str, help='輸出檔案')
    convert_parser.add_argument('-e', '--execute', action='store_true', help='執行生成的 SQL')
    convert_parser.add_argument('--format', choices=['text', 'json'], default='text', help='輸出格式')
    convert_parser.add_argument('-m', '--model', type=str, help='使用的語言模型')
    convert_parser.add_argument('--no-similar', action='store_true', help='禁用相似查詢推薦')
    convert_parser.add_argument('-s', '--session', type=str, help='對話會話ID，用於維持對話上下文')
    
    # 歷史命令
    history_parser = subparsers.add_parser('history', help='查看查詢歷史')
    history_parser.add_argument('-l', '--limit', type=int, default=10, help='顯示數量限制')
    
    # 執行命令
    execute_parser = subparsers.add_parser('execute', help='執行 SQL 查詢')
    execute_parser.add_argument('sql', type=str, nargs='?', help='要執行的 SQL 查詢')
    execute_parser.add_argument('-f', '--file', type=str, help='包含 SQL 的檔案')
    
    # 模型命令
    models_parser = subparsers.add_parser('models', help='查看和管理語言模型')
    models_parser.add_argument('-l', '--list', action='store_true', help='列出所有可用模型')
    models_parser.add_argument('-s', '--set-default', type=str, help='設置默認模型')
    models_parser.add_argument('-p', '--performance', action='store_true', help='顯示模型性能統計')
    
    # 向量存儲命令
    vector_parser = subparsers.add_parser('vector', help='管理向量存儲')
    vector_parser.add_argument('-s', '--stats', action='store_true', help='顯示向量存儲統計')
    vector_parser.add_argument('-c', '--clear', action='store_true', help='清除向量存儲')
    vector_parser.add_argument('-q', '--query', type=str, help='在向量存儲中搜索相似查詢')
    vector_parser.add_argument('-l', '--limit', type=int, default=5, help='最大返回結果數')
    
    # 對話命令
    conversation_parser = subparsers.add_parser('conversation', help='管理對話上下文')
    conversation_parser.add_argument('-l', '--list', action='store_true', help='列出所有活躍對話')
    conversation_parser.add_argument('-s', '--show', type=str, help='顯示特定對話的歷史')
    conversation_parser.add_argument('-c', '--clear', type=str, help='清除特定對話')
    conversation_parser.add_argument('--clear-all', action='store_true', help='清除所有對話')
    
    # 視覺化命令
    viz_parser = subparsers.add_parser('viz', help='生成查詢結果的視覺化圖表')
    viz_parser.add_argument('sql', type=str, nargs='?', help='要視覺化的 SQL 查詢')
    viz_parser.add_argument('-f', '--file', type=str, help='包含 SQL 的檔案')
    viz_parser.add_argument('-t', '--type', choices=['auto', 'bar', 'line', 'pie', 'scatter'], default='auto', 
                      help='圖表類型 (預設: 自動檢測)')
    viz_parser.add_argument('-o', '--output', type=str, help='視覺化輸出目錄')
    
    # 收藏命令
    fav_parser = subparsers.add_parser('favorite', help='管理查詢收藏')
    fav_parser.add_argument('-l', '--list', action='store_true', help='列出所有收藏的查詢')
    fav_parser.add_argument('-a', '--add', type=str, help='添加查詢到收藏 (指定查詢ID)')
    fav_parser.add_argument('-r', '--remove', type=str, help='從收藏中移除查詢 (指定查詢ID)')
    fav_parser.add_argument('-e', '--execute', type=str, help='執行收藏的查詢 (指定查詢ID)')
    
    # 模板命令
    template_parser = subparsers.add_parser('template', help='管理查詢模板')
    template_parser.add_argument('-l', '--list', action='store_true', help='列出所有查詢模板')
    template_parser.add_argument('-c', '--create', type=str, help='從查詢創建模板 (指定查詢ID)')
    template_parser.add_argument('-n', '--name', type=str, help='模板名稱 (用於創建)')
    template_parser.add_argument('-d', '--description', type=str, help='模板描述 (用於創建)')
    template_parser.add_argument('-t', '--tags', type=str, help='模板標籤，以逗號分隔 (用於創建或過濾)')
    template_parser.add_argument('-s', '--show', type=str, help='顯示特定模板的詳細信息 (指定模板ID)')
    template_parser.add_argument('-u', '--use', type=str, help='使用模板執行查詢 (指定模板ID)')
    template_parser.add_argument('--delete', type=str, help='刪除模板 (指定模板ID)')
    
    # 解析參數
    args = parser.parse_args()
    
    # 如果沒有指定命令，默認為轉換
    if not args.command:
        if len(sys.argv) > 1:
            args.command = 'convert'
            args.query = sys.argv[1]
            args.file = None
            args.output = None
            args.execute = False
            args.format = 'text'
        else:
            parser.print_help()
            sys.exit(1)
    
    # 初始化服務
    service = TextToSQLService()
    
    # 確保服務使用全局 conversation_manager
    service.conversation_manager = conversation_manager
    
    # 執行對應的命令
    if args.command == 'convert':
        # 檢查是否有查詢
        if not args.query and not args.file:
            convert_parser.print_help()
            sys.exit(1)
        
        # 獲取查詢
        query = args.query
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as file:
                    query = file.read().strip()
            except Exception as e:
                logger.error(f"無法讀取檔案: {e}")
                sys.exit(1)
        
        try:
            # 轉換查詢
            # 如果指定了模型，設置默認模型
            from .utils import settings
            original_default = settings.default_model
            
            if hasattr(args, 'model') and args.model:
                # 檢查模型是否存在
                if args.model not in settings.models:
                    available_models = list(settings.models.keys())
                    console.print(f"[bold red]錯誤: 未知的模型 '{args.model}'[/bold red]")
                    console.print(f"可用模型: {', '.join(available_models)}")
                    sys.exit(1)
                
                settings.default_model = args.model
                
            # 判斷是否啟用相似查詢推薦
            find_similar = not getattr(args, 'no_similar', False)
            
            # 獲取會話ID
            session_id = getattr(args, 'session', None)
            if session_id:
                console.print(f"[cyan]使用會話ID: {session_id}[/cyan]")
            
            result = service.text_to_sql(
                query=query, 
                session_id=session_id,
                execute=args.execute,
                find_similar=find_similar
            )
            
            # 恢復默認模型
            if hasattr(args, 'model') and args.model:
                settings.default_model = original_default
            
            # 處理輸出
            if args.format == 'json':
                # JSON 格式輸出
                output = json.dumps({
                    "sql": result.sql,
                    "explanation": result.explanation,
                    "execution_result": result.execution_result,
                    "query_id": result.query_id
                }, ensure_ascii=False, indent=2)
            else:
                # 文本格式輸出
                output = f"-- 查詢 ID: {result.query_id}\n\n-- SQL 查詢:\n{result.sql}\n\n-- 解釋:\n{result.explanation}"
                
                # 如果有相似查詢，添加到輸出
                if result.similar_queries:
                    output += "\n\n-- 相似查詢:\n"
                    for i, similar in enumerate(result.similar_queries):
                        similarity_percent = int(similar.similarity * 100)
                        output += f"\n--- 相似查詢 {i+1} (相似度: {similarity_percent}%):\n"
                        output += f"原始查詢: {similar.query}\n"
                        output += f"SQL: {similar.sql}\n"
                
                # 如果執行了查詢，添加執行結果
                if result.execution_result:
                    exec_time = result.execution_result.get("execution_time", 0)
                    row_count = result.execution_result.get("row_count", 0)
                    
                    output += f"\n\n-- 執行結果 ({row_count} 行, {exec_time:.2f} ms):\n"
                    if result.execution_result.get("error"):
                        output += f"錯誤: {result.execution_result.get('error')}"
                    else:
                        output += format_execution_result(result.execution_result)
                        
                # 如果有參數，顯示它們        
                if result.parameters:
                    output += f"\n\n-- 參數:\n{json.dumps(result.parameters, ensure_ascii=False, indent=2)}"
            
            # 輸出結果
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as file:
                    file.write(output)
                console.print(f"[green]結果已寫入 {args.output}[/green]")
            else:
                # 美化輸出
                if args.format == 'json':
                    console.print(Syntax(output, "json", theme="monokai", line_numbers=True))
                else:
                    # 語法高亮 SQL
                    console.print("\n[bold cyan]SQL 查詢:[/bold cyan]")
                    console.print(Syntax(result.sql, "sql", theme="monokai"))
                    
                    console.print("\n[bold green]解釋:[/bold green]")
                    console.print(result.explanation)
                    
                    # 如果有相似查詢，顯示相似查詢
                    if result.similar_queries:
                        console.print("\n[bold magenta]相似查詢:[/bold magenta]")
                        
                        for i, similar in enumerate(result.similar_queries):
                            similarity_percent = int(similar.similarity * 100)
                            console.print(f"\n[bold]相似查詢 {i+1} (相似度: {similarity_percent}%):[/bold]")
                            console.print(f"[cyan]原始查詢:[/cyan] {similar.query}")
                            console.print("\n[cyan]SQL:[/cyan]")
                            console.print(Syntax(similar.sql, "sql", theme="monokai"))
                    
                    # 如果有參數，顯示它們
                    if result.parameters:
                        console.print("\n[bold blue]參數:[/bold blue]")
                        console.print(Syntax(json.dumps(result.parameters, ensure_ascii=False, indent=2), "json", theme="monokai"))
                    
                    # 如果執行了查詢，顯示執行結果
                    if result.execution_result:
                        exec_time = result.execution_result.get("execution_time", 0)
                        row_count = result.execution_result.get("row_count", 0)
                        
                        console.print(f"\n[bold yellow]執行結果 ({row_count} 行, {exec_time:.2f} ms):[/bold yellow]")
                        if result.execution_result.get("error"):
                            console.print(f"[bold red]錯誤:[/bold red] {result.execution_result.get('error')}")
                        else:
                            print(format_execution_result(result.execution_result))
                            
                        # 如果有視覺化圖表，顯示相關信息
                        if "visualization" in result.execution_result:
                            viz_data = result.execution_result["visualization"]
                            viz_type = viz_data.get("type", "")
                            img_path = viz_data.get("file_path", "")
                            
                            if viz_type and viz_type != "table" and img_path:
                                console.print(f"\n[bold magenta]視覺化圖表:[/bold magenta]")
                                console.print(f"[green]類型:[/green] {viz_type.upper()}")
                                console.print(f"[green]圖像文件:[/green] {img_path}")
                                console.print("[dim]提示: 使用 'viz' 命令可以自定義圖表類型[/dim]")
            
        except Exception as e:
            logger.error(f"轉換查詢時發生錯誤: {e}")
            console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
            sys.exit(1)
    
    elif args.command == 'history':
        # 顯示查詢歷史
        print_query_history(service, args.limit)
    
    elif args.command == 'execute':
        # 檢查是否有 SQL
        if not args.sql and not args.file:
            execute_parser.print_help()
            sys.exit(1)
        
        # 獲取 SQL
        sql = args.sql
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as file:
                    sql = file.read().strip()
            except Exception as e:
                logger.error(f"無法讀取檔案: {e}")
                sys.exit(1)
        
        try:
            # 執行查詢
            result = service.execute_sql(sql)
            
            # 輸出結果
            if result.error:
                console.print(f"[bold red]執行錯誤:[/bold red] {result.error}")
            else:
                console.print(f"[bold green]執行成功 ({result.row_count} 行, {result.execution_time:.2f} ms)[/bold green]")
                print(format_execution_result(result.to_dict()))
        
        except Exception as e:
            logger.error(f"執行查詢時發生錯誤: {e}")
            console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
            sys.exit(1)
            
    elif args.command == 'models':
        from .services import llm_service
        from .utils import settings
        
        # 列出所有可用模型
        if args.list:
            available_models = llm_service.get_available_models()
            
            # 創建表格
            table = Table(title="可用語言模型")
            table.add_column("名稱", style="cyan")
            table.add_column("提供商", style="green")
            table.add_column("默認", style="yellow")
            
            for model_name in available_models:
                model_config = settings.models.get(model_name)
                is_default = "✓" if model_name == settings.default_model else ""
                
                table.add_row(
                    model_name,
                    str(model_config.provider) if model_config else "未知",
                    is_default
                )
            
            console.print(table)
        
        # 顯示模型性能統計
        elif args.performance:
            from .services import llm_service
            performance = llm_service.get_model_performance()
            
            if not performance:
                console.print("[yellow]沒有模型性能記錄[/yellow]")
                sys.exit(0)
            
            # 創建表格
            table = Table(title="模型性能統計")
            table.add_column("模型", style="cyan")
            table.add_column("平均評分", style="green")
            table.add_column("請求次數", style="yellow")
            
            for model, stats in performance.items():
                table.add_row(
                    model,
                    f"{stats.get('average_score', 0):.2f}",
                    str(stats.get('total_requests', 0))
                )
            
            console.print(table)
        
        # 設置默認模型
        elif args.set_default:
            model_name = args.set_default
            
            if model_name not in settings.models:
                available_models = list(settings.models.keys())
                console.print(f"[bold red]錯誤: 未知的模型 '{model_name}'[/bold red]")
                console.print(f"可用模型: {', '.join(available_models)}")
                sys.exit(1)
            
            # 更新默認模型
            # 注意: 這只在當前運行中有效，不會永久更改配置文件
            settings.default_model = model_name
            console.print(f"[green]已將默認模型設置為: {model_name}[/green]")
            console.print("[yellow]注意: 此更改僅在當前程序運行期間有效[/yellow]")
        
        else:
            models_parser.print_help()
            
    elif args.command == 'viz':
        # 視覺化命令處理
        # 檢查是否有 SQL 查詢
        if not args.sql and not args.file:
            viz_parser.print_help()
            sys.exit(1)
        
        # 獲取 SQL 查詢
        sql = args.sql
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as file:
                    sql = file.read().strip()
            except Exception as e:
                logger.error(f"無法讀取檔案: {e}")
                sys.exit(1)
        
        try:
            # 準備可視化服務並設置輸出目錄
            if args.output:
                visualization_service.output_dir = args.output
                os.makedirs(args.output, exist_ok=True)
                console.print(f"[cyan]將視覺化輸出至: {args.output}[/cyan]")
            
            # 執行查詢
            service = TextToSQLService()
            result = service.execute_sql(sql)
            
            if result.error:
                console.print(f"[bold red]執行錯誤:[/bold red] {result.error}")
                sys.exit(1)
            
            if not result.columns or not result.rows:
                console.print("[yellow]查詢未返回可視覺化的結果[/yellow]")
                sys.exit(1)
            
            # 設置圖表類型
            chart_type = None if args.type == 'auto' else args.type
            
            # 創建視覺化
            img_path, viz_metadata = visualization_service.create_visualization(
                columns=result.columns,
                rows=result.rows,
                chart_type=chart_type,
                title=f"SQL查詢視覺化: {sql[:30] + '...' if len(sql) > 30 else sql}"
            )
            
            if "error" in viz_metadata:
                console.print(f"[bold red]視覺化創建錯誤:[/bold red] {viz_metadata['error']}")
                console.print("[yellow]顯示查詢結果但不含視覺化:[/yellow]")
                print(format_execution_result(result.to_dict()))
            else:
                # 輸出結果和視覺化信息
                console.print(f"[bold green]查詢執行成功 ({result.row_count} 行)[/bold green]")
                console.print(f"[bold cyan]已創建 {viz_metadata['type']} 圖表:[/bold cyan]")
                console.print(f"圖像文件: {viz_metadata['file_path']}")
                
                # 添加視覺化信息到結果並顯示
                result_dict = result.to_dict()
                result_dict["visualization"] = viz_metadata
                print(format_execution_result(result_dict))
                
                # 顯示圖表類型選擇提示
                if args.type == 'auto':
                    console.print(f"[yellow]提示: 系統自動選擇了 {viz_metadata['type']} 圖表類型。[/yellow]")
                    console.print("[yellow]您可以使用 -t 參數指定其他圖表類型: bar, line, pie, scatter[/yellow]")
        
        except Exception as e:
            logger.error(f"視覺化創建失敗: {e}")
            console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
            sys.exit(1)
            
    elif args.command == 'conversation':
        from .services import conversation_manager
        
        # 列出所有活躍對話
        if args.list:
            conversations = conversation_manager.get_conversation_ids()
            
            if not conversations:
                console.print("[yellow]沒有活躍對話[/yellow]")
                sys.exit(0)
            
            # 創建表格
            table = Table(title="活躍對話列表")
            table.add_column("會話ID", style="cyan")
            table.add_column("查詢數", style="green")
            table.add_column("最後更新", style="magenta")
            
            for conv_id in conversations:
                context = conversation_manager.get_or_create_conversation(conv_id)
                
                # 格式化日期
                last_updated = context.last_updated.strftime("%Y-%m-%d %H:%M:%S") if context.last_updated else "未知"
                
                table.add_row(
                    conv_id,
                    str(len(context.queries)),
                    last_updated
                )
            
            console.print(table)
        
        # 顯示特定對話的歷史
        elif args.show:
            # 使用已初始化的服務實例
            
            # 獲取對話歷史
            conversation_history = service.history_service.get_history_by_conversation(args.show, limit=20)
            
            if not conversation_history:
                console.print(f"[yellow]找不到會話ID為 {args.show} 的對話歷史[/yellow]")
                sys.exit(0)
            
            # 創建表格
            table = Table(title=f"對話歷史 (會話ID: {args.show})")
            table.add_column("查詢ID", style="dim")
            table.add_column("原始查詢", style="cyan")
            table.add_column("解析後查詢", style="green")
            table.add_column("生成的SQL", style="blue")
            table.add_column("時間", style="magenta")
            
            for entry in conversation_history:
                # 處理日期格式
                created_at = entry.created_at
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                # 格式化日期
                date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created_at, datetime) else str(created_at)
                
                # 添加行
                table.add_row(
                    str(entry.id),
                    entry.user_query[:30] + ("..." if len(entry.user_query) > 30 else ""),
                    (entry.resolved_query or "")[:30] + ("..." if entry.resolved_query and len(entry.resolved_query) > 30 else ""),
                    entry.generated_sql[:30] + ("..." if len(entry.generated_sql) > 30 else ""),
                    date_str
                )
            
            console.print(table)
        
        # 清除特定對話
        elif args.clear:
            conversation_manager.clear_conversation(args.clear)
            console.print(f"[green]已清除會話ID為 {args.clear} 的對話[/green]")
        
        # 清除所有對話
        elif args.clear_all:
            for conv_id in conversation_manager.get_conversation_ids():
                conversation_manager.clear_conversation(conv_id)
            console.print("[green]已清除所有對話[/green]")
        
        else:
            conversation_parser.print_help()
    
    elif args.command == 'vector':
        from .services import vector_store
        
        # 顯示統計信息
        if args.stats:
            count = vector_store.get_count()
            console.print(f"[green]向量存儲中有 {count} 個查詢[/green]")
            
        # 清除向量存儲
        elif args.clear:
            try:
                vector_store.clear()
                console.print("[green]向量存儲已清除[/green]")
            except Exception as e:
                logger.error(f"清除向量存儲時發生錯誤: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        # 搜索相似查詢
        elif args.query:
            try:
                results = vector_store.search_similar(args.query, k=args.limit)
                
                if not results:
                    console.print("[yellow]沒有找到相似查詢[/yellow]")
                    sys.exit(0)
                
                console.print(f"[green]找到 {len(results)} 個相似查詢:[/green]\n")
                
                for i, result in enumerate(results):
                    similarity_percent = int(result["similarity"] * 100)
                    
                    console.print(f"[bold cyan]相似查詢 {i+1} (相似度: {similarity_percent}%):[/bold cyan]")
                    console.print(f"原始查詢: {result['query']}")
                    console.print("SQL:")
                    console.print(Syntax(result["sql"], "sql", theme="monokai"))
                    console.print("")
                    
            except Exception as e:
                logger.error(f"搜索相似查詢時發生錯誤: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        else:
            vector_parser.print_help()
            
    elif args.command == 'favorite':
        from .services import TextToSQLService
        service = TextToSQLService()
        
        # 列出收藏的查詢
        if args.list:
            try:
                favorites = service.history_service.get_favorites()
                
                if not favorites:
                    console.print("[yellow]沒有收藏的查詢[/yellow]")
                    sys.exit(0)
                    
                # 創建表格
                table = Table(title="收藏的查詢")
                table.add_column("ID", style="dim")
                table.add_column("查詢", style="cyan")
                table.add_column("SQL", style="green")
                table.add_column("收藏時間", style="magenta")
                
                for fav in favorites:
                    # 處理日期格式
                    created_at = fav.created_at
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except ValueError:
                            pass
                    
                    # 格式化日期
                    date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created_at, datetime) else str(created_at)
                    
                    # 添加行
                    table.add_row(
                        str(fav.id),
                        fav.user_query[:40] + ("..." if len(fav.user_query) > 40 else ""),
                        fav.generated_sql[:40] + ("..." if len(fav.generated_sql) > 40 else ""),
                        date_str
                    )
                
                console.print(table)
                
            except Exception as e:
                logger.error(f"獲取收藏查詢失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        # 添加查詢到收藏
        elif args.add:
            try:
                success = service.history_service.toggle_favorite(args.add)
                
                if success:
                    console.print(f"[green]已將查詢 {args.add} 添加到收藏[/green]")
                else:
                    console.print(f"[bold red]添加收藏失敗: 找不到查詢ID {args.add}[/bold red]")
                    sys.exit(1)
                    
            except Exception as e:
                logger.error(f"添加收藏失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        # 從收藏中移除
        elif args.remove:
            try:
                success = service.history_service.toggle_favorite(args.remove)
                
                if success:
                    console.print(f"[green]已從收藏中移除查詢 {args.remove}[/green]")
                else:
                    console.print(f"[bold red]移除收藏失敗: 找不到查詢ID {args.remove}[/bold red]")
                    sys.exit(1)
                    
            except Exception as e:
                logger.error(f"移除收藏失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        # 執行收藏的查詢
        elif args.execute:
            try:
                # 獲取收藏的查詢
                query = service.history_service.get_query_by_id(args.execute)
                
                if not query:
                    console.print(f"[bold red]執行收藏失敗: 找不到查詢ID {args.execute}[/bold red]")
                    sys.exit(1)
                    
                if not query.is_favorite:
                    console.print(f"[bold yellow]警告: 查詢 {args.execute} 不是收藏狀態[/bold yellow]")
                
                # 執行 SQL
                result = service.execute_sql(query.generated_sql, parameters=query.parameters)
                
                # 輸出結果
                if result.error:
                    console.print(f"[bold red]執行錯誤:[/bold red] {result.error}")
                else:
                    console.print(f"[bold green]執行成功 ({result.row_count} 行, {result.execution_time:.2f} ms)[/bold green]")
                    print(format_execution_result(result.to_dict()))
                    
            except Exception as e:
                logger.error(f"執行收藏查詢失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        else:
            fav_parser.print_help()
            
    elif args.command == 'template':
        from .services import TextToSQLService
        service = TextToSQLService()
        
        # 列出所有模板
        if args.list:
            try:
                # 處理標籤過濾
                tag = None
                if args.tags:
                    tag = args.tags.split(',')[0].strip()  # 只使用第一個標籤進行過濾
                
                templates = service.history_service.get_templates(tag=tag)
                
                if not templates:
                    if tag:
                        console.print(f"[yellow]沒有找到標籤為 '{tag}' 的模板[/yellow]")
                    else:
                        console.print("[yellow]沒有查詢模板[/yellow]")
                    sys.exit(0)
                
                # 創建表格
                title_text = "查詢模板"
                if tag:
                    title_text += f" (標籤: {tag})"
                    
                table = Table(title=title_text)
                table.add_column("ID", style="dim")
                table.add_column("名稱", style="cyan")
                table.add_column("描述", style="green")
                table.add_column("標籤", style="yellow")
                table.add_column("使用次數", style="magenta")
                
                for tmpl in templates:
                    # 格式化標籤
                    tags_str = ", ".join(tmpl.tags) if tmpl.tags else ""
                    
                    # 添加行
                    table.add_row(
                        str(tmpl.id),
                        tmpl.name,
                        (tmpl.description or "")[:40] + ("..." if tmpl.description and len(tmpl.description) > 40 else ""),
                        tags_str,
                        str(tmpl.usage_count)
                    )
                
                console.print(table)
                
            except Exception as e:
                logger.error(f"獲取模板失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        # 創建模板
        elif args.create:
            try:
                # 檢查參數
                if not args.name:
                    console.print("[bold red]錯誤: 創建模板需要提供名稱 (-n/--name)[/bold red]")
                    sys.exit(1)
                
                # 解析標籤
                tags = []
                if args.tags:
                    tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
                
                # 創建模板
                template = service.history_service.save_as_template(
                    query_id=args.create,
                    name=args.name,
                    description=args.description,
                    tags=tags
                )
                
                if template:
                    console.print(f"[green]成功創建模板: {template.name}[/green]")
                    console.print(f"ID: {template.id}")
                    
                    if template.description:
                        console.print(f"描述: {template.description}")
                        
                    if template.tags:
                        console.print(f"標籤: {', '.join(template.tags)}")
                else:
                    console.print(f"[bold red]創建模板失敗: 找不到查詢ID {args.create}[/bold red]")
                    sys.exit(1)
                    
            except Exception as e:
                logger.error(f"創建模板失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        # 顯示模板詳情
        elif args.show:
            try:
                template = service.history_service.get_template_by_id(args.show)
                
                if not template:
                    console.print(f"[bold red]找不到模板ID {args.show}[/bold red]")
                    sys.exit(1)
                
                # 顯示模板詳情
                console.print(f"[bold cyan]模板: {template.name}[/bold cyan]")
                console.print(f"[bold]ID:[/bold] {template.id}")
                
                if template.description:
                    console.print(f"[bold]描述:[/bold] {template.description}")
                    
                if template.tags:
                    console.print(f"[bold]標籤:[/bold] {', '.join(template.tags)}")
                    
                console.print(f"[bold]使用次數:[/bold] {template.usage_count}")
                
                console.print("\n[bold green]原始查詢:[/bold green]")
                console.print(template.user_query)
                
                console.print("\n[bold green]SQL 查詢:[/bold green]")
                console.print(Syntax(template.generated_sql, "sql", theme="monokai"))
                
                if template.explanation:
                    console.print("\n[bold green]說明:[/bold green]")
                    console.print(template.explanation)
                    
                if template.parameters:
                    console.print("\n[bold green]參數:[/bold green]")
                    console.print(Syntax(json.dumps(template.parameters, ensure_ascii=False, indent=2), "json", theme="monokai"))
                    
            except Exception as e:
                logger.error(f"獲取模板詳情失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        # 使用模板執行查詢
        elif args.use:
            try:
                template = service.history_service.get_template_by_id(args.use)
                
                if not template:
                    console.print(f"[bold red]找不到模板ID {args.use}[/bold red]")
                    sys.exit(1)
                
                # 增加使用次數
                service.history_service.increment_template_usage(args.use)
                
                # 執行 SQL
                console.print(f"[cyan]正在執行模板 '{template.name}' 的查詢...[/cyan]")
                result = service.execute_sql(template.generated_sql, parameters=template.parameters)
                
                # 輸出結果
                if result.error:
                    console.print(f"[bold red]執行錯誤:[/bold red] {result.error}")
                else:
                    console.print(f"[bold green]執行成功 ({result.row_count} 行, {result.execution_time:.2f} ms)[/bold green]")
                    print(format_execution_result(result.to_dict()))
                    
            except Exception as e:
                logger.error(f"使用模板失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
        
        # 刪除模板
        elif args.delete:
            try:
                success = service.history_service.delete_template(args.delete)
                
                if success:
                    console.print(f"[green]已刪除模板 {args.delete}[/green]")
                else:
                    console.print(f"[bold red]刪除模板失敗: 找不到模板ID {args.delete}[/bold red]")
                    sys.exit(1)
                    
            except Exception as e:
                logger.error(f"刪除模板失敗: {e}")
                console.print(f"[bold red]錯誤:[/bold red] {str(e)}")
                sys.exit(1)
                
        else:
            template_parser.print_help()


if __name__ == "__main__":
    main()