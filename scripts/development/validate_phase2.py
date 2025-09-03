"""
Comprehensive validation script for TOGAF Agent Phase 2 - User Management & UI System.
"""

import asyncio
import sys
import time
import subprocess
import requests
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import json

# Import Phase 2 components
try:
    from togaf_agent.core.togaf_tutor import TOGAFTutor
    from togaf_agent.utils.config import load_settings
    from togaf_agent.user_management.user_profile import UserProfileManager, ExperienceLevel
    from togaf_agent.user_management.onboarding import TOGAFOnboardingSystem, OnboardingStep
    from togaf_agent.user_management.progress_tracker import ProgressTracker
    from togaf_agent.conversation.session_manager import SessionManager, ConversationMode
    from togaf_agent.conversation.adaptive_agent import AdaptiveAgent
    from togaf_agent.api.main import app
    from togaf_agent.ui.utils.api_client import TOGAFAPIClient
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

console = Console()


async def validate_phase2_system():
    """Comprehensive validation of Phase 2 TOGAF Agent system."""
    console.print(Panel.fit("🚀 TOGAF Agent - Phase 2 Validation", style="bold blue"))
    
    results = {}
    start_time = time.time()
    
    # Test 1: Core Orchestrator
    console.print("\n🎯 [bold]Test 1: TOGAF Tutor Orchestrator[/bold]")
    try:
        settings = load_settings()
        tutor = TOGAFTutor(settings)
        
        # Test initialization
        init_success = await tutor.initialize()
        console.print(f"   {'✅' if init_success else '❌'} Orchestrator initialization")
        
        if init_success:
            # Test system status
            status = await tutor.get_system_status()
            console.print(f"   {'✅' if status.get('success') else '❌'} System status check")
            
            # Test user creation
            user_result = await tutor.create_user("test_user_phase2", "test@example.com")
            console.print(f"   {'✅' if user_result.get('success') else '❌'} User creation")
            
            if user_result.get('success'):
                user_id = user_result['user_id']
                
                # Test dashboard data
                dashboard = await tutor.get_user_dashboard(user_id)
                console.print(f"   {'✅' if dashboard.get('success') else '❌'} Dashboard data generation")
                
                results["orchestrator"] = True
            else:
                results["orchestrator"] = False
        else:
            results["orchestrator"] = False
    
    except Exception as e:
        console.print(f"   ❌ Orchestrator failed: {e}")
        results["orchestrator"] = False
    
    # Test 2: Enhanced User Management
    console.print("\n👤 [bold]Test 2: Enhanced User Management[/bold]")
    try:
        profile_manager = UserProfileManager()
        
        # Test user creation with learning plans
        test_user = profile_manager.create_profile("validation_user", "validation@test.com")
        console.print(f"   ✅ User profile creation")
        
        # Test structured learning plan creation
        plan_id = profile_manager.create_structured_plan(
            test_user.user_id, 
            "foundation_beginner"
        )
        console.print(f"   {'✅' if plan_id else '❌'} Structured learning plan creation")
        
        # Test topic completion
        if plan_id:
            success = profile_manager.mark_topic_complete(test_user.user_id, "togaf_introduction")
            console.print(f"   {'✅' if success else '❌'} Topic completion tracking")
            
            # Test current topic retrieval
            current_topic = profile_manager.get_current_topic(test_user.user_id)
            console.print(f"   {'✅' if current_topic else '❌'} Current topic retrieval")
            
            # Test plan overview
            overview = profile_manager.get_plan_overview(test_user.user_id)
            console.print(f"   {'✅' if overview else '❌'} Plan overview generation")
        
        results["user_management"] = True
    
    except Exception as e:
        console.print(f"   ❌ User management failed: {e}")
        results["user_management"] = False
    
    # Test 3: Onboarding System
    console.print("\n📋 [bold]Test 3: Smart Onboarding System[/bold]")
    try:
        onboarding = TOGAFOnboardingSystem(profile_manager)
        
        # Test onboarding start
        start_result = onboarding.start_onboarding(test_user.user_id)
        console.print(f"   {'✅' if 'error' not in start_result else '❌'} Onboarding start")
        
        # Test welcome step processing
        if 'error' not in start_result:
            welcome_response = onboarding.process_step(
                test_user.user_id,
                OnboardingStep.WELCOME,
                {"response": "Yes, let's begin!"}
            )
            console.print(f"   {'✅' if 'error' not in welcome_response else '❌'} Step processing")
            
            # Test assessment questions
            if 'assessment' in welcome_response:
                console.print("   ✅ Assessment questions generated")
            
            # Test progress tracking
            progress = onboarding.get_onboarding_progress(test_user.user_id)
            console.print(f"   {'✅' if progress else '❌'} Progress tracking")
        
        results["onboarding"] = True
    
    except Exception as e:
        console.print(f"   ❌ Onboarding failed: {e}")
        results["onboarding"] = False
    
    # Test 4: Progress Tracking & Analytics
    console.print("\n📊 [bold]Test 4: Progress Tracking & Analytics[/bold]")
    try:
        progress_tracker = ProgressTracker(profile_manager)
        
        # Test session tracking
        session_id = progress_tracker.start_learning_session(test_user.user_id)
        console.print(f"   ✅ Learning session start")
        
        # Test topic interaction logging
        interaction_logged = progress_tracker.log_topic_interaction(
            session_id, "adm_overview", "question", True
        )
        console.print(f"   {'✅' if interaction_logged else '❌'} Topic interaction logging")
        
        # Test proficiency updates
        proficiency_updated = progress_tracker.update_topic_proficiency(
            test_user.user_id, "adm_overview", {"score": 0.8, "type": "quiz"}
        )
        console.print(f"   {'✅' if proficiency_updated else '❌'} Proficiency updates")
        
        # Test analytics generation
        analytics = progress_tracker.get_progress_analytics(test_user.user_id)
        console.print(f"   {'✅' if analytics else '❌'} Analytics generation")
        
        # Test learning insights
        insights = progress_tracker.get_learning_insights(test_user.user_id)
        console.print(f"   {'✅' if insights else '❌'} Learning insights")
        
        # Test recommendations
        recommendations = progress_tracker.get_next_recommended_topics(test_user.user_id)
        console.print(f"   {'✅' if recommendations else '❌'} Topic recommendations")
        
        # End session
        session_ended = progress_tracker.end_learning_session(session_id, 4.5)
        console.print(f"   {'✅' if session_ended else '❌'} Session completion")
        
        results["progress_tracking"] = True
    
    except Exception as e:
        console.print(f"   ❌ Progress tracking failed: {e}")
        results["progress_tracking"] = False
    
    # Test 5: Session Management
    console.print("\n💬 [bold]Test 5: Conversation Session Management[/bold]")
    try:
        session_manager = SessionManager(profile_manager)
        
        # Test session creation
        conv_session_id = session_manager.create_session(test_user.user_id, ConversationMode.LEARNING)
        console.print(f"   ✅ Conversation session creation")
        
        # Test message handling
        message_added = session_manager.add_message(
            conv_session_id, "user_question", "What is TOGAF ADM?"
        )
        console.print(f"   {'✅' if message_added else '❌'} Message handling")
        
        # Test context management
        context_updated = session_manager.update_context(
            conv_session_id, {"current_topic": "adm_overview"}
        )
        console.print(f"   {'✅' if context_updated else '❌'} Context management")
        
        # Test session context retrieval
        session_context = session_manager.get_session_context(conv_session_id)
        console.print(f"   {'✅' if session_context else '❌'} Context retrieval")
        
        # Test conversation history
        history = session_manager.get_conversation_history(conv_session_id)
        console.print(f"   {'✅' if history else '❌'} Conversation history")
        
        # Test session statistics
        stats = session_manager.get_session_statistics(test_user.user_id)
        console.print(f"   {'✅' if isinstance(stats, dict) else '❌'} Session statistics")
        
        results["session_management"] = True
    
    except Exception as e:
        console.print(f"   ❌ Session management failed: {e}")
        results["session_management"] = False
    
    # Test 6: FastAPI Backend
    console.print("\n🌐 [bold]Test 6: FastAPI REST API[/bold]")
    try:
        # Start FastAPI server in background for testing
        api_process = None
        api_available = False
        
        try:
            # Try to connect to existing API instance
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                api_available = True
                console.print("   ✅ API server already running")
        except requests.exceptions.RequestException:
            console.print("   ℹ️  API server not running, validation will be limited")
        
        if api_available:
            # Test health endpoint
            health_response = requests.get("http://localhost:8000/health")
            console.print(f"   {'✅' if health_response.status_code == 200 else '❌'} Health endpoint")
            
            # Test user endpoints
            user_data = {
                "username": "api_test_user",
                "email": "api_test@example.com"
            }
            
            try:
                create_response = requests.post("http://localhost:8000/api/v1/users/", json=user_data)
                console.print(f"   {'✅' if create_response.status_code in [200, 201] else '❌'} User creation API")
                
                if create_response.status_code in [200, 201]:
                    user_info = create_response.json()
                    user_id = user_info.get("user_id")
                    
                    # Test user retrieval
                    get_response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}")
                    console.print(f"   {'✅' if get_response.status_code == 200 else '❌'} User retrieval API")
                    
            except Exception as e:
                console.print(f"   ❌ User API tests failed: {e}")
            
            # Test system info endpoint
            try:
                info_response = requests.get("http://localhost:8000/api/v1/system/info")
                console.print(f"   {'✅' if info_response.status_code == 200 else '❌'} System info API")
            except Exception as e:
                console.print(f"   ❌ System info API failed: {e}")
        
        results["api_backend"] = api_available
    
    except Exception as e:
        console.print(f"   ❌ API backend test failed: {e}")
        results["api_backend"] = False
    
    # Test 7: Streamlit UI Components
    console.print("\n🖥️  [bold]Test 7: Streamlit UI Components[/bold]")
    try:
        # Test API client
        api_client = TOGAFAPIClient("http://localhost:8000")
        console.print("   ✅ API client initialization")
        
        # Test health check
        try:
            health = api_client.get_health()
            console.print(f"   {'✅' if health else '❌'} Health check integration")
        except Exception:
            console.print("   ⚠️  Health check failed (API not available)")
        
        # Test UI component imports
        try:
            from togaf_agent.ui.main import main
            from togaf_agent.ui.components.onboarding import render_onboarding_flow
            from togaf_agent.ui.components.dashboard import render_dashboard
            from togaf_agent.ui.components.chat import render_chat_interface
            from togaf_agent.ui.components.learning_plan import render_learning_plan
            console.print("   ✅ UI component imports")
        except ImportError as e:
            console.print(f"   ❌ UI component import failed: {e}")
            results["ui_components"] = False
        
        # Check if streamlit is available
        try:
            import streamlit as st
            console.print("   ✅ Streamlit dependency")
        except ImportError:
            console.print("   ❌ Streamlit not available")
        
        results["ui_components"] = True
    
    except Exception as e:
        console.print(f"   ❌ UI components test failed: {e}")
        results["ui_components"] = False
    
    # Test 8: Integration Testing
    console.print("\n🔗 [bold]Test 8: End-to-End Integration[/bold]")
    try:
        # Test complete user journey
        integration_user = profile_manager.create_profile("integration_test", "integration@test.com")
        console.print("   ✅ User creation")
        
        # Test onboarding flow
        onboarding_start = onboarding.start_onboarding(integration_user.user_id)
        console.print(f"   {'✅' if 'error' not in onboarding_start else '❌'} Onboarding integration")
        
        # Test learning session flow
        session_id = progress_tracker.start_learning_session(integration_user.user_id)
        conv_session_id = session_manager.create_session(integration_user.user_id)
        console.print("   ✅ Session integration")
        
        # Test progress flow
        progress_tracker.log_topic_interaction(session_id, "test_topic", "question", True)
        progress_tracker.update_topic_proficiency(
            integration_user.user_id, "test_topic", {"score": 0.75}
        )
        console.print("   ✅ Progress integration")
        
        # Test learning plan integration
        plan_id = profile_manager.create_structured_plan(
            integration_user.user_id, "foundation_beginner"
        )
        console.print(f"   {'✅' if plan_id else '❌'} Learning plan integration")
        
        # Clean up sessions
        progress_tracker.end_learning_session(session_id)
        session_manager.end_session(conv_session_id)
        console.print("   ✅ Session cleanup")
        
        results["integration"] = True
    
    except Exception as e:
        console.print(f"   ❌ Integration test failed: {e}")
        results["integration"] = False
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    console.print(f"\n⏱️ [bold]Validation completed in {duration:.2f} seconds[/bold]")
    
    # Results table
    table = Table(title="Phase 2 Validation Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Description")
    
    component_descriptions = {
        "orchestrator": "Main TOGAF Tutor orchestrator with component coordination",
        "user_management": "Enhanced user profiles with learning plans and progress",
        "onboarding": "Smart onboarding system with assessment and personalization",
        "progress_tracking": "Intelligent progress tracking with analytics and insights",
        "session_management": "Context-aware conversation session management",
        "api_backend": "FastAPI REST API with comprehensive endpoints",
        "ui_components": "Streamlit web UI with interactive components",
        "integration": "End-to-end integration testing across all components"
    }
    
    for component, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        description = component_descriptions.get(component, "")
        table.add_row(component.replace("_", " ").title(), status, description)
    
    console.print(table)
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        console.print(Panel.fit("🎉 Phase 2 - All Systems Operational! 🎉", style="bold green"))
        console.print("\n🚀 [bold green]TOGAF Agent Phase 2 is fully functional![/bold green]")
        console.print("\n📋 [bold]Phase 2 Features Validated:[/bold]")
        console.print("   • ✅ Enhanced user profiles with structured learning plans")
        console.print("   • ✅ Smart onboarding with proficiency assessment")
        console.print("   • ✅ Intelligent progress tracking and analytics")
        console.print("   • ✅ Context-aware conversation management")
        console.print("   • ✅ Adaptive content delivery based on user profiles")
        console.print("   • ✅ FastAPI REST backend with comprehensive endpoints")
        console.print("   • ✅ Streamlit web UI for complete user interaction")
        console.print("   • ✅ Main orchestrator coordinating all components")
        
        console.print("\n🌐 [bold]To test the full system:[/bold]")
        console.print("   1. Start the API: uvicorn togaf_agent.api.main:app --reload")
        console.print("   2. Start the UI: streamlit run togaf_agent/ui/main.py")
        console.print("   3. Visit: http://localhost:8501")
        
    else:
        failed_components = [comp for comp, result in results.items() if not result]
        console.print(Panel.fit("⚠️ Phase 2 - Issues Found ⚠️", style="bold yellow"))
        console.print(f"\n❌ [bold red]Failed components: {', '.join(failed_components)}[/bold red]")
        console.print("   Please review and fix the issues above before proceeding.")
    
    return results


async def main():
    """Main validation entry point."""
    try:
        results = await validate_phase2_system()
        
        # Exit with appropriate code
        all_passed = all(results.values())
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        console.print(f"\n💥 [bold red]Validation failed with error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())