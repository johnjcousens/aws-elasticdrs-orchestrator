// Debug script to test tag preview data structure
// Run this in browser console on the protection group dialog page

console.log('=== Debug Tag Preview Data ===');

// Check if we can access the preview data
if (window.React && window.React.version) {
    console.log('React version:', window.React.version);
}

// Function to inspect server data structure
function inspectServerData() {
    // Try to find the preview servers data in React components
    const containers = document.querySelectorAll('[data-testid], .awsui-container');
    console.log('Found containers:', containers.length);
    
    // Look for server list items
    const serverItems = document.querySelectorAll('[style*="padding: 16px"]');
    console.log('Found potential server items:', serverItems.length);
    
    if (serverItems.length > 0) {
        console.log('First server item HTML:', serverItems[0].outerHTML.substring(0, 500));
    }
    
    // Check if there are any click handlers for expansion
    const expandableElements = document.querySelectorAll('[style*="cursor: pointer"]');
    console.log('Found clickable elements:', expandableElements.length);
    
    expandableElements.forEach((el, i) => {
        if (el.textContent.includes('Details') || el.textContent.includes('▶') || el.textContent.includes('▼')) {
            console.log(`Expandable element ${i}:`, el.textContent.trim());
        }
    });
}

// Run inspection
inspectServerData();

// Also check for any JavaScript errors
console.log('=== Checking for errors ===');
window.addEventListener('error', (e) => {
    console.error('JavaScript error:', e.error);
});

console.log('=== Debug complete ===');
console.log('Instructions:');
console.log('1. Open Protection Groups dialog');
console.log('2. Go to "Select by Tags" tab');
console.log('3. Add tags and click Preview');
console.log('4. Run inspectServerData() again to see the data');