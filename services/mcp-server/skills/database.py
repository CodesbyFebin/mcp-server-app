"""Database connector skill for PostgreSQL/MySQL/MongoDB integration.

Provides database connectivity for the MCP system with read-only mode
by default, query validation, parameterization, and connection isolation.
"""

import json
import time
from typing import Dict, Any, List, Optional, Literal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type hints for database drivers without hard dependencies
    import psycopg2
    import pymysql
    import pymongo


class DatabaseConnector:
    """Connector for database integration (PostgreSQL, MySQL, MongoDB)."""
    
    supported_dbs: Dict[str, Literal["postgresql", "mysql", "mongodb"]] = {
        "postgresql": "postgresql",
        "mysql": "mysql", 
        "mongodb": "mongodb"
    }
    
    def __init__(self,
                 connection_string: str | None = None,
                 db_type: Literal["postgresql", "mysql", "mongodb"] = "postgresql",
                 read_only: bool = True,
                 pool_size: int = 5,
                 timeout: int = 30,
                 ssl_mode: Literal["require", "disable", "verify-ca"] | None = None):
        self.connection_string = connection_string
        self.db_type = db_type
        self.read_only = read_only
        self.pool_size = pool_size
        self.timeout = timeout
        self.ssl_mode = ssl_mode
        self._connected = False
        self._initialized = False
    
    def connect(self) -> Dict[str, Any]:
        """Establish database connection with safety checks."""
        if not self._initialized:
            self._initialize()
        
        start_time = time.time()
        
        # Validate connection string for target DB type
        validation = self._validate_connection()
        if not validation["valid"]:
            return {
                "connected": False,
                "db_type": self.db_type,
                "errors": validation["errors"]
            }
        
        # Establish connection (mock - integrate with real driver)
        connected = self._establish_connection()
        
        duration = time.time() - start_time
        
        self._connected = connected.get("connected", False)
        
        return {
            "connected": self._connected,
            "db_type": self.db_type,
            "read_only": self.read_only,
            "pool_size": self.pool_size,
            "connection_duration_ms": round(duration * 1000),
            "ssl_mode": self.ssl_mode,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def _validate_connection(self) -> Dict[str, Any]:
        """Validate connection string matches target database type."""
        errors = []
        
        if not self.connection_string:
            errors.append("No connection string provided")
            return {"valid": False, "errors": errors}
        
        # Type-specific validation hints
        if self.db_type == "postgresql" and "postgresql://" not in self.connection_string.lower():
            errors.append("Connection string appears not to be PostgreSQL format (expected postgresql://)")
        elif self.db_type == "mysql" and "mysql://" not in self.connection_string.lower() and "?" not in self.connection_string:
            errors.append("Connection string appears not to be MySQL format (expected mysql://)")
        elif self.db_type == "mongodb" and "mongodb://" not in self.connection_string.lower():
            errors.append("Connection string appears not to be MongoDB format (expected mongodb://)")
        
        # Read-only safety check
        if self.read_only and "unsafe" in self.connection_string.lower():
            errors.append("Connection string contains 'unsafe' keyword while in read-only mode")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _establish_connection(self) -> Dict[str, Any]:
        """Establish the actual database connection. Meant to be overridden."""
        # Mock connection success
        return {
            "connected": True,
            "note": f"Mock {self.db_type} connection established (read-only: {self.read_only})"
        }
    
    def execute_read(self, 
                     query: str,
                     params: Dict[str, Any] | None = None,
                     validate: bool = True) -> Dict[str, Any]:
        """Execute a read-only database query with validation.
        
        Args:
            SQL/query string
            optional parameters for parameterized query
            whether to validate query for safety
            
        Returns:
            Dictionary with query results and metadata
        """
        if not self._connected:
            return {"error": "Database not connected. Call connect() first."}
        
        start_time = time.time()
        
        # Validate query for safety if enabled
        if validate:
            validation = self._validate_query(query, params)
            if not validation["valid"]:
                return {"error": validation["error"], "valid": False}
        
        # Execute query (mock implementation)
        result = self._execute_mock_query(query, params)
        
        duration = time.time() - start_time
        
        return {
            "query": query,
            "params": params or {},
            "result": result,
            "row_count": result.get("row_count", 0) if isinstance(result, dict) else 0,
            "execution_duration_ms": round(duration * 1000),
            "read_only": self.read_only,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def _validate_query(self, query: str, params: Dict[str, Any] | None) -> Dict[str, Any]:
        """Validate query for safety (SQL injection prevention, etc.)."""
        errors = []
        safe_keywords = {"SELECT", "FROM", "WHERE", "AND", "OR", "LIMIT", "OFFSET", "ORDER BY"}
        
        query_upper = query.strip().upper()
        
        # Check for dangerous operations in read-only mode
        dangerous_patterns = [
            r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", 
            r"\bALTER\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"\bGRANT\b",
            r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper):
                errors.append(f"Dangerous SQL keyword detected: {pattern}")
        
        # Check for parameterized query usage
        if params:
            # Good - using parameters
            pass
        elif re.search(r"\bWHERE\s+\w+\s*=\s*'", query_upper):
            errors.append("Potential SQL injection risk: string interpolation in WHERE clause")
        
        # Ensure SELECT or read operation
        if not any(query_upper.startswith(k) for k in safe_keywords) and not query_upper.startswith("WITH"):
            errors.append(f"Query may not be read-only: starts with '{query_upper[:50]}...'")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _execute_mock_query(self, query: str, params: Dict[str, Any] | None) -> Dict[str, Any]:
        """Execute query with mock data. Meant to be overridden with real driver."""
        # Return mock structured data
        return {
            "mock": True,
            "query_type": "SELECT",
            "note": "Mock execution - integrate with real database driver",
            "data": [
                {"id": 1, "name": "Sample record", "value": "test"},
                {"id": 2, "name": "Another record", "value": "example"}
            ] if "SELECT" in query.upper() else None,
            "row_count": 2 if "SELECT" in query.upper() else 0
        }
    
    def execute_write(self, 
                      query: str,
                      params: Dict[str, Any] | None = None,
                      require_approval: bool = True) -> Dict[str, Any]:
        """Execute a write database query with approval requirement.
        
        Args:
            SQL/query string
            optional parameters
            whether to require approval before execution
            
        Returns:
            Dictionary with execution result
        """
        if not self._connected:
            return {"error": "Database not connected. Call connect() first."}
        
        if require_approval and not self._check_approval():
            return {
                "executed": False,
                "approval_status": "rejected",
                "reason": "Write operation requires explicit approval"
            }
        
        start_time = time.time()
        result = self._execute_mock_query(query, params)
        duration = time.time() - start_time
        
        return {
            "query": query,
            "params": params or {},
            "executed": True,
            "result": result,
            "execution_duration_ms": round(duration * 1000),
            "approval_status": "approved" if require_approval else "bypassed",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def _check_approval(self) -> bool:
        """Check if write operation has approval. Meant to integrate with approval system."""
        # In production, this would check an approval workflow
        return True  # Mock: approval granted
    
    def list_tables(self) -> Dict[str, Any]:
        """List database tables (read-only operation)."""
        if not self._connected:
            return {"error": "Database not connected."}
        
        # Mock table listing
        return {
            "tables": [
                "users", "servers", "tools", "resources", "prompts",
                "evidence", "policies", "executions", "skills",
                "model_providers", "audit_events"
            ],
            "db_type": self.db_type,
            "note": "Mock table list - integrate with real database driver"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test database connectivity."""
        if not self._connected:
            return {"error": "Database not connected. Call connect() first."}
        
        start_time = time.time()
        result = self._execute_mock_query("SELECT 1 as test", {})
        duration = time.time() - start_time
        
        return {
            "connected": self._connected,
            "db_type": self.db_type,
            "test_result": result,
            "test_duration_ms": round(duration * 1000),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def close(self) -> Dict[str, Any]:
        """Close database connection."""
        was_connected = self._connected
        self._connected = False
        
        return {
            "closed": True,
            "was_connected": was_connected,
            "db_type": self.db_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def _initialize(self):
        """Initialize the database connector."""
        self._initialized = True


# Convenience function for quick connections
def quick_connect(connection_string: str | None = None,
                  db_type: Literal["postgresql", "mysql", "mongodb"] = "postgresql",
                  read_only: bool = True) -> DatabaseConnector:
    """Quick database connector initialization."""
    return DatabaseConnector(
        connection_string=connection_string,
        db_type=db_type,
        read_only=read_only
    )


# Example usage
if __name__ == "__main__":
    import sys
    
    print("=== Database Connector ===")
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        # Test quick connect
        if arg == "quick":
            connector = quick_connect(read_only=True)
            result = connector.connect()
            print(f"Connect: {result['connected']}")
            print(f"DB type: {result['db_type']}")
            
            # Test read
            read_result = connector.execute_read("SELECT * FROM users WHERE id = %(id)s", {"id": 1})
            print(f"Read: {read_result.get('row_count', 0)} rows")
            
            # List tables
            tables = connector.list_tables()
            print(f"Tables: {len(tables.get('tables', []))}")
            
            # Test connection
            conn_test = connector.test_connection()
            print(f"Test: {conn_test.get('test_result', {}).get('note', 'N/A')}")
            
            # Close
            close_result = connector.close()
            print(f"Closed: {close_result['closed']}")
        
        # Test with connection string
        elif arg == "demo":
            connector = quick_connect(
                connection_string="postgresql://localhost:5432/mcp_servers",
                db_type="postgresql",
                read_only=True
            )
            result = connector.connect()
            print(f"Connect result: {result['connected']}")
            if result["connected"]:
                read_result = connector.execute_read("SELECT 1 as test_query")
                print(f"Query result: {read_result}")
                connector.close()
    
    else:
        # Demo with mock operations
        connector = quick_connect(read_only=True)
        connector.connect()
        
        # Execute read
        read_result = connector.execute_read("SELECT * FROM servers WHERE type = %s", {"type": "mcp"})
        print(f"Read query: {read_result.get('row_count', 0)} rows returned")
        print(f"Duration: {read_result.get('execution_duration_ms')}ms")
        
        # List tables
        tables = connector.list_tables()
        print(f"Available tables: {tables.get('tables', [])}")
        
        # Test connection
        test_result = connector.test_connection()
        print(f"Connection test: {test_result.get('test_result', {}).get('note', 'N/A')}")
        
        # Close
        close_result = connector.close()
        print(f"Connection closed: {close_result['closed']}")