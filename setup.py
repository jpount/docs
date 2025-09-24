#!/usr/bin/env python3
"""
Enhanced Setup Script for Documentation & Diagram Generation Framework
Supports hands-off mode with agent selection, progress tracking, and restart capability
"""

import os
import sys
import json
import shutil
import platform
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

class Colors:
    """Terminal color codes"""
    RED = '\033[91m' if platform.system() != 'Windows' else ''
    GREEN = '\033[92m' if platform.system() != 'Windows' else ''
    YELLOW = '\033[93m' if platform.system() != 'Windows' else ''
    BLUE = '\033[94m' if platform.system() != 'Windows' else ''
    CYAN = '\033[96m' if platform.system() != 'Windows' else ''
    MAGENTA = '\033[95m' if platform.system() != 'Windows' else ''
    RESET = '\033[0m' if platform.system() != 'Windows' else ''
    BOLD = '\033[1m' if platform.system() != 'Windows' else ''

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    display_name: str
    description: str
    mandatory: bool = False
    default_selected: bool = False
    depends_on: List[str] = None
    category: str = "specialist"
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class EnhancedSetup:
    """Enhanced setup with hands-off mode"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.resolve()
        self.framework_dir = self.script_dir / "framework"
        self.output_dir = self.script_dir / "output"
        self.codebase_dir = self.script_dir / "codebase"
        self.config_file = self.script_dir / "analysis_config.json"
        self.log_dir = self.script_dir / "logs"
        
        # Setup logging
        self.setup_logging()
        
        # Define available agents
        self.agents = {
            # Mandatory agents (always included)
            "repomix-analyzer": AgentConfig(
                name="repomix-analyzer",
                display_name="Repomix Analyzer",
                description="Analyzes Repomix-generated codebase summaries (REQUIRED - ALWAYS FIRST)",
                mandatory=True,
                default_selected=True,
                category="mandatory"
            ),
            
            # Default agents
            "solution-architect": AgentConfig(
                name="solution-architect",
                display_name="Solution Architect", 
                description="Comprehensive C4 model analysis + technical + deployment + integration architecture",
                default_selected=True,
                depends_on=["repomix-analyzer"],
                category="default"
            ),
            "technical-architect": AgentConfig(
                name="technical-architect",
                display_name="Technical Architect",
                description="Multi-language technical deep dive - code quality, design patterns, technical implementation analysis",
                default_selected=True,
                depends_on=["repomix-analyzer", "solution-architect"],
                category="default"
            ),
            
            # All other agents (optional)
            "business-logic-analyst": AgentConfig(
                name="business-logic-analyst",
                display_name="Business Logic Analyst",
                description="Extracts business rules, domain logic, and process flows",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "java-architect": AgentConfig(
                name="java-architect", 
                display_name="Java Architect",
                description="Java/J2EE specialist - Spring, Enterprise JavaBeans, Java web technologies",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "angular-architect": AgentConfig(
                name="angular-architect",
                display_name="Angular Architect", 
                description="Angular specialist - AngularJS to Angular 17+, RxJS, NgRx, performance optimization",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "dotnet-architect": AgentConfig(
                name="dotnet-architect",
                display_name=".NET Architect",
                description=".NET specialist - C#, ASP.NET, .NET Framework/Core/5+, Entity Framework",
                default_selected=False, 
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "php-architect": AgentConfig(
                name="php-architect",
                display_name="PHP Architect",
                description="PHP specialist - Laravel, Symfony, CodeIgniter, legacy PHP patterns",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "delphi-architect": AgentConfig(
                name="delphi-architect",
                display_name="Delphi Architect",
                description="Delphi/Object Pascal specialist - VCL/FireMonkey, COM components, database connectivity",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "security-analyst": AgentConfig(
                name="security-analyst", 
                display_name="Security Analyst",
                description="Security vulnerabilities, OWASP Top 10, compliance gaps",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "performance-analyst": AgentConfig(
                name="performance-analyst",
                display_name="Performance Analyst", 
                description="Performance bottlenecks, memory leaks, scalability issues",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "integration-specialist": AgentConfig(
                name="integration-specialist",
                display_name="Integration Specialist",
                description="APIs, messaging systems, integration patterns, event-driven architecture",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            ),
            "ui-analyst": AgentConfig(
                name="ui-analyst",
                display_name="UI/UX Analyst",
                description="Frontend technology analysis, UI/UX assessment for modern and legacy UI",
                default_selected=False,
                depends_on=["repomix-analyzer"],
                category="optional"
            )
        }
    
    def setup_logging(self):
        """Setup logging for the setup process"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('setup')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = self.log_dir / f"setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for errors only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def run(self):
        """Main setup flow"""
        self.logger.info("Starting enhanced setup wizard")
        
        try:
            self.show_banner()
            
            
            # Step 1: Configure project
            self.configure_project()
            
            # Step 2: Choose mode
            mode = self.select_mode()
            
            if mode == "hands-off":
                # Step 3: Select agents
                selected_agents = self.select_agents()
                
                # Step 4: Create configuration and start analysis
                self.create_configuration(mode, selected_agents)
                self.start_hands_off_analysis(selected_agents)
            else:
                # Interactive mode
                self.create_configuration(mode, [])
                self.show_interactive_next_steps()
                
            self.logger.info("Setup completed successfully")
                
        except KeyboardInterrupt:
            self.logger.info("Setup interrupted by user")
            print(f"\n{Colors.YELLOW}Setup interrupted.{Colors.RESET}")
            
        except Exception as e:
            self.logger.error(f"Setup failed with error: {e}", exc_info=True)
            print(f"\n{Colors.RED}Setup failed: {e}{Colors.RESET}")
            print(f"Check logs for details: {self.log_dir}")
    
    def show_banner(self):
        """Display welcome banner"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.CYAN}    Documentation & Diagram Generation Framework{Colors.RESET}")
        print(f"{Colors.CYAN}              Enhanced Setup Wizard{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        print()
        print(f"{Colors.BLUE}Generate comprehensive documentation and diagrams{Colors.RESET}")
        print(f"{Colors.BLUE}from your codebase with intelligent agent orchestration.{Colors.RESET}")
        print()
    
    def has_existing_progress(self) -> bool:
        """Check if there's existing analysis progress"""
        return self.progress_file.exists()
    
    def handle_existing_progress(self) -> bool:
        """Handle existing progress file"""
        try:
            with open(self.progress_file, 'r') as f:
                progress_data = json.load(f)
                progress = AnalysisProgress(**progress_data)
            
            print(f"{Colors.YELLOW}⚠️  Existing analysis found:{Colors.RESET}")
            print(f"   Project: {Colors.CYAN}{progress.project_name}{Colors.RESET}")
            print(f"   Status: {Colors.CYAN}{progress.status}{Colors.RESET}")
            print(f"   Started: {Colors.CYAN}{progress.started_at}{Colors.RESET}")
            print(f"   Progress: {Colors.CYAN}{len(progress.completed_agents)}/{len(progress.selected_agents)} agents completed{Colors.RESET}")
            
            if progress.completed_agents:
                print(f"   Completed: {Colors.GREEN}{', '.join(progress.completed_agents)}{Colors.RESET}")
            
            if progress.failed_agents:
                print(f"   Failed: {Colors.RED}{', '.join(progress.failed_agents)}{Colors.RESET}")
                
            if progress.current_agent:
                print(f"   Current: {Colors.YELLOW}{progress.current_agent}{Colors.RESET}")
            
            print()
            print("Options:")
            print("1. Resume existing analysis")
            print("2. Start fresh analysis (will overwrite)")
            print("3. Exit")
            print()
            
            while True:
                choice = input("Your choice [1-3]: ").strip()
                if choice == "1":
                    self.resume_analysis(progress)
                    return True
                elif choice == "2":
                    self.progress_file.unlink()  # Remove existing progress
                    print(f"{Colors.GREEN}✓ Starting fresh analysis{Colors.RESET}")
                    print()
                    return False
                elif choice == "3":
                    print("Exiting...")
                    sys.exit(0)
                else:
                    print(f"{Colors.RED}Invalid choice. Please enter 1, 2, or 3.{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}Error reading progress file: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}Removing corrupted progress file and starting fresh.{Colors.RESET}")
            self.progress_file.unlink()
            return False
    
    def configure_project(self):
        """Configure project settings"""
        print(f"{Colors.BOLD}Step 1: Configure Project{Colors.RESET}")
        print()
        
        # Get project name
        default_name = "daytrader"  # Match the current CLAUDE.md
        project_name = input(f"Project name [{default_name}]: ").strip() or default_name
        self.project_name = project_name
        
        self.logger.info(f"Project name set to: {project_name}")
        
        # Ensure codebase directory exists
        codebase_path = self.codebase_dir / project_name
        if not codebase_path.exists():
            codebase_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created codebase directory: {codebase_path}")
            print(f"{Colors.YELLOW}📁 Created codebase directory: {codebase_path}{Colors.RESET}")
        else:
            self.logger.info(f"Found existing codebase directory: {codebase_path}")
            print(f"{Colors.GREEN}✓ Found existing codebase: {codebase_path}{Colors.RESET}")
        
        print(f"{Colors.GREEN}✓ Project configured: {project_name}{Colors.RESET}")
        print()
    
    def select_mode(self) -> str:
        """Select analysis mode"""
        print(f"{Colors.BOLD}Step 2: Choose Analysis Mode{Colors.RESET}")
        print()
        print("1. 🚀 Hands-off Mode - Fully automated agent execution")
        print("   • Select agents to run")
        print("   • Automatic execution with progress tracking") 
        print("   • Restart capability if interrupted")
        print("   • Perfect for CI/CD and n8n workflows")
        print()
        print("2. 🎯 Interactive Mode - Manual agent execution")
        print("   • Traditional Claude Code agent execution")
        print("   • Run agents individually as needed")
        print("   • Full control over the analysis process")
        print()
        
        while True:
            choice = input("Select mode [1-2]: ").strip()
            if choice == "1":
                print(f"{Colors.GREEN}✓ Hands-off mode selected{Colors.RESET}")
                print()
                return "hands-off"
            elif choice == "2":
                print(f"{Colors.GREEN}✓ Interactive mode selected{Colors.RESET}")  
                print()
                return "interactive"
            else:
                print(f"{Colors.RED}Invalid choice. Please enter 1 or 2.{Colors.RESET}")
    
    def select_agents(self) -> List[str]:
        """Select agents for analysis"""
        print(f"{Colors.BOLD}Step 3: Select Analysis Agents{Colors.RESET}")
        print()
        
        # Group agents by category
        categories = {
            "mandatory": [],
            "default": [],
            "optional": []
        }
        
        for agent_name, agent in self.agents.items():
            categories[agent.category].append((agent_name, agent))
        
        selected_agents = []
        
        # Show mandatory agents (always included)
        print(f"{Colors.CYAN}🔴 Mandatory Agent (always included):{Colors.RESET}")
        for agent_name, agent in categories["mandatory"]:
            print(f"   ✓ {agent.display_name} - {agent.description}")
            selected_agents.append(agent_name)
        print()
        
        # Show default agents
        print(f"{Colors.CYAN}⭐ Default Agents (recommended core set):{Colors.RESET}")
        for agent_name, agent in categories["default"]:
            default_marker = " (RECOMMENDED)" if agent.default_selected else ""
            print(f"   ✓ {agent.display_name}{default_marker}")
            print(f"      {agent.description}")
        print()
        
        # Ask about default agents
        include_defaults = input(f"Include all {len(categories['default'])} default agents? [Y/n]: ").strip().lower()
        if include_defaults != 'n' and include_defaults != 'no':
            for agent_name, agent in categories["default"]:
                selected_agents.append(agent_name)
                print(f"{Colors.GREEN}✓ Added: {agent.display_name}{Colors.RESET}")
        else:
            # Let them pick individual default agents
            print()
            print("Select individual default agents:")
            for i, (agent_name, agent) in enumerate(categories["default"], 1):
                include_agent = input(f"Include {agent.display_name}? [Y/n]: ").strip().lower()
                if include_agent != 'n' and include_agent != 'no':
                    selected_agents.append(agent_name)
                    print(f"{Colors.GREEN}✓ Added: {agent.display_name}{Colors.RESET}")
        print()
        
        # Show all optional agents in one multi-select
        print(f"{Colors.CYAN}🔧 Optional Agents (select any combination):{Colors.RESET}")
        optional_choices = {}
        for i, (agent_name, agent) in enumerate(categories["optional"], 1):
            print(f"   {i}. {agent.display_name}")
            print(f"      {agent.description}")
            optional_choices[str(i)] = agent_name
        print()
        
        # Select optional agents
        print("Select optional agents (enter numbers separated by commas):")
        print("• Press Enter to skip optional agents")  
        print("• Enter numbers for specific agents (e.g., 1,3,5)")
        print("• Enter 'all' to include all optional agents")
        print()
        
        optional_selection = input("Optional agents [none]: ").strip().lower()
        
        if optional_selection == "all":
            for agent_name, agent in categories["optional"]:
                selected_agents.append(agent_name)
                print(f"{Colors.GREEN}✓ Added: {agent.display_name}{Colors.RESET}")
        elif optional_selection and optional_selection != "none":
            # Parse specific selections
            try:
                selected_numbers = [choice.strip() for choice in optional_selection.split(",")]
                for choice in selected_numbers:
                    if choice in optional_choices:
                        selected_agents.append(optional_choices[choice])
                        agent_name = optional_choices[choice]
                        agent = self.agents[agent_name]
                        print(f"{Colors.GREEN}✓ Added: {agent.display_name}{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}Invalid choice '{choice}' - skipping{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}Invalid selection format, skipping optional agents{Colors.RESET}")
        
        print()
        
        # Show final selection
        print(f"{Colors.BOLD}📋 Selected Agents:{Colors.RESET}")
        for i, agent_name in enumerate(selected_agents, 1):
            agent = self.agents[agent_name]
            print(f"   {i}. {agent.display_name}")
        
        print(f"{Colors.GREEN}✓ {len(selected_agents)} agents selected for analysis{Colors.RESET}")
        print()
        
        return selected_agents
    
    def create_configuration(self, mode: str, selected_agents: List[str]):
        """Create configuration files"""
        print(f"{Colors.BOLD}Step 4: Creating Configuration{Colors.RESET}")
        print()
        
        # Create output directories
        dirs_to_create = [
            self.output_dir / "docs",
            self.output_dir / "diagrams", 
            self.output_dir / "context",
            self.output_dir / "reports"
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        config = {
            "project_name": self.project_name,
            "mode": mode,
            "selected_agents": selected_agents,
            "created_at": datetime.now().isoformat(),
            "framework_version": "2.1"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"{Colors.GREEN}✓ Configuration saved to analysis_config.json{Colors.RESET}")
        
        # Create/update CLAUDE.md
        self.update_claude_md(selected_agents)
        
        # Ensure repomix config exists
        self.ensure_repomix_config()
        
        # Ensure MCP config exists
        self.ensure_mcp_config()
        
        print(f"{Colors.GREEN}✓ Framework configured successfully{Colors.RESET}")
        print()
    
    def update_claude_md(self, selected_agents: List[str]):
        """Update CLAUDE.md with selected agents"""
        claude_md_content = f"""# Project Configuration for Claude Code

## Project Overview
- **Project Name:** {self.project_name}
- **Framework Mode:** Enhanced Documentation & Diagram Generation
- **Codebase Location:** codebase/{self.project_name}
- **Framework Version:** 2.1 (Enhanced)

## Core Workflow

### 🔴 STEP 1: Generate Repomix Summary (REQUIRED)
```bash
# Generate compressed codebase summary (80% token reduction)
repomix --config .repomix.config.json codebase/{self.project_name}/

# Verify output exists
ls -la output/reports/repomix-summary.md
```

### ⚡ STEP 2: Run Analysis Agents in Sequence
```bash
# Run selected agents in order (using analysis_config.json)
python3 -c "from run_analysis import run_analysis; import json; config = json.load(open('analysis_config.json')); run_analysis(config['selected_agents'])"

# Or run agents individually:
{chr(10).join(f'@{agent}' for agent in selected_agents)}
```

## Available Agents

### Current Agents ({len(selected_agents)} Selected)
{chr(10).join(f'- `@{agent}` - {self.agents[agent].description}' for agent in selected_agents)}

## Agent Data Flow Rules

### 🔴 CRITICAL: All Agents Must Follow This Priority
1. **PRIMARY**: Read `output/reports/repomix-summary.md` (compressed codebase)
2. **SECONDARY**: Read `output/context/*.json` (previous agent outputs)
3. **FALLBACK**: Access raw codebase only if needed

### Critical Rules for ALL Agents
⚠️ **SEE**: `framework/templates/CRITICAL_RULES.md` for complete rules

**Key requirements:**
- NO hardcoded data or fabricated metrics
- NO Serena MCP tools - use JSON context files only
- ALL Mermaid diagrams MUST validate with zero errors before completion
- State "Not detected" for missing information

### Required Agent Outputs
Each agent MUST produce:
- `output/context/{{agent-name}}-summary.json` - Context for next agents
- `output/docs/{{number}}-{{agent-name}}.md` - Documentation
- `output/diagrams/{{agent-name}}-*.mmd` - Diagrams (if applicable)

## Output Locations
- **Documentation:** `output/docs/`
- **Diagrams:** `output/diagrams/`
- **Context Summaries:** `output/context/`
- **Reports:** `output/reports/`

## Token Optimization Strategy
- **Repomix Summary:** ~50,000 tokens (80% reduction from raw codebase)
- **Context Chain:** Agents read previous summaries for efficiency
- **Raw Access:** Only when compressed data insufficient

---
*Generated dynamically on {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
        
        with open(self.script_dir / "CLAUDE.md", 'w') as f:
            f.write(claude_md_content)
        
        print(f"{Colors.GREEN}✓ Updated CLAUDE.md with selected agents{Colors.RESET}")
    
    def ensure_repomix_config(self):
        """Ensure repomix configuration exists"""
        repomix_config_file = self.script_dir / ".repomix.config.json"
        repomix_template_file = self.framework_dir / "mcp-configs" / "repomix.config.template.json"

        if not repomix_config_file.exists():
            if not repomix_template_file.exists():
                error_msg = f"Required repomix template not found: {repomix_template_file}"
                self.logger.error(error_msg)
                print(f"{Colors.RED}❌ SETUP ERROR: {error_msg}{Colors.RESET}")
                print(f"{Colors.RED}Cannot proceed without repomix configuration template.{Colors.RESET}")
                sys.exit(1)

            # Copy template and customize it
            try:
                with open(repomix_template_file, 'r') as f:
                    repomix_config = json.load(f)

                # Customize header text with project name
                repomix_config["output"]["headerText"] = f"# {self.project_name} Codebase Summary\\nGenerated by Repomix for AI-optimized analysis"

                with open(repomix_config_file, 'w') as f:
                    json.dump(repomix_config, f, indent=2)

                self.logger.info(f"Created repomix config from template: {repomix_template_file}")
                print(f"{Colors.GREEN}✓ Created .repomix.config.json from template{Colors.RESET}")

            except Exception as e:
                error_msg = f"Failed to create repomix config from template: {e}"
                self.logger.error(error_msg)
                print(f"{Colors.RED}❌ SETUP ERROR: {error_msg}{Colors.RESET}")
                sys.exit(1)
        else:
            self.logger.info("Repomix config already exists")
            print(f"{Colors.GREEN}✓ Found existing .repomix.config.json{Colors.RESET}")
    
    def ensure_mcp_config(self):
        """Ensure MCP configuration exists in root directory"""
        mcp_config_file = self.script_dir / ".mcp.json"
        mcp_template_file = self.framework_dir / "mcp-configs" / "mcp.template.json"
        
        if not mcp_config_file.exists():
            if mcp_template_file.exists():
                # Copy template to root
                try:
                    shutil.copy2(mcp_template_file, mcp_config_file)
                    self.logger.info(f"Copied MCP template from {mcp_template_file} to {mcp_config_file}")
                    print(f"{Colors.GREEN}✓ Created .mcp.json from template{Colors.RESET}")
                except Exception as e:
                    self.logger.error(f"Failed to copy MCP template: {e}")
                    self.create_basic_mcp_config(mcp_config_file)
            else:
                # Create basic MCP config
                self.logger.warning("MCP template not found, creating basic config")
                self.create_basic_mcp_config(mcp_config_file)
        else:
            self.logger.info("MCP config already exists")
            print(f"{Colors.GREEN}✓ Found existing .mcp.json{Colors.RESET}")
    
    def create_basic_mcp_config(self, mcp_config_file: Path):
        """Create a basic MCP configuration"""
        basic_mcp = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(self.script_dir)],
                    "env": {}
                },
                "memory": {
                    "command": "npx", 
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "env": {}
                }
            }
        }
        
        try:
            with open(mcp_config_file, 'w') as f:
                json.dump(basic_mcp, f, indent=2)
            self.logger.info(f"Created basic MCP config at {mcp_config_file}")
            print(f"{Colors.GREEN}✓ Created basic .mcp.json{Colors.RESET}")
        except Exception as e:
            self.logger.error(f"Failed to create basic MCP config: {e}")
            print(f"{Colors.RED}❌ Failed to create .mcp.json: {e}{Colors.RESET}")
    
    def start_hands_off_analysis(self, selected_agents: List[str]):
        """Start hands-off analysis"""
        print(f"{Colors.BOLD}Step 5: Ready for Analysis{Colors.RESET}")
        print()
        
        print(f"{Colors.CYAN}🚀 Analysis Configuration Complete{Colors.RESET}")
        print(f"   Project: {self.project_name}")
        print(f"   Agents: {len(selected_agents)} selected")
        print()
        
        # Check if Repomix summary exists
        repomix_file = self.output_dir / "reports" / "repomix-summary.md"
        if not repomix_file.exists():
            print(f"{Colors.YELLOW}⚠️  Repomix summary not found{Colors.RESET}")
            print(f"   Expected at: {repomix_file}")
            print()
            print(f"{Colors.BLUE}💡 Generate it first:{Colors.RESET}")
            print(f"   repomix --config .repomix.config.json codebase/{self.project_name}/")
            print()
        else:
            print(f"{Colors.GREEN}✅ Found Repomix summary{Colors.RESET}")

            # Check if citations have been extracted
            citations_file = self.output_dir / "context" / "codebase-citations.json"
            if not citations_file.exists():
                print(f"{Colors.YELLOW}⚠️  Citations not extracted yet{Colors.RESET}")
                print(f"   Extracting citations from repomix summary...")

                # Run citation extraction
                try:
                    result = subprocess.run(
                        ["python3", "framework/scripts/extract_citations.py"],
                        capture_output=True,
                        text=True,
                        cwd=self.script_dir
                    )
                    if result.returncode == 0:
                        print(f"{Colors.GREEN}✅ Citations extracted successfully{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}⚠️  Citation extraction had issues{Colors.RESET}")
                        if result.stderr:
                            print(f"   {result.stderr}")
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️  Could not extract citations: {e}{Colors.RESET}")
                    print(f"   You can manually run: python3 framework/scripts/extract_citations.py")
            else:
                print(f"{Colors.GREEN}✅ Found extracted citations{Colors.RESET}")

            print()
        
        # Show execution plan
        print(f"{Colors.BOLD}📋 Execution Plan:{Colors.RESET}")
        for i, agent_name in enumerate(selected_agents, 1):
            agent = self.agents[agent_name]
            print(f"   {i}. @{agent_name} - {agent.display_name}")
        print()
        
        print(f"{Colors.CYAN}🎯 Ready to execute!{Colors.RESET}")
        print()
        print("Next steps:")
        print(f"1. {Colors.YELLOW}Terminal execution:{Colors.RESET}")
        print(f"   python3 run_analysis.py")
        print()
        print(f"2. {Colors.YELLOW}n8n workflow:{Colors.RESET}")
        print(f"   Configure n8n to use the agents from analysis_config.json")
        print()
        print(f"3. {Colors.YELLOW}Manual execution:{Colors.RESET}")
        print(f"   Run agents individually: @repomix-analyzer, @solution-architect, etc.")
        print()
    
    def show_interactive_next_steps(self):
        """Show next steps for interactive mode"""
        print(f"{Colors.BOLD}Setup Complete - Interactive Mode{Colors.RESET}")
        print()
        print(f"{Colors.CYAN}Next Steps:{Colors.RESET}")
        print()
        print(f"1. {Colors.YELLOW}Generate Repomix Summary (Required):{Colors.RESET}")
        print(f"   repomix --config .repomix.config.json codebase/{self.project_name}/")
        print()
        print(f"2. {Colors.YELLOW}Start Claude Code and run agents manually:{Colors.RESET}")
        print(f"   @repomix-analyzer         # Always run first")
        print(f"   @solution-architect       # High-level architecture")
        print(f"   @technical-architect      # Deep technical analysis")
        print(f"   # See CLAUDE.md for complete workflow")
        print()
        print(f"3. {Colors.YELLOW}Check outputs:{Colors.RESET}")
        print(f"   Documentation: output/docs/")
        print(f"   Diagrams: output/diagrams/")
        print()

if __name__ == "__main__":
    setup = EnhancedSetup()
    setup.run()