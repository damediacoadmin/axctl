#!/usr/bin/env node
/**
 * AXCTL License Activation
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const API_URL = 'https://agile-enjoyment-production-82c8.up.railway.app';
const CONFIG_DIR = path.join(require('os').homedir(), '.axctl');
const LICENSE_FILE = path.join(CONFIG_DIR, 'license.json');

function getMachineId() {
  try {
    // Get hardware UUID on macOS
    const uuid = execSync('system_profiler SPHardwareDataType | grep "Hardware UUID"', { encoding: 'utf8' });
    return uuid.split(':')[1].trim();
  } catch (err) {
    console.error('Error getting machine ID:', err.message);
    process.exit(1);
  }
}

function activateLicense(licenseKey) {
  const machineId = getMachineId();
  
  console.log('Activating license...');
  console.log('License:', licenseKey);
  console.log('Machine ID:', machineId);
  
  const data = JSON.stringify({
    license_key: licenseKey,
    machine_id: machineId
  });
  
  const options = {
    hostname: 'agile-enjoyment-production-82c8.up.railway.app',
    path: '/activate',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': data.length
    }
  };
  
  const req = https.request(options, (res) => {
    let body = '';
    
    res.on('data', (chunk) => {
      body += chunk;
    });
    
    res.on('end', () => {
      try {
        const response = JSON.parse(body);
        
        if (res.statusCode === 200 && (response.valid || response.success)) {
          // Save license locally
          if (!fs.existsSync(CONFIG_DIR)) {
            fs.mkdirSync(CONFIG_DIR, { recursive: true });
          }
          
          const licenseData = {
            key: licenseKey,
            machine_id: machineId,
            plan: response.plan,
            activated_at: new Date().toISOString()
          };
          
          fs.writeFileSync(LICENSE_FILE, JSON.stringify(licenseData, null, 2));
          
          console.log('\n✅ License activated successfully!');
          console.log('Plan:', response.plan);
          console.log('Max machines:', response.max_machines);
          if (response.message) {
            console.log('Note:', response.message);
          }
          console.log('\nYou can now use Pro features:');
          console.log('  - xcodebuild automation');
          console.log('  - App Store Connect API');
          console.log('\nStored in:', LICENSE_FILE);
        } else {
          console.error('\n❌ Activation failed:', response.error || response.message || 'Unknown error');
          process.exit(1);
        }
      } catch (err) {
        console.error('Error parsing response:', err.message);
        console.error('Response:', body);
        process.exit(1);
      }
    });
  });
  
  req.on('error', (err) => {
    console.error('Network error:', err.message);
    process.exit(1);
  });
  
  req.write(data);
  req.end();
}

function showStatus() {
  if (!fs.existsSync(LICENSE_FILE)) {
    console.log('No license activated.');
    console.log('\nTo activate a license:');
    console.log('  axctl activate YOUR-LICENSE-KEY');
    console.log('\nGet a license at: https://axctl.dev');
    return;
  }
  
  const license = JSON.parse(fs.readFileSync(LICENSE_FILE, 'utf8'));
  console.log('License Status:');
  console.log('  Key:', license.key);
  console.log('  Plan:', license.plan);
  console.log('  Machine ID:', license.machine_id);
  console.log('  Activated:', license.activated_at);
}

// Main
const args = process.argv.slice(2);

if (args.length === 0) {
  showStatus();
} else if (args[0] === 'status') {
  showStatus();
} else {
  const licenseKey = args[0];
  if (!licenseKey.startsWith('AXCTL-')) {
    console.error('Invalid license key format. Should start with AXCTL-');
    process.exit(1);
  }
  activateLicense(licenseKey);
}
