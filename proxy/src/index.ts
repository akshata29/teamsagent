// Proxy entry point — hosts the Custom Engine Agent over the Agents SDK Express adapter.
import 'dotenv/config'
import { startServer } from '@microsoft/agents-hosting-express'
import { CapMarketsAgent } from './agent.js'

const agent = new CapMarketsAgent()

// startServer wires the Bot Framework adapter + auth and listens on PORT (default 3978).
startServer(agent)
