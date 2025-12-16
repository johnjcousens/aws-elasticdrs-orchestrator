#!/usr/bin/env node

/**
 * Debug Hardware Issue
 * 
 * This script will make the exact same API call as the frontend
 * and then simulate the exact same rendering logic to identify
 * where the hardware data is being lost.
 */

const axios = require('axios');

const API_ENDPOINT = 'https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev';
const REGION = 'us-west-2';

async function getCognitoToken() {
  const AWS = require('aws-sdk');
  const cognito = new AWS.CognitoIdentityServiceProvider({ region: 'us-east-1' });
  
  const params = {
    AuthFlow: 'USER_PASSWORD_AUTH',
    ClientId: '5bpcd63knd89c4pnbneth6u21j',
    AuthParameters: {
      USERNAME: 'testuser@example.com',
      PASSWORD: 'TestPassword123!'
    }
  };
  
  const result = await cognito.initiateAuth(params).promise();
  return result.AuthenticationResult.IdToken;
}

async function debugHardwareIssue() {
  console.log('=== Debug Hardware Issue ===');
  
  try {
    console.log('1. Getting Cognito token...');
    const token = await getCognitoToken();
    
    console.log('2. Making API call (same as frontend)...');
    const response = await axios.get(`${API_ENDPOINT}/drs/source-servers`, {
      params: { region: REGION },
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('3. Raw response data type:', typeof response.data);
    console.log('4. Raw response keys:', Object.keys(response.data));
    
    const apiData = response.data;
    console.log('5. API data structure:');
    console.log('   - servers array length:', apiData.servers?.length);
    console.log('   - first server keys:', Object.keys(apiData.servers?.[0] || {}));
    
    const firstServer = apiData.servers?.[0];
    if (firstServer) {
      console.log('6. First server analysis:');
      console.log('   - hostname:', firstServer.hostname);
      console.log('   - hardware exists:', !!firstServer.hardware);
      console.log('   - hardware type:', typeof firstServer.hardware);
      console.log('   - hardware keys:', firstServer.hardware ? Object.keys(firstServer.hardware) : 'none');
      console.log('   - hardware object:', JSON.stringify(firstServer.hardware, null, 2));
      
      // Simulate frontend logic exactly
      const hardware = firstServer.hardware;
      console.log('7. Frontend simulation:');
      console.log('   - hardware variable:', hardware);
      console.log('   - !!hardware:', !!hardware);
      console.log('   - hardware ? "exists" : "missing":', hardware ? "exists" : "missing");
      
      if (hardware) {
        console.log('   - totalCores:', hardware.totalCores);
        console.log('   - ramGiB:', hardware.ramGiB);
        console.log('   - totalDiskGiB:', hardware.totalDiskGiB);
        console.log('   - totalCores type:', typeof hardware.totalCores);
        console.log('   - ramGiB type:', typeof hardware.ramGiB);
        console.log('   - totalDiskGiB type:', typeof hardware.totalDiskGiB);
        
        // Test nullish coalescing
        console.log('   - totalCores ?? "Unknown":', hardware.totalCores ?? "Unknown");
        console.log('   - ramGiB ?? "Unknown":', hardware.ramGiB ?? "Unknown");
        console.log('   - totalDiskGiB ?? "Unknown":', hardware.totalDiskGiB ?? "Unknown");
        
        // Test logical OR (old way)
        console.log('   - totalCores || "Unknown":', hardware.totalCores || "Unknown");
        console.log('   - ramGiB || "Unknown":', hardware.ramGiB || "Unknown");
        console.log('   - totalDiskGiB || "Unknown":', hardware.totalDiskGiB || "Unknown");
      }
      
      // Test all servers
      console.log('8. All servers hardware check:');
      apiData.servers.forEach((server, i) => {
        const hw = server.hardware;
        console.log(`   Server ${i + 1} (${server.hostname}):`, {
          hasHardware: !!hw,
          totalCores: hw?.totalCores,
          ramGiB: hw?.ramGiB,
          totalDiskGiB: hw?.totalDiskGiB
        });
      });
    }
    
  } catch (error) {
    console.error('Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
  }
  
  console.log('=== Debug Complete ===');
}

debugHardwareIssue();