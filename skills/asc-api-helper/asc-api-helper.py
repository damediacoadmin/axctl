#!/usr/bin/env python3
"""App Store Connect API Helper CLI."""

import argparse
import json
import os
import subprocess
import sys
import time

from asc_auth import generate_token
from asc_api import list_apps, list_builds, get_app


def check_license():
    """Check for valid Pro license."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    check_script = os.path.join(script_dir, '..', '..', 'bin', 'check-license.js')
    
    if not os.path.exists(check_script):
        # Try alternative path
        check_script = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'bin', 'check-license.js')
    
    if os.path.exists(check_script):
        result = subprocess.run(['node', check_script], capture_output=True)
        if result.returncode != 0:
            sys.exit(1)
    else:
        print('❌ License checker not found. Please reinstall AXCTL.', file=sys.stderr)
        sys.exit(1)


def main():
    # Check for valid Pro license
    check_license()
    parser = argparse.ArgumentParser(
        description='App Store Connect API Helper'
    )
    
    # Common arguments
    parser.add_argument('--key-id', required=True, help='App Store Connect Key ID')
    parser.add_argument('--issuer-id', required=True, help='App Store Connect Issuer ID')
    parser.add_argument('--key-file', required=True, help='Path to .p8 private key file')
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # auth-test command
    subparsers.add_parser('auth-test', help='Verify API credentials')
    
    # list-apps command
    subparsers.add_parser('list-apps', help='List all apps in account')
    
    # list-builds command
    list_builds_parser = subparsers.add_parser('list-builds', help='List builds for an app')
    list_builds_parser.add_argument('--app-id', required=True, help='App ID')
    list_builds_parser.add_argument('--limit', type=int, default=10, help='Max builds to return')
    
    # get-app command
    get_app_parser = subparsers.add_parser('get-app', help='Get detailed app info')
    get_app_parser.add_argument('--app-id', required=True, help='App ID')
    
    args = parser.parse_args()
    
    # Generate token
    try:
        token = generate_token(args.key_id, args.issuer_id, args.key_file)
    except FileNotFoundError:
        print(json.dumps({'error': f'Key file not found: {args.key_file}'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': f'Failed to generate token: {e}'}))
        sys.exit(1)
    
    # Execute command
    if args.command == 'auth-test':
        result = {
            'success': True,
            'issuer_id': args.issuer_id,
            'key_id': args.key_id,
            'token_expires': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() + 1200))
        }
        print(json.dumps(result))
        sys.exit(0)
    
    elif args.command == 'list-apps':
        result = list_apps(token)
        if 'error' in result:
            # Check if it's an auth error
            if 'Authentication failed' in result.get('error', ''):
                print(json.dumps(result))
                sys.exit(2)
            print(json.dumps(result))
            sys.exit(1)
        print(json.dumps(result))
        sys.exit(0)
    
    elif args.command == 'list-builds':
        result = list_builds(token, args.app_id, args.limit)
        if 'error' in result:
            if 'Authentication failed' in result.get('error', ''):
                print(json.dumps(result))
                sys.exit(2)
            print(json.dumps(result))
            sys.exit(1)
        print(json.dumps(result))
        sys.exit(0)
    
    elif args.command == 'get-app':
        result = get_app(token, args.app_id)
        if 'error' in result:
            if 'Authentication failed' in result.get('error', ''):
                print(json.dumps(result))
                sys.exit(2)
            print(json.dumps(result))
            sys.exit(1)
        print(json.dumps(result))
        sys.exit(0)


if __name__ == '__main__':
    main()
