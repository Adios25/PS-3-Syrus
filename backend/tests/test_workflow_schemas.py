"""
FLOW-JR-001: Unit tests for ChecklistItem Pydantic validation.
Tests cover: valid names, boundary lengths, special characters, description length.
"""
import pytest
from pydantic import ValidationError

from app.api.schemas import ChecklistItemCreate


class TestChecklistTitleValidation:
    def test_valid_title_minimum_length(self):
        """Title with exactly 3 chars should be accepted."""
        item = ChecklistItemCreate(title="Set", is_completed=False)
        assert item.title == "Set"

    def test_valid_title_maximum_length(self):
        """Title with exactly 100 chars should be accepted."""
        title = "A" + "a" * 99  # 100 chars, starts alphanumeric
        item = ChecklistItemCreate(title=title, is_completed=False)
        assert len(item.title) == 100

    def test_valid_title_with_underscores_hyphens_spaces(self):
        """Title with allowed special chars (_, -, space) should pass."""
        item = ChecklistItemCreate(title="Setup local-env_v2 guide", is_completed=False)
        assert item.title == "Setup local-env_v2 guide"

    def test_title_too_short_raises_error(self):
        """Title with fewer than 3 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChecklistItemCreate(title="ab", is_completed=False)
        errors = exc_info.value.errors()
        assert any("at least 3" in str(e["msg"]) for e in errors)

    def test_title_empty_string_raises_error(self):
        """Empty title should raise ValidationError (too short)."""
        with pytest.raises(ValidationError):
            ChecklistItemCreate(title="", is_completed=False)

    def test_title_too_long_raises_error(self):
        """Title with more than 100 chars should raise ValidationError."""
        long_title = "A" * 101
        with pytest.raises(ValidationError) as exc_info:
            ChecklistItemCreate(title=long_title, is_completed=False)
        errors = exc_info.value.errors()
        assert any("at most 100" in str(e["msg"]) for e in errors)

    def test_title_starting_with_special_char_raises_error(self):
        """Title starting with a special character should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChecklistItemCreate(title="!Bad title", is_completed=False)
        errors = exc_info.value.errors()
        assert any("alphanumeric" in str(e["msg"]) for e in errors)

    def test_title_with_script_tags_raises_error(self):
        """Title containing HTML/script characters should raise ValidationError."""
        with pytest.raises(ValidationError):
            ChecklistItemCreate(title="<script>alert(1)</script>", is_completed=False)

    def test_title_with_leading_trailing_whitespace_is_stripped(self):
        """Whitespace around title should be stripped before validation."""
        item = ChecklistItemCreate(title="  My Task  ", is_completed=False)
        assert item.title == "My Task"

    def test_title_boundary_exactly_3_chars(self):
        """Exactly 3-char title starting with alphanumeric must pass."""
        item = ChecklistItemCreate(title="A1b", is_completed=False)
        assert item.title == "A1b"


class TestChecklistDescriptionValidation:
    def test_description_none_is_allowed(self):
        """Optional description can be omitted."""
        item = ChecklistItemCreate(title="Valid Title", description=None, is_completed=False)
        assert item.description is None

    def test_description_within_limit(self):
        """Description under 500 chars should pass."""
        desc = "x" * 499
        item = ChecklistItemCreate(title="Valid Title", description=desc, is_completed=False)
        assert len(item.description) == 499

    def test_description_exactly_500_chars(self):
        """Description of exactly 500 chars should pass."""
        desc = "x" * 500
        item = ChecklistItemCreate(title="Valid Title", description=desc, is_completed=False)
        assert len(item.description) == 500

    def test_description_over_500_chars_raises_error(self):
        """Description over 500 chars should raise ValidationError."""
        desc = "x" * 501
        with pytest.raises(ValidationError) as exc_info:
            ChecklistItemCreate(title="Valid Title", description=desc, is_completed=False)
        errors = exc_info.value.errors()
        assert any("500" in str(e["msg"]) for e in errors)
