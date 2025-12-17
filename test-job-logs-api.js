#!/usr/bin/env node

/**
 * Test the job logs API directly to debug the issue
 */

const https = require('https');

// Test configuration
const EXECUTION_ID = '118991a4-6b5a-4400-a159-4b0b88b2f446';
const JOB_ID = 'drsjob-534ec63fb6d3edd46';
const API_ENDPOINT = 'https://1oyfgy2k66.execute-api.us-east-1.amazonaws.com/test';

// Test user credentials
const TEST_EMAIL = 'testuser@example.com';
const TEST_PASSWORD = 'TestPassword123!';

async function getCognitoToken() {
  console.log('🔐 Getting Cognito token...');
  
  const AWS = require('aws-sdk');
  const cognito = new AWS.CognitoIdentityServiceProvider({ region: 'us-east-1' });
  
  try {
    const params = {
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: '2ej8aqhqvhqhvhqhvhqhvhqhvh', // This will need to be the real client ID
      AuthParameters: {
        USERNAME: TEST_EMAIL,
        PASSWORD: TEST_PASSWORD
      }
    };
    
    const result = await cognito.initiateAuth(params).promise();
    const token = result.AuthenticationResult.IdToken;
    console.log('✅ Got Cognito token');
    return token;
  } catch (error) {
    console.error('❌ Failed to get Cognito token:', error.message);
    return null;
  }
}

async function testJobLogsAPI(token) {
  console.log(`🔍 Testing job logs API for execution ${EXECUTION_ID}...`);
  
  const url = `${API_ENDPOINT}/executions/${EXECUTION_ID}/job-logs`;
  
  return new Promise((resolve, reject) => {
    const options = {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(url, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        console.log(`📊 API Response Status: ${res.statusCode}`);
        console.log(`📊 API Response Headers:`, res.headers);
        
        try {
          const response = JSON.parse(data);
          console.log(`📊 API Response Body:`, JSON.stringify(response, null, 2));
          resolve(response);
        } catch (error) {
          console.log(`📊 Raw Response Body:`, data);
          resolve({ error: 'Invalid JSON response', raw: data });
        }
      });
    });
    
    req.on('error', (error) => {
      console.error('❌ API Request failed:', error.message);
      reject(error);
    });
    
    req.end();
  });
}

async function testWithoutAuth() {
  console.log('🔍 Testing job logs API without auth (should fail)...');
  
  const url = `${API_ENDPOINT}/executions/${EXECUTION_ID}/job-logs`;
  
  return new Promise((resolve, reject) => {
    const options = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(url, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        console.log(`📊 No-Auth Response Status: ${res.statusCode}`);
        try {
          const response = JSON.parse(data);
          console.log(`📊 No-Auth Response:`, JSON.stringify(response, null, 2));
        } catch (error) {
          console.log(`📊 No-Auth Raw Response:`, data);
        }
        resolve();
      });
    });
    
    req.on('error', (error) => {
      console.error('❌ No-Auth Request failed:', error.message);
      resolve();
    });
    
    req.end();
  });
}

async function main() {
  console.log('🚀 Starting job logs API test...\n');
  
  // Test without auth first
  await testWithoutAuth();
  console.log('\n' + '='.repeat(50) + '\n');
  
  // For now, let's skip the Cognito auth and just test the structure
  console.log('⚠️  Skipping Cognito auth for now - testing API structure');
  
  // Let's check if we can reach the API at all
  console.log('🔍 Testing API connectivity...');
  
  const testUrl = `${API_ENDPOINT}/health`;
  
  return new Promise((resolve, reject) => {
    const options = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(testUrl, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        console.log(`📊 Health Check Status: ${res.statusCode}`);
        try {
          const response = JSON.parse(data);
          console.log(`📊 Health Check Response:`, JSON.stringify(response, null, 2));
        } catch (error) {
          console.log(`📊 Health Check Raw Response:`, data);
        }
        resolve();
      });
    });
    
    req.on('error', (error) => {
      console.error('❌ Health Check failed:', error.message);
      resolve();
    });
    
    req.end();
  });
}

if (require.main === module) {
  main().catch(console.error);
}