"""Sound profile discovery and loading."""

from mechkey.profiles.loader import discover_profiles, load_profile
from mechkey.profiles.models import Profile

__all__ = ["Profile", "discover_profiles", "load_profile"]
