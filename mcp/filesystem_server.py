"""
File System MCP Server

Provides secure file system access for code generation.
Handles writing POMs, tests, and other generated artifacts.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json


class FileSystemMCPServer:
    """
    MCP Server for file system operations.
    
    Provides tools for:
    - Writing code files (POMs, tests)
    - Creating directory structures
    - Reading template files
    - Managing generated artifacts
    """
    
    def __init__(self, base_dir: Path, allowed_extensions: Optional[List[str]] = None):
        """
        Initialize File System MCP Server.
        
        Args:
            base_dir: Base directory for all file operations
            allowed_extensions: List of allowed file extensions (e.g., ['.ts', '.js', '.py'])
                               If None, allows all extensions
        """
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = allowed_extensions or [
            '.ts', '.js', '.py', '.json', '.md', '.yml', '.yaml'
        ]
    
    def _validate_path(self, path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate that a path is safe to write to.
        
        Args:
            path: Path to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Resolve to absolute path
            abs_path = path.resolve()
            
            # Check if path is within base_dir
            if not str(abs_path).startswith(str(self.base_dir)):
                return False, f"Path {path} is outside base directory {self.base_dir}"
            
            # Check file extension
            if self.allowed_extensions and abs_path.suffix not in self.allowed_extensions:
                return False, f"Extension {abs_path.suffix} not allowed. Allowed: {self.allowed_extensions}"
            
            return True, None
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
    
    def write_file(
        self,
        relative_path: str,
        content: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            relative_path: Path relative to base_dir
            content: File content to write
            overwrite: Whether to overwrite existing files
        
        Returns:
            Dict with status and file info
        """
        try:
            file_path = self.base_dir / relative_path
            
            # Validate path
            is_valid, error = self._validate_path(file_path)
            if not is_valid:
                return {
                    "status": "error",
                    "error": error,
                }
            
            # Check if file exists
            if file_path.exists() and not overwrite:
                return {
                    "status": "error",
                    "error": f"File {relative_path} already exists. Set overwrite=True to replace.",
                }
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "path": str(file_path),
                "relative_path": relative_path,
                "size_bytes": len(content.encode('utf-8')),
                "overwritten": file_path.exists(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def read_file(self, relative_path: str) -> Dict[str, Any]:
        """
        Read content from a file.
        
        Args:
            relative_path: Path relative to base_dir
        
        Returns:
            Dict with status and file content
        """
        try:
            file_path = self.base_dir / relative_path
            
            # Validate path
            is_valid, error = self._validate_path(file_path)
            if not is_valid:
                return {
                    "status": "error",
                    "error": error,
                }
            
            # Check if file exists
            if not file_path.exists():
                return {
                    "status": "error",
                    "error": f"File {relative_path} does not exist",
                }
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "path": str(file_path),
                "relative_path": relative_path,
                "content": content,
                "size_bytes": len(content.encode('utf-8')),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def create_directory(self, relative_path: str) -> Dict[str, Any]:
        """
        Create a directory structure.
        
        Args:
            relative_path: Directory path relative to base_dir
        
        Returns:
            Dict with status and directory info
        """
        try:
            dir_path = self.base_dir / relative_path
            
            # Check if path is within base_dir
            if not str(dir_path.resolve()).startswith(str(self.base_dir)):
                return {
                    "status": "error",
                    "error": f"Path {relative_path} is outside base directory",
                }
            
            # Create directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "status": "success",
                "path": str(dir_path),
                "relative_path": relative_path,
                "created": True,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def list_files(
        self,
        relative_path: str = "",
        pattern: str = "*",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        List files in a directory.
        
        Args:
            relative_path: Directory path relative to base_dir
            pattern: Glob pattern to match files
            recursive: Whether to search recursively
        
        Returns:
            Dict with status and list of files
        """
        try:
            dir_path = self.base_dir / relative_path
            
            if not dir_path.exists():
                return {
                    "status": "error",
                    "error": f"Directory {relative_path} does not exist",
                }
            
            if not dir_path.is_dir():
                return {
                    "status": "error",
                    "error": f"{relative_path} is not a directory",
                }
            
            # List files
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))
            
            # Convert to relative paths
            file_info = []
            for file in files:
                if file.is_file():
                    rel_path = file.relative_to(self.base_dir)
                    file_info.append({
                        "path": str(rel_path),
                        "name": file.name,
                        "size_bytes": file.stat().st_size,
                        "extension": file.suffix,
                    })
            
            return {
                "status": "success",
                "directory": relative_path,
                "count": len(file_info),
                "files": file_info,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def delete_file(self, relative_path: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            relative_path: Path relative to base_dir
        
        Returns:
            Dict with status
        """
        try:
            file_path = self.base_dir / relative_path
            
            # Validate path
            is_valid, error = self._validate_path(file_path)
            if not is_valid:
                return {
                    "status": "error",
                    "error": error,
                }
            
            # Check if file exists
            if not file_path.exists():
                return {
                    "status": "error",
                    "error": f"File {relative_path} does not exist",
                }
            
            # Delete file
            file_path.unlink()
            
            return {
                "status": "success",
                "path": str(file_path),
                "relative_path": relative_path,
                "deleted": True,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def write_json(
        self,
        relative_path: str,
        data: Dict[str, Any],
        overwrite: bool = False,
        indent: int = 2
    ) -> Dict[str, Any]:
        """
        Write JSON data to a file.
        
        Args:
            relative_path: Path relative to base_dir
            data: Dictionary to serialize as JSON
            overwrite: Whether to overwrite existing files
            indent: JSON indentation level
        
        Returns:
            Dict with status and file info
        """
        try:
            content = json.dumps(data, indent=indent, default=str)
            return self.write_file(relative_path, content, overwrite=overwrite)
        except Exception as e:
            return {
                "status": "error",
                "error": f"JSON serialization error: {str(e)}",
                "error_type": type(e).__name__,
            }
    
    def read_json(self, relative_path: str) -> Dict[str, Any]:
        """
        Read JSON data from a file.
        
        Args:
            relative_path: Path relative to base_dir
        
        Returns:
            Dict with status and parsed JSON data
        """
        result = self.read_file(relative_path)
        
        if result["status"] != "success":
            return result
        
        try:
            data = json.loads(result["content"])
            result["data"] = data
            del result["content"]  # Remove raw content, keep parsed data
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"JSON parse error: {str(e)}",
                "error_type": "JSONDecodeError",
            }


# Example usage
if __name__ == "__main__":
    # Example: Create a file system server for generated code
    fs_server = FileSystemMCPServer(
        base_dir=Path("./output/example-project"),
        allowed_extensions=['.ts', '.js', '.json']
    )
    
    # Create directory structure
    print(fs_server.create_directory("pages"))
    print(fs_server.create_directory("tests"))
    
    # Write a POM file
    pom_content = """import { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  async navigate() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.page.getByLabel('Username').fill(username);
    await this.page.getByLabel('Password').fill(password);
    await this.page.getByRole('button', { name: 'Login' }).click();
  }
}
"""
    
    result = fs_server.write_file("pages/LoginPage.ts", pom_content)
    print(json.dumps(result, indent=2))
    
    # List files
    files = fs_server.list_files("pages", pattern="*.ts")
    print(json.dumps(files, indent=2))
