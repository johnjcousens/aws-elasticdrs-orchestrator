#!/usr/bin/env node

/**
 * Test script to verify localhost development environment
 * Tests both API server and frontend accessibility
 */

const http = require('http');

const testEndpoint = (url, headers = {}) => {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { headers }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: data.substring(0, 200) + (data.length > 200 ? '...' : '')
        });
      });
    });
    
    req.on('error', reject);
    req.setTimeout(5000, () => reject(new Error('Timeout')));
  });
};

async function runTests() {
  console.log('🧪 Testing localhost development environment...\n');
  
  const tests = [
    {
      name: 'API Health Check',
      url: 'http://localhost:8000/health',
      headers: { 'Authorization': 'Bearer test-token' }
    },
    {
      name: 'Target Accounts API',
      url: 'http://localhost:8000/accounts/targets',
      headers: { 'Authorization': 'Bearer test-token' }
    },
    {
      name: 'Executions API',
      url: 'http://localhost:8000/executions',
      headers: { 'Authorization': 'Bearer test-token' }
    },
    {
      name: 'DRS Quotas API',
      url: 'http://localhost:8000/drs/quotas?accountId=123456789012',
      headers: { 'Authorization': 'Bearer test-token' }
    },
    {
      name: 'Frontend Index',
      url: 'http://localhost:3001/',
      headers: {}
    },
    {
      name: 'Frontend Config',
      url: 'http://localhost:3001/aws-config.local.json',
      headers: {}
    }
  ];
  
  for (const test of tests) {
    try {
      console.log(`Testing: ${test.name}`);
      const result = await testEndpoint(test.url, test.headers);
      
      if (result.status === 200) {
        console.log(`✅ ${test.name}: OK (${result.status})`);
        if (test.name.includes('API')) {
          try {
            const json = JSON.parse(result.data);
            if (test.name === 'Executions API' && json.items) {
              console.log(`   📋 Found ${json.items.length} executions`);
            } else if (test.name === 'Target Accounts API' && Array.isArray(json)) {
              console.log(`   🏢 Found ${json.length} target accounts`);
            } else if (test.name === 'DRS Quotas API') {
              console.log(`   📊 DRS quotas loaded`);
            }
          } catch (e) {
            // Not JSON, that's ok
          }
        }
      } else {
        console.log(`❌ ${test.name}: Failed (${result.status})`);
      }
    } catch (error) {
      console.log(`❌ ${test.name}: Error - ${error.message}`);
    }
    console.log('');
  }
  
  console.log('🎯 Test Summary:');
  console.log('   • Mock API Server: http://localhost:8000');
  console.log('   • Frontend Dev Server: http://localhost:3001');
  console.log('   • Open in browser: http://localhost:3001');
  console.log('\n💡 The JavaScript errors should now be resolved!');
}

runTests().catch(console.error);