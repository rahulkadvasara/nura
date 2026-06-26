"""
Nura - Prompt Loader Unit Tests
Verifies loading templates, validation errors for missing placeholders, and regex behavior on JSON braces.
"""

import pytest
import os
import tempfile
from app.prompts.loader import PromptLoader


def test_prompt_loader_get_version():
    """Verify registry version of templates"""
    loader = PromptLoader()
    assert loader.get_version("chat_prompt") == "1.0.0"
    assert loader.get_version("non_existent") == "1.0.0"


def test_prompt_loader_placeholder_regex_and_validation():
    """Verify regex ignores JSON double braces but parses single braces"""
    loader = PromptLoader()
    template = "Hello {name}, here is some JSON: {{'key': 'json_value'}} and metadata {meta_id}."
    
    placeholders = loader.get_placeholders(template)
    assert placeholders == {"name", "meta_id"}
    
    # Validation should succeed if we pass name and meta_id
    loader.validate_placeholders(template, {"name": "Alice", "meta_id": "123"})
    
    # Validation should fail if we miss name
    with pytest.raises(ValueError) as exc:
        loader.validate_placeholders(template, {"meta_id": "123"})
    assert "Missing required prompt placeholders: ['name']" in str(exc.value)


def test_prompt_loader_render():
    """Verify rendering replaces variables successfully"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy directories structure
        os.makedirs(os.path.join(tmpdir, "system"))
        os.makedirs(os.path.join(tmpdir, "templates"))
        
        system_path = os.path.join(tmpdir, "system", "test_sys.md")
        template_path = os.path.join(tmpdir, "templates", "test_tpl.md")
        
        with open(system_path, "w", encoding="utf-8") as f:
            f.write("System: {system_var}")
            
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("User: {user_var} and metadata {meta}")
            
        loader = PromptLoader(base_path=tmpdir)
        
        # Test render system prompt
        sys_rendered = loader.render("test_sys", {"system_var": "sys_val"}, is_system=True)
        assert sys_rendered == "System: sys_val"
        
        # Test render templates prompt
        tpl_rendered = loader.render("test_tpl", {"user_var": "user_val", "meta": "meta_val"}, is_system=False)
        assert tpl_rendered == "User: user_val and metadata meta_val"
        
        # Test cache hit
        assert "system:test_sys" in loader.cache
        assert "template:test_tpl" in loader.cache


def test_prompt_loader_file_not_found():
    """Verify template not found error path"""
    loader = PromptLoader()
    with pytest.raises(FileNotFoundError):
        loader.get_template("non_existent_prompt", is_system=True)
