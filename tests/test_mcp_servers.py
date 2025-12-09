"""
Tests for MCP Servers
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from mcp.browser_server import BrowserMCPServer
from mcp.filesystem_server import FileSystemMCPServer


class TestFileSystemMCPServer:
    """Test suite for File System MCP Server"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def fs_server(self, temp_dir):
        """Create File System MCP Server instance"""
        return FileSystemMCPServer(
            base_dir=temp_dir,
            allowed_extensions=['.ts', '.js', '.json']
        )
    
    def test_write_file_success(self, fs_server):
        """Test successful file write"""
        result = fs_server.write_file(
            "test.ts",
            "console.log('test');",
            overwrite=False
        )
        
        assert result["status"] == "success"
        assert "test.ts" in result["path"]
        assert result["size_bytes"] > 0
    
    def test_write_file_prevents_overwrite(self, fs_server):
        """Test that overwrite protection works"""
        fs_server.write_file("test.ts", "content1")
        result = fs_server.write_file("test.ts", "content2", overwrite=False)
        
        assert result["status"] == "error"
        assert "already exists" in result["error"]
    
    def test_write_file_allows_overwrite(self, fs_server):
        """Test that overwrite=True works"""
        fs_server.write_file("test.ts", "content1")
        result = fs_server.write_file("test.ts", "content2", overwrite=True)
        
        assert result["status"] == "success"
    
    def test_write_file_rejects_invalid_extension(self, fs_server):
        """Test that invalid extensions are rejected"""
        result = fs_server.write_file("test.py", "print('test')")
        
        assert result["status"] == "error"
        assert "not allowed" in result["error"]
    
    def test_write_file_prevents_path_traversal(self, fs_server):
        """Test that path traversal is prevented"""
        result = fs_server.write_file("../../../etc/passwd", "malicious")
        
        assert result["status"] == "error"
        assert "outside base directory" in result["error"]
    
    def test_create_directory(self, fs_server):
        """Test directory creation"""
        result = fs_server.create_directory("pages/components")
        
        assert result["status"] == "success"
        assert Path(result["path"]).exists()
    
    def test_read_file(self, fs_server):
        """Test file reading"""
        content = "test content"
        fs_server.write_file("test.ts", content)
        
        result = fs_server.read_file("test.ts")
        
        assert result["status"] == "success"
        assert result["content"] == content
    
    def test_write_and_read_json(self, fs_server):
        """Test JSON operations"""
        data = {"key": "value", "number": 42}
        
        write_result = fs_server.write_json("data.json", data)
        assert write_result["status"] == "success"
        
        read_result = fs_server.read_json("data.json")
        assert read_result["status"] == "success"
        assert read_result["data"] == data
    
    def test_list_files(self, fs_server):
        """Test file listing"""
        fs_server.write_file("file1.ts", "content1")
        fs_server.write_file("file2.ts", "content2")
        fs_server.write_file("file3.js", "content3")
        
        result = fs_server.list_files("", pattern="*.ts")
        
        assert result["status"] == "success"
        assert result["count"] == 2
    
    def test_delete_file(self, fs_server):
        """Test file deletion"""
        fs_server.write_file("test.ts", "content")
        
        result = fs_server.delete_file("test.ts")
        
        assert result["status"] == "success"
        assert result["deleted"] is True


class TestBrowserMCPServer:
    """Test suite for Browser MCP Server"""
    
    @pytest.fixture
    async def browser_server(self):
        """Create Browser MCP Server instance"""
        server = BrowserMCPServer(headless=True)
        await server.initialize()
        yield server
        await server.cleanup()
    
    @pytest.mark.asyncio
    async def test_navigate_success(self, browser_server):
        """Test successful navigation"""
        result = await browser_server.navigate("https://example.com")
        
        assert result["status"] == "success"
        assert "example.com" in result["final_url"]
        assert result["title"] is not None
    
    @pytest.mark.asyncio
    async def test_capture_dom(self, browser_server):
        """Test DOM capture"""
        await browser_server.navigate("https://example.com")
        result = await browser_server.capture_dom()
        
        assert result["status"] == "success"
        assert len(result["html"]) > 0
        assert result["size_bytes"] > 0
    
    @pytest.mark.asyncio
    async def test_discover_elements(self, browser_server):
        """Test element discovery"""
        await browser_server.navigate("https://example.com")
        result = await browser_server.discover_elements()
        
        assert result["status"] == "success"
        assert result["count"] >= 0
        assert isinstance(result["elements"], list)
    
    @pytest.mark.asyncio
    async def test_get_page_metadata(self, browser_server):
        """Test metadata extraction"""
        await browser_server.navigate("https://example.com")
        result = await browser_server.get_page_metadata()
        
        assert result["status"] == "success"
        assert "title" in result
        assert "url" in result
    
    @pytest.mark.asyncio
    async def test_capture_screenshot(self, browser_server):
        """Test screenshot capture"""
        await browser_server.navigate("https://example.com")
        result = await browser_server.capture_screenshot()
        
        assert result["status"] == "success"
        assert "data" in result  # Base64 encoded
        assert result["size_bytes"] > 0
