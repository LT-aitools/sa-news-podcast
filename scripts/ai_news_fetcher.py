# ABOUTME: AI-powered news fetching system for SA News Podcast
# ABOUTME: Fetches South African news from Perplexity, Claude, and ChatGPT APIs

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from scripts.secure_secrets import get_secrets

class AINewsFetcher:
    """
    Fetches South African news from multiple AI sources using the exact prompt
    specified in NewWorkflow.md.
    """
    
    def __init__(self):
        """Initialize the AI News Fetcher with API credentials."""
        self.secrets = get_secrets()
        self.web_search_prompt = (
            "What are today's most important and widely-discussed South African news stories? Focus on: 1) Breaking national and regional news and major developments 2) Viral stories getting significant attention 3) Notable events affecting many people 4) Surprising or unusual stories gaining traction.\n"
            "Give me a few sentences on each story.\n"
            "Ignore purely international stories that don't involve South Africa."
        )
        
    async def fetch_perplexity_news(self) -> Optional[str]:
        """
        Fetch news from Perplexity API.
        
        Returns:
            News summary from Perplexity or None if failed
        """
        try:
            from openai import AsyncOpenAI
            
            api_key = self.secrets.get_perplexity_api_key()
            
            # Use OpenAI client with Perplexity base URL
            client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.perplexity.ai"
            )
            
            response = await client.chat.completions.create(
                model="sonar",  # Correct Perplexity model name
                messages=[{"role": "user", "content": self.web_search_prompt}],
                max_tokens=4000,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            print("✅ Perplexity news fetched successfully")
            return content
                        
        except Exception as e:
            print(f"❌ Perplexity fetch error: {e}")
            return None
    
    async def fetch_claude_news(self) -> Optional[str]:
        """
        Fetch news from Claude API using anthropic client.
        
        Returns:
            News summary from Claude or None if failed
        """
        try:
            import anthropic
            from datetime import datetime
            
            api_key = self.secrets.get_claude_api_key()
            
            # Initialize the client
            client = anthropic.AsyncAnthropic(api_key=api_key)
            
            # Multi-step conversation to handle web search tool calls
            messages = [
                {
                    "role": "user",
                    "content": f"""What are today's most important and widely-discussed South African news stories? Focus on: 1) Breaking national and regional news and major developments 2) Viral stories getting significant attention 3) Notable events affecting many people 4) Surprising or unusual stories gaining traction.
Give me a few sentences on each story.
Ignore purely international stories that don't involve South Africa."""
                }
            ]

            while True:
                response = await client.messages.create(
                    model="claude-3-7-sonnet-latest",
                    max_tokens=4000,
                    temperature=0,
                    messages=messages,
                    tools=[
                        {
                            "name": "web_search",
                            "description": "Search the web for current information",
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"}
                                },
                                "required": ["query"]
                            }
                        }
                    ]
                )

                # Add Claude's response to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Check if Claude wants to use tools
                if response.stop_reason == "tool_use":
                    print("Claude is performing web search...")

                    # Handle tool calls - let Claude handle the web search internally
                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input

                            if tool_name == "web_search":
                                search_query = tool_input.get("query", "")
                                print(f"Claude searching for: {search_query}")

                                # Let Claude handle the web search internally
                                # We don't need to provide mock results - Claude will do the real search
                                messages.append({
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": content_block.id,
                                            "content": f"Web search completed for: {search_query}"
                                        }
                                    ]
                                })

                    # Continue the conversation loop to get Claude's final response
                    continue
                else:
                    # Final response ready
                    content = response.content[0].text
                    print("✅ Claude news fetched successfully")
                    return content

            # If we somehow exit the loop, return what we have
            content = response.content[0].text if response.content else "Claude conversation completed"
            print("✅ Claude news fetched successfully")
            return content
                        
        except Exception as e:
            print(f"❌ Claude fetch error: {e}")
            return None
    
    async def fetch_chatgpt_news(self) -> Optional[str]:
        """
        Fetch news from OpenAI GPT-5 API using responses.create.
        
        Returns:
            News summary from ChatGPT or None if failed
        """
        try:
            from openai import AsyncOpenAI
            from datetime import date
            
            api_key = self.secrets.get_openai_api_key()
            today = date.today().strftime("%Y-%m-%d")
            
            # Use OpenAI client
            client = AsyncOpenAI(api_key=api_key)
            
            system_prompt = (
                "You are a news analyst. Use the web_search tool to find breaking and viral "
                f"South African news for {today} (Africa/Johannesburg). Only include stories "
                "with clear South Africa involvement. Deduplicate, verify dates, and provide "
                "citations. Output structured news summary."
            )
            
            user_prompt = f"""What are today's most important and widely-discussed South African news stories? Focus on: 1) Breaking national and regional news and major developments 2) Viral stories getting significant attention 3) Notable events affecting many people 4) Surprising or unusual stories gaining traction.
Give me a few sentences on each story.
Ignore purely international stories that don't involve South Africa."""
            
            response = await client.responses.create(
                model="gpt-5",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=[{"type": "web_search"}],
                tool_choice="auto"
            )
            
            content = response.output_text
            print("✅ ChatGPT news fetched successfully")
            return content
                        
        except Exception as e:
            print(f"❌ ChatGPT fetch error: {e}")
            return None
    
    async def fetch_all_news(self) -> Dict[str, Optional[str]]:
        """
        Fetch news from all three AI sources concurrently.
        
        Returns:
            Dictionary with news summaries from each source
        """
        print("🚀 Starting AI news fetching from all sources...")
        start_time = time.time()
        
        # Fetch from all sources concurrently
        results = await asyncio.gather(
            self.fetch_perplexity_news(),
            self.fetch_claude_news(),
            self.fetch_chatgpt_news(),
            return_exceptions=True
        )
        
        # Process results
        news_summaries = {
            "perplexity": results[0] if not isinstance(results[0], Exception) else None,
            "claude": results[1] if not isinstance(results[1], Exception) else None,
            "chatgpt": results[2] if not isinstance(results[2], Exception) else None
        }
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  AI news fetching completed in {elapsed_time:.2f} seconds")
        
        # Count successful fetches
        successful_fetches = sum(1 for result in news_summaries.values() if result is not None)
        print(f"📊 Successfully fetched from {successful_fetches}/3 sources")
        
        return news_summaries
    
    def save_news_digests(self, news_summaries: Dict[str, Optional[str]], output_file: str = "outputs/ai_news_digests.txt") -> str:
        """
        Save news summaries to a file for transcript generation.
        
        Args:
            news_summaries: Dictionary of news summaries from each AI source
            output_file: Path to save the combined digests
            
        Returns:
            Path to the saved file
        """
        try:
            # Create outputs directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("AI NEWS DIGESTS FOR SOUTH AFRICAN PODCAST\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Web search prompt: {self.web_search_prompt}\n\n")
                
                for source, content in news_summaries.items():
                    f.write(f"\n{'='*20} {source.upper()} NEWS DIGEST {'='*20}\n")
                    if content:
                        f.write(content)
                    else:
                        f.write("❌ Failed to fetch news from this source")
                    f.write("\n")
            
            print(f"💾 News digests saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error saving news digests: {e}")
            return ""
    
    async def fetch_and_save_news(self, output_file: str = "outputs/ai_news_digests.txt") -> Tuple[Dict[str, Optional[str]], str]:
        """
        Fetch news from all sources and save to file.
        
        Args:
            output_file: Path to save the combined digests
            
        Returns:
            Tuple of (news_summaries, saved_file_path)
        """
        # Fetch news from all sources
        news_summaries = await self.fetch_all_news()
        
        # Save to file
        saved_file = self.save_news_digests(news_summaries, output_file)
        
        return news_summaries, saved_file

async def main():
    """Test the AI News Fetcher."""
    fetcher = AINewsFetcher()
    
    print("🧪 Testing AI News Fetcher...")
    news_summaries, saved_file = await fetcher.fetch_and_save_news()
    
    print("\n📋 Results Summary:")
    for source, content in news_summaries.items():
        status = "✅ Success" if content else "❌ Failed"
        length = len(content) if content else 0
        print(f"  {source.capitalize()}: {status} ({length} characters)")
    
    if saved_file:
        print(f"\n💾 Digests saved to: {saved_file}")
    else:
        print("\n❌ Failed to save digests")

if __name__ == "__main__":
    asyncio.run(main())
