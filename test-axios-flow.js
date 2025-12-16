// Test the exact axios flow that the frontend uses
const https = require('https');
const { URL } = require('url');

async function makeAxiosLikeRequest() {
  try {
    // Get token first
    const { execSync } = require('child_process');
    const token = execSync(`aws cognito-idp initiate-auth --client-id 5bpcd63knd89c4pnbneth6u21j --auth-flow USER_PASSWORD_AUTH --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! --query 'AuthenticationResult.IdToken' --output text --region us-east-1`, { encoding: 'utf8' }).trim();
    
    console.log('✅ Token obtained');
    
    // Make request exactly like axios would with query parameters
    const baseURL = 'https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev';
    const path = '/drs/source-servers';
    const params = new URLSearchParams({ region: 'us-west-2' });
    const fullURL = `${baseURL}${path}?${params.toString()}`;
    
    console.log('🔗 Making request to:', fullURL);
    
    const url = new URL(fullURL);
    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname + url.search,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    };
    
    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            const response = JSON.parse(data);
            console.log('📊 Response status:', res.statusCode);
            console.log('📊 Response headers:', res.headers);
            console.log('📊 Response keys:', Object.keys(response));
            console.log('📊 Servers count:', response.servers?.length);
            
            if (response.servers && response.servers.length > 0) {
              const firstServer = response.servers[0];
              console.log('🖥️  First server:', firstServer.hostname);
              console.log('🔧 Hardware exists:', !!firstServer.hardware);
              console.log('🔧 Hardware object:', JSON.stringify(firstServer.hardware, null, 2));
              
              if (firstServer.hardware) {
                console.log('📈 Hardware fields:');
                console.log('   totalCores:', firstServer.hardware.totalCores, '(type:', typeof firstServer.hardware.totalCores, ')');
                console.log('   ramGiB:', firstServer.hardware.ramGiB, '(type:', typeof firstServer.hardware.ramGiB, ')');
                console.log('   totalDiskGiB:', firstServer.hardware.totalDiskGiB, '(type:', typeof firstServer.hardware.totalDiskGiB, ')');
                
                // Test the exact logic from ServerListItem
                const hardware = firstServer.hardware;
                const hardwareExists = !!hardware;
                const totalCores = hardware?.totalCores || 'Unknown';
                const ramGiB = hardware?.ramGiB || 'Unknown';
                const totalDiskGiB = hardware?.totalDiskGiB || 'Unknown';
                
                console.log('🧪 ServerListItem logic test:');
                console.log('   hardwareExists:', hardwareExists);
                console.log('   totalCores with fallback:', totalCores);
                console.log('   ramGiB with fallback:', ramGiB);
                console.log('   totalDiskGiB with fallback:', totalDiskGiB);
                
                // Test the conditional rendering logic
                if (hardware) {
                  console.log('✅ Hardware condition is truthy - should render hardware info');
                  console.log('   Display: CPU:', totalCores, 'cores | RAM:', ramGiB, 'GiB | Disk:', totalDiskGiB, 'GiB');
                } else {
                  console.log('❌ Hardware condition is falsy - should show "NO HARDWARE DATA FOUND"');
                }
              } else {
                console.log('❌ No hardware object found');
              }
            } else {
              console.log('❌ No servers found in response');
            }
            
            resolve(response);
          } catch (error) {
            console.error('❌ Error parsing response:', error);
            console.error('Raw response:', data);
            reject(error);
          }
        });
      });
      
      req.on('error', (error) => {
        console.error('❌ Request error:', error);
        reject(error);
      });
      
      req.end();
    });
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

console.log('🚀 Testing axios-like request flow...');
makeAxiosLikeRequest().then(() => {
  console.log('✅ Test completed');
}).catch((error) => {
  console.error('❌ Test failed:', error);
});