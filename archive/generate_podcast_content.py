# ABOUTME: Complete podcast content generation workflow
# ABOUTME: Combines AI news fetching and transcript generation

import asyncio
import os
from datetime import datetime
from ai_news_fetcher import AINewsFetcher
from transcript_generator import TranscriptGenerator

async def generate_complete_podcast_content():
    """
    Complete workflow: fetch AI news and generate podcast transcript.
    
    Returns:
        Dictionary with results from both steps
    """
    print("🎙️  Starting complete podcast content generation...")
    print("=" * 60)
    
    # Step 1: Fetch AI news
    print("\n📰 Step 1: Fetching AI news from all sources...")
    fetcher = AINewsFetcher()
    
    news_summaries, digests_file = await fetcher.fetch_and_save_news()
    
    if not digests_file:
        print("❌ Failed to fetch AI news. Cannot proceed with transcript generation.")
        return {
            "success": False,
            "error": "Failed to fetch AI news",
            "news_summaries": news_summaries,
            "digests_file": "",
            "transcript_results": None
        }
    
    print(f"✅ AI news fetched and saved to: {digests_file}")
    
    # Step 2: Generate transcript
    print("\n📝 Step 2: Generating podcast transcript...")
    generator = TranscriptGenerator()
    
    transcript_results = await generator.generate_transcript_from_file(digests_file)
    
    if not transcript_results["success"]:
        print("❌ Failed to generate transcript.")
        return {
            "success": False,
            "error": "Failed to generate transcript",
            "news_summaries": news_summaries,
            "digests_file": digests_file,
            "transcript_results": transcript_results
        }
    
    print(f"✅ Transcript generated and saved to: {transcript_results['saved_file']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 PODCAST CONTENT GENERATION COMPLETE!")
    print("=" * 60)
    
    # News summary
    successful_news_sources = sum(1 for content in news_summaries.values() if content is not None)
    print(f"📊 News Sources: {successful_news_sources}/3 successful")
    
    # Transcript summary
    validation = transcript_results["validation"]
    print(f"📝 Transcript: {validation['word_count']} words, {validation['character_count']} characters")
    print(f"✅ Valid: {'Yes' if validation['is_valid'] else 'No'}")
    
    if validation["warnings"]:
        print(f"⚠️  Warnings: {len(validation['warnings'])}")
        for warning in validation["warnings"][:3]:  # Show first 3 warnings
            print(f"   - {warning}")
    
    return {
        "success": True,
        "error": None,
        "news_summaries": news_summaries,
        "digests_file": digests_file,
        "transcript_results": transcript_results
    }

async def main():
    """Main function to run the complete podcast content generation."""
    try:
        results = await generate_complete_podcast_content()
        
        if results["success"]:
            print(f"\n🚀 Ready for podcast creation!")
            print(f"📄 Transcript file: {results['transcript_results']['saved_file']}")
            print(f"📰 News digests: {results['digests_file']}")
            print(f"\n💡 Next step: Run podcast_creator.py to generate audio")
        else:
            print(f"\n❌ Podcast content generation failed: {results['error']}")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
