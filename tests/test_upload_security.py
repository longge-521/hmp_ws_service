import pytest
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter

def test_secure_filename():
    adapter = LocalStorageAdapter()
    assert adapter.secure_filename("test.txt") == "test.txt"
    assert adapter.secure_filename("../../etc/passwd") == "passwd"
    assert adapter.secure_filename("a/b/c.jpg") == "c.jpg"
    assert adapter.secure_filename("测试 文件.png") == "测试_文件.png"

def test_validate_upload_id():
    adapter = LocalStorageAdapter()
    
    # 正常情况
    adapter._validate_upload_id("valid_upload_123")
    adapter._validate_upload_id("hash-val.123")
    
    # 非法字符
    with pytest.raises(ValueError):
        adapter._validate_upload_id("invalid/id")
    
    with pytest.raises(ValueError):
        adapter._validate_upload_id("invalid;id")
        
    with pytest.raises(ValueError):
        adapter._validate_upload_id("invalid\\id")

def test_path_traversal_prevention():
    adapter = LocalStorageAdapter()
    
    # 尝试注入路径穿越的 upload_id
    with pytest.raises(ValueError):
        adapter.get_temp_upload_dir("../stolen_path")
        
    with pytest.raises(ValueError):
        adapter.get_temp_upload_dir("..\\stolen_path")
