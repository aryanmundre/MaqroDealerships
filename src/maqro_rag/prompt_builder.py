"""
Centralized prompt builder for conversational RAG responses.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class AgentConfig:
    """Configuration for agent persona and tone."""
    tone: str = "friendly"  # friendly, professional, concise
    dealership_name: str = "our dealership"
    persona_blurb: str = "friendly, persuasive car salesperson"
    signature: Optional[str] = None
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "AgentConfig":
        """Create AgentConfig from dictionary."""
        return cls(
            tone=config.get("tone", "friendly"),
            dealership_name=config.get("dealership_name", "our dealership"),
            persona_blurb=config.get("persona_blurb", "friendly, persuasive car salesperson"),
            signature=config.get("signature")
        )


class PromptBuilder:
    """Builder for conversational prompts with SMS-style responses."""
    
    def __init__(self, agent_config: AgentConfig):
        """Initialize prompt builder with agent configuration."""
        self.agent_config = agent_config
        self.few_shot_examples = self._get_few_shot_examples()
    
    def build_grounded_prompt(
        self, 
        user_message: str, 
        retrieved_cars: List[Dict[str, Any]], 
        agent_config: Optional[AgentConfig] = None
    ) -> str:
        """Build prompt for responses with retrieved vehicle data."""
        if agent_config is None:
            agent_config = self.agent_config
        
        # Format retrieved cars
        cars_text = self._format_cars_for_prompt(retrieved_cars)
        
        # Build system prompt
        system_prompt = self._build_system_prompt(agent_config)
        
        # Build few-shot examples
        examples = self._get_relevant_examples("grounded")
        
        # Build user prompt
        user_prompt = f"""Customer message: "{user_message}"

Available vehicles:
{cars_text}

Please respond in a conversational, SMS-style manner. Keep it to 2-5 short sentences with one clear next step or question."""

        return f"{system_prompt}\n\n{examples}\n\n{user_prompt}"
    
    def build_generic_prompt(
        self, 
        user_message: str, 
        agent_config: Optional[AgentConfig] = None
    ) -> str:
        """Build prompt for responses without specific vehicle data."""
        if agent_config is None:
            agent_config = self.agent_config
        
        # Build system prompt
        system_prompt = self._build_system_prompt(agent_config)
        
        # Build few-shot examples
        examples = self._get_relevant_examples("generic")
        
        # Build user prompt
        user_prompt = f"""Customer message: "{user_message}"

No specific vehicles found in inventory. Please respond helpfully and ask a clarifying question to better understand their needs."""

        return f"{system_prompt}\n\n{examples}\n\n{user_prompt}"
    
    def _build_system_prompt(self, agent_config: AgentConfig) -> str:
        """Build the system prompt with agent configuration."""
        tone_instructions = {
            "friendly": "Use contractions, casual language, and be warm and approachable.",
            "professional": "Be polite and business-like while remaining conversational.",
            "concise": "Keep responses brief and to the point while being helpful."
        }
        
        tone_instruction = tone_instructions.get(agent_config.tone, tone_instructions["friendly"])
        
        system_prompt = f"""You are a {agent_config.persona_blurb} for {agent_config.dealership_name}. 

Style guidelines:
- Reply as SMS: short sentences, contractions, no corporate jargon
- Be specific but casual and conversational
- Include exactly one clear next step (ask a single question or provide one CTA)
- If you aren't sure about something, ask a clarifying question
- Never invent inventory details you don't have
- Reference cars naturally in conversation (not as bullet lists)
- {tone_instruction}
- Keep responses to 2-5 short sentences maximum
- Personalize with customer name if available

When referencing vehicles, weave key details (year/make/model/price/mileage/availability) into natural prose."""
        
        if agent_config.signature:
            system_prompt += f"\n\nEnd responses with: {agent_config.signature}"
        
        return system_prompt
    
    def _format_cars_for_prompt(self, cars: List[Dict[str, Any]]) -> str:
        """Format retrieved cars for prompt inclusion."""
        if not cars:
            return "No specific vehicles found."
        
        formatted_cars = []
        for i, car in enumerate(cars[:3], 1):  # Limit to top 3
            vehicle = car.get('vehicle', {})
            score = car.get('similarity_score', 0)
            
            year = vehicle.get('year', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            price = vehicle.get('price', 0)
            mileage = vehicle.get('mileage', 0)
            color = vehicle.get('color', '')
            features = vehicle.get('features', '')
            
            price_str = f"${price:,}" if price else "Price available upon request"
            mileage_str = f"{mileage:,} miles" if mileage else "Mileage available upon request"
            
            car_text = f"{i}. {year} {make} {model}"
            if color:
                car_text += f" in {color}"
            car_text += f" - {price_str}, {mileage_str}"
            
            if features:
                car_text += f" (Features: {features})"
            
            car_text += f" [Match: {score:.1%}]"
            formatted_cars.append(car_text)
        
        return "\n".join(formatted_cars)
    
    def _get_few_shot_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Get few-shot examples for different scenarios."""
        return {
            "grounded": [
                {
                    "input": "Do you have a white Tiguan under 32k?",
                    "output": "Hey! I found a 2021 Volkswagen Tiguan in white for $29,500 with 28,000 miles. It's in great condition and ready for a test drive. Would you like to come by this weekend to check it out?"
                },
                {
                    "input": "Looking for a 2021-2023 Civic EX around 20k.",
                    "output": "Perfect! I've got a 2022 Honda Civic EX with 35,000 miles for $19,800. It's loaded with features and has a clean history. When would you like to take it for a spin?"
                },
                {
                    "input": "Any hybrids under 25k?",
                    "output": "Great timing! I have a 2021 Toyota Prius with 42,000 miles for $23,900. It's in excellent condition and gets amazing fuel economy. Want me to hold it for you to see this week?"
                }
            ],
            "generic": [
                {
                    "input": "SUV with 3rd row this weekend.",
                    "output": "I'd love to help you find the perfect SUV with a third row! What's your budget range, and do you have a preference for make or size? This will help me show you the best options we have available."
                },
                {
                    "input": "Do you still have the blue Camry SE from your site?",
                    "output": "Let me check our current inventory for that blue Camry SE. Can you tell me what year it was and roughly when you saw it on our site? This will help me find the exact vehicle you're interested in."
                },
                {
                    "input": "What's your best deal on a sedan?",
                    "output": "I'd be happy to show you our best sedan deals! To find the perfect match, what's your budget range and do you have any specific features you're looking for? We have several great options across different price points."
                }
            ]
        }
    
    def _get_relevant_examples(self, example_type: str) -> str:
        """Get relevant few-shot examples for the prompt."""
        examples = self.few_shot_examples.get(example_type, [])
        
        if not examples:
            return ""
        
        examples_text = "Examples:\n"
        for example in examples[:2]:  # Limit to 2 examples
            examples_text += f'Customer: "{example["input"]}"\n'
            examples_text += f'You: "{example["output"]}"\n\n'
        
        return examples_text 