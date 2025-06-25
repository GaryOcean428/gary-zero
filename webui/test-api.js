// Test script to verify API functionality with mock backend
const baseUrl = 'http://localhost:8080';

async function testApiEndpoint(endpoint, data) {
    try {
        console.log(`Testing ${endpoint}...`);
        const response = await fetch(`${baseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log(`✅ ${endpoint} - Success:`, result);
        return result;
    } catch (error) {
        console.error(`❌ ${endpoint} - Error:`, error.message);
        return null;
    }
}

async function testAllEndpoints() {
    console.log('🚀 Starting API endpoint tests...\n');
    
    // Test /poll endpoint
    await testApiEndpoint('/poll', {
        log_from: 0,
        context: null,
        timezone: 'America/New_York'
    });
    
    // Test /send endpoint  
    await testApiEndpoint('/send', {
        message: 'Hello, this is a test message!',
        context: 'test'
    });
    
    // Test /reset endpoint
    await testApiEndpoint('/reset', {});
    
    // Test /new_chat endpoint
    await testApiEndpoint('/new_chat', {
        title: 'Test Chat'
    });
    
    console.log('\n🎉 API endpoint testing completed!');
}

// Run the tests
testAllEndpoints();
