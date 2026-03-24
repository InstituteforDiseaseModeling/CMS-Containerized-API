import pytest
import sys
from pathlib import Path

# Add parent directory to path to import emodl_validator
sys.path.insert(0, str(Path(__file__).parent.parent))
from emodl_validator import is_valid_emodl


def test_valid_emodl():
    valid_emodl = """
    (import (rnrs) (emodl cmslib))

    (start-model "test_model")

    (species S 1000)
    (species I 10)

    (param beta 0.3)
    (param gamma 0.1)

    (reaction infection (S) (I) (/ (* beta S I) (+ S I)) 0)
    (reaction recovery (I) () (* gamma I) 0)

    (observe S S)
    (observe I I)

    (end-model)
    """
    is_valid, error = is_valid_emodl(valid_emodl)
    assert is_valid
    assert error is None


@pytest.mark.parametrize("filename", ["seir.emodl", "garki.emodl", "polio-surveillance.emodl"])
def test_specific_model_files(filename):
    """Test specific known model files individually"""
    models_dir = Path(__file__).parent.parent / "models"
    emodl_file = models_dir / filename
    
    assert emodl_file.exists(), f"Expected model file {filename} not found"
    
    content = emodl_file.read_text()
    is_valid, error = is_valid_emodl(content)
    assert is_valid, f"{filename} should be valid but validation failed"
    assert error is None, f"{filename} should have no validation error but got: {error}"



def test_invalid_emodl_parens():
    invalid_emodl = """
    import (rnrs) (emodl cmslib))

    (start-model "test_model")

    (species S 1000)
    (species I 10)

    (param beta 0.3)
    (param gamma 0.1)

    (reaction infection (S) (I) (/ (* beta S I) (+ S I)) 0)
    (reaction recovery (I) () (* gamma I) 0)

    (observe S S)
    (observe I I)

    (end-model)
    """
    is_valid, error = is_valid_emodl(invalid_emodl)
    assert not is_valid
    assert "Unmatched closing parenthesis" in error


def test_invalid_empty_content():
    """Test empty EMODL content"""
    is_valid, error = is_valid_emodl("")
    assert not is_valid
    assert error == "Empty EMODL content"


def test_invalid_missing_start_model():
    """Test EMODL missing start-model declaration"""
    invalid_emodl = """
    (import (rnrs) (emodl cmslib))

    (species S 1000)
    (species I 10)

    (end-model)
    """
    is_valid, error = is_valid_emodl(invalid_emodl)
    assert not is_valid
    assert "Missing (start-model ...) declaration" in error


def test_invalid_missing_end_model():
    """Test EMODL missing end-model declaration"""
    invalid_emodl = """
    (import (rnrs) (emodl cmslib))

    (start-model "test_model")

    (species S 1000)
    (species I 10)
    """
    is_valid, error = is_valid_emodl(invalid_emodl)
    assert not is_valid
    assert "Missing (end-model) declaration" in error


def test_invalid_no_species():
    """Test EMODL with no species declarations"""
    invalid_emodl = """
    (import (rnrs) (emodl cmslib))

    (start-model "test_model")

    (param beta 0.3)

    (end-model)
    """
    is_valid, error = is_valid_emodl(invalid_emodl)
    assert not is_valid
    assert "Missing At least one species declaration" in error


def test_invalid_malformed_syntax():
    """Test EMODL with malformed syntax"""
    invalid_emodl = """
    (import (rnrs) (emodl cmslib))

    (start-model "test_model")

    (species S 1000)
    (species)

    (end-model)
    """
    is_valid, error = is_valid_emodl(invalid_emodl)
    assert not is_valid
    assert "Malformed syntax: Empty species declaration" in error


def test_invalid_unbalanced_parens_missing_closing():
    """Test EMODL with missing closing parenthesis"""
    invalid_emodl = """
    (import (rnrs) (emodl cmslib)

    (start-model "test_model")

    (species S 1000)

    (end-model)
    """
    is_valid, error = is_valid_emodl(invalid_emodl)
    assert not is_valid
    assert "Unbalanced parentheses" in error