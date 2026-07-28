// Azure Bot Service + Teams channel for Option A direct publish.
// The bot messaging endpoint is the Foundry agent activity-protocol URL.
//
// Deploy: az deployment group create -g <rg> -f deploy/bicep/botservice.bicep \
//   -p botName=capmarkets-bot msaAppId=<app-id> \
//      agentActivityEndpoint='https://<acct>.services.ai.azure.com/api/projects/<proj>/agents/capmarkets-research-agent/endpoint/protocols/activityProtocol?api-version=2025-05-15-preview'

@description('Azure Bot Service resource name')
param botName string

@description('Microsoft App (Entra) ID backing the bot')
param msaAppId string

@description('Foundry agent activity-protocol messaging endpoint')
param agentActivityEndpoint string

@description('Bot SKU')
param sku string = 'S1'

resource bot 'Microsoft.BotService/botServices@2022-09-15' = {
  name: botName
  location: 'global'
  sku: {
    name: sku
  }
  kind: 'azurebot'
  properties: {
    displayName: botName
    endpoint: agentActivityEndpoint
    msaAppId: msaAppId
    msaAppType: 'SingleTenant'
  }
}

resource teamsChannel 'Microsoft.BotService/botServices/channels@2021-03-01' = {
  parent: bot
  name: 'MsTeamsChannel'
  location: 'global'
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      isEnabled: true
    }
  }
}

output botId string = bot.id
