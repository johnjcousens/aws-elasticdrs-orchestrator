// Simple test to verify API response structure
const axios = require('axios');

async function testAPI() {
  try {
    // Get token
    const { execSync } = require('child_process');
    const token = execSync(`aws cognito-idp initiate-auth --client-id 5bpcd63knd89c4pnbneth6u21j --auth-flow USER_PASSWORD_AUTH --auth-parameters USERNAME=***REMOVED***,PASSWORD=***REMOVED*** --query 'AuthenticationResult.IdToken' --output text --region us-east-1`, { encoding: 'utf8' }).trim();
    
    console.log('Token obtained:', token.substring(0, 50) + '...');
    
    // Make API call
    const response = await axios.get('https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev/drs/source-servers?region=us-west-2', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('Response status:', response.status);
    console.log('Response data keys:', Object.keys(response.data));
    console.log('Servers count:', response.data.servers?.length);
    console.log('First server hardware:', response.data.servers?.[0]?.hardware);
    console.log('Hardware types:', {
      totalCores: typeof response.data.servers?.[0]?.hardware?.totalCores,
      ramGiB: typeof response.data.servers?.[0]?.hardware?.ramGiB,
      totalDiskGiB: typeof response.data.servers?.[0]?.hardware?.totalDiskGiB
    });
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

testAPI();