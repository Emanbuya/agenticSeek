# nina_launcher.py
"""
Nina AI Assistant Launcher
Clean architecture without circular imports
"""

import sys
import asyncio
import argparse
import configparser
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    print("""
    ╔══════════════════════════════════════════════╗
    ║              Nina AI Assistant               ║
    ╟──────────────────────────────────────────────╢
    ║  Choose your interaction mode:               ║
    ║                                              ║
    ║  1. Voice Mode  - Full speech-to-speech      ║
    ║  2. API Mode    - Web interface + Voice out  ║
    ║  3. CLI Mode    - Terminal interaction       ║
    ║                                              ║
    ╚══════════════════════════════════════════════╝
    """)


async def launch_voice_mode():
    """Launch Nina in full voice mode"""
    print("\n🚀 Starting Nina Voice Mode...")
    
    # Import here to avoid circular imports
    from sources.llm_provider import Provider
    from sources.agents import CasualAgent, CoderAgent, FileAgent, BrowserAgent, PlannerAgent
    from sources.browser import Browser, create_driver
    from sources.utility import pretty_print
    
    # Custom interaction for voice mode
    from nina_voice_system import create_nina_system
    
    # Load config
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Initialize components
    pretty_print("Initializing components...", color="status")
    
    provider = Provider(
        provider_name=config["MAIN"]["provider_name"],
        model=config["MAIN"]["provider_model"],
        server_address=config["MAIN"]["provider_server_address"],
        is_local=config.getboolean('MAIN', 'is_local')
    )
    
    languages = config["MAIN"]["languages"].split(' ')
    browser = Browser(
        create_driver(headless=True, stealth_mode=False, lang=languages[0]),
        anticaptcha_manual_install=False
    )
    
    personality_folder = "jarvis" if config.getboolean('MAIN', 'jarvis_personality') else "base"
    
    agents = [
        CasualAgent(
            name="Nina",
            prompt_path=f"prompts/{personality_folder}/casual_agent.txt",
            provider=provider,
            verbose=False
        ),
        CoderAgent(
            name="coder",
            prompt_path=f"prompts/{personality_folder}/coder_agent.txt",
            provider=provider,
            verbose=False
        ),
        FileAgent(
            name="File Agent",
            prompt_path=f"prompts/{personality_folder}/file_agent.txt",
            provider=provider,
            verbose=False
        ),
        BrowserAgent(
            name="Browser",
            prompt_path=f"prompts/{personality_folder}/browser_agent.txt",
            provider=provider,
            verbose=False,
            browser=browser
        ),
        PlannerAgent(
            name="Planner",
            prompt_path=f"prompts/{personality_folder}/planner_agent.txt",
            provider=provider,
            verbose=False,
            browser=browser
        ),
    ]
    
    # Create a minimal interaction wrapper for voice mode
    class VoiceInteraction:
        def __init__(self, agents):
            from sources.router import AgentRouter
            self.agents = agents
            self.router = AgentRouter(agents, supported_language=languages)
            self.current_agent = None
            self.last_query = None
            self.last_answer = None
            self.last_reasoning = None
            
        def set_query(self, query):
            self.last_query = query
            
        async def think(self):
            if not self.last_query:
                return False
                
            # Select agent
            agent = self.router.select_agent(self.last_query)
            if not agent:
                return False
                
            self.current_agent = agent
            
            # Process query - we need a mock speech module for now
            class MockSpeech:
                def speak(self, text):
                    pass
                    
            mock_speech = MockSpeech()
            self.last_answer, self.last_reasoning = await agent.process(self.last_query, mock_speech)
            
            return bool(self.last_answer)
    
    # Create voice interaction
    interaction = VoiceInteraction(agents)
    
    # Create and start Nina system
    nina = create_nina_system(interaction)
    nina.start()


async def launch_api_mode():
    """Launch standard API mode"""
    print("\n🌐 Starting API Mode...")
    
    # Import and run api.py
    import api
    import uvicorn
    
    # Start the API server
    uvicorn.run(api.api, host="0.0.0.0", port=8000)


async def launch_cli_mode():
    """Launch standard CLI mode"""
    print("\n💻 Starting CLI Mode...")
    
    # First, let's fix the circular import in interaction.py
    # We'll use the original Speech class
    interaction_file = Path("sources/interaction.py")
    if interaction_file.exists():
        content = interaction_file.read_text()
        if "nina_jarvis_voice" in content:
            # Replace with original import
            fixed_content = content.replace(
                "from sources.nina_jarvis_voice import Speech",
                "from sources.text_to_speech import Speech"
            )
            # Remove the enhance_interaction lines
            lines = fixed_content.split('\n')
            filtered_lines = []
            skip_next = False
            for line in lines:
                if "enhance_interaction" in line:
                    skip_next = True
                    continue
                if skip_next and line.strip().startswith("self.speech.enhance_interaction"):
                    skip_next = False
                    continue
                filtered_lines.append(line)
            
            fixed_content = '\n'.join(filtered_lines)
            interaction_file.write_text(fixed_content)
            print("✅ Fixed circular import in interaction.py")
    
    # Now import and run CLI
    import cli
    await cli.main()


def main():
    parser = argparse.ArgumentParser(description='Nina AI Assistant')
    parser.add_argument('--mode', choices=['voice', 'api', 'cli'], 
                       help='Launch mode')
    args = parser.parse_args()
    
    if not args.mode:
        print_banner()
        choice = input("\nEnter your choice (1-3): ").strip()
        mode_map = {'1': 'voice', '2': 'api', '3': 'cli'}
        args.mode = mode_map.get(choice, 'voice')
    
    try:
        if args.mode == 'voice':
            asyncio.run(launch_voice_mode())
        elif args.mode == 'api':
            asyncio.run(launch_api_mode())
        elif args.mode == 'cli':
            asyncio.run(launch_cli_mode())
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using Nina!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Ensure we have required directories
    Path(".nina_profiles").mkdir(exist_ok=True)
    Path(".screenshots").mkdir(exist_ok=True)
    
    main()