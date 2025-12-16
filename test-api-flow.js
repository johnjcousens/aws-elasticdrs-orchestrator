#!/usr/bin/env node

const axios = require('axios');

async function testApiFlow() {
    try {
        console.log('=== Testing API Flow ===');
        
        // Step 1: Get Cognito token
        console.log('1. Getting Cognito token...');
        const { execSync } = require('child_process');
        const token = execSync(`aws cognito-idp initiate-auth --client-id 5bpcd63knd89c4pnbneth6u21j --auth-flow USER_PASSWORD_AUTH --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! --query 'AuthenticationResult.IdToken' --output text --region us-east-1`, { encoding: 'utf8' }).trim();
        console.log('Token obtained:', token.substring(0, 50) + '...');
        
        // Step 2: Make API call
        console.log('2. Making API call...');
        const response = await axios.get('https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev/drs/source-servers?region=us-west-2', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('3. API Response Status:', response.status);
        console.log('4. Response Headers:', response.headers['content-type']);
        console.log('5. Response Data Type:', typeof response.data);
        console.log('6. Response Keys:', Object.keys(response.data));
        
        // Step 3: Check servers array
        const servers = response.data.servers;
        console.log('7. Servers Array Length:', servers?.length);
        console.log('8. First Server Keys:', Object.keys(servers?.[0] || {}));
        
        // Step 4: Check hardware data specifically
        const firstServer = servers?.[0];
        console.log('9. First Server Hardware:', JSON.stringify(firstServer?.hardware, null, 2));
        console.log('10. Hardware Type:', typeof firstServer?.hardware);
        console.log('11. Hardware Keys:', Object.keys(firstServer?.hardware || {}));
        
        // Step 5: Test the exact logic from ServerListItem
        const hardware = firstServer?.hardware;
        console.log('12. Hardware Variable:', hardware);
        console.log('13. totalCores:', hardware?.totalCores);
        console.log('14. ramGiB:', hardware?.ramGiB);
        console.log('15. totalDiskGiB:', hardware?.totalDiskGiB);
        
        // Step 6: Test nullish coalescing
        console.log('16. CPU Display:', hardware?.totalCores ?? 'Unknown');
        console.log('17. RAM Display:', hardware?.ramGiB ?? 'Unknown');
        console.log('18. Disk Display:', hardware?.totalDiskGiB ?? 'Unknown');
        
        // Step 7: Test logical OR (old approach)
        console.log('19. CPU Display (OR):', hardware?.totalCores || 'Unknown');
        console.log('20. RAM Display (OR):', hardware?.ramGiB || 'Unknown');
        console.log('21. Disk Display (OR):', hardware?.totalDiskGiB || 'Unknown');
        
        console.log('=== Test Complete ===');
        
    } catch (error) {
        console.error('Error:', error.message);
        if (error.response) {
            console.error('Response Status:', error.response.status);
            console.error('Response Data:', error.response.data);
        }
    }
}

testApiFlow();