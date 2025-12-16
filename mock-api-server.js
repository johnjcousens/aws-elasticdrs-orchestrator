#!/usr/bin/env node

const express = require('express');
const cors = require('cors');
const app = express();
const port = 8000;

// Enable CORS for all routes
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:5173', 'http://localhost:4173'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Origin', 'Accept']
}));

// Parse JSON bodies
app.use(express.json());

// Mock data storage
let targetAccounts = [
  {
    accountId: '123456789012',
    name: 'Current Account',
    description: 'The account where this solution is deployed',
    crossAccountRoleArn: '',
    stagingAccountId: '',
    isCurrentAccount: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
];

// Mock authentication middleware
const mockAuth = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ message: 'Unauthorized' });
  }
  
  // Mock user info
  req.user = {
    sub: 'mock-user-id',
    email: 'test@example.com'
  };
  
  next();
};

// Logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path} - Origin: ${req.headers.origin || 'none'}`);
  if (req.headers.authorization) {
    console.log(`  Auth: ${req.headers.authorization.substring(0, 20)}...`);
  }
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Target Accounts endpoints
app.get('/accounts/targets', mockAuth, (req, res) => {
  console.log('📋 GET /accounts/targets - Returning target accounts');
  res.json(targetAccounts);
});

app.post('/accounts/targets', mockAuth, (req, res) => {
  console.log('➕ POST /accounts/targets - Creating target account:', req.body);
  
  const { accountId, name, description, crossAccountRoleArn, stagingAccountId } = req.body;
  
  // Validation
  if (!accountId || !name) {
    return res.status(400).json({ 
      message: 'Missing required fields: accountId and name are required' 
    });
  }
  
  // Check if account already exists
  if (targetAccounts.find(acc => acc.accountId === accountId)) {
    return res.status(409).json({ 
      message: 'Account already exists' 
    });
  }
  
  const newAccount = {
    accountId,
    name,
    description: description || '',
    crossAccountRoleArn: crossAccountRoleArn || '',
    stagingAccountId: stagingAccountId || '',
    isCurrentAccount: false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
  
  targetAccounts.push(newAccount);
  
  res.status(201).json(newAccount);
});

app.put('/accounts/targets/:id', mockAuth, (req, res) => {
  console.log(`✏️ PUT /accounts/targets/${req.params.id} - Updating target account:`, req.body);
  
  const accountId = req.params.id;
  const accountIndex = targetAccounts.findIndex(acc => acc.accountId === accountId);
  
  if (accountIndex === -1) {
    return res.status(404).json({ message: 'Account not found' });
  }
  
  const { name, description, crossAccountRoleArn, stagingAccountId } = req.body;
  
  // Update account
  targetAccounts[accountIndex] = {
    ...targetAccounts[accountIndex],
    name: name || targetAccounts[accountIndex].name,
    description: description !== undefined ? description : targetAccounts[accountIndex].description,
    crossAccountRoleArn: crossAccountRoleArn !== undefined ? crossAccountRoleArn : targetAccounts[accountIndex].crossAccountRoleArn,
    stagingAccountId: stagingAccountId !== undefined ? stagingAccountId : targetAccounts[accountIndex].stagingAccountId,
    updatedAt: new Date().toISOString()
  };
  
  res.json(targetAccounts[accountIndex]);
});

app.delete('/accounts/targets/:id', mockAuth, (req, res) => {
  console.log(`🗑️ DELETE /accounts/targets/${req.params.id} - Deleting target account`);
  
  const accountId = req.params.id;
  const accountIndex = targetAccounts.findIndex(acc => acc.accountId === accountId);
  
  if (accountIndex === -1) {
    return res.status(404).json({ message: 'Account not found' });
  }
  
  // Don't allow deleting current account
  if (targetAccounts[accountIndex].isCurrentAccount) {
    return res.status(400).json({ message: 'Cannot delete current account' });
  }
  
  targetAccounts.splice(accountIndex, 1);
  
  res.status(200).json({ message: 'Account deleted successfully' });
});

app.post('/accounts/targets/:id/validate', mockAuth, (req, res) => {
  console.log(`✅ POST /accounts/targets/${req.params.id}/validate - Validating target account`);
  
  const accountId = req.params.id;
  const account = targetAccounts.find(acc => acc.accountId === accountId);
  
  if (!account) {
    return res.status(404).json({ message: 'Account not found' });
  }
  
  // Mock validation - always return success for demo
  setTimeout(() => {
    res.json({
      valid: true,
      message: 'Account validation successful',
      details: {
        accountExists: true,
        roleAccessible: account.crossAccountRoleArn ? true : null,
        permissions: ['drs:*', 'ec2:*']
      }
    });
  }, 1000); // Simulate network delay
});

// Mock DRS quotas endpoint for dashboard
app.get('/drs/quotas', mockAuth, (req, res) => {
  console.log('📊 GET /drs/quotas - Returning mock DRS quotas');
  
  const accountId = req.query.accountId || '123456789012';
  const region = req.query.region || 'us-east-1';
  
  // Return format expected by frontend (DRSQuotaStatus)
  res.json({
    accountId: accountId,
    accountName: 'Current Account',
    region: region,
    limits: {
      MAX_SERVERS_PER_JOB: 100,
      MAX_CONCURRENT_JOBS: 20,
      MAX_SERVERS_IN_ALL_JOBS: 500,
      MAX_REPLICATING_SERVERS: 300,
      MAX_SOURCE_SERVERS: 4000,
      WARNING_REPLICATING_THRESHOLD: 250,
      CRITICAL_REPLICATING_THRESHOLD: 280
    },
    capacity: {
      totalSourceServers: 6,
      replicatingServers: 6,
      maxReplicatingServers: 300,
      maxSourceServers: 4000,
      availableReplicatingSlots: 294,
      status: 'OK',
      message: 'Capacity OK: 6/300 replicating servers'
    },
    concurrentJobs: {
      current: 0,
      max: 20,
      available: 20
    },
    serversInJobs: {
      current: 0,
      max: 500
    }
  });
});

// Mock tag sync endpoint
app.post('/drs/tag-sync', mockAuth, (req, res) => {
  console.log('🏷️ POST /drs/tag-sync - Mock tag sync');
  
  setTimeout(() => {
    res.json({
      message: 'Tag synchronization completed successfully',
      syncedServers: 3,
      totalTags: 12
    });
  }, 2000); // Simulate processing time
});

// Mock executions endpoints
app.get('/executions', mockAuth, (req, res) => {
  console.log('📋 GET /executions - Returning mock executions');
  
  const mockExecutions = [
    {
      executionId: 'exec-12345678',
      planId: 'plan-abcd1234',
      planName: 'Production DR Test',
      status: 'COMPLETED',
      executionType: 'DRILL',
      initiatedBy: 'test@example.com',
      startTime: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      endTime: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), // 1 hour ago
      totalWaves: 3,
      completedWaves: 3,
      totalServers: 12,
      launchedServers: 12
    },
    {
      executionId: 'exec-87654321',
      planId: 'plan-efgh5678',
      planName: 'Database Tier Recovery',
      status: 'IN_PROGRESS',
      executionType: 'DRILL',
      initiatedBy: 'admin@example.com',
      startTime: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
      endTime: null,
      totalWaves: 2,
      completedWaves: 1,
      totalServers: 6,
      launchedServers: 3
    },
    {
      executionId: 'exec-11223344',
      planId: 'plan-ijkl9012',
      planName: 'Web Tier Failover',
      status: 'FAILED',
      executionType: 'RECOVERY',
      initiatedBy: 'ops@example.com',
      startTime: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 24 hours ago
      endTime: new Date(Date.now() - 23 * 60 * 60 * 1000).toISOString(), // 23 hours ago
      totalWaves: 1,
      completedWaves: 0,
      totalServers: 4,
      launchedServers: 0,
      error: 'DRS job failed: Insufficient EC2 capacity'
    }
  ];
  
  // Return the format expected by the frontend (PaginatedResponse<ExecutionListItem>)
  res.json({
    items: mockExecutions,  // Frontend expects 'items' not 'executions'
    count: mockExecutions.length,
    nextToken: null
  });
});

