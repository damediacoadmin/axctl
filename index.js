#!/usr/bin/env node
/**
 * AXCTL - macOS Automation Toolkit
 * 
 * Main entry point for the AXCTL package
 * 
 * Components:
 * - Xcode Build Automation (bash scripts)
 * - App Store Connect API (Python CLI)
 * - Accessibility API Helper (Python CLI)
 */

const path = require('path');
const { execSync } = require('child_process');

// Export paths to the tools
module.exports = {
  paths: {
    xcodebuild: path.join(__dirname, 'skills/xcodebuild'),
    ascApi: path.join(__dirname, 'skills/asc-api-helper/asc-api-helper.py'),
    axHelper: path.join(__dirname, 'skills/ax-helper/ax-helper.py')
  },
  
  // Helper function to run ax-helper
  axHelper: (args) => {
    const script = path.join(__dirname, 'skills/ax-helper/ax-helper.py');
    return execSync(`python3 ${script} ${args}`, { encoding: 'utf8' });
  },
  
  // Helper function to run asc-api
  ascApi: (args) => {
    const script = path.join(__dirname, 'skills/asc-api-helper/asc-api-helper.py');
    return execSync(`python3 ${script} ${args}`, { encoding: 'utf8' });
  }
};

// If run directly, show help
if (require.main === module) {
  console.log(`
AXCTL - macOS Automation Toolkit

Tools:
  ax-helper    Accessibility API automation (query/click/type)
  asc-api      App Store Connect API client
  xcodebuild   Xcode automation scripts (archive/export/upload)

Documentation: https://axctl.dev
GitHub: https://github.com/damediacoadmin/axctl
  `);
}
