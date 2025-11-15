# AI Agent Frontend Integration Guide

## Overview

The AI Insights feature has been **completely replaced** with a new **AI Agent** system that provides conversational CRM interactions. This guide explains the changes required in the frontend to integrate with the new system.

---

## What Changed

### Old System (DEPRECATED)
- **Fixed endpoints**: `/api/v1/ai-insights/generate-lead-score/`, `/api/v1/ai-insights/generate-deal-prediction/`
- **UI Pattern**: Dedicated buttons for each AI action (e.g., "Generate Lead Score" button)
- **Interaction**: Click button → See result
- **Limitations**: Fixed functionality, no flexibility

### New System (ACTIVE)
- **Unified endpoint**: `/api/v1/ai-agent/query/`
- **UI Pattern**: Chat interface for natural language queries
- **Interaction**: Type question → Agent understands, executes, responds
- **Capabilities**: Unlimited - agent can perform any supported CRM action

---

## New API Endpoints

### 1. Agent Query Endpoint

**POST** `/api/v1/ai-agent/query/`

Process natural language queries and execute CRM actions.

#### Request Body
```json
{
  "query": "Show me my pipeline summary",
  "conversation_history": []  // Optional: for multi-turn conversations
}
```

#### Response
```json
{
  "success": true,
  "response": "Here's your pipeline summary: You have 45 total deals worth $2.3M...",
  "function_calls": [
    {
      "function": "get_pipeline_summary",
      "arguments": {
        "account_id": 123
      },
      "result": {
        "success": true,
        "pipeline": {
          "total_deals": 45,
          "total_value": 2300000,
          "active_deals": 32,
          "won_deals": 8,
          "lost_deals": 5
        }
      }
    }
  ],
  "conversation_history": [...]  // Use this for follow-up queries
}
```

#### Example Queries
- `"Show me my pipeline summary"`
- `"Create a new lead named John Doe from Acme Corp with email john@acme.com"`
- `"What's the status of deal #123?"`
- `"Update lead #456 status to qualified"`
- `"Search for leads from Google"`
- `"Show me all deals in the proposal stage"`

---

### 2. Suggestions Endpoint

**POST** `/api/v1/ai-agent/suggestions/`

Get contextual suggestions for what the user might want to do next.

#### Request Body
```json
{
  "context": {
    "recent_action": "viewed_pipeline",
    "current_view": "dashboard"
  }
}
```

#### Response
```json
{
  "success": true,
  "suggestions": [
    "Show me my pipeline summary",
    "What are my newest leads?",
    "Create a new lead"
  ]
}
```

---

## Frontend Implementation

### Recommended UI Components

#### 1. Chat Interface (Primary)

Create a chat-style component for the main AI interaction:

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const AIAgentChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendQuery = async () => {
    if (!input.trim()) return;

    // Add user message to UI
    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setLoading(true);

    try {
      const response = await axios.post('/api/v1/ai-agent/query/', {
        query: input,
        conversation_history: conversationHistory
      });

      // Add agent response to UI
      const agentMessage = {
        role: 'agent',
        content: response.data.response,
        functionCalls: response.data.function_calls
      };
      setMessages([...messages, userMessage, agentMessage]);

      // Update conversation history for multi-turn
      setConversationHistory(response.data.conversation_history || []);

      setInput('');
    } catch (error) {
      console.error('Agent query failed:', error);
      // Show error message
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {loading && <div className="loading">Agent is thinking...</div>}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendQuery()}
          placeholder="Ask me anything about your CRM..."
        />
        <button onClick={sendQuery} disabled={loading}>Send</button>
      </div>
    </div>
  );
};

