# Frontend Integration Guideline - JWT Authentication & Role-Based Access

## 🎯 **Integration Flow Overview**

### **Step 1: Authentication Setup**
1. **Create login/register pages** that call these endpoints:
   - `POST /api/auth/register/` - User registration
   - `POST /api/auth/login/` - User login
   - `POST /api/auth/token/refresh/` - Token refresh
   - `POST /api/auth/logout/` - User logout

2. **Store tokens securely** after successful login:
   - Access token (1 hour lifetime)
   - Refresh token (7 days lifetime)
   - User profile data

### **Step 2: API Request Authentication**
1. **Add Authorization header** to all protected API calls:
   ```
   Authorization: Bearer <access_token>
   ```

2. **Handle token expiration** (401 errors):
   - Automatically refresh token using refresh token
   - Retry the original request with new access token
   - If refresh fails, redirect to login

### **Step 3: Role-Based UI Control**
1. **Check user role** from stored user data:
   - `is_admin: true/false` - Admin privileges
   - `is_authenticated: true/false` - Logged in status

2. **Show/hide UI elements** based on role:
   - **Anonymous**: Login/Register buttons only
   - **Student**: Query + Upload + Personal Stats
   - **Admin**: Full dashboard + Analytics + System metrics

---

## 🔄 **Complete User Journey**

### **Anonymous User Flow**
```
1. User visits site → Can use anonymous chat immediately
2. User can chat via /api/chat/ endpoint (no authentication required)
3. User sees "Register for full features" message
4. User can register → Gets tokens → Full access to all features
```

### **Student User Flow**
```
1. User logs in → Gets tokens → Redirected to student dashboard
2. User can:
   - Ask questions (POST /api/query/)
   - Upload documents (POST /api/upload/document/)
   - Upload CSV files (POST /api/upload/csv/)
   - View personal stats (GET /api/users/me/stats/)
   - View own analytics (filtered by user)
```

### **Admin User Flow**
```
1. Admin logs in → Gets tokens → Redirected to admin dashboard
2. Admin can:
   - All student features PLUS:
   - View system metrics (GET /api/metrics/)
   - View analytics (GET /api/analytics/queries/)
   - Access developer dashboard (GET /api/dashboard/)
   - View all user data (not filtered by user)
```

---

## 🛠 **Implementation Checklist**

### **Frontend Requirements**
- [ ] Login/Register forms
- [ ] Token storage (localStorage/sessionStorage)
- [ ] Automatic token refresh mechanism
- [ ] Role-based UI visibility
- [ ] Error handling for 401/403 responses
- [ ] Logout functionality

### **API Integration Points**
- [ ] All API calls include Authorization header
- [ ] Handle token expiration gracefully
- [ ] Implement retry logic for failed requests
- [ ] Show appropriate error messages

### **UI Components by Role**

#### **Anonymous Users**
- Login form
- Register form
- Public query interface (if allowed)

#### **Student Users**
- Personal dashboard
- Query interface
- File upload (documents/CSV)
- Personal statistics
- Profile management

#### **Admin Users**
- Admin dashboard
- System metrics
- Analytics dashboard
- User management
- All student features

---

## 🔐 **Security Implementation**

### **Token Management**
1. **Store tokens securely**:
   - Use `sessionStorage` for better security
   - Never expose tokens in URLs or logs
   - Clear tokens on logout

2. **Handle token expiration**:
   - Check token validity before requests
   - Implement automatic refresh
   - Redirect to login if refresh fails

3. **API Security**:
   - Always use HTTPS in production
   - Include Authorization header in all protected requests
   - Handle 401/403 responses appropriately

### **Role-Based Access**
1. **Frontend validation**:
   - Check user role before showing UI elements
   - Hide admin features from students
   - Redirect unauthorized users

2. **API validation**:
   - Backend enforces role-based access
   - Students only see their own data
   - Admins can see all data

---

## 📱 **Frontend Framework Integration**

### **React/Vue/Angular**
- Use context/store for authentication state
- Implement protected route components
- Create role-based component rendering

### **Vanilla JavaScript**
- Use localStorage/sessionStorage for token storage
- Implement global authentication state
- Create role-based UI functions

### **Mobile Apps**
- Use secure storage (Keychain/Keystore)
- Implement token refresh in background
- Handle network connectivity issues

---

## 🚨 **Error Handling Scenarios**

### **Authentication Errors**
- **401 Unauthorized**: Token expired → Refresh token → Retry request
- **403 Forbidden**: Insufficient privileges → Show access denied message
- **Network Error**: Server unavailable → Show retry option

### **Token Management Errors**
- **Refresh Token Expired**: Redirect to login
- **Invalid Token**: Clear storage → Redirect to login
- **No Token**: Show login form

### **Role-Based Errors**
- **Access Denied**: Show appropriate message based on user role
- **Feature Not Available**: Hide or disable unavailable features
- **Permission Error**: Redirect to appropriate dashboard

---

## 🎨 **UI/UX Considerations**

### **Login/Register Flow**
- Clear error messages for validation failures
- Loading states during authentication
- Success feedback after login
- Remember me functionality (optional)

### **Dashboard Navigation**
- Role-appropriate navigation menus
- Clear indication of user role
- Easy logout option
- Breadcrumb navigation

### **Error States**
- User-friendly error messages
- Retry mechanisms for failed requests
- Loading indicators for async operations
- Graceful degradation for network issues

---

## 🔧 **Development Workflow**

### **1. Setup Phase**
- Create authentication service
- Implement token storage
- Set up API client with auth headers

### **2. Integration Phase**
- Add auth to existing API calls
- Implement role-based UI
- Add error handling

### **3. Testing Phase**
- Test all user roles
- Test token expiration scenarios
- Test network error handling
- Test role-based access control

### **4. Production Phase**
- Enable HTTPS
- Implement secure token storage
- Add monitoring and logging
- Performance optimization

---

## 📋 **Quick Reference**

### **API Endpoints**
```
Anonymous Access:
- POST /api/chat/              (Anonymous only - no auth required)

Authentication:
- POST /api/auth/register/     (Public)
- POST /api/auth/login/        (Public)
- POST /api/auth/logout/       (Auth required)
- POST /api/auth/token/refresh/ (Public)

Protected Endpoints:
- POST /api/query/             (Auth required)
- POST /api/upload/document/   (Auth required)
- POST /api/upload/csv/        (Auth required)
- GET /api/users/me/stats/     (Auth required)
- GET /api/metrics/            (Admin only)
- GET /api/analytics/queries/  (Admin only)
- GET /api/dashboard/          (Admin only)
```

### **Headers Required**
```
Content-Type: application/json
Authorization: Bearer <access_token>
```

### **User Roles**
```
Anonymous: No authentication, can use /api/chat/ only
Student: Authenticated, can query + upload + view own stats
Admin: Authenticated + is_admin=true, full access
```

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] Users can register and login
- [ ] Tokens are stored and managed securely
- [ ] API calls include proper authentication
- [ ] Role-based UI is implemented correctly
- [ ] Error handling works for all scenarios

### **Security Requirements**
- [ ] Tokens are not exposed in client-side code
- [ ] HTTPS is enforced in production
- [ ] Role-based access is enforced
- [ ] Token expiration is handled gracefully

### **User Experience**
- [ ] Smooth authentication flow
- [ ] Clear role-based navigation
- [ ] Appropriate error messages
- [ ] Responsive design for all devices

---

**This guideline provides the complete integration flow without implementation details. Follow this structure to successfully integrate JWT authentication and role-based access into your frontend application.**
