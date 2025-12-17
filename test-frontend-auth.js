// Test script to verify frontend authentication and account loading
// Run this in browser console at http://localhost:3000

console.log('=== Frontend Authentication Test ===');

// Check if AWS config is loaded
console.log('1. AWS Config:', window.AWS_CONFIG);

// Check if Amplify is configured
console.log('2. Amplify configured:', typeof window.Amplify !== 'undefined');

// Test authentication
async function testAuth() {
  try {
    console.log('3. Testing authentication...');
    
    // Import Amplify auth
    const { fetchAuthSession } = await import('aws-amplify/auth');
    
    // Get current session
    const session = await fetchAuthSession();
    console.log('4. Auth session:', {
      tokens: !!session.tokens,
      idToken: !!session.tokens?.idToken,
      accessToken: !!session.tokens?.accessToken
    });
    
    if (session.tokens?.idToken) {
      const token = session.tokens.idToken.toString();
      console.log('5. Token length:', token.length);
      console.log('6. Token preview:', token.substring(0, 50) + '...');
      
      // Test API call
      console.log('7. Testing API call...');
      const response = await fetch('https://1oyfgy2k66.execute-api.us-east-1.amazonaws.com/test/accounts/targets', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('8. API Response status:', response.status);
      const data = await response.json();
      console.log('9. API Response data:', data);
      
    } else {
      console.log('5. No auth token available');
    }
    
  } catch (error) {
    console.error('Auth test failed:', error);
  }
}

// Run the test
testAuth();