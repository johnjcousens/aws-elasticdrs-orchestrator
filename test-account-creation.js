// Test script to create target account without cross-account role ARN
const testAccountCreation = async () => {
  const apiEndpoint = 'https://ixqhqhqhqh.execute-api.us-east-1.amazonaws.com/prod';
  
  // Test data - current account without cross-account role ARN
  const testData = {
    accountId: '438465159935',
    accountName: 'Current Account Test',
    stagingAccountId: '',
    stagingAccountName: '',
    crossAccountRoleArn: '' // Empty - should be allowed for current account
  };
  
  try {
    const response = await fetch(`${apiEndpoint}/accounts/targets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer mock-token' // You'll need real token
      },
      body: JSON.stringify(testData)
    });
    
    const result = await response.json();
    console.log('Response status:', response.status);
    console.log('Response data:', result);
    
    if (!response.ok) {
      console.error('Error:', result);
    } else {
      console.log('Success:', result);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};

// Run the test
testAccountCreation();