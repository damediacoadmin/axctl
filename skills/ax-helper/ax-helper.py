#!/usr/bin/env python3
"""
AX Helper - macOS Accessibility Automation CLI

Lightweight Python CLI for automating macOS apps using Accessibility APIs.
Returns structured JSON for efficient integration with automation tools.

Usage:
    ./ax-helper.py <command> [options]

Commands:
    query       Find UI elements matching criteria
    click       Click an element by path
    type        Type text into an element
    get-value   Read element value/text
    list-apps   List running applications
    tree        Dump full accessibility tree
    press       Press a key (Return, Tab, etc.)

Exit Codes:
    0 - Success
    1 - Error
    2 - Not found
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Optional

# Import modules from the same package
from ax_core import (
    get_app_by_name,
    serialize_element,
    list_running_apps,
)
from ax_search import (
    query_elements,
    parse_element_path,
)
from ax_actions import (
    perform_click,
    perform_type,
    perform_press_key,
    get_value as ax_get_value,
)


def utc_now() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def exit_with_code(exit_code: int, data: dict[str, Any]) -> None:
    """Print JSON output and exit with given code."""
    print(json.dumps(data, indent=2))
    sys.exit(exit_code)


def cmd_list_apps() -> dict[str, Any]:
    """List running applications."""
    apps = list_running_apps()
    return {"apps": apps}


def cmd_query(app_name: str, filters: list[str], max_depth: int) -> dict[str, Any]:
    """Query elements in an application."""
    # Find the application
    app_element = get_app_by_name(app_name)
    if app_element is None:
        exit_with_code(2, {
            "error": f"Application '{app_name}' not found",
            "app": app_name,
        })
    
    # Parse filters from "key=value" format
    filter_dict = {}
    for f in filters:
        if "=" in f:
            key, value = f.split("=", 1)
            filter_dict[key.strip()] = value.strip()
    
    # Query elements
    elements = query_elements(
        app_element,
        filter_dict,
        max_depth=max_depth,
        max_results=100,
    )
    
    return {
        "app": app_name,
        "elements": elements,
        "count": len(elements),
    }


def cmd_click(app_name: str, element_path: str) -> dict[str, Any]:
    """Click an element by path."""
    # Find the application
    app_element = get_app_by_name(app_name)
    if app_element is None:
        exit_with_code(2, {
            "error": f"Application '{app_name}' not found",
            "app": app_name,
            "action": "click",
        })
    
    # Parse and navigate to element
    element = parse_element_path(app_element, element_path)
    if element is None:
        exit_with_code(2, {
            "error": f"Element not found: {element_path}",
            "element": element_path,
            "action": "click",
        })
    
    # Perform click
    success = perform_click(element)
    
    if success:
        return {
            "success": True,
            "element": element_path,
            "action": "click",
            "timestamp": utc_now(),
        }
    else:
        exit_with_code(1, {
            "success": False,
            "error": "Click action failed",
            "element": element_path,
            "action": "click",
            "timestamp": utc_now(),
        })


def cmd_type(app_name: str, element_path: str, text: str) -> dict[str, Any]:
    """Type text into an element."""
    # Find the application
    app_element = get_app_by_name(app_name)
    if app_element is None:
        exit_with_code(2, {
            "error": f"Application '{app_name}' not found",
            "app": app_name,
            "action": "type",
        })
    
    # Parse and navigate to element
    element = parse_element_path(app_element, element_path)
    if element is None:
        exit_with_code(2, {
            "error": f"Element not found: {element_path}",
            "element": element_path,
            "action": "type",
        })
    
    # Perform type
    success = perform_type(element, text)
    
    if success:
        return {
            "success": True,
            "element": element_path,
            "action": "type",
            "text": text,
            "timestamp": utc_now(),
        }
    else:
        exit_with_code(1, {
            "success": False,
            "error": "Type action failed",
            "element": element_path,
            "action": "type",
            "text": text,
            "timestamp": utc_now(),
        })


def cmd_get_value(app_name: str, element_path: str) -> dict[str, Any]:
    """Get value from an element."""
    # Find the application
    app_element = get_app_by_name(app_name)
    if app_element is None:
        exit_with_code(2, {
            "error": f"Application '{app_name}' not found",
            "app": app_name,
        })
    
    # Parse and navigate to element
    element = parse_element_path(app_element, element_path)
    if element is None:
        exit_with_code(2, {
            "error": f"Element not found: {element_path}",
            "element": element_path,
        })
    
    # Get value and serialize element
    value = ax_get_value(element)
    serialized = serialize_element(element)
    
    return {
        "element": element_path,
        "value": value,
        "role": serialized.get("role") if serialized else None,
        "enabled": serialized.get("enabled") if serialized else None,
    }


def cmd_tree(app_name: str, max_depth: int) -> dict[str, Any]:
    """Dump accessibility tree for an application."""
    # Find the application
    app_element = get_app_by_name(app_name)
    if app_element is None:
        exit_with_code(2, {
            "error": f"Application '{app_name}' not found",
            "app": app_name,
        })
    
    # Query all elements up to max_depth (no filters = get everything)
    elements = query_elements(
        app_element,
        {},  # No filters - get all elements
        max_depth=max_depth,
        max_results=500,
    )
    
    return {
        "app": app_name,
        "tree": elements,
        "count": len(elements),
    }


def cmd_press(app_name: str, key: str) -> dict[str, Any]:
    """Press a key in an application."""
    # Find the application
    app_element = get_app_by_name(app_name)
    if app_element is None:
        exit_with_code(2, {
            "error": f"Application '{app_name}' not found",
            "app": app_name,
            "action": "press",
        })
    
    # Perform key press (element can be None for system-wide)
    success = perform_press_key(app_element, key)
    
    if success:
        return {
            "success": True,
            "key": key,
            "action": "press",
            "timestamp": utc_now(),
        }
    else:
        exit_with_code(1, {
            "success": False,
            "error": f"Failed to press key: {key}",
            "key": key,
            "action": "press",
            "timestamp": utc_now(),
        })


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AX Helper - macOS Accessibility Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # list-apps command
    subparsers.add_parser("list-apps", help="List running applications")
    
    # query command
    query_parser = subparsers.add_parser("query", help="Find UI elements")
    query_parser.add_argument("app", help="Application name (e.g., Safari, Finder)")
    query_parser.add_argument(
        "--filter", "-f",
        action="append",
        default=[],
        help="Filter in key=value format (e.g., role=button)",
    )
    query_parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum depth to traverse (default: 10)",
    )
    
    # click command
    click_parser = subparsers.add_parser("click", help="Click an element")
    click_parser.add_argument("app", help="Application name")
    click_parser.add_argument("path", help="Element path (e.g., window[0].button[3])")
    
    # type command
    type_parser = subparsers.add_parser("type", help="Type text into element")
    type_parser.add_argument("app", help="Application name")
    type_parser.add_argument("path", help="Element path")
    type_parser.add_argument("text", help="Text to type")
    
    # get-value command
    getvalue_parser = subparsers.add_parser("get-value", help="Get element value")
    getvalue_parser.add_argument("app", help="Application name")
    getvalue_parser.add_argument("path", help="Element path")
    
    # tree command
    tree_parser = subparsers.add_parser("tree", help="Dump accessibility tree")
    tree_parser.add_argument("app", help="Application name")
    tree_parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum depth (default: 5)",
    )
    
    # press command
    press_parser = subparsers.add_parser("press", help="Press a key")
    press_parser.add_argument("app", help="Application name")
    press_parser.add_argument("key", help="Key to press (Return, Tab, Escape, etc.)")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        result: dict[str, Any]
        
        if args.command == "list-apps":
            result = cmd_list_apps()
        
        elif args.command == "query":
            result = cmd_query(args.app, args.filter, args.max_depth)
        
        elif args.command == "click":
            result = cmd_click(args.app, args.path)
        
        elif args.command == "type":
            result = cmd_type(args.app, args.path, args.text)
        
        elif args.command == "get-value":
            result = cmd_get_value(args.app, args.path)
        
        elif args.command == "tree":
            result = cmd_tree(args.app, args.max_depth)
        
        elif args.command == "press":
            result = cmd_press(args.app, args.key)
        
        else:
            parser.print_help()
            sys.exit(1)
        
        # Success - exit code 0
        exit_with_code(0, result)
        
    except Exception as e:
        # Unexpected error - exit code 1
        exit_with_code(1, {
            "error": str(e),
            "command": args.command,
        })


if __name__ == "__main__":
    main()
