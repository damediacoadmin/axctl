"""API client functions for App Store Connect."""

import requests

BASE_URL = 'https://api.appstoreconnect.apple.com/v1'


def list_apps(token: str) -> dict:
    """
    List all apps in the account.
    
    Args:
        token: JWT token for authentication
        
    Returns:
        Dict containing apps list and count
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.get(
            f'{BASE_URL}/apps',
            headers=headers,
            params={'limit': 200}
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return {'error': 'Authentication failed. Check your credentials.'}
        return {'error': f'HTTP error: {e}'}
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {e}'}
    
    data = response.json()
    
    apps = []
    for app in data.get('data', []):
        apps.append({
            'id': app['id'],
            'bundle_id': app['attributes'].get('bundleId', ''),
            'name': app['attributes'].get('name', ''),
            'sku': app['attributes'].get('sku', ''),
            'platform': app['attributes'].get('platform', '')
        })
    
    return {
        'apps': apps,
        'count': len(apps)
    }


def list_builds(token: str, app_id: str, limit: int = 10) -> dict:
    """
    List builds for an app.
    
    Args:
        token: JWT token for authentication
        app_id: The app ID to list builds for
        limit: Maximum number of builds to return
        
    Returns:
        Dict containing builds list and count
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.get(
            f'{BASE_URL}/builds',
            headers=headers,
            params={
                'filter[app]': app_id,
                'limit': limit
            }
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return {'error': 'Authentication failed. Check your credentials.'}
        return {'error': f'HTTP error: {e}'}
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {e}'}
    
    data = response.json()
    
    builds = []
    for build in data.get('data', []):
        builds.append({
            'id': build['id'],
            'version': build['attributes'].get('version', ''),
            'build_number': build['attributes'].get('buildNumber', ''),
            'upload_date': build['attributes'].get('uploadDate', ''),
            'processing_state': build['attributes'].get('processingState', ''),
            'expired': build['attributes'].get('expired', False),
            'testflight_enabled': build['attributes'].get('testflightEnabled', True)
        })
    
    return {
        'builds': builds,
        'count': len(builds)
    }


def get_app(token: str, app_id: str) -> dict:
    """
    Get detailed app info.
    
    Args:
        token: JWT token for authentication
        app_id: The app ID to get details for
        
    Returns:
        Dict containing app details
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.get(
            f'{BASE_URL}/apps/{app_id}',
            headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return {'error': 'Authentication failed. Check your credentials.'}
        return {'error': f'HTTP error: {e}'}
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {e}'}
    
    data = response.json()
    app = data.get('data', {})
    attrs = app.get('attributes', {})
    
    return {
        'id': app.get('id', ''),
        'bundle_id': attrs.get('bundleId', ''),
        'name': attrs.get('name', ''),
        'sku': attrs.get('sku', ''),
        'primary_locale': attrs.get('primaryLocale', ''),
        'available_in_new_territories': attrs.get('availableInNewTerritories', True),
        'content_rights_declaration': attrs.get('contentRightsDeclaration', '')
    }
