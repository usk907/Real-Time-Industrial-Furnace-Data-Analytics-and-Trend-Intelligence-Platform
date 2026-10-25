"""
Unit tests for Generator Tag Dictionary and Random Walk logic.
"""
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "generator"))

from tags import TAGS, TAG_MAP
from generator import FurnaceDataGenerator

def test_tag_count():
    assert len(TAGS) == 60, f"Expected 60 tags, got {len(TAGS)}"

def test_tag_bounds():
    for tag in TAGS:
        assert tag["min"] <= tag["max"], f"Tag {tag['name']} has min > max"
        assert tag["min"] <= tag["start"] <= tag["max"], f"Tag {tag['name']} start value outside min/max"
        assert tag["step"] > 0, f"Tag {tag['name']} has non-positive step"

def test_generator_state_progression():
    gen = FurnaceDataGenerator()
    initial_cumulative = {
        t["name"]: gen.state[t["name"]] 
        for t in TAGS if t.get("cumulative")
    }
    
    # Advance state 5 times
    for _ in range(5):
        gen.advance_state()

    # Cumulative tags must only increase
    for name, prev_val in initial_cumulative.items():
        assert gen.state[name] > prev_val, f"Cumulative tag {name} did not increase"

if __name__ == "__main__":
    test_tag_count()
    test_tag_bounds()
    test_generator_state_progression()
    print("All generator tag tests passed successfully!")
