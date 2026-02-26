#!/usr/bin/env python3
"""
ax_core.py - Core PyObjC wrapper for macOS Accessibility APIs

Provides low-level functions for interacting with macOS accessibility elements.
Used by the AX Helper CLI tool for automation tasks.

Functions:
    - get_app_by_name(app_name): Find running app by name, return AXUIElement
    - get_app_element(pid): Get AXUIElement for process ID
    - get_attribute(element, attr_name): Read AX attribute value
    - get_attribute_names(element): List all available attributes
    - serialize_element(element): Convert AXUIElement to dict

Requirements:
    - Python 3.9+
    - PyObjC (Cocoa, ApplicationServices)

Author: AX Helper Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any, Optional

# PyObjC imports for macOS Accessibility APIs
from Cocoa import NSWorkspace, NSRunningApplication, NSValue
from CoreFoundation import CGPoint, CGSize
from ApplicationServices import (
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeValue,
    AXUIElementCopyAttributeNames,
    AXValueGetValue,
)

# Try to import AXValue type constants, fallback to values if unavailable
try:
    from ApplicationServices import (
        kAXValueTypeCGPoint,
        kAXValueTypeCGSize,
    )
except ImportError:
    # Fallback values (these are the enum values)
    kAXValueTypeCGPoint = 1  # kAXValueCGPointType
    kAXValueTypeCGSize = 2   # kAXValueCGSizeType

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Type aliases for clarity
AXUIElement = Any  # AXUIElementRef is an opaque type
AXErrorCode = int


# Try to import AX constants, fallback to strings if unavailable
try:
    from ApplicationServices import (
        kAXRoleAttribute,
        kAXTitleAttribute,
        kAXDescriptionAttribute,
        kAXValueAttribute,
        kAXEnabledAttribute,
        kAXFocusedAttribute,
        kAXPositionAttribute,
        kAXSizeAttribute,
        kAXWindowsAttribute,
        kAXChildrenAttribute,
        kAXParentAttribute,
        kAXSubroleAttribute,
        kAXIdentifierAttribute,
        kAXHelpAttribute,
        kAXSelectedAttribute,
        kAXSelectedTextAttribute,
        kAXVisibleAttribute,
        kAXMinValueAttribute,
        kAXMaxValueAttribute,
        kAXIncrementAttribute,
        kAXPlaceholderValueAttribute,
    )
    _AX_CONSTANTS_AVAILABLE = True
except ImportError:
    _AX_CONSTANTS_AVAILABLE = False
    # Fallback string constants
    kAXRoleAttribute = "AXRole"
    kAXTitleAttribute = "AXTitle"
    kAXDescriptionAttribute = "AXDescription"
    kAXValueAttribute = "AXValue"
    kAXEnabledAttribute = "AXEnabled"
    kAXFocusedAttribute = "AXFocused"
    kAXPositionAttribute = "AXPosition"
    kAXSizeAttribute = "AXSize"
    kAXWindowsAttribute = "AXWindows"
    kAXChildrenAttribute = "AXChildren"
    kAXParentAttribute = "AXParent"
    kAXSubroleAttribute = "AXSubrole"
    kAXIdentifierAttribute = "AXIdentifier"
    kAXHelpAttribute = "AXHelp"
    kAXSelectedAttribute = "AXSelected"
    kAXSelectedTextAttribute = "AXSelectedText"
    kAXVisibleAttribute = "AXVisible"
    kAXMinValueAttribute = "AXMinValue"
    kAXMaxValueAttribute = "AXMaxValue"
    kAXIncrementAttribute = "AXIncrement"
    kAXPlaceholderValueAttribute = "AXPlaceholderValue"


def get_app_by_name(app_name: str) -> Optional[AXUIElement]:
    """
    Find a running application by name and return its AXUIElement.
    
    Searches through running applications using NSWorkspace to find
    an app matching the given name (case-insensitive match).
    
    Args:
        app_name: The name of the application (e.g., "Safari", "Finder").
                  Can be full name or partial match.
    
    Returns:
        AXUIElement for the application, or None if not found.
    
    Example:
        >>> app_element = get_app_by_name("Safari")
        >>> if app_element:
        ...     print("Found Safari!")
    """
    try:
        # Get all running applications from NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        # Search for the requested application
        for ns_app in running_apps:
            # Get the app name (localizedName handles localization)
            app_name_str = ns_app.localizedName()
            
            if app_name_str is None:
                continue
                
            # Case-insensitive comparison
            if app_name_str.lower() == app_name.lower():
                pid = ns_app.processIdentifier()
                logger.info(f"Found app '{app_name}' with PID {pid}")
                return get_app_element(pid)
        
        # Try partial match if exact match fails
        for ns_app in running_apps:
            app_name_str = ns_app.localizedName()
            if app_name_str and app_name.lower() in app_name_str.lower():
                pid = ns_app.processIdentifier()
                logger.info(f"Found partial match '{app_name_str}' with PID {pid}")
                return get_app_element(pid)
        
        logger.warning(f"Application '{app_name}' not found")
        return None
        
    except Exception as e:
        logger.error(f"Error finding app '{app_name}': {e}")
        return None


def get_app_element(pid: int) -> Optional[AXUIElement]:
    """
    Get the AXUIElement for a process ID.
    
    Creates an AXUIElement reference for the application associated
    with the given process ID.
    
    Args:
        pid: The process ID of the application.
    
    Returns:
        AXUIElement for the application, or None on error.
    
    Example:
        >>> app_element = get_app_element(12345)
        >>> if app_element:
        ...     print(f"Got AX element for PID {pid}")
    """
    try:
        # Create AXUIElement for the application
        app_element = AXUIElementCreateApplication(pid)
        
        if app_element is None:
            logger.error(f"Failed to create AXUIElement for PID {pid}")
            return None
        
        logger.debug(f"Created AXUIElement for PID {pid}")
        return app_element
        
    except Exception as e:
        logger.error(f"Error getting app element for PID {pid}: {e}")
        return None


def get_attribute(element: AXUIElement, attr_name: str) -> Optional[Any]:
    """
    Read an AX attribute from an element.
    
    Retrieves the value of a specific accessibility attribute
    from an AXUIElement.
    
    Args:
        element: The AXUIElement to query.
        attr_name: The name of the attribute to read.
                   Can be a constant (e.g., kAXRoleAttribute) or string
                   (e.g., "AXRole", "AXTitle", "AXValue").
    
    Returns:
        The attribute value, or None if not found or on error.
    
    Example:
        >>> role = get_attribute(element, "AXRole")
        >>> title = get_attribute(element, kAXTitleAttribute)
        >>> print(f"Role: {role}, Title: {title}")
    """
    if element is None:
        logger.warning("Cannot get attribute from None element")
        return None
    
    try:
        # Convert string attribute name to AX API constant if needed
        attr = _resolve_attribute_name(attr_name)
        
        # Copy the attribute value - returns (err, value) tuple
        err, value = AXUIElementCopyAttributeValue(element, attr, None)
        if err != 0:
            logger.debug(f"Error getting attribute '{attr_name}': error code {err}")
            return None
        
        # AXErrorNoValue means the attribute exists but has no value
        # AXErrorAttributeUnsupported means the attribute doesn't exist
        if value is None:
            # Check if it's actually an error vs just empty
            # The API returns (value, error) tuple in some contexts
            logger.debug(f"Attribute '{attr_name}' returned None")
            return None
            
        logger.debug(f"Got attribute '{attr_name}': {value}")
        return value
        
    except Exception as e:
        # AXUIElementCopyAttributeValue raises AXError on failure
        logger.debug(f"Error getting attribute '{attr_name}': {e}")
        return None


def get_attribute_names(element: AXUIElement) -> Optional[list[str]]:
    """
    List all available attributes for an element.
    
    Returns the complete list of accessibility attributes
    that can be queried on the given element.
    
    Args:
        element: The AXUIElement to query.
    
    Returns:
        A list of attribute name strings, or None on error.
    
    Example:
        >>> attrs = get_attribute_names(element)
        >>> if attrs:
        ...     print(f"Available attributes: {attrs}")
    """
    if element is None:
        logger.warning("Cannot get attribute names from None element")
        return None
    
    try:
        # Get all attribute names - returns (err, attr_names) tuple
        err, attr_names = AXUIElementCopyAttributeNames(element, None)
        if err != 0:
            logger.error(f"Error getting attribute names: error code {err}")
            return None
        
        if attr_names is None:
            logger.debug("Element has no attributes")
            return []
        
        # Convert to list if needed (might be an array)
        if hasattr(attr_names, '__iter__'):
            result = list(attr_names)
        else:
            result = [attr_names]
        
        logger.debug(f"Found {len(result)} attributes")
        return result
        
    except Exception as e:
        logger.error(f"Error getting attribute names: {e}")
        return None


def serialize_element(element: AXUIElement) -> Optional[dict[str, Any]]:
    """
    Convert an AXUIElement to a dictionary with common attributes.
    
    Extracts the most commonly useful accessibility information
    from an element and returns it as a dictionary.
    
    Args:
        element: The AXUIElement to serialize.
    
    Returns:
        A dictionary containing:
            - role: The element's AXRole (e.g., "AXButton", "AXTextField")
            - subrole: Optional subrole for more specific classification
            - title: The element's title/label
            - description: The element's description
            - value: The element's current value (for text fields, etc.)
            - enabled: Boolean indicating if element is enabled
            - focused: Boolean indicating if element has focus
            - position: Dict with 'x' and 'y' coordinates
            - size: Dict with 'width' and 'height'
            - identifier: Optional identifier string
            - All available attributes in 'attributes' key
    
    Returns None on error.
    
    Example:
        >>> data = serialize_element(element)
        >>> if data:
        ...     print(f"Element: {data['role']} - {data.get('title', 'No title')}")
    """
    if element is None:
        logger.warning("Cannot serialize None element")
        return None
    
    try:
        result = {}
        
        # Get role (most fundamental attribute)
        role = get_attribute(element, kAXRoleAttribute)
        result["role"] = str(role) if role else None
        
        # Get subrole for more detail
        subrole = get_attribute(element, kAXSubroleAttribute)
        result["subrole"] = str(subrole) if subrole else None
        
        # Get title
        title = get_attribute(element, kAXTitleAttribute)
        result["title"] = str(title) if title else None
        
        # Get description
        description = get_attribute(element, kAXDescriptionAttribute)
        result["description"] = str(description) if description else None
        
        # Get value (varies by element type)
        value = get_attribute(element, kAXValueAttribute)
        if value is not None:
            # Preserve native JSON types (bool, int, float, str, None)
            if isinstance(value, (bool, int, float, str, type(None))):
                result["value"] = value
            elif hasattr(value, '__str__'):
                result["value"] = str(value)
            else:
                result["value"] = value
        else:
            result["value"] = None
        
        # Get enabled state
        enabled = get_attribute(element, kAXEnabledAttribute)
        result["enabled"] = bool(enabled) if enabled is not None else None
        
        # Get focused state
        focused = get_attribute(element, kAXFocusedAttribute)
        result["focused"] = bool(focused) if focused is not None else None
        
        # Get position (AXPoint - CGPoint wrapped in AXValueRef)
        position = get_attribute(element, kAXPositionAttribute)
        if position is not None:
            try:
                # Try to unwrap AXValueRef wrapper using AXValueGetValue
                # AXPosition is an AXValueRef that wraps a CGPoint
                # Returns (success_bool, output_struct) - struct has .x/.y attributes
                success, point = AXValueGetValue(position, kAXValueTypeCGPoint, None)
                if success:
                    result["position"] = {"x": point.x, "y": point.y}
                # Fallback: try CGPoint attributes
                elif hasattr(position, 'x') and hasattr(position, 'y'):
                    result["position"] = {"x": position.x, "y": position.y}
                elif isinstance(position, (tuple, list)) and len(position) >= 2:
                    result["position"] = {"x": position[0], "y": position[1]}
                else:
                    result["position"] = position
            except Exception as e:
                logger.debug(f"Could not parse position: {e}")
                result["position"] = str(position)
        else:
            result["position"] = None
        
        # Get size (AXSize - CGSize wrapped in AXValueRef)
        size = get_attribute(element, kAXSizeAttribute)
        if size is not None:
            try:
                # Try to unwrap AXValueRef wrapper using AXValueGetValue
                # AXSize is an AXValueRef that wraps a CGSize
                # Returns (success_bool, output_struct) - struct has .width/.height attributes
                success, sz = AXValueGetValue(size, kAXValueTypeCGSize, None)
                if success:
                    result["size"] = {"width": sz.width, "height": sz.height}
                # Fallback: try CGSize attributes
                elif hasattr(size, 'width') and hasattr(size, 'height'):
                    result["size"] = {"width": size.width, "height": size.height}
                elif isinstance(size, (tuple, list)) and len(size) >= 2:
                    result["size"] = {"width": size[0], "height": size[1]}
                else:
                    result["size"] = size
            except Exception as e:
                logger.debug(f"Could not parse size: {e}")
                result["size"] = str(size)
        else:
            result["size"] = None
        
        # Get identifier
        identifier = get_attribute(element, kAXIdentifierAttribute)
        result["identifier"] = str(identifier) if identifier else None
        
        # Get help text
        help_text = get_attribute(element, kAXHelpAttribute)
        result["help"] = str(help_text) if help_text else None
        
        # Get selected state
        selected = get_attribute(element, kAXSelectedAttribute)
        result["selected"] = bool(selected) if selected is not None else None
        
        # Get placeholder (for text fields)
        placeholder = get_attribute(element, kAXPlaceholderValueAttribute)
        result["placeholder"] = str(placeholder) if placeholder else None
        
        # Get all available attributes as raw list
        all_attrs = get_attribute_names(element)
        result["_available_attributes"] = all_attrs if all_attrs else []
        
        logger.debug(f"Serialized element: {result.get('role')} - {result.get('title')}")
        return result
        
    except Exception as e:
        logger.error(f"Error serializing element: {e}")
        return None


def _resolve_attribute_name(attr_name: str) -> str:
    """
    Resolve attribute name string to AX API constant.
    
    Handles conversion between string attribute names and
    AX API constant names.
    
    Args:
        attr_name: The attribute name as a string.
    
    Returns:
        The resolved attribute name (constant or original string).
    """
    # Map of common attribute names
    attr_map = {
        "AXRole": kAXRoleAttribute,
        "AXTitle": kAXTitleAttribute,
        "AXDescription": kAXDescriptionAttribute,
        "AXValue": kAXValueAttribute,
        "AXEnabled": kAXEnabledAttribute,
        "AXFocused": kAXFocusedAttribute,
        "AXPosition": kAXPositionAttribute,
        "AXSize": kAXSizeAttribute,
        "AXWindows": kAXWindowsAttribute,
        "AXChildren": kAXChildrenAttribute,
        "AXParent": kAXParentAttribute,
        "AXSubrole": kAXSubroleAttribute,
        "AXIdentifier": kAXIdentifierAttribute,
        "AXHelp": kAXHelpAttribute,
        "AXSelected": kAXSelectedAttribute,
        "AXSelectedText": kAXSelectedTextAttribute,
        "AXVisible": kAXVisibleAttribute,
    }
    
    # Return mapped value or original
    return attr_map.get(attr_name, attr_name)


def get_windows(element: AXUIElement) -> Optional[list[AXUIElement]]:
    """
    Get all windows of an application element.
    
    Convenience function to get all AXWindow elements
    from an application.
    
    Args:
        element: The AXUIElement for an application.
    
    Returns:
        List of window elements, or empty list if none found.
    """
    windows = get_attribute(element, kAXWindowsAttribute)
    if windows is None:
        return []
    
    # Convert to list if needed
    if hasattr(windows, '__iter__'):
        return list(windows)
    return [windows]


def get_children(element: AXUIElement) -> Optional[list[AXUIElement]]:
    """
    Get all children of an element.
    
    Args:
        element: The AXUIElement to get children from.
    
    Returns:
        List of child elements, or empty list if none found.
    """
    children = get_attribute(element, kAXChildrenAttribute)
    if children is None:
        return []
    
    if hasattr(children, '__iter__'):
        return list(children)
    return [children]


def list_running_apps() -> list[dict[str, Any]]:
    """
    List all running applications with name, PID, and bundle ID.
    
    Returns:
        List of dicts with 'name', 'pid', 'bundle_id' keys.
    """
    try:
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        result = []
        for app in running_apps:
            name = app.localizedName()
            if not name:
                continue
            
            result.append({
                "name": str(name),
                "pid": int(app.processIdentifier()),
                "bundle_id": str(app.bundleIdentifier() or "")
            })
        
        return result
    except Exception as e:
        logger.error(f"Error listing apps: {e}")
        return []


def get_parent(element: AXUIElement) -> Optional[AXUIElement]:
    """
    Get the parent of an element.
    
    Args:
        element: The AXUIElement to get parent from.
    
    Returns:
        Parent element, or None on error.
    """
    return get_attribute(element, kAXParentAttribute)


# ============================================================================
# Module self-test (run when executed directly)
# ============================================================================

if __name__ == "__main__":
    print("AX Core Module - Self Test")
    print("=" * 50)
    
    # Test 1: List running apps (using NSWorkspace directly)
    print("\n[Test 1] Finding running applications...")
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    print("Top 5 running applications:")
    for i, app in enumerate(running_apps[:5]):
        name = app.localizedName() or "Unknown"
        pid = app.processIdentifier()
        print(f"  {i+1}. {name} (PID: {pid})")
    
    # Test 2: Find a specific app
    print("\n[Test 2] Finding 'Finder'...")
    finder = get_app_by_name("Finder")
    if finder:
        print("  ✓ Found Finder")
        finder_data = serialize_element(finder)
        print(f"  Role: {finder_data.get('role')}")
    else:
        print("  ✗ Finder not found")
    
    # Test 3: Get attribute names
    if finder:
        print("\n[Test 3] Getting attribute names for Finder...")
        attrs = get_attribute_names(finder)
        if attrs:
            print(f"  Found {len(attrs)} attributes")
            # Show first 5
            print(f"  First 5: {list(attrs)[:5]}")
    
    # Test 4: Serialize Finder
    if finder:
        print("\n[Test 4] Serializing Finder element...")
        data = serialize_element(finder)
        if data:
            print(f"  Role: {data.get('role')}")
            print(f"  Title: {data.get('title')}")
            print(f"  Windows: {data.get('value')}")
    
    print("\n" + "=" * 50)
    print("Self-test complete!")