// Mock protection groups endpoints
app.get('/protection-groups', mockAuth, (req, res) => {
  console.log('🛡️ GET /protection-groups - Returning mock protection groups');
  
  const mockGroups = [
    {
      groupId: 'pg-12345678',
      name: 'Production Database Servers',
      description: 'Critical database servers for production workloads',
      region: 'us-east-1',
      tags: {
        Environment: 'Production',
        Tier: 'Database'
      },
      serverCount: 4,
      createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      groupId: 'pg-87654321',
      name: 'Web Application Servers',
      description: 'Frontend web servers and load balancers',
      region: 'us-west-2',
      tags: {
        Environment: 'Production',
        Tier: 'Web'
      },
      serverCount: 8,
      createdAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
    }
  ];
  
  res.json({
    groups: mockGroups,
    count: mockGroups.length
  });
});

// Mock recovery plans endpoints
app.get('/recovery-plans', mockAuth, (req, res) => {
  console.log('📋 GET /recovery-plans - Returning mock recovery plans');
  
  const mockPlans = [
    {
      planId: 'plan-abcd1234',
      name: 'Production DR Test',
      description: 'Complete production environment disaster recovery test',
      waves: [
        {
          waveNumber: 1,
          protectionGroupId: 'pg-12345678',
          protectionGroupName: 'Production Database Servers',
          pauseBeforeWave: false
        },
        {
          waveNumber: 2,
          protectionGroupId: 'pg-87654321',
          protectionGroupName: 'Web Application Servers',
          pauseBeforeWave: true
        }
      ],
      createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
    }
  ];
  
  res.json({
    plans: mockPlans,
    count: mockPlans.length
  });
});

