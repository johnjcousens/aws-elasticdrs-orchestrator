// Debug the frontend flow by simulating the exact API client behavior
const axios = require('axios');

async function testFrontendFlow() {
  try {
    // Get token
    const { execSync } = require('child_process');
    const token = execSync(`aws cognito-idp initiate-auth --client-id 5bpcd63knd89c4pnbneth6u21j --auth-flow USER_PASSWORD_AUTH --auth-parameters USERNAME=***REMOVED***,PASSWORD=***REMOVED*** --query 'AuthenticationResult.IdToken' --output text --region us-east-1`, { encoding: 'utf8' }).trim();
    
    console.log('✅ Token obtained');
    
    // Create axios instance exactly like the frontend
    const axiosInstance = axios.create({
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Set baseURL and auth header like the frontend interceptor
    const baseURL = 'https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev';
    
    console.log('🔗 Making request to:', `${baseURL}/drs/source-servers`);
    
    // Make the exact request the frontend makes
    const response = await axiosInstance.get('/drs/source-servers', {
      baseURL: baseURL,
      params: { region: 'us-west-2' },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('📊 Response status:', response.status);
    console.log('📊 Response data keys:', Object.keys(response.data));
    console.log('📊 Servers count:', response.data.servers?.length);
    
    // Test the exact flow that ServerDiscoveryPanel uses
    const apiResponse = response.data;
    console.log('🔍 API Response structure:');
    console.log('   - region:', apiResponse.region);
    console.log('   - initialized:', apiResponse.initialized);
    console.log('   - servers array length:', apiResponse.servers?.length);
    console.log('   - hardwareDataIncluded:', apiResponse.hardwareDataIncluded);
    
    if (apiResponse.servers && apiResponse.servers.length > 0) {
      const firstServer = apiResponse.servers[0];
      console.log('🖥️  First server analysis:');
      console.log('   - hostname:', firstServer.hostname);
      console.log('   - hardware exists:', !!firstServer.hardware);
      console.log('   - hardware keys:', firstServer.hardware ? Object.keys(firstServer.hardware) : 'none');
      
      if (firstServer.hardware) {
        console.log('   - totalCores:', firstServer.hardware.totalCores, '(type:', typeof firstServer.hardware.totalCores, ')');
        console.log('   - ramGiB:', firstServer.hardware.ramGiB, '(type:', typeof firstServer.hardware.ramGiB, ')');
        console.log('   - totalDiskGiB:', firstServer.hardware.totalDiskGiB, '(type:', typeof firstServer.hardware.totalDiskGiB, ')');
        
        // Test ServerListItem rendering logic
        const hardware = firstServer.hardware;
        console.log('🧪 ServerListItem rendering test:');
        console.log('   - hardware truthy check:', !!hardware);
        console.log('   - hardware?.totalCores:', hardware?.totalCores);
        console.log('   - hardware?.ramGiB:', hardware?.ramGiB);
        console.log('   - hardware?.totalDiskGiB:', hardware?.totalDiskGiB);
        
        // Simulate the exact JSX condition
        if (hardware) {
          console.log('✅ JSX condition {hardware ? (...) : (...)} would render hardware block');
          console.log('   Display would be: CPU:', (hardware.totalCores || 'Unknown'), 'cores | RAM:', (hardware.ramGiB || 'Unknown'), 'GiB | Disk:', (hardware.totalDiskGiB || 'Unknown'), 'GiB');
        } else {
          console.log('❌ JSX condition would render "NO HARDWARE DATA FOUND"');
        }
      }
      
      // Test all servers
      console.log('📋 All servers hardware check:');
      apiResponse.servers.forEach((server, index) => {
        const hasHardware = !!server.hardware;
        const cores = server.hardware?.totalCores || 'N/A';
        const ram = server.hardware?.ramGiB || 'N/A';
        const disk = server.hardware?.totalDiskGiB || 'N/A';
        console.log(`   ${index + 1}. ${server.hostname}: hardware=${hasHardware} | CPU=${cores} | RAM=${ram} | Disk=${disk}`);
      });
    }
    
    return apiResponse;
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.response) {
      console.error('   Status:', error.response.status);
      console.error('   Data:', error.response.data);
    }
  }
}

console.log('🚀 Testing frontend axios flow...');
testFrontendFlow().then(() => {
  console.log('✅ Frontend flow test completed');
}).catch((error) => {
  console.error('❌ Frontend flow test failed:', error);
});