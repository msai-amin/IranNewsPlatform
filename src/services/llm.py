"""Tiered LLM client for cost-efficient model selection."""

import json
from typing import Optional, Literal, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import Config


def _extract_text_content(content: Union[str, list]) -> str:
    """Extract text from LLM response content.
    
    Handles both string and list responses (some models return content blocks).
    
    Args:
        content: Response content - may be string or list of content blocks
        
    Returns:
        Extracted text as string
    """
    if isinstance(content, str):
        return content.strip()
    
    if isinstance(content, list):
        # Content blocks: extract text from each block
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                # Handle {"type": "text", "text": "..."} format
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(block["text"])
                elif "text" in block:
                    text_parts.append(block["text"])
            elif hasattr(block, "text"):
                text_parts.append(block.text)
        return " ".join(text_parts).strip()
    
    # Fallback: convert to string
    return str(content).strip()


class TieredLLMClient:
    """Manages tiered LLM access with automatic model selection."""
    
    def __init__(self):
        """Initialize LLM clients."""
        self.gemini_scout = ChatGoogleGenerativeAI(
            model=Config.MODEL_SCOUT,
            google_api_key=Config.GOOGLE_AI_API_KEY,
            temperature=0.1
        )
        self.gemini_flash = ChatGoogleGenerativeAI(
            model=Config.MODEL_TRANSLATOR,
            google_api_key=Config.GOOGLE_AI_API_KEY,
            temperature=0.2
        )
        self.gemini_pro = ChatGoogleGenerativeAI(
            model=Config.MODEL_EDITOR,
            google_api_key=Config.GOOGLE_AI_API_KEY,
            temperature=0.3
        )
        
        # Claude fallback for editor
        self.claude_sonnet = None
        if Config.ANTHROPIC_API_KEY:
            self.claude_sonnet = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                anthropic_api_key=Config.ANTHROPIC_API_KEY,
                temperature=0.3
            )
    
    async def scout_classify(self, text: str) -> dict:
        """Use Scout model (Flash-Lite) for news classification.
        
        Args:
            text: Raw Persian text to classify
            
        Returns:
            dict with 'is_news' boolean
        """
        prompt = """You are a news filter. Analyze this Persian text and determine if it is political, economic, or social news about Iran.

Rules:
- Ignore advertisements, sports scores, cryptic poetry, personal messages
- Focus on news about Iran: politics, economy, society, international relations
- Return ONLY valid JSON

Text to analyze:
{text}

Return JSON format: {{"is_news": true/false}}"""

        try:
            response = await self.gemini_scout.ainvoke([
                HumanMessage(content=prompt.format(text=text))
            ])
            
            # Extract JSON from response
            content = _extract_text_content(response.content)
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return {"is_news": bool(result.get("is_news", False))}
        except Exception as e:
            # On error, default to False (conservative)
            return {"is_news": False, "error": str(e)}
    
    async def translate_persian(self, persian_text: str) -> str:
        """Use Translator model (Flash) for literal Persian-English translation.
        
        Args:
            persian_text: Raw Persian text
            
        Returns:
            Literal English translation
        """
        prompt = """Translate this Persian text into English. Follow these critical rules:

1. Do NOT summarize - translate literally word-by-word where possible
2. Explicitly identify implied subjects (Persian drops pronouns - add them back)
3. Preserve the original tone and word choice exactly:
   - If source uses "rioters" instead of "protesters", keep "rioters"
   - If source uses "martyrs", keep "martyrs"
   - Maintain the bias and perspective of the source
4. Do not add context or explanations
5. Maintain sentence structure

Persian text:
{text}

English translation:"""

        try:
            response = await self.gemini_flash.ainvoke([
                HumanMessage(content=prompt.format(text=persian_text))
            ])
            return _extract_text_content(response.content)
        except Exception as e:
            return f"[Translation error: {str(e)}]"
    
    async def extract_claims(self, english_text: str) -> list[str]:
        """Use Analyst model (Flash) to extract factual claims.
        
        Args:
            english_text: Translated English text
            
        Returns:
            List of factual claims to verify
        """
        prompt = """Extract the key factual claims from this news text. Focus on:
- Specific events, dates, locations
- Numbers, statistics, quotes
- Statements that can be verified or contradicted

Return a JSON array of claims, one per line.

Text:
{text}

Return JSON format: {{"claims": ["claim1", "claim2", ...]}}"""

        try:
            response = await self.gemini_flash.ainvoke([
                HumanMessage(content=prompt.format(text=english_text))
            ])
            
            content = _extract_text_content(response.content)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return result.get("claims", [])
        except Exception as e:
            return []
    
    async def generate_news_copy(
        self,
        english_translation: str,
        fact_check_notes: list[str],
        fact_check_status: str
    ) -> str:
        """Use Editor model (Pro or Claude) to generate AP Style news copy.
        
        Args:
            english_translation: Literal translation
            fact_check_notes: Notes from fact-checking
            fact_check_status: Status from fact-checking
            
        Returns:
            AP Style news article
        """
        notes_text = "\n".join(f"- {note}" for note in fact_check_notes) if fact_check_notes else "None"
        
        prompt = """Write a journalistic news piece based on the following translation and fact-check notes. 

Requirements:
- Adhere to AP Style guidelines
- If claims are unverified, attribute them properly: "State media claims..." or "According to..."
- If status is 'propaganda', note skepticism: "Unverified claims suggest..."
- Maintain journalistic objectivity
- Include relevant context

Translation:
{translation}

Fact-check status: {status}
Fact-check notes:
{notes}

News article:"""

        try:
            # Try Gemini Pro first, fallback to Claude
            model = self.gemini_pro
            if Config.MODEL_EDITOR == "claude-3-5-sonnet" and self.claude_sonnet:
                model = self.claude_sonnet
            
            response = await model.ainvoke([
                SystemMessage(content="You are an experienced journalist writing for an international news outlet."),
                HumanMessage(content=prompt.format(
                    translation=english_translation,
                    status=fact_check_status,
                    notes=notes_text
                ))
            ])
            return _extract_text_content(response.content)
        except Exception as e:
            return f"[Editor error: {str(e)}]"
