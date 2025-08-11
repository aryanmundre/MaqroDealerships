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
        agent_config: Optional[AgentConfig] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
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
        
        # Build conversation context (if provided)
        conversation_context = ""
        if conversation_history:
            conversation_context = self._format_conversation_context(conversation_history)
        
        # Build user prompt
        user_prompt = f"""Customer message: "{user_message}"

Available vehicles:
{cars_text}

Please respond in a conversational, SMS-style manner. Keep it to 2-5 short sentences with one clear next step or question."""

        # Combine all parts
        full_prompt = f"{system_prompt}\n\n{examples}"
        if conversation_context:
            full_prompt += f"\n\n{conversation_context}"
        full_prompt += f"\n\n{user_prompt}"

        return full_prompt
    
    def build_generic_prompt(
        self, 
        user_message: str, 
        agent_config: Optional[AgentConfig] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build prompt for responses without specific vehicle data."""
        if agent_config is None:
            agent_config = self.agent_config
        
        # Build system prompt
        system_prompt = self._build_system_prompt(agent_config)
        
        # Build few-shot examples
        examples = self._get_relevant_examples("generic")
        
        # Build conversation context (if provided)
        conversation_context = ""
        if conversation_history:
            conversation_context = self._format_conversation_context(conversation_history)
        
        # Build user prompt
        user_prompt = f"""Customer message: "{user_message}"

No specific vehicles found in inventory. Please respond helpfully and ask a clarifying question to better understand their needs."""

        # Combine all parts
        full_prompt = f"{system_prompt}\n\n{examples}"
        if conversation_context:
            full_prompt += f"\n\n{conversation_context}"
        full_prompt += f"\n\n{user_prompt}"

        return full_prompt
    
    def _build_system_prompt(self, agent_config: AgentConfig) -> str:
        """Build the system prompt with agent configuration."""
        system_prompt = f"""ROLE
You are a friendly, persuasive car salesperson at {agent_config.dealership_name}. You text like a human: short, natural sentences, contractions, no corporate jargon.

PRIMARY OUTCOME
Book test drives and sell cars. Be proactive but conversational - ask ONE question at a time and respond to their answer before moving forward.

STYLE
- SMS tone: 2–5 short sentences. No bullet lists. No long paragraphs.
- Personal, confident, helpful. Use the customer's name if available.
- Reference specific details (year/trim/price/mileage) from retrieved data. Be specific about what you have.
- Ask ONE question at a time and wait for their response.
- Build conversation naturally - don't bombard with multiple questions.

DECISION POLICY (WHEN TO USE A CTA)
1) Customer is ending conversation (thanks, goodbye, have a great day, etc.):
   - Acknowledge warmly and end conversation naturally
   - NO sales push or offers
   - Use next_action: "end_conversation"

2) Customer shows interest (looking for, interested in, want, need, etc.):
   - If you have matching vehicles: Offer them immediately with test drive CTA
   - If vague but you have relevant inventory: Suggest specific cars and offer test drive
   - If no relevant inventory: Ask ONE clarifying question and wait for response

3) Customer answers a question (budget, preferences, timing):
   - Respond to their answer and offer relevant vehicles
   - Don't ask another question immediately - offer what matches their answer

4) Customer asks specific questions (features, availability, price):
   - Answer and immediately offer test drive with specific time slots

5) Customer hesitates ("not now", "maybe later"):
   - Acknowledge and offer a low-friction slot (10–15 min spin)

6) No suitable inventory:
   - Offer what you DO have that's close, or ask ONE clarifying question

CTAs (BE CONVERSATIONAL)
- Offer test drives when customer shows interest
- Don't push sales when customer is ending conversation
- Ask ONE question at a time and wait for response
- Make it easy: "Want to swing by today 5:30 or tomorrow 10:00?"
- Include {agent_config.dealership_name} location

SAFETY / HONESTY
- Never invent specifics. If unsure, say "I'll double-check."
- Only reference vehicles you actually have in inventory

OUTPUT SHAPE
- Natural text reply (2–5 sentences), followed by a compact control object on the final line:
  JSON: {{"next_action":"<ask_clarify|offer_test_drive|confirm_test_drive|end_conversation>",
         "proposed_slots":["ISO1","ISO2"],
         "location_label":"{agent_config.dealership_name}",
         "confidence": 0.0-1.0}}
