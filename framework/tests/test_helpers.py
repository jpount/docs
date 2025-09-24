#!/usr/bin/env python3
"""
Test helper utilities for RepomixParser tests
Provides sample data and utility functions for testing
"""

class SampleRepomixData:
    """Sample repomix file contents for testing"""

    MINIMAL_FILE = """# File Summary

## File: Test.java
```java
public class Test {}
```
"""

    JAVA_COMPLETE = """# File Summary

## File: com/example/CompleteExample.java
```java
package com.example;

import java.util.*;
import java.io.IOException;

// Test class with various components
@Entity
@Table(name = "users")
public class User extends BaseEntity implements Serializable {
    private Long id;
    private String name;

    public User() {}

    public User(String name) {
        this.name = name;
    }

    @Id
    @GeneratedValue
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    @Column(nullable = false)
    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    @Transactional
    public void updateName(String newName) throws ValidationException {
        if (newName == null || newName.trim().isEmpty()) {
            throw new ValidationException("Name cannot be empty");
        }
        this.name = newName;
    }

    private void validateState() {
        // Private helper method
    }

    public static User createDefault() {
        return new User("Default");
    }

    // Inner class
    public static class Builder {
        private String name;

        public Builder withName(String name) {
            this.name = name;
            return this;
        }

        public User build() {
            return new User(name);
        }
    }

    // Inner interface
    public interface UserListener {
        void onUserUpdated(User user);
    }

    // Inner enum
    public enum Status {
        ACTIVE, INACTIVE, SUSPENDED
    }
}
```
"""

    PYTHON_COMPLETE = """# File Summary

## File: example.py
```python
#!/usr/bin/env python3
\"\"\"
Example Python module with various components
\"\"\"

import os
import sys
from typing import List, Optional
from dataclasses import dataclass

# Global constant
MAX_RETRIES = 3

# Decorator
def retry(max_attempts=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_attempts - 1:
                        raise
            return None
        return wrapper
    return decorator

# Data class
@dataclass
class Config:
    host: str
    port: int
    debug: bool = False

# Regular class
class Service:
    \"\"\"Main service class\"\"\"

    def __init__(self, config: Config):
        self.config = config
        self._connection = None

    @property
    def connected(self) -> bool:
        return self._connection is not None

    @retry(max_attempts=MAX_RETRIES)
    def connect(self) -> None:
        \"\"\"Connect to service\"\"\"
        # Connection logic here
        pass

    async def fetch_data(self, query: str) -> List[dict]:
        \"\"\"Fetch data asynchronously\"\"\"
        # Async implementation
        return []

    @staticmethod
    def parse_response(response: dict) -> Optional[str]:
        \"\"\"Parse API response\"\"\"
        return response.get('data')

    @classmethod
    def from_env(cls):
        \"\"\"Create instance from environment variables\"\"\"
        config = Config(
            host=os.getenv('SERVICE_HOST', 'localhost'),
            port=int(os.getenv('SERVICE_PORT', 8080)),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )
        return cls(config)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def disconnect(self):
        \"\"\"Disconnect from service\"\"\"
        self._connection = None

# Function
def process_items(items: List[str]) -> dict:
    \"\"\"Process a list of items\"\"\"
    result = {}
    for item in items:
        result[item] = len(item)
    return result

# Async function
async def async_operation():
    \"\"\"Perform async operation\"\"\"
    await asyncio.sleep(1)
    return "Done"

# Lambda function
calculate = lambda x, y: x + y

# Generator function
def fibonacci(n):
    \"\"\"Generate Fibonacci sequence\"\"\"
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# API decorators (Flask-style)
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.post('/api/users')
async def create_user(request):
    data = await request.json()
    return {'id': 1, **data}

@api.endpoint('/health')
def health_check():
    return {'status': 'healthy'}

if __name__ == '__main__':
    service = Service.from_env()
    with service:
        print("Service running")
```
"""

    JSP_COMPLETE = """# File Summary

## File: webapp/dashboard.jsp
```jsp
<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="java.util.*" %>
<%@ page import="com.example.model.*" %>
<%@ page import="com.example.service.UserService" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/fmt" prefix="fmt" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>

<jsp:useBean id="userBean" class="com.example.model.User" scope="session"/>
<jsp:useBean id="dashboardBean" class="com.example.bean.DashboardBean" scope="request"/>
<jsp:useBean id="settingsBean" type="com.example.bean.SettingsBean" scope="application"/>

<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <script>
        function validateForm() {
            var username = document.getElementById("username").value;
            if (username == "") {
                alert("Username must be filled out");
                return false;
            }
        }
    </script>
</head>
<body>
    <h1>Welcome ${userBean.username}!</h1>

    <%-- JSP Comment: User info section --%>
    <div id="userInfo">
        <%
            // Java scriptlet
            String role = (String) session.getAttribute("userRole");
            UserService userService = new UserService();
            List<User> users = userService.getAllUsers();

            if (role != null && role.equals("admin")) {
                out.println("<p>Admin Panel</p>");
            }

            // Inline method definition (rare but valid)
            class Helper {
                public String formatDate(Date date) {
                    return new SimpleDateFormat("yyyy-MM-dd").format(date);
                }
            }

            Helper helper = new Helper();
            String today = helper.formatDate(new Date());
        %>

        <p>Today's date: <%= today %></p>
        <p>Total users: <%= users.size() %></p>
    </div>

    <%-- JSTL Conditionals --%>
    <c:if test="${not empty userBean.email}">
        <p>Email: ${userBean.email}</p>
    </c:if>

    <c:choose>
        <c:when test="${userBean.status == 'active'}">
            <span class="status-active">Active</span>
        </c:when>
        <c:when test="${userBean.status == 'pending'}">
            <span class="status-pending">Pending</span>
        </c:when>
        <c:otherwise>
            <span class="status-inactive">Inactive</span>
        </c:otherwise>
    </c:choose>

    <%-- JSTL Loops --%>
    <c:forEach items="${dashboardBean.notifications}" var="notification">
        <div class="notification">
            <c:out value="${notification.message}"/>
            <fmt:formatDate value="${notification.date}" pattern="MM/dd/yyyy"/>
        </div>
    </c:forEach>

    <c:forEach begin="1" end="5" var="i">
        <p>Item ${i}</p>
    </c:forEach>

    <%-- Form with validation --%>
    <form action="updateUser.jsp" method="post" onsubmit="return validateForm()">
        <input type="text" id="username" name="username" value="${userBean.username}"/>
        <input type="email" name="email" value="${userBean.email}"/>
        <input type="submit" value="Update"/>
    </form>

    <%-- Include another JSP --%>
    <jsp:include page="footer.jsp">
        <jsp:param name="year" value="2024"/>
    </jsp:include>

    <%!
        // Declaration section
        private static final String VERSION = "1.0.0";

        public String getVersion() {
            return VERSION;
        }

        private int counter = 0;

        public int incrementCounter() {
            return ++counter;
        }
    %>

    <p>Version: <%= getVersion() %></p>
    <p>Page views: <%= incrementCounter() %></p>
</body>
</html>
```
"""

    JSF_XHTML = """# File Summary

## File: webapp/userForm.xhtml
```xhtml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:h="http://xmlns.jcp.org/jsf/html"
      xmlns:f="http://xmlns.jcp.org/jsf/core"
      xmlns:ui="http://xmlns.jcp.org/jsf/facelets"
      xmlns:p="http://primefaces.org/ui">

<h:head>
    <title>User Registration</title>
</h:head>

<h:body>
    <h:form id="userForm">
        <h:panelGrid columns="3">
            <h:outputLabel for="username" value="Username:"/>
            <h:inputText id="username" value="#{userBean.username}" required="true">
                <f:validateLength minimum="3" maximum="20"/>
                <f:ajax event="blur" render="usernameMessage"/>
            </h:inputText>
            <h:message id="usernameMessage" for="username"/>

            <h:outputLabel for="email" value="Email:"/>
            <h:inputText id="email" value="#{userBean.email}" required="true">
                <f:validateRegex pattern="^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$"/>
            </h:inputText>
            <h:message for="email"/>

            <h:outputLabel for="age" value="Age:"/>
            <h:inputText id="age" value="#{userBean.age}">
                <f:validateLongRange minimum="18" maximum="120"/>
            </h:inputText>
            <h:message for="age"/>

            <h:outputLabel for="country" value="Country:"/>
            <h:selectOneMenu id="country" value="#{userBean.country}">
                <f:selectItems value="#{applicationBean.countries}"/>
            </h:selectOneMenu>
            <h:message for="country"/>

            <h:outputLabel for="interests" value="Interests:"/>
            <h:selectManyCheckbox id="interests" value="#{userBean.interests}">
                <f:selectItems value="#{applicationBean.interestOptions}"/>
            </h:selectManyCheckbox>
            <h:message for="interests"/>

            <h:commandButton value="Submit" action="#{userController.saveUser}">
                <f:ajax execute="@form" render="@form :messages"/>
            </h:commandButton>

            <h:commandButton value="Cancel" action="#{userController.cancel}" immediate="true"/>
        </h:panelGrid>

        <h:dataTable value="#{userController.users}" var="user" rendered="#{not empty userController.users}">
            <h:column>
                <f:facet name="header">Username</f:facet>
                #{user.username}
            </h:column>
            <h:column>
                <f:facet name="header">Email</f:facet>
                #{user.email}
            </h:column>
            <h:column>
                <f:facet name="header">Actions</f:facet>
                <h:commandLink action="#{userController.edit(user)}" value="Edit"/>
                <h:commandLink action="#{userController.delete(user)}" value="Delete">
                    <f:ajax render="@form"/>
                </h:commandLink>
            </h:column>
        </h:dataTable>
    </h:form>

    <h:messages id="messages" globalOnly="true"/>

    <ui:repeat value="#{dashboardBean.alerts}" var="alert">
        <div class="alert">
            <h:outputText value="#{alert.message}" escape="false"/>
        </div>
    </ui:repeat>
</h:body>
</html>
```
"""

    JAVASCRIPT_COMPLETE = """# File Summary

## File: src/app.js
```javascript
// ES6+ JavaScript with various components
import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';

// Constants
const API_URL = 'https://api.example.com';
const MAX_RETRIES = 3;

// Interface (TypeScript)
interface User {
    id: number;
    name: string;
    email: string;
}

// Type alias
type Status = 'active' | 'inactive' | 'pending';

// Enum (TypeScript)
enum Role {
    Admin = 'ADMIN',
    User = 'USER',
    Guest = 'GUEST'
}

// Class component
class UserService {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.cache = new Map();
    }

    async getUser(id) {
        if (this.cache.has(id)) {
            return this.cache.get(id);
        }

        const response = await axios.get(`${this.apiUrl}/users/${id}`);
        this.cache.set(id, response.data);
        return response.data;
    }

    static getInstance() {
        if (!UserService.instance) {
            UserService.instance = new UserService(API_URL);
        }
        return UserService.instance;
    }
}

// Function component
export function UserList({ users }) {
    const [selectedUser, setSelectedUser] = useState(null);

    const handleUserClick = (user) => {
        setSelectedUser(user);
    };

    return (
        <div>
            {users.map(user => (
                <UserCard key={user.id} user={user} onClick={handleUserClick} />
            ))}
        </div>
    );
}

// Arrow function component
export const UserCard = ({ user, onClick }) => {
    return (
        <div onClick={() => onClick(user)}>
            <h3>{user.name}</h3>
            <p>{user.email}</p>
        </div>
    );
};

// Regular function
function formatDate(date) {
    return new Intl.DateTimeFormat('en-US').format(date);
}

// Async function
async function fetchUsers(page = 1) {
    try {
        const response = await axios.get(`${API_URL}/users?page=${page}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching users:', error);
        throw error;
    }
}

// Generator function
function* idGenerator() {
    let id = 1;
    while (true) {
        yield id++;
    }
}

// Arrow functions
const add = (a, b) => a + b;
const multiply = (a, b) => a * b;
const isEven = num => num % 2 === 0;

// IIFE
(function() {
    console.log('Initialized');
})();

// Object with methods
const utils = {
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Higher-order function
const withAuth = (Component) => {
    return function AuthenticatedComponent(props) {
        const isAuthenticated = useAuth();
        if (!isAuthenticated) {
            return <Redirect to="/login" />;
        }
        return <Component {...props} />;
    };
};

// Custom hook
export function useAuth() {
    const [user, setUser] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            validateToken(token).then(setUser);
        }
    }, []);

    return user;
}

// Export variations
export default UserService;
export { formatDate, fetchUsers };
export const API_KEY = 'xyz123';
```
"""

    CONFIG_FILES = """# File Summary

## File: application.properties
```properties
# Server Configuration
server.port=8080
server.context-path=/api
server.shutdown=graceful

# Database Configuration
spring.datasource.url=jdbc:mysql://localhost:3306/mydb
spring.datasource.username=dbuser
spring.datasource.password=${DB_PASSWORD}
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver

# JPA Configuration
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
spring.jpa.database-platform=org.hibernate.dialect.MySQL8Dialect

# Logging
logging.level.root=INFO
logging.level.com.example=DEBUG
logging.file.name=app.log

# Custom Properties
app.name=MyApplication
app.version=1.0.0
app.security.jwt-secret=${JWT_SECRET:defaultSecret}
app.security.jwt-expiration=86400000

# Feature Flags
feature.new-ui=true
feature.beta-api=false

#commented.property=should-be-ignored
```

## File: config.yml
```yaml
# Application Configuration
app:
  name: MyApplication
  version: 1.0.0
  description: Sample application configuration

server:
  host: localhost
  port: 8080
  ssl:
    enabled: true
    keystore: /path/to/keystore.jks

database:
  primary:
    url: jdbc:mysql://localhost:3306/maindb
    username: root
    password: secret
  replica:
    url: jdbc:mysql://localhost:3306/replicadb
    username: readonly
    password: readonly123

cache:
  type: redis
  host: localhost
  port: 6379
  ttl: 3600

features:
  authentication: true
  notifications: true
  analytics: false

# Nested configuration
logging:
  level:
    root: INFO
    com.example: DEBUG
  appenders:
    - type: console
      pattern: "%d{ISO8601} [%thread] %-5level %logger{36} - %msg%n"
    - type: file
      file: /var/log/app.log
      maxSize: 100MB
```

## File: pom.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>myapp</artifactId>
    <version>1.0.0</version>
    <packaging>war</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <spring.version>5.3.9</spring.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>${spring.version}</version>
        </dependency>
    </dependencies>
</project>
```
"""

    EDGE_CASES = """# File Summary

## File: EdgeCases.java
```java
// Edge case: Missing class name
public class {
}

// Edge case: Invalid method syntax
public void method( {
}

// Edge case: Class name starting with number (invalid)
class 123Invalid {
}

// Edge case: Double modifier
public public class DoubleModifier {
}

// Edge case: Unclosed string
String unclosed = "This is an unclosed string
```

## File: Empty.java
```java
```

## File: OnlyComments.java
```java
// This file only contains comments
/* Multi-line comment
   with no actual code */
// Another comment
```

## File: SpecialChars.java
```java
public class ŪñïçödëClass {
    public void método() {
        String 中文 = "Chinese characters";
    }
}
```

## File: Nested.java
```java
public class Outer {
    public class Inner {
        public class DeepNested {
            public class VeryDeepNested {
                public void deepMethod() {}
            }
        }
    }
}
```
"""

    MULTI_LANGUAGE = """# File Summary

## File: mixed.jsp
```jsp
<%@ page import="java.util.*" %>
<jsp:useBean id="userBean" class="User" scope="session"/>

<%
    // Java code in JSP
    public class InlineClass {
        public void process() {}
    }
%>

<script>
    // JavaScript in JSP
    function validate() {
        return true;
    }

    class JSClass {
        constructor() {}
    }
</script>

<style>
    /* CSS is not extracted */
    .container { margin: 0; }
</style>

<c:forEach items="${items}" var="item">
    ${item.name}
</c:forEach>
```

## File: polyglot.html
```html
<!DOCTYPE html>
<html>
<head>
    <script type="text/javascript">
        function initPage() {
            console.log("Initializing");
        }
    </script>
    <style>
        body { margin: 0; }
    </style>
</head>
<body>
    <?php
        echo "PHP code in HTML";
        function phpFunction() {
            return "Hello";
        }
    ?>
</body>
</html>
```
"""

    @staticmethod
    def create_large_file(num_classes=100, num_methods_per_class=10):
        """Generate a large repomix file for performance testing"""
        lines = ["# File Summary\n\n"]

        for i in range(num_classes):
            lines.append(f"## File: com/example/Class{i}.java\n")
            lines.append("```java\n")
            lines.append(f"public class Class{i} {{\n")

            for j in range(num_methods_per_class):
                lines.append(f"    public void method{j}() {{\n")
                lines.append(f"        // Method implementation\n")
                lines.append(f"    }}\n\n")

            lines.append("}\n")
            lines.append("```\n\n")

        return "".join(lines)


class TestUtilities:
    """Utility functions for testing"""

    @staticmethod
    def count_components(parser):
        """Count total extracted components"""
        return sum(len(v) for v in parser.components.values())

    @staticmethod
    def get_component_by_name(parser, component_type, name):
        """Find a specific component by name"""
        components = parser.components.get(component_type, [])
        return next((c for c in components if c.name == name), None)

    @staticmethod
    def assert_component_exists(test_case, parser, component_type, name):
        """Assert that a component exists"""
        component = TestUtilities.get_component_by_name(parser, component_type, name)
        test_case.assertIsNotNone(
            component,
            f"Component {name} not found in {component_type}"
        )
        return component

    @staticmethod
    def create_parser_with_content(content, temp_dir="/tmp"):
        """Create a parser with given content"""
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            dir=temp_dir,
            delete=False
        ) as f:
            f.write(content)
            temp_file = f.name

        parser = RepomixParser(temp_file)
        parser.load()
        return parser, temp_file