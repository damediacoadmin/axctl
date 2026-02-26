#!/usr/bin/env python3
"""
ax_actions.py - Action functions for macOS Accessibility Automation

Provides high-level action functions for interacting with macOS accessibility
elements. Used by the AX Helper CLI tool for automation tasks.

Functions:
    - perform_click(element): Trigger AXPress action on element
    - perform_type(element, text): Set AXValue to text string
    - perform_press_key(element, key): Press key using CGEventPost
    - perform_focus(element): Set AXFocused to True
    - get_value(element): Read AXValue from element

Requirements:
    - Python 3.9+
    - PyObjC (Cocoa, ApplicationServices, CoreGraphics)

Author: AX Helper Team
License: MIT
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

# PyObjC imports for macOS Accessibility APIs
from Quartz.CoreGraphics import (
    CGEventPost,
    CGEventCreateKeyboardEvent,
    CGEventKeyboardSetUnicodeString,
    CGEventCreateMouseEvent,
    CGEventSetFlags,
    CGEventSetIntegerValueField,
    kCGEventSourceStateHIDSystemState,
    kCGHIDEventTap,
)

# ApplicationServices imports for AX actions
from ApplicationServices import (
    AXUIElementCopyAttributeValue,
    AXUIElementSetAttributeValue,
    AXUIElementPerformAction,
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Type aliases for clarity
AXUIElement = Any  # AXUIElementRef is an opaque type

# Try to import AX constants, fallback to strings if unavailable
try:
    from ApplicationServices import (
        kAXRoleAttribute,
        kAXValueAttribute,
        kAXFocusedAttribute,
        kAXPressAction,
        kAXRaiseAction,
        kAXPress,
    )
    _AX_CONSTANTS_AVAILABLE = True
except ImportError:
    _AX_CONSTANTS_AVAILABLE = False
    # Fallback string constants
    kAXRoleAttribute = "AXRole"
    kAXValueAttribute = "AXValue"
    kAXFocusedAttribute = "AXFocused"
    kAXPressAction = "AXPress"
    kAXRaiseAction = "AXRaise"
    kAXPress = "AXPress"

# Key code mapping for common keys
KEY_CODES = {
    "return": 0x24,
    "enter": 0x24,
    "tab": 0x30,
    "space": 0x31,
    "delete": 0x33,
    "escape": 0x35,
    "backspace": 0x33,
    "up": 0x7E,
    "down": 0x7D,
    "left": 0x7B,
    "right": 0x7C,
    "home": 0x73,
    "end": 0x77,
    "pageup": 0x74,
    "pagedown": 0x79,
    "f1": 0x7A,
    "f2": 0x78,
    "f3": 0x63,
    "f4": 0x76,
    "f5": 0x60,
    "f6": 0x61,
    "f7": 0x62,
    "f8": 0x64,
    "f9": 0x65,
    "f10": 0x6D,
    "f11": 0x67,
    "f12": 0x6F,
}


def get_value(element: AXUIElement) -> Optional[Any]:
    """
    Read the AXValue attribute from an element.
    
    Retrieves the current value of an accessibility element,
    which varies by element type:
    - Text fields: the text content
    - Sliders: the numeric value
    - Checkboxes: "AXValue" can be "true" or "false"
    - Combo boxes: the selected value
    
    Args:
        element: The AXUIElement to read from.
    
    Returns:
        The element's value (type varies), or None if not available.
    
    Example:
        >>> value = get_value(text_field_element)
        >>> if value:
        ...     print(f"Current text: {value}")
    """
    if element is None:
        logger.warning("Cannot get value from None element")
        return None
    
    try:
        err, value = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
        if err != 0:
            logger.debug(f"Error getting AXValue: error code {err}")
            return None
        
        if value is None:
            return None
        
        # Return the value in its native type
        # Could be str, int, float, bool, or None
        logger.debug(f"Got AXValue: {value}")
        return value
        
    except Exception as e:
        logger.error(f"Error getting element value: {e}")
        return None


def perform_click(element: AXUIElement) -> bool:
    """
    Trigger the AXPress action on an element.
    
    Simulates a mouse click by performing the AXPress accessibility
    action on the element. This is the preferred way to click buttons,
    checkboxes, and other interactive elements.
    
    Note: The element must be visible and enabled for this to work.
    For elements that don't support AXPress, consider using perform_raise().
    
    Args:
        element: The AXUIElement to click.
    
    Returns:
        True if the click was successful, False otherwise.
    
    Example:
        >>> # Click a button
        >>> button = find_element_by_path(app, "window[0].button[0]")
        >>> if button:
        ...     success = perform_click(button)
        ...     if success:
        ...         print("Button clicked!")
    """
    if element is None:
        logger.warning("Cannot click None element")
        return False
    
    try:
        # Determine the action to use
        action = kAXPressAction if _AX_CONSTANTS_AVAILABLE else kAXPress
        
        # Try to perform the press action
        err = AXUIElementPerformAction(element, action)
        
        if err != 0:
            logger.debug(f"AXPress action failed with error code: {err}")
            # Try alternative: use AXRaise to bring element into view
            # and then try again
            try:
                AXUIElementPerformAction(element, kAXRaiseAction)
            except Exception:
                pass
            # Try again after raise
            err = AXUIElementPerformAction(element, action)
            
            if err != 0:
                logger.error(f"Failed to perform click: error code {err}")
                return False
        
        logger.info("Successfully clicked element")
        return True
        
    except Exception as e:
        logger.error(f"Error performing click: {e}")
        return False


def perform_raise(element: AXUIElement) -> bool:
    """
    Raise an element to make it visible and focused.
    
    Performs the AXRaise action to bring the element into view
    and give it focus. Useful for elements that are not currently visible.
    
    Args:
        element: The AXUIElement to raise.
    
    Returns:
        True if successful, False otherwise.
    """
    if element is None:
        logger.warning("Cannot raise None element")
        return False
    
    try:
        if _AX_CONSTANTS_AVAILABLE:
            err = AXUIElementPerformAction(element, kAXRaiseAction)
        else:
            # Fallback: try with string
            err = AXUIElementPerformAction(element, "AXRaise")
        
        if err != 0:
            logger.debug(f"AXRaise action failed: error code {err}")
            return False
        
        logger.info("Successfully raised element")
        return True
        
    except Exception as e:
        logger.error(f"Error raising element: {e}")
        return False


def perform_focus(element: AXUIElement) -> bool:
    """
    Set focus to an accessibility element.
    
    Sets the AXFocused attribute to True, giving keyboard focus
    to the element. This is useful for text fields, list items,
    and other elements that can receive keyboard input.
    
    Args:
        element: The AXUIElement to focus.
    
    Returns:
        True if focus was set successfully, False otherwise.
    
    Example:
        >>> # Focus a text field before typing
        >>> text_field = find_element_by_path(app, "window[0].textfield[0]")
        >>> if text_field:
        ...     success = perform_focus(text_field)
        ...     if success:
        ...         perform_type(text_field, "Hello World")
    """
    if element is None:
        logger.warning("Cannot focus None element")
        return False
    
    try:
        # Set AXFocused to True
        if _AX_CONSTANTS_AVAILABLE:
            err = AXUIElementSetAttributeValue(element, kAXFocusedAttribute, True)
        else:
            err = AXUIElementSetAttributeValue(element, "AXFocused", True)
        
        if err != 0:
            logger.error(f"Failed to set focus: error code {err}")
            return False
        
        # Verify focus was set
        err, is_focused = AXUIElementCopyAttributeValue(element, kAXFocusedAttribute, None)
        if err != 0 or not is_focused:
            logger.warning(f"Focus set but element reports as not focused")
            # Don't return False - the set might have worked even if verify fails
        
        logger.info("Successfully focused element")
        return True
        
    except Exception as e:
        logger.error(f"Error setting focus: {e}")
        return False


def perform_type(element: AXUIElement, text: str) -> bool:
    """
    Set the value of an element to a text string.
    
    Directly sets the AXValue attribute of an element to the
    provided text string. This is the most reliable way to
    input text into text fields.
    
    Args:
        element: The AXUIElement (typically a text field) to type into.
        text: The text string to insert.
    
    Returns:
        True if text was set successfully, False otherwise.
    
    Example:
        >>> # Type into a text field
        >>> text_field = find_element_by_path(app, "window[0].textfield[0]")
        >>> if text_field:
        ...     perform_focus(text_field)
        ...     success = perform_type(text_field, "https://example.com")
        ...     if success:
        ...         print("Text inserted!")
    """
    if element is None:
        logger.warning("Cannot type into None element")
        return False
    
    if text is None:
        logger.warning("Cannot type None text")
        return False
    
    try:
        # First, try to focus the element
        perform_focus(element)
        
        # Set the value directly via AXValue attribute
        if _AX_CONSTANTS_AVAILABLE:
            err = AXUIElementSetAttributeValue(element, kAXValueAttribute, text)
        else:
            err = AXUIElementSetAttributeValue(element, "AXValue", text)
        
        if err != 0:
            logger.error(f"Failed to set text value: error code {err}")
            return False
        
        # Small delay to allow the value to be set
        time.sleep(0.05)
        
        # Verify the value was set
        current_value = get_value(element)
        if current_value is None:
            logger.warning("Value set but readback returned None")
        
        logger.info(f"Successfully typed text: {text[:20]}{'...' if len(text) > 20 else ''}")
        return True
        
    except Exception as e:
        logger.error(f"Error typing text: {e}")
        return False


def perform_press_key(element: AXUIElement, key: str) -> bool:
    """
    Press a key using CGEvent keyboard simulation.
    
    Simulates a keyboard key press using CoreGraphics CGEventPost.
    This is useful for pressing keys like Return, Tab, Escape,
    Arrow keys, etc.
    
    Note: This sends the key event to the system, not directly
    to the element. For element-specific actions, use perform_click()
    or perform_focus() instead.
    
    Args:
        element: The AXUIElement (used for focusing if needed, can be None).
        key: The key to press. Can be:
            - Named keys: "return", "enter", "tab", "space", "delete",
              "escape", "backspace", "up", "down", "left", "right",
              "home", "end", "pageup", "pagedown"
            - Function keys: "f1" through "f12"
            - Single characters: "a", "1", etc. (uses Unicode)
    
    Returns:
        True if the key press was successful, False otherwise.
    
    Example:
        >>> # Press Enter/Return
        >>> success = perform_press_key(text_field, "return")
        >>>
        >>> # Press Tab
        >>> success = perform_press_key(None, "tab")
        >>>
        >>> # Press Escape
        >>> success = perform_press_key(None, "escape")
    """
    try:
        # Try to focus the element first (if provided)
        if element is not None:
            perform_focus(element)
        
        # Small delay to ensure focus is set
        time.sleep(0.05)
        
        # Resolve key to keycode
        key_lower = key.lower().strip()
        
        # Check if it's a named key
        if key_lower in KEY_CODES:
            keycode = KEY_CODES[key_lower]
            use_unicode = False
        elif len(key_lower) == 1:
            # Single character - use Unicode string for arbitrary characters
            keycode = 0
            use_unicode = True
            char = key_lower
        else:
            logger.error(f"Unknown key: {key}")
            return False
        
        # Create keyboard event source
        # Use None for HID system-wide event
        event_source = None
        
        # Create key down event
        key_down = CGEventCreateKeyboardEvent(event_source, keycode, True)
        if key_down is None:
            logger.error("Failed to create key down event")
            return False
        
        # For single characters, use CGEventKeyboardSetUnicodeString
        if use_unicode:
            CGEventKeyboardSetUnicodeString(key_down, 1, [ord(char)])
        
        # Create key up event
        key_up = CGEventCreateKeyboardEvent(event_source, keycode, False)
        if key_up is None:
            logger.error("Failed to create key up event")
            return False
        
        # For single characters, use CGEventKeyboardSetUnicodeString on key up too
        if use_unicode:
            CGEventKeyboardSetUnicodeString(key_up, 1, [ord(char)])
        
        # Post the events (key down then key up)
        CGEventPost(0, key_down)  # 0 = kCGHIDEventTap
        time.sleep(0.01)  # Small delay between down and up
        CGEventPost(0, key_up)
        
        logger.info(f"Successfully pressed key: {key}")
        return True
        
    except Exception as e:
        logger.error(f"Error pressing key: {e}")
        return False


def perform_double_click(element: AXUIElement) -> bool:
    """
    Perform a double-click action on an element.
    
    Simulates a double-click using CGEvent with clickCount=2.
    Useful for opening files, folders, or items
    that require double-click to activate.
    
    Args:
        element: The AXUIElement to double-click.
    
    Returns:
        True if successful, False otherwise.
    """
    if element is None:
        logger.warning("Cannot double-click None element")
        return False
    
    try:
        # Get the position of the element
        err, position = AXUIElementCopyAttributeValue(element, "AXPosition", None)
        if err != 0:
            logger.error(f"Could not get element position: {err}")
            return perform_click(element)  # Fallback to single click
        
        # Extract x, y from position (it's a CGPoint)
        try:
            x = position.x
            y = position.y
        except AttributeError:
            # Position might be a tuple or list
            x, y = position
        
        # Create mouse events for double-click
        event_source = None
        
        # Create left mouse down event with clickCount=2
        mouse_down = CGEventCreateMouseEvent(
            event_source,  # source
            0x01,         # kCGEventLeftMouseDown
            (x, y),       # location
            0             # kCGMouseButtonLeft (0 = left button)
        )
        CGEventSetIntegerValueField(mouse_down, 0x0A, 2)  # kCGMouseEventClickState = 2 for double-click
        
        # Create left mouse up event with clickCount=2
        mouse_up = CGEventCreateMouseEvent(
            event_source,  # source
            0x02,          # kCGEventLeftMouseUp
            (x, y),        # location
            0              # kCGMouseButtonLeft (0 = left button)
        )
        CGEventSetIntegerValueField(mouse_up, 0x0A, 2)  # kCGMouseEventClickState = 2
        
        # Post the events
        CGEventPost(0, mouse_down)
        time.sleep(0.02)
        CGEventPost(0, mouse_up)
        
        logger.info("Successfully double-clicked element")
        return True
        
    except Exception as e:
        logger.error(f"Error performing double-click: {e}")
        # Fallback to two rapid clicks
        return perform_click(element) and perform_click(element)


def perform_select_all(element: AXUIElement) -> bool:
    """
    Select all text in a text field.
    
    Uses keyboard simulation to send Cmd+A (Select All)
    to the focused element.
    
    Args:
        element: The AXUIElement (typically a text field).
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Focus the element
        if not perform_focus(element):
            logger.warning("Could not focus element for select all")
        
        time.sleep(0.05)
        
        # Create Cmd+A key combination
        event_source = None
        
        # 'a' key = 0x00
        key_down = CGEventCreateKeyboardEvent(event_source, 0x00, True)
        key_up = CGEventCreateKeyboardEvent(event_source, 0x00, False)
        
        # Set command modifier using CGEventSetFlags (0x100000 = kCGEventFlagMaskCommand)
        CGEventSetFlags(key_down, 0x100000)
        
        CGEventPost(0, key_down)
        time.sleep(0.01)
        CGEventPost(0, key_up)
        
        logger.info("Successfully selected all text")
        return True
        
    except Exception as e:
        logger.error(f"Error selecting all: {e}")
        return False


