#!/usr/bin/env python3
"""
ax_search.py - Element search and filtering for macOS Accessibility APIs

Provides high-level search and navigation functions for finding UI elements
within an application's accessibility tree. Built on top of ax_core.py.

Functions:
    - query_elements(app_element, filters): Search tree for matching elements
    - parse_element_path(path): Navigate to element via path string
    - build_element_path(element): Build path string from element to root

Requirements:
    - Python 3.9+
    - PyObjC (Cocoa, ApplicationServices)
    - ax_core module

Author: AX Helper Team
License: MIT
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Optional

from ax_core import (
    get_attribute,
    get_children,
    get_attribute_names,
    serialize_element,
    kAXRoleAttribute,
    kAXTitleAttribute,
    kAXDescriptionAttribute,
    kAXValueAttribute,
    kAXIdentifierAttribute,
    kAXChildrenAttribute,
    kAXParentAttribute,
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Type aliases
AXUIElement = Any


def query_elements(
    app_element: AXUIElement,
    filters: dict[str, str],
    max_depth: int = 50,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """
    Search the accessibility tree for elements matching the given filters.
    
    Performs a breadth-first or depth-first search through the element
    hierarchy to find all elements that match the specified criteria.
    
    Args:
        app_element: The AXUIElement for the application (root of search).
        filters: Dictionary of attribute filters.
                 Supported keys: role, title, description, value, identifier, subrole
                 Values are matched as case-insensitive substrings.
        max_depth: Maximum depth to traverse (default 50).
        max_results: Maximum number of results to return (default 100).
    
    Returns:
        List of dictionaries, each containing:
            - role: The element's AXRole
            - title: The element's title/label
            - description: The element's description
            - value: The element's value (if applicable)
            - enabled: Boolean indicating if element is enabled
            - focused: Boolean indicating if element has focus
            - position: Dict with 'x' and 'y' coordinates (if available)
            - size: Dict with 'width' and 'height' (if available)
            - path: Navigable path string (e.g., "window[0].toolbar[0].button[3]")
            - identifier: The element's identifier (if available)
    
    Example:
        >>> from ax_core import get_app_by_name
        >>> app = get_app_by_name("Safari")
        >>> results = query_elements(app, {"role": "button", "title": "Submit"})
        >>> for elem in results:
        ...     print(f"Found: {elem['path']}")
    """
    if app_element is None:
        logger.warning("Cannot query None app element")
        return []
    
    # Empty filters = match all elements (useful for tree dumps)
    # If filters dict is empty, we'll still traverse but match everything
    
    results: list[dict[str, Any]] = []
    visited: set[int] = set()  # Track visited element IDs to avoid circular refs
    deadline = time.monotonic() + 30.0  # 30-second timeout
    
    # Normalize filters - convert "role=button" style to dict
    normalized_filters = _normalize_filters(filters)
    
    # Start recursive search from app element
    _search_recursive(
        element=app_element,
        filters=normalized_filters,
        current_depth=0,
        max_depth=max_depth,
        max_results=max_results,
        results=results,
        path_prefix="",
        visited=visited,
        deadline=deadline,
    )
    
    logger.info(f"Found {len(results)} matching elements")
    return results


def _search_recursive(
    element: AXUIElement,
    filters: dict[str, str],
    current_depth: int,
    max_depth: int,
    max_results: int,
    results: list[dict[str, Any]],
    path_prefix: str,
    visited: set[int] | None = None,
    deadline: float = 0,
) -> None:
    """
    Recursively search for matching elements.
    
    Internal function that performs depth-first traversal.
    
    Args:
        element: Current element to check.
        filters: Normalized filter dictionary.
        current_depth: Current traversal depth.
        max_depth: Maximum depth to traverse.
        max_results: Maximum results to collect.
        results: Results list to append to.
        path_prefix: Current path string prefix.
        visited: Set of visited element IDs (circular ref protection).
        deadline: Monotonic timestamp to stop at (timeout protection).
    """
    # Stop if timed out
    if deadline and time.monotonic() > deadline:
        logger.warning("Search timed out after 30 seconds")
        return
    
    # Stop if we've reached max results
    if len(results) >= max_results:
        return
    
    # Stop if we've reached max depth
    if current_depth > max_depth:
        return
    
    # Circular reference protection
    elem_id = id(element)
    if visited is not None:
        if elem_id in visited:
            return
        visited.add(elem_id)
    
    # Check if current element matches filters
    if _element_matches_filters(element, filters):
        # Use path_prefix directly (path is built during traversal)
        element_path = path_prefix
        
        # Serialize the element
        serialized = serialize_element(element)
        if serialized:
            serialized["path"] = element_path
            results.append(serialized)
            
            logger.debug(f"Matched element: {element_path}")
    
    # Get children and continue search
    children = get_children(element)
    if not children:
        return
    
    # Build child path prefix
    # Use per-role index counters (not raw enumeration index)
    role_counters: dict[str, int] = {}
    
    for child in children:
        # Get each child's role BEFORE building its path
        child_role = get_attribute(child, kAXRoleAttribute)
        child_role_str = str(child_role).lower() if child_role else "element"
        
        # Strip "AX" prefix to match spec examples: window[0] not axwindow[0]
        child_role_str = child_role_str.replace('ax', '', 1)
        
        # Use per-role index counter
        role_idx = role_counters.get(child_role_str, 0)
        role_counters[child_role_str] = role_idx + 1
        
        # Construct path for child: parentRole[parentIndex].childRole[childIndex]
        if current_depth == 0:
            child_path = f"{child_role_str}[{role_idx}]"
        else:
            child_path = f"{path_prefix}.{child_role_str}[{role_idx}]"
        
        _search_recursive(
            element=child,
            filters=filters,
            current_depth=current_depth + 1,
            max_depth=max_depth,
            max_results=max_results,
            results=results,
            path_prefix=child_path,
            visited=visited,
            deadline=deadline,
        )


def _element_matches_filters(element: AXUIElement, filters: dict[str, str]) -> bool:
    """
    Check if an element matches all the given filters.
    
    Args:
        element: The AXUIElement to check.
        filters: Dictionary of attribute->value filters.
    
    Returns:
        True if element matches all filters, False otherwise.
    """
    if not filters:
        return True
    
    # Map filter keys to AX attribute names
    attr_map = {
        "role": kAXRoleAttribute,
        "title": kAXTitleAttribute,
        "description": kAXDescriptionAttribute,
        "value": kAXValueAttribute,
        "identifier": kAXIdentifierAttribute,
        "subrole": "AXSubrole",
    }
    
    for filter_key, filter_value in filters.items():
        # Get the corresponding AX attribute
        ax_attr = attr_map.get(filter_key, filter_key)
        
        # Get the element's attribute value
        attr_value = get_attribute(element, ax_attr)
        
        # Convert to string for comparison
        if attr_value is None:
            return False
        
        attr_str = str(attr_value).lower()
        filter_str = filter_value.lower()
        
        # Check if filter value is in the attribute (substring match)
        if filter_str not in attr_str:
            return False
    
    return True


def _normalize_filters(filters: dict[str, str] | list[str]) -> dict[str, str]:
    """
    Normalize filters from various input formats.
    
    Args:
        filters: Either a dict or list of "key=value" strings.
    
    Returns:
        Normalized dictionary of key->value filters.
    
    Example:
        >>> _normalize_filters({"role": "button"})
        {'role': 'button'}
        >>> _normalize_filters(["role=button", "title=Submit"])
        {'role': 'button', 'title': 'Submit'}
    """
    if isinstance(filters, dict):
        return {k: str(v) for k, v in filters.items()}
    
    # Handle list format ["role=button", "title=Submit"]
    normalized = {}
    for item in filters:
        if isinstance(item, str) and "=" in item:
            key, value = item.split("=", 1)
            normalized[key.strip()] = value.strip()
        elif isinstance(item, dict):
            normalized.update({k: str(v) for k, v in item.items()})
    
    return normalized


def parse_element_path(
    app_element: AXUIElement,
    path: str,
) -> Optional[AXUIElement]:
    """
    Parse a path string and navigate to the specific element.
    
    Path format: "window[0].toolbar[0].button[3]"
    - Each segment is role.lower() followed by [index]
    - Segments are separated by dots
    - Root is the app element itself
    
    Args:
        app_element: The AXUIElement for the application (root).
        path: The navigable path string.
              Can start with role (e.g., "window[0]") or be empty for app root.
    
    Returns:
        The AXUIElement at the specified path, or None if not found.
    
    Example:
        >>> from ax_core import get_app_by_name
        >>> app = get_app_by_name("Safari")
        >>> element = parse_element_path(app, "window[0].toolbar[0].button[3]")
        >>> if element:
        ...     print("Found element!")
    """
    if app_element is None:
        logger.warning("Cannot parse path from None app element")
        return None
    
    if not path:
        logger.warning("Empty path provided")
        return None
    
    # Parse the path into segments
    segments = _parse_path_string(path)
    
    if not segments:
        logger.error(f"Invalid path format: {path}")
        return None
    
    # Navigate to the element
    current_element = app_element
    current_path = ""
    
    for idx, segment in enumerate(segments):
        role_pattern = segment["role"]
        target_index = segment["index"]
        
        # Get children of current element
        children = get_children(current_element)
        
        if not children:
            logger.debug(f"No children at path: {current_path}")
            return None
        
        # Find matching child by role and index
        found_element = None
        matching_count = 0
        
        for child_idx, child in enumerate(children):
            child_role = get_attribute(child, kAXRoleAttribute)
            if child_role:
                child_role_str = str(child_role).lower()
                
                # Check if role matches
                if child_role_str == role_pattern:
                    if matching_count == target_index:
                        found_element = child
                        current_path = f"{current_path}.{role_pattern}[{target_index}]" if current_path else f"{role_pattern}[{target_index}]"
                        break
                    matching_count += 1
        
        if found_element is None:
            logger.debug(f"Element not found at path: {current_path}, looking for {role_pattern}[{target_index}]")
            return None
        
        current_element = found_element
    
    logger.info(f"Successfully navigated to: {path}")
    return current_element


def _parse_path_string(path: str) -> list[dict[str, str | int]]:
    """
    Parse a path string into structured segments.
    
    Args:
        path: Path string like "window[0].toolbar[0].button[3]"
    
    Returns:
        List of dicts with 'role' and 'index' keys.
    
    Example:
        >>> _parse_path_string("window[0].toolbar[0].button[3]")
        [{'role': 'window', 'index': 0}, {'role': 'toolbar', 'index': 0}, {'role': 'button', 'index': 3}]
    """
    # Pattern: role[index] - role is alphanumeric, index is integer
    pattern = re.compile(r'([a-zA-Z0-9_]+)\[(\d+)\]')
    
    segments = []
    for match in pattern.finditer(path):
        role = match.group(1)
        index = int(match.group(2))
        segments.append({"role": role, "index": index})
    
    return segments


def find_element_by_role(
    app_element: AXUIElement,
    role: str,
    title: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Convenience function to find a single element by role and optional title.
    
    Args:
        app_element: The AXUIElement for the application.
        role: The AX role to search for (e.g., "AXButton", "AXTextField").
        title: Optional title/label to filter by.
    
    Returns:
        Dictionary with element data and path, or None if not found.
    
    Example:
        >>> app = get_app_by_name("Safari")
        >>> elem = find_element_by_role(app, "AXTextField", title="Address")
        >>> if elem:
        ...     print(f"Found at: {elem['path']}")
    """
    filters = {"role": role}
    if title:
        filters["title"] = title
    
    results = query_elements(app_element, filters, max_results=1)
    
    return results[0] if results else None


