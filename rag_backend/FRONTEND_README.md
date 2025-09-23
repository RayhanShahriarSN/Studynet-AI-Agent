# RAG AI Agent Frontend

A modern, responsive web interface for the Django RAG backend, built with vanilla HTML, CSS, and JavaScript.

## Features

### 🎨 **Modern UI/UX**
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Gradient Backgrounds**: Beautiful gradient backgrounds and glassmorphism effects
- **Smooth Animations**: Fade-in effects, hover animations, and smooth transitions
- **Professional Typography**: Inter font family for clean, modern text

### 💬 **Interactive Chat Interface**
- **Real-time Messaging**: Send and receive messages with the RAG AI agent
- **Message History**: Persistent conversation history with session management
- **Typing Indicators**: Visual feedback when the AI is processing
- **Message Sources**: Display sources used for AI responses
- **Confidence Scores**: Show confidence levels for AI responses

### ⚙️ **Advanced Features**
- **Web Search Toggle**: Enable/disable web search for responses
- **Enhanced Formatting**: Toggle enhanced response formatting
- **Document Upload**: Drag-and-drop file upload with progress indicators
- **Session Management**: Automatic session ID generation and management
- **Recent Queries**: Quick access to previous queries

### 📊 **System Monitoring**
- **API Status**: Real-time API health monitoring
- **Knowledge Base Status**: Document count and system status
- **Response Times**: Track query response performance
- **Active Sessions**: Monitor concurrent user sessions

## File Structure

```
static/
├── css/
│   └── style.css          # Main stylesheet with all UI components
├── js/
│   └── app.js             # Main JavaScript application logic
├── images/
│   └── favicon.ico        # Website favicon
└── index.html             # Static HTML file (backup)

templates/
└── index.html             # Django template with static file integration
```

## Key Components

### 1. **Chat Interface** (`chat-container`)
- Message display area with scrollable history
- User and assistant message bubbles
- Source citations and metadata display
- Welcome message with feature highlights

### 2. **Input System** (`input-area`)
- Text input with auto-resize functionality
- Send button with loading states
- Option toggles for web search and formatting
- Keyboard shortcuts (Enter to send)

### 3. **Sidebar** (`sidebar`)
- System status monitoring
- Session information display
- Recent queries history
- Settings and configuration

### 4. **Document Upload** (`uploadModal`)
- Modal dialog for file uploads
- Drag-and-drop functionality
- Progress indicators
- Support for multiple file formats

### 5. **Loading States** (`loadingOverlay`)
- Full-screen loading overlay
- Spinner animations
- Processing status messages

## CSS Architecture

### **Design System**
- **Color Palette**: Purple/blue gradients with neutral grays
- **Typography**: Inter font family with weight variations
- **Spacing**: Consistent 8px grid system
- **Border Radius**: 8px, 12px, 16px, 18px for different elements
- **Shadows**: Layered shadow system for depth

### **Layout System**
- **Grid Layout**: CSS Grid for main content areas
- **Flexbox**: Flexible component layouts
- **Responsive**: Mobile-first responsive design
- **Glassmorphism**: Backdrop blur effects for modern look

### **Component Classes**
- `.btn` - Button base styles with variants
- `.message` - Chat message containers
- `.modal` - Modal dialog system
- `.status-card` - Status information cards
- `.feature` - Feature highlight components

## JavaScript Architecture

### **RAGAgent Class**
Main application class that handles:
- API communication with Django backend
- Chat message management
- File upload processing
- System status monitoring
- Local storage for recent queries

### **Key Methods**
- `sendMessage()` - Process user queries
- `addMessage()` - Add messages to chat
- `loadSystemStatus()` - Monitor system health
- `handleFileUpload()` - Process document uploads
- `showNotification()` - Display user feedback

### **API Integration**
- RESTful API calls to Django backend
- Error handling and user feedback
- Loading states and progress indicators
- Session management and persistence

## Responsive Design

### **Breakpoints**
- **Desktop**: 1024px+ (Full sidebar and chat layout)
- **Tablet**: 768px-1023px (Stacked layout)
- **Mobile**: <768px (Single column, compact design)

### **Mobile Optimizations**
- Touch-friendly button sizes
- Optimized input areas
- Collapsible sidebar
- Swipe gestures for navigation

## Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **CSS Features**: CSS Grid, Flexbox, Custom Properties
- **JavaScript**: ES6+ features with fallbacks
- **APIs**: Fetch API, Local Storage, File API

## Performance Features

### **Optimizations**
- **Lazy Loading**: Images and components load on demand
- **Debounced Input**: Prevents excessive API calls
- **Efficient DOM Updates**: Minimal reflows and repaints
- **Cached Responses**: Local storage for recent queries

### **Loading States**
- **Skeleton Screens**: Placeholder content while loading
- **Progress Indicators**: Visual feedback for long operations
- **Error Handling**: Graceful degradation on failures

## Customization

### **Theming**
The color scheme can be easily customized by modifying CSS custom properties:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #38a169;
    --error-color: #e53e3e;
    --warning-color: #d69e2e;
}
```

### **Layout Modifications**
- Grid columns can be adjusted in `.main-content`
- Sidebar width can be changed in CSS Grid template
- Message bubble styles can be customized in `.message-bubble`

## Integration with Django

### **Template Integration**
- Uses Django's `{% load static %}` for asset management
- Template variables for dynamic content
- CSRF protection for form submissions

### **API Endpoints**
- `/api/` - Frontend interface
- `/api/health/` - System health check
- `/api/query/` - Chat query processing
- `/api/upload/document/` - Document upload
- `/api/sessions/` - Session management

## Development

### **Local Development**
1. Start Django development server
2. Navigate to `http://localhost:8000/api/`
3. Use browser developer tools for debugging
4. Modify CSS/JS files and refresh browser

### **File Watching**
For automatic reloading during development:
```bash
# Install live-reload extension or use Django's auto-reload
python manage.py runserver
```

## Production Deployment

### **Static Files**
1. Run `python manage.py collectstatic`
2. Configure web server to serve static files
3. Enable gzip compression for CSS/JS files
4. Set appropriate cache headers

### **Performance**
- Minify CSS and JavaScript files
- Optimize images and icons
- Enable browser caching
- Use CDN for external assets

## Troubleshooting

### **Common Issues**
1. **Static files not loading**: Check `STATIC_URL` and `STATIC_ROOT` settings
2. **API calls failing**: Verify CORS settings and API endpoints
3. **Upload not working**: Check file size limits and allowed formats
4. **Responsive issues**: Test on different screen sizes

### **Debug Mode**
Enable browser developer tools to see:
- Console errors and warnings
- Network request/response details
- CSS layout issues
- JavaScript execution flow

## Future Enhancements

### **Planned Features**
- **Dark Mode**: Toggle between light and dark themes
- **Voice Input**: Speech-to-text for queries
- **Export Chat**: Download conversation history
- **Advanced Settings**: More customization options
- **Real-time Updates**: WebSocket integration for live updates

### **Accessibility**
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: ARIA labels and descriptions
- **High Contrast**: Alternative color schemes
- **Font Size**: Adjustable text sizes

The frontend provides a complete, modern interface for interacting with the RAG AI agent, combining beautiful design with powerful functionality! 🚀