// Mock DRS source servers endpoint
app.get('/drs/source-servers', mockAuth, (req, res) => {
  console.log('🖥️ GET /drs/source-servers - Returning mock DRS servers');
  
  const region = req.query.region || 'us-east-1';
  
  const mockServers = [
    {
      sourceServerId: 's-1234567890abcdef0',
      hostname: 'web-server-01.example.com',
      nameTag: 'Web Server 01',
      sourceInstanceId: 'i-0123456789abcdef0',
      sourceIp: '10.0.1.100',
      sourceRegion: region,
      sourceAccount: '123456789012',
      state: 'HEALTHY',
      replicationState: 'CONTINUOUS_REPLICATION',
      lagDuration: 'PT2M30S',
      tags: {
        Name: 'Web Server 01',
        Environment: 'Production',
        Tier: 'Web'
      }
    },
    {
      sourceServerId: 's-abcdef1234567890',
      hostname: 'db-server-01.example.com',
      nameTag: 'Database Server 01',
      sourceInstanceId: 'i-abcdef1234567890',
      sourceIp: '10.0.2.100',
      sourceRegion: region,
      sourceAccount: '123456789012',
      state: 'HEALTHY',
      replicationState: 'CONTINUOUS_REPLICATION',
      lagDuration: 'PT1M15S',
      tags: {
        Name: 'Database Server 01',
        Environment: 'Production',
        Tier: 'Database'
      }
    }
  ];
  
  res.json({
    servers: mockServers,
    count: mockServers.length,
    region: region
  });
});

// Catch-all for unhandled routes
app.use((req, res) => {
  console.log(`❓ Unhandled route: ${req.method} ${req.originalUrl}`);
  res.status(404).json({ 
    message: 'Endpoint not found',
    method: req.method,
    path: req.originalUrl
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('💥 Server error:', err);
  res.status(500).json({ 
    message: 'Internal server error',
    error: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// Start server
app.listen(port, () => {
  console.log(`🚀 Mock API server running at http://localhost:${port}`);
  console.log(`📋 Available endpoints:`);
  console.log(`   GET    /health`);
  console.log(`   GET    /accounts/targets`);
  console.log(`   POST   /accounts/targets`);
  console.log(`   PUT    /accounts/targets/:id`);
  console.log(`   DELETE /accounts/targets/:id`);
  console.log(`   POST   /accounts/targets/:id/validate`);
  console.log(`   GET    /drs/quotas`);
  console.log(`   POST   /drs/tag-sync`);
  console.log(`\n💡 Use Authorization: Bearer <any-token> header for requests`);
});