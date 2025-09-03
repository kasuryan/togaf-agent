"""
System startup script for TOGAF Agent - starts both API and UI servers.
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

# Global process references
api_process = None
ui_process = None


def start_api_server():
    """Start the FastAPI backend server."""
    global api_process
    
    try:
        console.print("🚀 Starting FastAPI backend server...")
        
        # Start the API server
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "togaf_agent.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        console.print("   ✅ API server starting on http://localhost:8000")
        return True
        
    except Exception as e:
        console.print(f"   ❌ Failed to start API server: {e}")
        return False


def start_ui_server():
    """Start the Streamlit UI server."""
    global ui_process
    
    try:
        console.print("🎨 Starting Streamlit UI server...")
        
        # Start the UI server
        ui_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run",
            "togaf_agent/ui/main.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        console.print("   ✅ UI server starting on http://localhost:8501")
        return True
        
    except Exception as e:
        console.print(f"   ❌ Failed to start UI server: {e}")
        return False


def wait_for_server(url: str, max_attempts: int = 30) -> bool:
    """Wait for server to be ready."""
    import requests
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
    
    return False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    console.print("\n⚠️  Shutting down TOGAF Agent system...")
    
    if api_process:
        console.print("   🛑 Stopping API server...")
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_process.kill()
    
    if ui_process:
        console.print("   🛑 Stopping UI server...")
        ui_process.terminate()
        try:
            ui_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ui_process.kill()
    
    console.print("   ✅ System shutdown complete")
    sys.exit(0)


def main():
    """Main startup function."""
    console.print(Panel.fit("🎯 TOGAF Agent - System Startup", style="bold blue"))
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check environment
    console.print("\n📋 [bold]Environment Check[/bold]")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        console.print("   ⚠️  .env file not found")
        console.print("   💡 Copy .env.example to .env and add your OpenAI API key")
        
        env_example = Path(".env.example")
        if env_example.exists():
            console.print("   📝 Creating .env from .env.example...")
            import shutil
            shutil.copy(env_example, env_file)
            console.print("   ✅ .env file created - please add your OpenAI API key")
        else:
            console.print("   ❌ .env.example not found")
            return False
    else:
        console.print("   ✅ .env file found")
    
    # Check required directories
    required_dirs = ["user_data/user_profiles", "user_data/analytics", "user_data/conversation_sessions"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            console.print(f"   ✅ Created directory: {dir_name}")
    
    # Start servers
    console.print("\n🚀 [bold]Starting Services[/bold]")
    
    # Start API server
    if not start_api_server():
        console.print("❌ Failed to start API server")
        return False
    
    # Wait a moment for API to initialize
    time.sleep(3)
    
    # Start UI server
    if not start_ui_server():
        console.print("❌ Failed to start UI server")
        return False
    
    # Wait for servers to be ready
    console.print("\n⏳ [bold]Waiting for servers to be ready...[/bold]")
    
    # Check API server
    if wait_for_server("http://localhost:8000/health"):
        console.print("   ✅ API server ready")
    else:
        console.print("   ⚠️  API server may not be ready (continuing anyway)")
    
    # Give UI server time to start
    console.print("   ⏳ UI server initializing...")
    time.sleep(5)
    console.print("   ✅ UI server should be ready")
    
    # Display system information
    console.print("\n🎉 [bold green]TOGAF Agent System Ready![/bold green]")
    console.print(Panel.fit("""
🌐 Access Points:
   • Web UI: http://localhost:8501
   • API Docs: http://localhost:8000/docs
   • Health Check: http://localhost:8000/health

🎯 Quick Start:
   1. Open http://localhost:8501 in your browser
   2. Create a new account or login
   3. Complete the onboarding process
   4. Start your TOGAF learning journey!

⚠️  Press Ctrl+C to shutdown the system
    """, style="bold cyan"))
    
    # Keep the main thread alive and monitor processes
    try:
        while True:
            # Check if processes are still running
            if api_process and api_process.poll() is not None:
                console.print("   ⚠️  API server stopped unexpectedly")
                break
            
            if ui_process and ui_process.poll() is not None:
                console.print("   ⚠️  UI server stopped unexpectedly")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)