# ABOUTME: Unit tests for enhanced text sanitization
# ABOUTME: Tests apostrophe removal and TTS optimization for Microsoft TTS

import pytest
from podcast_creator import sanitize_text

class TestTextSanitization:
    """Test cases for the enhanced text sanitization function."""
    
    def test_apostrophe_removal_basic(self):
        """Test basic apostrophe removal."""
        text = "South Africa's problems"
        result = sanitize_text(text)
        assert result == "South Africas problems"
    
    def test_apostrophe_removal_curly(self):
        """Test removal of curly apostrophes."""
        text = "South Africa's problems"
        result = sanitize_text(text)
        assert result == "South Africas problems"
    
    def test_apostrophe_removal_grave(self):
        """Test removal of grave accent apostrophes."""
        text = "South Africa`s problems"
        result = sanitize_text(text)
        assert result == "South Africas problems"
    
    def test_contraction_expansion_cant(self):
        """Test expansion of 'can't' contraction."""
        text = "We cant do this"
        result = sanitize_text(text)
        assert result == "We cannot do this"
    
    def test_contraction_expansion_wont(self):
        """Test expansion of 'won't' contraction."""
        text = "They wont come"
        result = sanitize_text(text)
        assert result == "They will not come"
    
    def test_contraction_expansion_dont(self):
        """Test expansion of 'don't' contraction."""
        text = "I dont know"
        result = sanitize_text(text)
        assert result == "I do not know"
    
    def test_contraction_expansion_isnt(self):
        """Test expansion of 'isn't' contraction."""
        text = "This isnt right"
        result = sanitize_text(text)
        assert result == "This is not right"
    
    def test_contraction_expansion_arent(self):
        """Test expansion of 'aren't' contraction."""
        text = "They arent here"
        result = sanitize_text(text)
        assert result == "They are not here"
    
    def test_contraction_expansion_wasnt(self):
        """Test expansion of 'wasn't' contraction."""
        text = "It wasnt there"
        result = sanitize_text(text)
        assert result == "It was not there"
    
    def test_contraction_expansion_werent(self):
        """Test expansion of 'weren't' contraction."""
        text = "They werent ready"
        result = sanitize_text(text)
        assert result == "They were not ready"
    
    def test_contraction_expansion_hasnt(self):
        """Test expansion of 'hasn't' contraction."""
        text = "He hasnt arrived"
        result = sanitize_text(text)
        assert result == "He has not arrived"
    
    def test_contraction_expansion_havent(self):
        """Test expansion of 'haven't' contraction."""
        text = "We havent seen it"
        result = sanitize_text(text)
        assert result == "We have not seen it"
    
    def test_contraction_expansion_hadnt(self):
        """Test expansion of 'hadn't' contraction."""
        text = "I hadnt known"
        result = sanitize_text(text)
        assert result == "I had not known"
    
    def test_contraction_expansion_wouldnt(self):
        """Test expansion of 'wouldn't' contraction."""
        text = "She wouldnt go"
        result = sanitize_text(text)
        assert result == "She would not go"
    
    def test_contraction_expansion_couldnt(self):
        """Test expansion of 'couldn't' contraction."""
        text = "I couldnt help"
        result = sanitize_text(text)
        assert result == "I could not help"
    
    def test_contraction_expansion_shouldnt(self):
        """Test expansion of 'shouldn't' contraction."""
        text = "You shouldnt do that"
        result = sanitize_text(text)
        assert result == "You should not do that"
    
    def test_contraction_expansion_theyre(self):
        """Test expansion of 'they're' contraction."""
        text = "Theyre coming"
        result = sanitize_text(text)
        assert result == "They are coming"
    
    def test_contraction_expansion_were(self):
        """Test that 'were' is not expanded (ambiguous - could be past tense or contraction)."""
        text = "Were going now"
        result = sanitize_text(text)
        assert result == "Were going now"  # Should remain unchanged due to ambiguity
    
    def test_contraction_expansion_youre(self):
        """Test expansion of 'you're' contraction."""
        text = "Youre right"
        result = sanitize_text(text)
        assert result == "You are right"
    
    def test_contraction_expansion_its(self):
        """Test expansion of 'it's' contraction."""
        text = "Its working"
        result = sanitize_text(text)
        assert result == "It is working"
    
    def test_contraction_expansion_thats(self):
        """Test expansion of 'that's' contraction."""
        text = "Thats correct"
        result = sanitize_text(text)
        assert result == "That is correct"
    
    def test_contraction_expansion_theres(self):
        """Test expansion of 'there's' contraction."""
        text = "Theres a problem"
        result = sanitize_text(text)
        assert result == "There is a problem"
    
    def test_contraction_expansion_heres(self):
        """Test expansion of 'here's' contraction."""
        text = "Heres the answer"
        result = sanitize_text(text)
        assert result == "Here is the answer"
    
    def test_contraction_expansion_case_insensitive(self):
        """Test that contraction expansion is case-insensitive."""
        text = "CANT you see"
        result = sanitize_text(text)
        assert result == "Cannot you see"  # Preserves capitalization
    
    def test_contraction_expansion_word_boundaries(self):
        """Test that contractions are only expanded at word boundaries."""
        text = "cantilever bridge"
        result = sanitize_text(text)
        assert result == "cantilever bridge"  # Should not expand "cant" in "cantilever"
    
    def test_multiple_contractions(self):
        """Test text with multiple contractions."""
        text = "I cant believe theyre not here"
        result = sanitize_text(text)
        assert result == "I cannot believe they are not here"
    
    def test_apostrophes_and_contractions_combined(self):
        """Test text with both apostrophes and contractions."""
        text = "South Africa's government cant solve the country's problems"
        result = sanitize_text(text)
        assert result == "South Africas government cannot solve the countrys problems"
    
    def test_curly_quotes_replacement(self):
        """Test replacement of curly quotes with straight quotes."""
        text = "He said \"hello\" and \"goodbye\""
        result = sanitize_text(text)
        assert result == 'He said "hello" and "goodbye"'
    
    def test_em_dash_replacement(self):
        """Test replacement of em dashes with hyphens."""
        text = "This is important—very important"
        result = sanitize_text(text)
        assert result == "This is important-very important"
    
    def test_ellipsis_replacement(self):
        """Test replacement of ellipsis with three dots."""
        text = "Wait for it…"
        result = sanitize_text(text)
        assert result == "Wait for it..."
    
    def test_emoji_removal(self):
        """Test removal of emojis and non-ASCII characters."""
        text = "Hello 😀 world 🌍"
        result = sanitize_text(text)
        assert result == "Hello world"
    
    def test_newline_replacement(self):
        """Test replacement of newlines with spaces."""
        text = "Line 1\nLine 2\n\nLine 3"
        result = sanitize_text(text)
        assert result == "Line 1 Line 2 Line 3"
    
    def test_multiple_spaces_cleanup(self):
        """Test cleanup of multiple spaces."""
        text = "This    has    multiple    spaces"
        result = sanitize_text(text)
        assert result == "This has multiple spaces"
    
    def test_complex_text_sanitization(self):
        """Test complex text with multiple issues."""
        text = """South Africa's government can't solve the country's problems.
        They're not doing enough—it's a crisis!
        "We need action," said the minister.
        The situation is getting worse…"""
        
        result = sanitize_text(text)
        expected = 'South Africas government cannot solve the countrys problems. They are not doing enough-it is a crisis! "We need action," said the minister. The situation is getting worse...'
        
        assert result == expected
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = sanitize_text("")
        assert result == ""
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only string."""
        result = sanitize_text("   \n\t   ")
        assert result == ""
    
    def test_no_changes_needed(self):
        """Test text that doesn't need any changes."""
        text = "This is clean text without any issues"
        result = sanitize_text(text)
        assert result == text
    
    def test_south_african_news_example(self):
        """Test with a realistic South African news example."""
        text = """South Africa's economy can't recover without government intervention.
        The country's unemployment rate isn't improving.
        "We're facing a crisis," said the minister.
        The situation won't get better without action."""
    
        result = sanitize_text(text)
        expected = """South Africas economy cannot recover without government intervention. The countrys unemployment rate is not improving. "Were facing a crisis," said the minister. The situation will not get better without action."""
    
        assert result == expected

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
