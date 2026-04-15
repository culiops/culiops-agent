// platform stack — AKS + Application Gateway + Front Door + Workload Identity (UAMI).
// Consumes the infra stack's resources via `existing` references rather than
// by direct composition (cross-stack boundary — each stack deploys separately).

targetScope = 'resourceGroup'

@description('Deployment environment (prod, staging).')
@allowed([ 'prod', 'staging' ])
param environment string

@description('Azure region.')
param location string = 'westeurope'

@description('Resource group that holds the infra stack.')
param infraResourceGroup string

@description('Kubernetes control-plane version.')
param k8sVersion string = '1.29'

@description('Node pool VM size.')
param nodeVmSize string

@description('Minimum node count (cluster autoscaler).')
param nodeMinCount int

@description('Maximum node count (cluster autoscaler).')
param nodeMaxCount int

@description('Namespace + ServiceAccount that the workload UAMI federates to.')
param workloadNamespace string = 'widgetapi'

@description('ServiceAccount name that the workload UAMI federates to.')
param workloadServiceAccount string = 'widgetapi'

@description('Front Door profile SKU (Standard_AzureFrontDoor, Premium_AzureFrontDoor).')
@allowed([ 'Standard_AzureFrontDoor', 'Premium_AzureFrontDoor' ])
param afdSkuName string

var namePrefix = 'widgetapi-${environment}'

// --------------------------------------------------------------------------
// Cross-stack references (from the infra stack — same subscription, other RG).
// --------------------------------------------------------------------------

resource infraVnet 'Microsoft.Network/virtualNetworks@2024-01-01' existing = {
  name: '${namePrefix}-vnet'
  scope: resourceGroup(infraResourceGroup)
}

resource aksSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-01-01' existing = {
  name: 'aks'
  parent: infraVnet
}

resource uploadsStorage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: 'widgetapi${environment}uploads'
  scope: resourceGroup(infraResourceGroup)
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: '${namePrefix}-kv'
  scope: resourceGroup(infraResourceGroup)
}

resource sbNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' existing = {
  name: '${namePrefix}-sb'
  scope: resourceGroup(infraResourceGroup)
}

// --------------------------------------------------------------------------
// User-Assigned Managed Identity for the widgetapi pods (Workload Identity).
// --------------------------------------------------------------------------

resource workloadUami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-id'
  location: location
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

// --------------------------------------------------------------------------
// AKS cluster with OIDC issuer + workload-identity enabled.
// --------------------------------------------------------------------------

resource aks 'Microsoft.ContainerService/managedClusters@2024-02-01' = {
  name: '${namePrefix}-aks'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: k8sVersion
    dnsPrefix: '${namePrefix}-aks'
    enableRBAC: true
    oidcIssuerProfile: {
      enabled: true
    }
    securityProfile: {
      workloadIdentity: {
        enabled: true
      }
    }
    agentPoolProfiles: [
      {
        name: 'default'
        mode: 'System'
        vmSize: nodeVmSize
        osType: 'Linux'
        osSKU: 'AzureLinux'
        count: nodeMinCount
        minCount: nodeMinCount
        maxCount: nodeMaxCount
        enableAutoScaling: true
        vnetSubnetID: aksSubnet.id
        type: 'VirtualMachineScaleSets'
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'cilium'
      networkDataplane: 'cilium'
      loadBalancerSku: 'standard'
    }
    addonProfiles: {
      azureKeyvaultSecretsProvider: {
        enabled: true
        config: {
          enableSecretRotation: 'true'
        }
      }
    }
  }
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

// --------------------------------------------------------------------------
// Federated credential: AKS OIDC issuer → widgetapi ServiceAccount → UAMI.
// --------------------------------------------------------------------------

resource workloadFedCred 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: workloadUami
  name: '${namePrefix}-widgetapi-sa'
  properties: {
    issuer: aks.properties.oidcIssuerProfile.issuerURL
    subject: 'system:serviceaccount:${workloadNamespace}:${workloadServiceAccount}'
    audiences: [ 'api://AzureADTokenExchange' ]
  }
}

// --------------------------------------------------------------------------
// Role assignments — what the workload can do with Azure resources.
// (Role definition IDs are built-in GUIDs. Scope is the target resource.)
// --------------------------------------------------------------------------

// Storage Blob Data Contributor on the uploads storage account.
resource blobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(uploadsStorage.id, workloadUami.id, 'blob-data-contributor')
  scope: uploadsStorage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: workloadUami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Azure Service Bus Data Sender + Receiver on the async queue namespace.
resource sbSenderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sbNamespace.id, workloadUami.id, 'sb-sender')
  scope: sbNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39')
    principalId: workloadUami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource sbReceiverRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sbNamespace.id, workloadUami.id, 'sb-receiver')
  scope: sbNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0')
    principalId: workloadUami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Key Vault Secrets User (read-only secret values) on the vault.
resource kvSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, workloadUami.id, 'kv-secrets-user')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: workloadUami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// --------------------------------------------------------------------------
// Application Gateway (ingress into AKS via AGIC).
// --------------------------------------------------------------------------

resource agwPip 'Microsoft.Network/publicIPAddresses@2024-01-01' = {
  name: '${namePrefix}-agw-pip'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource agw 'Microsoft.Network/applicationGateways@2024-01-01' = {
  name: '${namePrefix}-agw'
  location: location
  properties: {
    sku: {
      name: environment == 'prod' ? 'WAF_v2' : 'Standard_v2'
      tier: environment == 'prod' ? 'WAF_v2' : 'Standard_v2'
    }
    autoscaleConfiguration: {
      minCapacity: environment == 'prod' ? 2 : 1
      maxCapacity: environment == 'prod' ? 10 : 3
    }
    gatewayIPConfigurations: []
    frontendIPConfigurations: [
      {
        name: 'public'
        properties: {
          publicIPAddress: { id: agwPip.id }
        }
      }
    ]
    frontendPorts: [
      {
        name: 'https'
        properties: { port: 443 }
      }
    ]
    // Listeners, backend pools, rules are wired up by AGIC (the AKS add-on)
    // at runtime based on Kubernetes Ingress objects. This template only
    // provisions the AGW itself.
    backendAddressPools: []
    backendHttpSettingsCollection: []
    httpListeners: []
    requestRoutingRules: []
  }
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

// --------------------------------------------------------------------------
// Azure Front Door (CDN + WAF in front of AGW).
// --------------------------------------------------------------------------

resource afd 'Microsoft.Cdn/profiles@2024-02-01' = {
  name: '${namePrefix}-afd'
  location: 'Global'
  sku: {
    name: afdSkuName
  }
  properties: {}
  tags: {
    project: 'widgetapi'
    environment: environment
  }
}

resource afdEndpoint 'Microsoft.Cdn/profiles/afdEndpoints@2024-02-01' = {
  parent: afd
  name: '${namePrefix}-ep'
  location: 'Global'
  properties: {
    enabledState: 'Enabled'
  }
}

// --------------------------------------------------------------------------
// Outputs
// --------------------------------------------------------------------------

output aksName string = aks.name
output aksOidcIssuerUrl string = aks.properties.oidcIssuerProfile.issuerURL
output workloadIdentityClientId string = workloadUami.properties.clientId
output workloadIdentityPrincipalId string = workloadUami.properties.principalId
output agwPublicIp string = agwPip.properties.ipAddress
output agwName string = agw.name
output afdProfileName string = afd.name
output afdEndpointHost string = afdEndpoint.properties.hostName