# ============================================================================
# Module self-test (run when executed directly)
# ============================================================================

if __name__ == "__main__":
    print("AX Actions Module - Self Test")
    print("=" * 50)
    
    # Import test utilities from ax_core
    try:
        import sys
        sys.path.insert(0, __file__.rsplit('/', 1)[0])
        from ax_core import get_app_by_name, serialize_element
    except ImportError:
        print("Could not import ax_core for testing")
        get_app_by_name = None
        serialize_element = None
    
    # Test 1: Find an app
    print("\n[Test 1] Finding 'Finder' for testing...")
    if get_app_by_name:
        finder = get_app_by_name("Finder")
        if finder:
            print("  ✓ Found Finder")
            data = serialize_element(finder) if serialize_element else None
            if data:
                print(f"    Role: {data.get('role')}")
        else:
            print("  ✗ Finder not found")
    
    # Test 2: Test key codes
    print("\n[Test 2] Testing key code lookup...")
    test_keys = ["return", "tab", "escape", "up", "down"]
    for k in test_keys:
        if k in KEY_CODES:
            print(f"  ✓ '{k}' -> 0x{KEY_CODES[k]:02X}")
        else:
            print(f"  ✗ '{k}' not found")
    
    print("\n" + "=" * 50)
    print("Self-test complete!")