- Use ask_clarify for ONE question, then wait for response"""
        
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
    
    def _format_conversation_context(self, conversations: List[Dict[str, Any]], max_messages: int = 8) -> str:
        """Format conversation history with smart truncation to keep costs low."""
        if not conversations:
            return ""
        
        # Take only the most recent messages to keep context manageable
        recent_conversations = conversations[-max_messages:] if len(conversations) > max_messages else conversations
        
        context_parts = ["--- CONVERSATION HISTORY ---"]
        
        for conv in recent_conversations:
            role = "Customer" if conv.get("sender") == "customer" else "Agent"
            message = conv.get("message", "")
            
            # Truncate very long messages to keep costs down
            if len(message) > 200:
                message = message[:200] + "..."
            
            context_parts.append(f"{role}: {message}")
        
        # Add indicator if we truncated
        if len(conversations) > max_messages:
            context_parts.append(f"\n[Previous {len(conversations) - max_messages} messages omitted for brevity]")
        
        return "\n".join(context_parts)
    
    def _get_few_shot_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Get few-shot examples for different scenarios."""
        return {
            "grounded": [
                {
                    "input": "Is the 2022 Tiguan SE in white still available?",
                    "output": "Yes! We have that 2022 Tiguan SE in white at $29,900 with only 28k miles. It's clean and ready to go. Want to swing by today 5:30 or tomorrow 10:00 at our Mission Bay Auto for a quick spin?\n{\"next_action\":\"offer_test_drive\",\"proposed_slots\":[\"2025-08-12T17:30:00-07:00\",\"2025-08-13T10:00:00-07:00\"],\"location_label\":\"Mission Bay Auto\",\"confidence\":0.9}"
                },
                {
                    "input": "Looking for an SUV",
                    "output": "Great! I've got a few SUVs in stock. What's your budget range?\n{\"next_action\":\"ask_clarify\",\"confidence\":0.8}"
                },
                {
                    "input": "What's your best deal on a sedan?",
                    "output": "I've got a 2021 Honda Civic EX in blue for $19,800 with 35k miles - great value! Also have a 2022 Toyota Camry SE for $24,500. Want to see either today 5:30 or tomorrow 10:00?\n{\"next_action\":\"offer_test_drive\",\"proposed_slots\":[\"2025-08-12T17:30:00-07:00\",\"2025-08-13T10:00:00-07:00\"],\"location_label\":\"Mission Bay Auto\",\"confidence\":0.88}"
                },
                {
                    "input": "Thanks, have a great day",
                    "output": "You too! Have a wonderful day. Feel free to reach out anytime if you need anything.\n{\"next_action\":\"end_conversation\",\"confidence\":0.95}"
                }
            ],
            "generic": [
                {
                    "input": "Any 3-row SUV under 30k?",
                    "output": "I've got a 2021 Honda Pilot EX-L for $28,500 and a 2020 Toyota Highlander for $29,200. Both have third rows and are under your budget. Want to check them out today 6:00 or tomorrow 9:30?\n{\"next_action\":\"offer_test_drive\",\"proposed_slots\":[\"2025-08-12T18:00:00-07:00\",\"2025-08-13T09:30:00-07:00\"],\"location_label\":\"Mission Bay Auto\",\"confidence\":0.82}"
                },
                {
                    "input": "Hey, my name is Aryan and I am interested in sedans.",
                    "output": "Hey Aryan! Nice to meet you. What's your budget range for a sedan?\n{\"next_action\":\"ask_clarify\",\"confidence\":0.8}"
                },
                {
                    "input": "Around 30k",
                    "output": "Perfect! I've got a 2022 Tiguan SE for $29,900 and a 2021 Honda CR-V for $25,500. Both are in great shape. Want to check them out today 6:00 or tomorrow 9:45?\n{\"next_action\":\"offer_test_drive\",\"proposed_slots\":[\"2025-08-12T18:00:00-07:00\",\"2025-08-13T09:45:00-07:00\"],\"location_label\":\"Mission Bay Auto\",\"confidence\":0.85}"
                },
                {
                    "input": "Under 25k",
                    "output": "Great! I've got a 2021 Honda Civic EX for $19,800 and a 2020 Toyota Corolla for $18,500. Both are reliable and under your budget. Want to see them today 6:00 or tomorrow 9:45?\n{\"next_action\":\"offer_test_drive\",\"proposed_slots\":[\"2025-08-12T18:00:00-07:00\",\"2025-08-13T09:45:00-07:00\"],\"location_label\":\"Mission Bay Auto\",\"confidence\":0.85}"
                },
                {
                    "input": "Goodbye, thanks for your help",
                    "output": "You're welcome! Have a great day. Don't hesitate to reach out if you need anything else.\n{\"next_action\":\"end_conversation\",\"confidence\":0.95}"
                }
            ]
        }
    
    def _get_relevant_examples(self, example_type: str) -> str:
        """Get relevant few-shot examples for the prompt."""
        examples = self.few_shot_examples.get(example_type, [])
        
        if not examples:
            return ""
        
        examples_text = "--- FEW-SHOT MICRO-EXAMPLES ---\n\n"
        for i, example in enumerate(examples, 1):
            examples_text += f"{chr(64+i)}) {example['input']}\n"
            examples_text += f"User: \"{example['input']}\"\n"
            examples_text += f"Assistant: \"{example['output']}\"\n\n"
        
        return examples_text 