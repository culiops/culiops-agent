// infra stack — VNet, PostgreSQL Flexible, Azure Cache for Redis,
// Storage Account (blob), Service Bus, Key Vault.

targetScope = 'resourceGroup'

@description('Deployment environment (prod, staging).')
@allowed([ 'prod', 'staging' ])
param environment string

@description('Azure region.')
param location string = 'westeurope'

@description('CIDR for the VNet.')
param vnetAddressPrefix string

@description('CIDR for the AKS subnet.')
param aksSubnetPrefix string

@description('CIDR for the data subnet (Postgres / Redis private endpoints).')
param dataSubnetPrefix string

@description('PostgreSQL Flexible Server SKU name (e.g. Standard_D2ds_v5).')
param pgSkuName string

@description('PostgreSQL Flexible Server SKU tier (GeneralPurpose, MemoryOptimized).')
param pgSkuTier string

@description('Storage size for the Postgres primary in GiB.')
param pgStorageSizeGB int

@description('High-availability mode for Postgres (Disabled, SameZone, ZoneRedundant).')
@allowed([ 'Disabled', 'SameZone', 'ZoneRedundant' ])
param pgHighAvailability string

@description('Backup retention days for Postgres.')
param pgBackupRetentionDays int

@description('Whether to create a read replica of Postgres.')
param pgCreateReadReplica bool

@description('Azure Cache for Redis SKU name (Basic, Standard, Premium).')
@allowed([ 'Basic', 'Standard', 'Premium' ])
param redisSkuName string

@description('Azure Cache for Redis family (C for Basic/Standard, P for Premium).')
@allowed([ 'C', 'P' ])
param redisFamily string

@description('Redis capacity (size within the SKU).')
param redisCapacity int

@description('Service Bus namespace SKU (Basic, Standard, Premium).')
@allowed([ 'Basic', 'Standard', 'Premium' ])
param serviceBusSku string

@description('Resource name prefix — "widgetapi-<env>".')
var namePrefix = 'widgetapi-${environment}'

// --------------------------------------------------------------------------
// Networking
// --------------------------------------------------------------------------

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: '${namePrefix}-vnet'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [ vnetAddressPrefix ]
    }
    subnets: [
      {
        name: 'aks'
        properties: {
          addressPrefix: aksSubnetPrefix
        }
      }
      {
        name: 'data'
        properties: {
          addressPrefix: dataSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
          delegations: [
            {
              name: 'postgres-flex'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
        }
      }
    ]
  }
  tags: {
    project: 'widgetapi'
    environment: environment
    managedBy: 'bicep'
    stack: 'infra'
  }
}

// --------------------------------------------------------------------------
// Key Vault (stores the Postgres admin password + the Datadog API keys etc.)
// --------------------------------------------------------------------------

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}-kv'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enabledForDeployment: false
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'Disabled'
  }
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

// --------------------------------------------------------------------------
// PostgreSQL Flexible Server (primary + optional read replica)
// --------------------------------------------------------------------------

resource pgPrimary 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: '${namePrefix}-pg'
  location: location
  sku: {
    name: pgSkuName
    tier: pgSkuTier
  }
  properties: {
    version: '15'
    administratorLogin: 'widgetapi'
    // Admin password is provisioned by a pipeline step into Key Vault and
    // read from there at deploy time — not baked into this template.
    // For fixture purposes we reference a Key Vault secret URI via the
    // administratorLoginPassword that the pipeline renders.
    administratorLoginPassword: '@Microsoft.KeyVault(SecretUri=https://${kv.name}.vault.azure.net/secrets/pg-admin-password/)'
    storage: {
      storageSizeGB: pgStorageSizeGB
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: pgBackupRetentionDays
      geoRedundantBackup: environment == 'prod' ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: pgHighAvailability
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/data'
    }
  }
  tags: {
    project: 'widgetapi'
    environment: environment
    role: 'primary'
  }
}

resource pgReadReplica 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = if (pgCreateReadReplica) {
  name: '${namePrefix}-pg-ro'
  location: location
  sku: {
    name: pgSkuName
    tier: pgSkuTier
  }
  properties: {
    createMode: 'Replica'
    sourceServerResourceId: pgPrimary.id
  }
  tags: {
    project: 'widgetapi'
    environment: environment
    role: 'replica'
  }
}

// --------------------------------------------------------------------------
// Azure Cache for Redis
// --------------------------------------------------------------------------

resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: '${namePrefix}-cache'
  location: location
  properties: {
    sku: {
      name: redisSkuName
      family: redisFamily
      capacity: redisCapacity
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

// --------------------------------------------------------------------------
// Storage Account for blob uploads
// --------------------------------------------------------------------------

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'widgetapi${environment}uploads'
  location: location
  kind: 'StorageV2'
  sku: {
    name: environment == 'prod' ? 'Standard_ZRS' : 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: { enabled: true }
        file: { enabled: true }
      }
      keySource: 'Microsoft.Storage'
    }
  }
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

resource blobSvc 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: environment == 'prod' ? 30 : 7
    }
  }
}

resource uploadsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobSvc
  name: 'uploads'
  properties: {
    publicAccess: 'None'
  }
}

// --------------------------------------------------------------------------
// Service Bus (queue + dead-letter routing)
// --------------------------------------------------------------------------

resource sbNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: '${namePrefix}-sb'
  location: location
  sku: {
    name: serviceBusSku
  }
  properties: {
    publicNetworkAccess: 'Disabled'
  }
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

resource asyncQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: sbNamespace
  name: 'async'
  properties: {
    maxDeliveryCount: 5
    // Messages failing 5 deliveries move to the built-in DLQ.
    deadLetteringOnMessageExpiration: true
    lockDuration: 'PT1M'
    defaultMessageTimeToLive: 'P4D'
  }
}

// --------------------------------------------------------------------------
// Outputs — consumed by the platform stack via `existing` references.
// --------------------------------------------------------------------------

output vnetId string = vnet.id
output aksSubnetId string = '${vnet.id}/subnets/aks'
output dataSubnetId string = '${vnet.id}/subnets/data'

output pgPrimaryHost string = '${pgPrimary.name}.postgres.database.azure.com'
output pgReadReplicaHost string = pgCreateReadReplica ? '${pgReadReplica.name}.postgres.database.azure.com' : ''
output pgSecretUri string = 'https://${kv.name}.vault.azure.net/secrets/pg-admin-password/'

output redisHost string = redis.properties.hostName
output redisSslPort int = redis.properties.sslPort

output uploadsAccountName string = storage.name
output uploadsContainer string = uploadsContainer.name

output serviceBusNamespace string = sbNamespace.name
output asyncQueueName string = asyncQueue.name

output keyVaultName string = kv.name
output keyVaultUri string = kv.properties.vaultUri
