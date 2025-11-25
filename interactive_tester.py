#!/usr/bin/env python3
"""
Pranthora SDK Interactive Explorer
A terminal-based UI (TUI) to explore and test the Pranthora SDK interactively.
"""

import sys
import time
import json
import os
from typing import Any, Dict, List, Optional
from pranthora import Pranthora
from pranthora.exceptions import *

# Try to import rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    print("Rich library not found. Please install it: pip install rich")
    sys.exit(1)

class APIInspector:
    """Captures API interactions for display"""
    def __init__(self):
        self.last_request: Dict[str, Any] = {}
        self.last_response: Any = None
        self.last_status_code: int = 0
        self.last_url: str = ""
        self.last_method: str = ""
        self.history: List[Dict[str, Any]] = []

    def capture(self, method, url, params=None, data=None, response=None, status_code=200):
        interaction = {
            "timestamp": time.strftime("%H:%M:%S"),
            "method": method,
            "url": url,
            "params": params,
            "data": data,
            "response": response,
            "status_code": status_code
        }
        self.last_request = {"params": params, "data": data}
        self.last_response = response
        self.last_status_code = status_code
        self.last_url = url
        self.last_method = method
        self.history.append(interaction)

class InteractiveApp:
    def __init__(self, api_key: str, base_url: str):
        self.console = Console()
        self.api_key = api_key
        self.base_url = base_url
        self.client = Pranthora(api_key=api_key, base_url=base_url)
        self.inspector = APIInspector()
        self.active_agent_id = None
        
        # Monkey patch the requestor to capture details
        self._original_request = self.client.requestor.request
        self.client.requestor.request = self._intercept_request

    def _intercept_request(self, method, url, params=None, data=None):
        try:
            response = self._original_request(method, url, params=params, data=data)
            # We don't have easy access to status code in the raw return of _original_request 
            # unless we change how it returns. But assuming success if no exception.
            self.inspector.capture(method, url, params, data, response, 200)
            return response
        except APIError as e:
            self.inspector.capture(method, url, params, data, e.body, e.status_code)
            raise e
        except Exception as e:
            self.inspector.capture(method, url, params, data, str(e), 500)
            raise e

    def clear_screen(self):
        self.console.clear()

    def print_header(self):
        self.clear_screen()
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(Panel(
            Text("🚀 Pranthora SDK Explorer", justify="center", style="bold magenta"),
            style="magenta",
            subtitle=f"Connected to {self.base_url}"
        ))
        self.console.print(grid)

    def show_main_menu(self):
        while True:
            self.print_header()
            
            # Status Panel
            status_text = Text()
            status_text.append("Active Agent ID: ", style="bold cyan")
            status_text.append(self.active_agent_id or "None", style="yellow")
            if self.inspector.last_method:
                status_text.append("\nLast API Call: ", style="bold cyan")
                status_text.append(f"{self.inspector.last_method} {self.inspector.last_url}", style="green")
            
            self.console.print(Panel(status_text, title="Session Status", border_style="blue"))

            # Menu Options
            menu = Table(show_header=False, box=box.SIMPLE)
            menu.add_column("Key", style="cyan bold", width=4)
            menu.add_column("Action")
            
            menu.add_row("1", "List All Agents")
            menu.add_row("2", "Create New Agent")
            menu.add_row("3", "Get Agent Details")
            menu.add_row("4", "Update Active Agent")
            menu.add_row("5", "Delete Active Agent")
            menu.add_row("6", "Inspect Last API Call (Debug View)")
            menu.add_row("q", "Quit")
            
            self.console.print(Panel(menu, title="Main Menu", border_style="green"))
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "q"], default="1")
            
            if choice == "q":
                self.console.print("[bold]Goodbye! 👋[/bold]")
                sys.exit(0)
            elif choice == "1":
                self.view_list_agents()
            elif choice == "2":
                self.view_create_agent()
            elif choice == "3":
                self.view_get_agent()
            elif choice == "4":
                self.view_update_agent()
            elif choice == "5":
                self.view_delete_agent()
            elif choice == "6":
                self.view_inspection_details()

    def wait_for_enter(self):
        self.console.print("\n[dim]Press Enter to return to menu...[/dim]")
        input()

    def view_list_agents(self):
        self.print_header()
        self.console.print("[bold cyan]Fetching agents list...[/bold cyan]")
        
        try:
            agents = self.client.agents.list()
            
            if not agents:
                self.console.print("[yellow]No agents found.[/yellow]")
            else:
                table = Table(title="Available Agents", show_header=True, header_style="bold magenta", expand=True)
                table.add_column("Index", style="dim", width=4)
                table.add_column("Name", style="cyan")
                table.add_column("ID", style="green")
                table.add_column("Status", justify="center")
                
                for idx, agent in enumerate(agents, 1):
                    agent_data = agent.get('agent', {})
                    name = agent_data.get('name', 'N/A')
                    a_id = agent_data.get('id', 'N/A')
                    is_active = agent_data.get('is_active', False)
                    status = "[green]Active[/green]" if is_active else "[red]Inactive[/red]"
                    table.add_row(str(idx), name, a_id, status)
                
                self.console.print(table)
                
                # Option to select agent
                sel = Prompt.ask("\nEnter Index to select Agent (or Enter to skip)", default="")
                if sel.isdigit() and 1 <= int(sel) <= len(agents):
                    selected = agents[int(sel)-1]
                    self.active_agent_id = selected['agent']['id']
                    self.console.print(f"[green]Selected Agent: {self.active_agent_id}[/green]")
                    time.sleep(1)
                    
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}")
            
        self.wait_for_enter()

    def view_create_agent(self):
        self.print_header()
        self.console.print("[bold cyan]Creating new agent...[/bold cyan]")
        
        name = f"Explorer Agent {int(time.time())}"
        
        try:
            with self.console.status("Sending create request...", spinner="dots"):
                response = self.client.agents.create(
                    name=name,
                    description="Created via Interactive Explorer",
                    model="gpt-4.1-mini",
                    voice="thalia",
                    transcriber="deepgram_nova_3"
                )
            
            # Extract ID
            if 'agent' in response:
                new_id = response['agent']['id']
            else:
                new_id = response.get('id')
                
            self.active_agent_id = new_id
            self.console.print(f"[bold green]✅ Agent Created Successfully![/bold green]")
            self.console.print(f"ID: [cyan]{new_id}[/cyan]")
            
            # Show details immediately
            self.view_inspection_details(wait=False)
            
        except Exception as e:
            self.console.print(f"[bold red]Creation Failed:[/bold red] {e}")
            
        self.wait_for_enter()

    def view_get_agent(self):
        if not self.active_agent_id:
            self.console.print("[yellow]No active agent selected. Please list and select an agent first.[/yellow]")
            time.sleep(2)
            return

        self.print_header()
        self.console.print(f"[bold cyan]Fetching details for {self.active_agent_id}...[/bold cyan]")
        
        try:
            agent = self.client.agents.get(self.active_agent_id)
            
            # Display nicely
            agent_info = agent.get('agent', {})
            configs = agent.get('configurations', {})
            
            grid = Table.grid(expand=True, padding=1)
            grid.add_column(ratio=1)
            grid.add_column(ratio=1)
            
            # Left side: Basic Info
            info_text = Text()
            info_text.append(f"Name: {agent_info.get('name')}\n", style="bold")
            info_text.append(f"ID: {agent_info.get('id')}\n", style="dim")
            info_text.append(f"Status: {'Active' if agent_info.get('is_active') else 'Inactive'}\n", style="green" if agent_info.get('is_active') else "red")
            info_text.append(f"Created: {agent_info.get('created_at')}\n")
            
            # Right side: Configs
            config_text = Text()
            if 'model' in configs:
                config_text.append("🧠 Model: ", style="bold magenta")
                config_text.append(f"{configs['model'].get('model_provider_id')}\n")
            if 'tts' in configs:
                config_text.append("🗣️  Voice: ", style="bold magenta")
                config_text.append(f"{configs['tts'].get('voice_name')}\n")
            if 'transcriber' in configs:
                config_text.append("👂 STT: ", style="bold magenta")
                config_text.append(f"{configs['transcriber'].get('model_name')}\n")

            grid.add_row(
                Panel(info_text, title="Agent Info", border_style="cyan"),
                Panel(config_text, title="Configuration", border_style="magenta")
            )
            self.console.print(grid)
            
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}")
            
        self.wait_for_enter()

    def view_update_agent(self):
        if not self.active_agent_id:
            self.console.print("[yellow]No active agent selected.[/yellow]")
            time.sleep(2)
            return
            
        new_name = Prompt.ask("Enter new name", default=f"Updated Agent {int(time.time())}")
        
        try:
            self.client.agents.update(self.active_agent_id, name=new_name)
            self.console.print("[bold green]✅ Update Successful![/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]Update Failed:[/bold red] {e}")
            
        self.wait_for_enter()

    def view_delete_agent(self):
        if not self.active_agent_id:
            self.console.print("[yellow]No active agent selected.[/yellow]")
            time.sleep(2)
            return
            
        if not Confirm.ask(f"Are you sure you want to delete {self.active_agent_id}?"):
            return

        try:
            self.client.agents.delete(self.active_agent_id)
            self.console.print("[bold green]✅ Agent Deleted![/bold green]")
            self.active_agent_id = None
        except Exception as e:
            self.console.print(f"[bold red]Delete Failed:[/bold red] {e}")
            
        self.wait_for_enter()

    def view_inspection_details(self, wait=True):
        """Show full details of the last API interaction"""
        self.print_header()
        
        if not self.inspector.last_url:
            self.console.print("[yellow]No API calls made yet.[/yellow]")
            if wait: self.wait_for_enter()
            return

        # Request Details
        req_table = Table(title="Request Details", show_header=False, box=box.ROUNDED)
        req_table.add_column("Key", style="bold cyan")
        req_table.add_column("Value")
        
        req_table.add_row("Method", self.inspector.last_method)
        req_table.add_row("URL", self.inspector.last_url)
        req_table.add_row("Status", str(self.inspector.last_status_code))
        
        # Payloads
        req_json = json.dumps(self.inspector.last_request, indent=2)
        res_json = json.dumps(self.inspector.last_response, indent=2)
        
        self.console.print(req_table)
        
        grid = Table.grid(expand=True, padding=1)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        
        grid.add_row(
            Panel(Syntax(req_json, "json", theme="monokai"), title="Request Payload", border_style="blue"),
            Panel(Syntax(res_json, "json", theme="monokai"), title="Response Body", border_style="green")
        )
        
        self.console.print(grid)
        
        if wait:
            self.wait_for_enter()

def main():
    API_KEY = "1317d2fdec128bfd086fbcc2f10de57d"
    BASE_URL = "http://localhost:5050"
    
    app = InteractiveApp(API_KEY, BASE_URL)
    try:
        app.show_main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
