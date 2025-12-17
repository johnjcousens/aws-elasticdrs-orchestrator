#!/usr/bin/env node

// Complete test of frontend authentication and account loading
// This simulates what happens in the browser

const https = require('https');
const fs = require('fs');

async function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, data: parsed });
        } catch (e) {
          resolve({ status: res.statusCode, data: data });
        }
      });
    });
    
    req.on('error', reject);
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  });
}

async function testFrontendFlow() {
  console.log('=== Frontend Authentication Flow Test ===\n');
  
  try {
    // Step 1: Load local config (simulate browser loading aws-config.local.json)
    console.log('1. Loading local config...');
    const configPath = './frontend/public/aws-config.local.json';
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    console.log('   Config loaded:', {
      region: config.region,
      userPoolId: config.userPoolId,
      clientId: config.userPoolClientId,
      apiEndpoint: config.apiEndpoint
    });
    
    // Step 2: Authenticate with Cognito (simulate Amplify auth)
    console.log('\n2. Authenticating with Cognito...');
    const authResponse = await makeRequest('https://cognito-idp.us-east-1.amazonaws.com/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
      },
      body: JSON.stringify({
        ClientId: config.userPoolClientId,
        AuthFlow: 'USER_PASSWORD_AUTH',
        AuthParameters: {
          USERNAME: '***REMOVED***',
          PASSWORD: '***REMOVED***'
        }
      })
    });
    
    if (authResponse.status !== 200) {
      throw new Error(`Auth failed: ${authResponse.status} - ${JSON.stringify(authResponse.data)}`);
    }
    
    const token = authResponse.data.AuthenticationResult.IdToken;
    console.log('   ✅ Authentication successful');
    console.log('   Token length:', token.length);
    
    // Step 3: Test accounts API (simulate AccountContext.refreshAccounts)
    console.log('\n3. Testing accounts API...');
    const accountsResponse = await makeRequest(config.apiEndpoint + '/accounts/targets', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('   API Response status:', accountsResponse.status);
    if (accountsResponse.status === 200) {
      console.log('   ✅ Accounts loaded successfully');
      console.log('   Accounts:', accountsResponse.data);
      
      // Step 4: Test executions API (simulate ExecutionsPage)
      console.log('\n4. Testing executions API...');
      const executionsResponse = await makeRequest(config.apiEndpoint + '/executions', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('   Executions API status:', executionsResponse.status);
      if (executionsResponse.status === 200) {
        console.log('   ✅ Executions loaded successfully');
        console.log('   Execution count:', executionsResponse.data.count);
        console.log('   First execution:', executionsResponse.data.items[0]?.executionId);
        
        console.log('\n=== TEST RESULT: SUCCESS ===');
        console.log('✅ Frontend authentication flow is working correctly');
        console.log('✅ Account loading should work in browser');
        console.log('✅ Drill executions should be visible in UI');
        
      } else {
        console.log('   ❌ Executions API failed:', executionsResponse.data);
      }
      
    } else {
      console.log('   ❌ Accounts API failed:', accountsResponse.data);
    }
    
  } catch (error) {
    console.error('\n=== TEST RESULT: FAILED ===');
    console.error('❌ Error:', error.message);
  }
}

testFrontendFlow();