def count_elements_by_role(
    app_element: AXUIElement,
    role: str,
) -> int:
    """
    Count elements of a specific role in the application.
    
    Args:
        app_element: The AXUIElement for the application.
        role: The AX role to count (e.g., "AXButton").
    
    Returns:
        Number of elements with that role.
    
    Example:
        >>> app = get_app_by_name("Safari")
        >>> button_count = count_elements_by_role(app, "AXButton")
        >>> print(f"Safari has {button_count} buttons")
    """
    results = query_elements(app_element, {"role": role}, max_results=1000)
    return len(results)


# ============================================================================
# Module self-test (run when executed directly)
# ============================================================================

if __name__ == "__main__":
    print("AX Search Module - Self Test")
    print("=" * 50)
    
    from ax_core import get_app_by_name
    
    # Test 1: Find an app and query elements
    print("\n[Test 1] Finding Finder and querying elements...")
    finder = get_app_by_name("Finder")
    
    if finder:
        print("  ✓ Found Finder")
        
        # Test query with role filter
        print("\n[Test 2] Querying for AXButton elements...")
        buttons = query_elements(finder, {"role": "button"}, max_results=5)
        print(f"  Found {len(buttons)} buttons (showing up to 5)")
        for btn in buttons[:3]:
            print(f"    - {btn.get('path')}: {btn.get('title')}")
        
        # Test query with multiple filters
        print("\n[Test 3] Querying for windows...")
        windows = query_elements(finder, {"role": "window"}, max_results=3)
        print(f"  Found {len(windows)} windows")
        for win in windows[:3]:
            print(f"    - {win.get('path')}: {win.get('title')}")
        
        # Test parse_element_path
        if windows:
            print("\n[Test 4] Testing parse_element_path...")
            first_window_path = windows[0].get("path", "window[0]")
            print(f"  Parsing path: {first_window_path}")
            element = parse_element_path(finder, first_window_path)
            if element:
                print("  ✓ Successfully navigated to element")
                serialized = serialize_element(element)
                print(f"    Role: {serialized.get('role')}")
            else:
                print("  ✗ Failed to parse path")
        
        # Test find_element_by_role convenience function
        print("\n[Test 5] Testing find_element_by_role...")
        window = find_element_by_role(finder, "AXWindow")
        if window:
            print(f"  ✓ Found window: {window.get('path')}")
        else:
            print("  ✗ No window found")
        
        # Test count_elements_by_role
        print("\n[Test 6] Testing count_elements_by_role...")
        role_counts = [
            ("AXButton", "buttons"),
            ("AXTextField", "text fields"),
            ("AXWindow", "windows"),
            ("AXToolbar", "toolbars"),
        ]
        for role, name in role_counts:
            count = count_elements_by_role(finder, role)
            print(f"  {name}: {count}")
    
    else:
        print("  ✗ Finder not found")
    
    # Test 7: Path string parsing
    print("\n[Test 7] Testing path string parsing...")
    test_paths = [
        "window[0]",
        "window[0].toolbar[0]",
        "window[0].toolbar[0].button[3]",
        "AXWindow[0].AXToolbar[0].AXButton[3]",
    ]
    for test_path in test_paths:
        parsed = _parse_path_string(test_path)
        print(f"  '{test_path}' -> {parsed}")
    
    print("\n" + "=" * 50)
    print("Self-test complete!")
