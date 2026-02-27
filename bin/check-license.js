#!/usr/bin/env node
/**
 * Check if user has a valid Pro license
 * Exit 0 if licensed, exit 1 if not
 */

const fs = require('fs');
const path = require('path');

const LICENSE_FILE = path.join(require('os').homedir(), '.axctl', 'license.json');

if (!fs.existsSync(LICENSE_FILE)) {
  console.error('❌ No AXCTL license found.');
  console.error('\nThis is a Pro feature. To use it:');
  console.error('  1. Get a license at https://axctl.dev');
  console.error('  2. Activate: axctl activate YOUR-LICENSE-KEY');
  console.error('\nOr use the free ax-helper tool for desktop automation.');
  process.exit(1);
}

try {
  const license = JSON.parse(fs.readFileSync(LICENSE_FILE, 'utf8'));
  
  // Basic validation
  if (!license.key || !license.plan) {
    console.error('❌ Invalid license file. Please reactivate.');
    console.error('Run: axctl activate YOUR-LICENSE-KEY');
    process.exit(1);
  }
  
  // For now, we trust the local license
  // TODO: Add online validation check
  
  // Silent success (exit 0)
  process.exit(0);
  
} catch (err) {
  console.error('❌ Error reading license:', err.message);
  process.exit(1);
}
