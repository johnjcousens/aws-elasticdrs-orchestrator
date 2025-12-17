#!/usr/bin/env node

/**
 * Debug script to test job logs API and understand the data structure
 * Run with: node test-job-events-debug.js
 */

const https = require('https');
const { URL } = require('url');

// Configuration from aws-config.json
const API_ENDPOINT = 'https://1oyfgy2k66.execute-api.us-east-1.amazonaws.com/test';
const EXECUTION_ID = '118991a4-6b5a-4400-a159-4b0b88b2f446';
const JOB_ID = 'drsjob-534ec63fb6d3edd46';

// Cognito config
const COGNITO_REGION = 'us-east-1';
const USER_POOL_ID = 'us-east-1_mo3iSHXvq';
const CLIENT_ID = '6tusgg2ekvmp2ke03u3hkhln74';

async function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const reqOptions = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || 443,
      path: parsedUrl.pathname + parsedUrl.search,
      method: options.method || 'GET',
      headers: options.headers || {}
    };

    const req = https.request(reqOptions, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: JSON.parse(data)
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: data
          });
        }
      });
    });

    req.on('error', reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function getAuthToken() {
  try {
    console.log(`🔐 Using Cognito Client ID: ${CLIENT_ID}`);
    
    // Use AWS SDK v3 to get token
    const { CognitoIdentityProviderClient, InitiateAuthCommand } = require('@aws-sdk/client-cognito-identity-provider');
    const cognito = new CognitoIdentityProviderClient({ region: COGNITO_REGION });
    
    const command = new InitiateAuthCommand({
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: CLIENT_ID,
      AuthParameters: {
        USERNAME: '***REMOVED***',
        PASSWORD: '***REMOVED***'
      }
    });
    
    const result = await cognito.send(command);
    console.log('✅ Got Cognito token');
    return result.AuthenticationResult.IdToken;
  } catch (error) {
    console.error('❌ Auth error:', error.message);
    return null;
  }
}

async function testJobLogsAPI(token) {
  console.log('\n📊 Testing Job Logs API...');
  console.log(`   Execution ID: ${EXECUTION_ID}`);
  console.log(`   Job ID: ${JOB_ID}`);
  
  const url = `${API_ENDPOINT}/executions/${EXECUTION_ID}/job-logs`;
  
  try {
    const result = await makeRequest(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`\n📊 Response Status: ${result.status}`);
    
    if (result.status === 200) {
      const data = result.data;
      console.log(`\n📊 Response Structure:`);
      console.log(`   executionId: ${data.executionId}`);
      console.log(`   jobLogs count: ${data.jobLogs?.length || 0}`);
      
      if (data.jobLogs && data.jobLogs.length > 0) {
        console.log(`\n📊 Job Logs Details:`);
        data.jobLogs.forEach((log, idx) => {
          console.log(`\n   Wave ${idx}:`);
          console.log(`     waveNumber: ${log.waveNumber} (type: ${typeof log.waveNumber})`);
          console.log(`     jobId: ${log.jobId}`);
          console.log(`     events count: ${log.events?.length || 0}`);
          console.log(`     error: ${log.error || 'none'}`);
          
          if (log.events && log.events.length > 0) {
            console.log(`\n     Events:`);
            log.events.slice(0, 5).forEach((event, eventIdx) => {
              console.log(`       ${eventIdx + 1}. ${event.event} at ${event.logDateTime}`);
              if (event.sourceServerId) console.log(`          sourceServerId: ${event.sourceServerId}`);
              if (event.conversionServerId) console.log(`          conversionServerId: ${event.conversionServerId}`);
            });
            if (log.events.length > 5) {
              console.log(`       ... and ${log.events.length - 5} more events`);
            }
          }
        });
      } else {
        console.log('\n⚠️  No job logs returned!');
      }
      
      // Full response for debugging
      console.log('\n📊 Full Response (JSON):');
      console.log(JSON.stringify(data, null, 2));
    } else {
      console.log(`\n❌ Error Response:`, result.data);
    }
  } catch (error) {
    console.error('❌ Request failed:', error.message);
  }
}

async function testExecutionDetails(token) {
  console.log('\n📊 Testing Execution Details API...');
  
  const url = `${API_ENDPOINT}/executions/${EXECUTION_ID}`;
  
  try {
    const result = await makeRequest(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`\n📊 Response Status: ${result.status}`);
    
    if (result.status === 200) {
      const data = result.data;
      console.log(`\n📊 Execution Details:`);
      console.log(`   ExecutionId: ${data.ExecutionId || data.executionId}`);
      console.log(`   Status: ${data.Status || data.status}`);
      console.log(`   Region: ${data.Region || data.region}`);
      
      const waves = data.Waves || data.waves || [];
      console.log(`   Waves count: ${waves.length}`);
      
      waves.forEach((wave, idx) => {
        console.log(`\n   Wave ${idx}:`);
        console.log(`     WaveNumber: ${wave.WaveNumber ?? wave.waveNumber}`);
        console.log(`     WaveName: ${wave.WaveName || wave.waveName}`);
        console.log(`     Status: ${wave.Status || wave.status}`);
        console.log(`     JobId: ${wave.JobId || wave.jobId || 'none'}`);
      });
    } else {
      console.log(`\n❌ Error Response:`, result.data);
    }
  } catch (error) {
    console.error('❌ Request failed:', error.message);
  }
}

async function main() {
  console.log('🚀 DRS Job Events Debug Script\n');
  console.log('='.repeat(60));
  
  // Get auth token
  const token = await getAuthToken();
  
  if (!token) {
    console.log('\n⚠️  Could not get auth token. Exiting.');
    return;
  }
  
  // Test execution details first
  await testExecutionDetails(token);
  
  console.log('\n' + '='.repeat(60));
  
  // Test job logs API
  await testJobLogsAPI(token);
  
  console.log('\n' + '='.repeat(60));
  console.log('✅ Debug complete');
}

main().catch(console.error);
