"""
Analyze factory data using Claude AI.

Takes extracted factory data and generates optimization recommendations.
"""

import json
import os
from typing import Dict, Any, Optional
from anthropic import Anthropic


class FactoryAnalyzer:
    """Analyze factory data and generate AI-powered insights."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the analyzer with Claude API.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
            )
        
        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history = []
    
    def analyze(self, factory_data: Dict[str, Any]) -> str:
        """
        Analyze factory data and return optimization recommendations.
        
        Args:
            factory_data: Extracted factory data from parse_save.py
            
        Returns:
            Analysis report as formatted string
        """
        prompt = self._build_analysis_prompt(factory_data)
        
        # Use Claude 3.5 Sonnet by default (best quality/cost ratio)
        # Or set CLAUDE_MODEL env var for alternatives
        model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        
        response = self.client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return response.content[0].text
    
    def analyze_interactive(self, factory_data: Dict[str, Any]) -> None:
        """
        Start an interactive analysis session.
        
        Allows follow-up questions about the factory.
        """
        print("Starting interactive factory analysis...")
        print("(Type 'quit' to exit)\n")
        
        # Initial analysis
        initial_prompt = self._build_analysis_prompt(factory_data)
        self.conversation_history.append({
            "role": "user",
            "content": initial_prompt
        })
        
        model = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
        
        response = self.client.messages.create(
            model=model,
            max_tokens=2000,
            messages=self.conversation_history
        )
        
        analysis = response.content[0].text
        print("=== Factory Analysis ===\n")
        print(analysis)
        print("\n" + "="*50 + "\n")
        
        self.conversation_history.append({
            "role": "assistant",
            "content": analysis
        })
        
        # Interactive follow-ups
        while True:
            user_input = input("Ask a follow-up question (or 'quit'): ").strip()
            if user_input.lower() == 'quit':
                break
            if not user_input:
                continue
            
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            response = self.client.messages.create(
                model=model,
                max_tokens=1500,
                messages=self.conversation_history
            )
            
            answer = response.content[0].text
            print(f"\n{answer}\n")
            
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })
    
    @staticmethod
    def _build_analysis_prompt(factory_data: Dict[str, Any]) -> str:
        """Build the prompt for Claude analysis."""
        
        session = factory_data.get("session", {})
        buildings = factory_data.get("buildings", [])
        power = factory_data.get("powerGrid", {})
        resources = factory_data.get("resources", {})
        
        prompt = f"""You are an expert Satisfactory factory advisor. Analyze this factory and provide optimization recommendations.

FACTORY DATA:
- Session: {session.get('name', 'Unknown')}
- Play Time: {session.get('playTime', 0) / 3600:.1f} hours
- Game Phase: {session.get('gamePhase', 0)}
- Active Milestone: {session.get('activeMilestone', 'None')}

BUILDINGS ({len(buildings)} total):
{json.dumps(buildings[:20], indent=2) if buildings else "No data"}

POWER GRID:
- Production: {power.get('totalProduction', 0)} MW
- Consumption: {power.get('totalConsumption', 0)} MW
- Storage: {power.get('storage', 0)} MWh
- Batteries: {power.get('batteries', 0)}

RESOURCES MINED:
{json.dumps(resources, indent=2) if resources else "No data"}

Please provide:
1. **Bottlenecks** - What's limiting production?
2. **Power Analysis** - How efficient is the power grid?
3. **Key Recommendations** - Top 3 priorities for optimization
4. **Building Suggestions** - Specific building count adjustments
5. **Estimated Impact** - Time/resource cost for each recommendation

Be specific and actionable. Reference actual building types and numbers."""
        
        return prompt


def analyze_save_file(save_data: Dict[str, Any], interactive: bool = False) -> str:
    """
    Analyze factory save data using Claude.
    
    Args:
        save_data: Parsed factory data
        interactive: If True, start interactive session
        
    Returns:
        Analysis report as string
    """
    try:
        analyzer = FactoryAnalyzer()
        
        if interactive:
            analyzer.analyze_interactive(save_data)
            return ""
        else:
            return analyzer.analyze(save_data)
    
    except ValueError as e:
        return f"Error: {e}\n\nMake sure to set the ANTHROPIC_API_KEY environment variable."
    except Exception as e:
        return f"Analysis error: {e}"


if __name__ == "__main__":
    # Example usage
    sample_data = {
        "session": {
            "name": "Test Factory",
            "playTime": 3600,
            "gamePhase": 1
        },
        "buildings": [],
        "powerGrid": {},
        "resources": {}
    }
    
    print(analyze_save_file(sample_data))