export default AIAgentChat;
```

#### 2. Quick Action Buttons (Secondary)

Provide quick access buttons that trigger common queries:

```jsx
const QuickActions = ({ onQuerySelect }) => {
  const quickQueries = [
    { label: "Pipeline Summary", query: "Show me my pipeline summary" },
    { label: "Recent Leads", query: "Show me my 10 most recent leads" },
    { label: "Top Deals", query: "Show me my highest value deals" },
  ];

  return (
    <div className="quick-actions">
      {quickQueries.map((item, idx) => (
        <button
          key={idx}
          onClick={() => onQuerySelect(item.query)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
};
```

#### 3. Suggestion Chips

Display contextual suggestions from the API:

```jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const SuggestionChips = ({ context, onSuggestionClick }) => {
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const response = await axios.post('/api/v1/ai-agent/suggestions/', {
          context: context
        });
        setSuggestions(response.data.suggestions || []);
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
      }
    };

    fetchSuggestions();
  }, [context]);

  return (
    <div className="suggestion-chips">
      <span>Suggested:</span>
      {suggestions.map((suggestion, idx) => (
        <button
          key={idx}
          className="chip"
          onClick={() => onSuggestionClick(suggestion)}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
};

export default SuggestionChips;
```

---

## Migration Strategy

### Phase 1: Add New AI Agent UI (Week 1)
1. Create new chat component
2. Add "AI Assistant" button/tab in the main navigation
3. Keep old AI Insights UI as-is (don't remove yet)

### Phase 2: Deprecation Warning (Week 2)
1. Add visual warnings to old AI Insights buttons:
   ```jsx
   <button onClick={oldAIFunction}>
     Generate Lead Score
     <span className="deprecated-badge">Deprecated</span>
   </button>
   ```
2. Show a banner: "This feature is being replaced. Try the new AI Assistant!"

### Phase 3: Full Migration (Week 3-4)
1. Remove old AI Insights buttons
2. Make AI Agent the default/only AI interface
3. Update all documentation

---

## UI/UX Best Practices

### 1. Loading States
```jsx
{loading && (
  <div className="agent-loading">
    <Spinner />
    <span>Agent is thinking...</span>
  </div>
)}
```

### 2. Error Handling
```jsx
if (!response.data.success) {
  showNotification({
    type: 'error',
    message: response.data.response || 'Agent encountered an error'
  });
}
```

### 3. Show Function Calls (Optional)
Display what actions the agent took:
```jsx
{message.functionCalls?.length > 0 && (
  <div className="function-calls">
    <small>Actions taken:</small>
    <ul>
      {message.functionCalls.map((call, idx) => (
        <li key={idx}>{call.function}</li>
      ))}
    </ul>
  </div>
)}
```

### 4. Input Validation
```jsx
const validateQuery = (query) => {
  if (!query.trim()) {
    return { valid: false, error: 'Please enter a query' };
  }
  if (query.length > 500) {
    return { valid: false, error: 'Query too long (max 500 characters)' };
  }
  return { valid: true };
};
```

---

## Example Use Cases

### Use Case 1: Lead Scoring (Replacing Old Feature)

**Old Way:**
1. User goes to lead detail page
2. Clicks "Generate Lead Score" button
3. Sees score in a modal

**New Way:**
```jsx
// User can ask naturally:
"Score lead #123"
"How good is the lead from Acme Corp?"
"Should I prioritize lead #456?"

// Agent responds with score AND context:
// "Lead #123 (John Doe from Acme Corp) scores 85/100.
//  This is a high-priority lead because..."
```

### Use Case 2: Pipeline Analytics

**Old Way:**
- Navigate to Reports page
- Click various filters
- View static dashboard

**New Way:**
```jsx
// Natural language queries:
"What's my pipeline looking like?"
"Show me deals in the proposal stage"
"Which deals are at risk?"
"Compare this month's pipeline to last month"
```

### Use Case 3: Creating Records

**Old Way:**
- Click "New Lead" button
- Fill out form
- Submit

**New Way:**
```jsx
// Quick creation via chat:
"Create a lead named Sarah Johnson from Microsoft,
 email sarah@microsoft.com, phone 555-1234"

// Agent creates it and confirms:
// "I've created a new lead for Sarah Johnson from Microsoft
//  with ID #789. Would you like me to assign it to someone?"
```

---

## Testing Checklist

### Frontend Developer Testing
- [ ] Chat interface loads without errors
- [ ] User can send queries and receive responses
- [ ] Loading states display correctly
- [ ] Error messages show when API fails
- [ ] Conversation history persists across multiple queries
- [ ] Suggestions display and are clickable
- [ ] Quick action buttons work
- [ ] Mobile responsive design works

### QA Testing
- [ ] Test all example queries from documentation
- [ ] Test error cases (empty query, API down, etc.)
- [ ] Test multi-turn conversations
- [ ] Verify old AI Insights endpoints show deprecation warnings
- [ ] Test with different user permissions
- [ ] Verify logged actions appear in activity feed

---

## API Response Examples

### Successful Query
```json
{
  "success": true,
  "response": "I found 5 leads from Google:\n1. John Doe (john@google.com)\n2. Jane Smith (jane@google.com)\n...",
  "function_calls": [
    {
      "function": "search_leads",
      "arguments": {
        "query": "Google",
        "account_id": 123,
        "limit": 10
      },
      "result": {
        "success": true,
        "results": [...],
        "count": 5
      }
    }
  ],
  "conversation_history": [...]
}
```

### Error Response
```json
{
  "success": false,
  "response": "I encountered an error while searching for leads: Database connection failed",
  "error": "Database connection failed"
}
```

### Multi-Function Call
```json
{
  "success": true,
  "response": "I've created lead #890 for Alice Cooper and immediately scored it at 72/100. This is a medium-priority lead.",
  "function_calls": [
    {
      "function": "create_lead",
      "arguments": {...},
      "result": {"success": true, "lead_id": 890}
    },
    {
      "function": "get_lead",
      "arguments": {"lead_id": 890, "account_id": 123},
      "result": {"success": true, "lead": {...}}
    }
  ],
  "conversation_history": [...]
}
```

---

## Styling Recommendations

### Chat Container
```css
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  background: #007bff;
  color: white;
  margin-left: auto;
  text-align: right;
}

.message.agent {
  background: #f5f5f5;
  color: #333;
}

.input-area {
  display: flex;
  padding: 16px;
  border-top: 1px solid #e0e0e0;
}

.input-area input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 8px;
}

.input-area button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
```

---

## Security Considerations

1. **Input Sanitization**: Always sanitize user input before displaying
2. **Rate Limiting**: Implement client-side rate limiting to prevent spam
3. **Authentication**: Ensure API calls include proper auth tokens
4. **Error Messages**: Don't expose sensitive error details to users

---

## Performance Optimization

1. **Debouncing**: Debounce suggestion requests
2. **Caching**: Cache common queries locally
3. **Lazy Loading**: Load chat history lazily as user scrolls
4. **Optimistic UI**: Show user message immediately, confirm later

---

## Support & Troubleshooting

### Common Issues

**Issue**: "Agent takes too long to respond"
- **Solution**: Add timeout (30s), show clear loading state

**Issue**: "Conversation history grows too large"
- **Solution**: Limit to last 10 turns, provide "clear conversation" button

**Issue**: "User doesn't know what to ask"
- **Solution**: Show examples, provide quick action buttons, display suggestions

---

## Future Enhancements

Planned features (not yet implemented):
- Voice input/output
- Scheduled queries
- Agent memory across sessions
- Proactive suggestions
- Integration with email/calendar

---

## Questions?

For backend API questions, refer to:
- `automation/services/agent_service.py` - Agent logic
- `automation/services/ai_tools.py` - Available tools
- `api/views.py` (AIAgentViewSet) - Endpoint implementation

For migration support, contact the backend team.
