# Source - Azure SignalR - Current State

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5399020036/Source%20-%20Azure%20SignalR%20-%20Current%20State

**Created by:** Sreenivas Algoti on January 05, 2026  
**Last modified by:** Sreenivas Algoti on January 05, 2026 at 07:34 PM

---

Overview
========

The Source application uses **Azure SignalR Service** (managed/hosted version) for real-time client-to-server communication. This is a Microsoft technology that provides an abstraction layer over WebSockets, Server-Sent Events, and long polling.

Current Architecture
====================

Hosting Model
-------------

* Managed Azure SignalR Service (subscription-based, pay-per-message model)
* Previously self-hosted on IIS with sticky sessions (had scaling issues), now migrated to Managed Azure SignalR Service
* Azure SignalR Service provides a connection string for the clients to connect to SignalR Service.

Technology Stack
----------------

| Component | Technology |
| --- | --- |
| Server-side SDK | .NET NuGet package |
| Client-side SDK | JavaScript/NPM package (Angular) |
| Session tracking | Redis (stores user IDs/connections) |
| Authentication | Azure AD (same credentials as Source UI) |

Current User Cases
==================

1. **Permission/Role Change Notifications**
-------------------------------------------

When an administrator modifies a user's role or permissions while they're logged in:

* Server pushes a toast notification to affected user(s)
* Non-blocking - if message fails, user still gets logged out on next action

2. **Cross-Tab Session Management**
-----------------------------------

* Each browser tab creates a separate SignalR connection
* When user logs out from one tab, server broadcasts logout event to all tabs for that user
* Ensures consistent session state across browser instances

3. **License/Feature Flag Updates**
-----------------------------------

License management service sends out notifications to users about license updates:

* When feature flags are toggled, SignalR notifies UI to refresh
* Example: "License updated, refresh your browser"

4. **General UI Notifications**
-------------------------------

* Toast messages for trivial updates
* No business-critical data transmitted

Technical Characteristics
=========================

Message Flow
------------

| Aspect | Details |
| --- | --- |
| Direction | Primarily server-to-client (bidirectional capability exists but rarely used client-to-server) |
| Message Content | Very trivial/lightweight (e.g., "log\_off\_initiated") |
| Ordering | Messages are ordered |
| Delivery Guarantee | None - dropped messages are lost |
| Business Criticality | Not critical - system functions even if SignalR fails |

Connection Lifecycle
--------------------

1. **Initiation**: Browser triggers SignalR connection on user login
2. **Identification**: User ID passed during connection setup
3. **Tracking**: Connection stored in Redis
4. **Reconnection**: SDK auto-retries (~10 attempts) on network failures
5. **Termination**: SignalR connection disconnected on user logout

Groups Feature
--------------

* 3-4 groups currently defined
* Users can belong to multiple groups simultaneously
* Enables targeted group messaging (broadcast to all users in a specific group)

Authorization
-------------

* No SignalR-level authorization
* Group membership is the only targeting mechanism
* All authenticated users can receive messages for their groups

Scaling & Performance
=====================

| Metric | Details |
| --- | --- |
| User Volume | Varies by client; one large client has 500+ users |
| Connections per User | One per browser tab (user with 5 tabs = 5 connections) |
| Latency | Real-time (milliseconds) |
| Current Status | Performing well with Azure SignalR Service |

Important Notes for AWS Migration
=================================

What SignalR is NOT used for:
-----------------------------

* Business-critical message delivery
* Database triggers or direct database integration
* Heavy data payloads
* Guaranteed/exactly-once delivery scenarios

Current Temporary Usage:
------------------------

* Some temporary business logic added for a CPM project (Phase 2)
* Temporary business logic will be moved to microservices/background processes in Phase 3
* Goal is to decouple business logic from UI layer

Future Considerations:
----------------------

* Another team is planning expanded SignalR usage (details unknown - follow-up needed)
* Roadmap includes decoupling business logic from UI

Clarification Questions
=======================

1. **Latency Requirements**: Is sub-second latency strictly required, or would a few seconds delay be acceptable for these notifications?
2. **Connection Persistence**: How long do users typically stay connected? Are there idle timeout requirements?
3. **Offline Handling**: When a user is offline/disconnected and a notification is sent, should they receive it upon reconnection, or is it acceptable to lose it?
4. **Group Dynamics**: Are group memberships static per user, or do they change dynamically during a session?
5. **Scale Projections**: Are there growth projections for user counts or message volumes?
6. **Integration Points**: Besides the license management service, are there other backend services that trigger SignalR messages?