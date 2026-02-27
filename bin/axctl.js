#!/usr/bin/env node
/**
 * AXCTL CLI
 * Main command-line interface
 */

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === 'help' || args[0] === '--help' || args[0] === '-h') {
  console.log(`
╔═══════════════════════════════════════════════════════════════╗
║                   AXCTL - macOS Automation Toolkit             ║
╚═══════════════════════════════════════════════════════════════╝

USAGE:
  axctl <command> [options]

COMMANDS:
  help              Show this help message
  activate <key>    Activate your AXCTL license
  version           Show version information

TOOLS:
  ax-helper         Accessibility API automation
  asc-api           App Store Connect API client
  
XCODE SCRIPTS:
  Located in: node_modules/@axctl/core/skills/xcodebuild/
  - xcode-archive.sh       Build and archive Xcode project
  - xcode-export.sh        Export IPA from archive
  - xcode-upload.sh        Upload to App Store Connect
  - xcode-increment-build.sh  Increment build number

EXAMPLES:
  # Query UI elements in Chrome
  ax-helper query "Google Chrome"
  
  # Archive and export iOS app
  cd YourApp
  xcode-archive.sh
  xcode-export.sh path/to/YourApp.xcarchive
  
  # Get app info from App Store Connect
  asc-api apps list

DOCUMENTATION:
  Website: https://axctl.dev
  GitHub:  https://github.com/damediacoadmin/axctl
  Support: hello@axctl.dev

LICENSE:
  Your license status and machine registration is managed at:
  https://agile-enjoyment-production-82c8.up.railway.app
`);
  process.exit(0);
}

// Handle version command
if (args[0] === 'version' || args[0] === '--version' || args[0] === '-v') {
  const pkg = require('../package.json');
  console.log(`AXCTL v${pkg.version}`);
  process.exit(0);
}

// Handle activate command
if (args[0] === 'activate') {
  const { execSync } = require('child_process');
  const path = require('path');
  const activateScript = path.join(__dirname, 'activate.js');
  
  try {
    execSync(`node ${activateScript} ${args.slice(1).join(' ')}`, { stdio: 'inherit' });
  } catch (err) {
    process.exit(1);
  }
  process.exit(0);
}

console.error(`Unknown command: ${args[0]}`);
console.log('Run "axctl help" for usage information');
process.exit(1);
