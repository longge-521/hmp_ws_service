import os
import re
import shutil
import time
import logging
from typing import List, Union

logger = logging.getLogger("hmp_ws_service")

class LocalStorageAdapter:
    """本地磁盘存储适配器：负责临时分片保存、目录清理、物理合并"""
    
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.upload_dir = os.getenv("UPLOAD_DIR", os.path.join(self.base_dir, "uploads"))
        self.temp_dir = os.getenv("TEMP_DIR", os.path.join(self.base_dir, "temp_uploads"))
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [self.upload_dir, self.temp_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def secure_filename(self, filename: str) -> str:
        """过滤文件名中的路径穿越字符，仅保留安全的文件名部分。"""
        filename = os.path.basename(filename)
        filename = re.sub(r'[^\w\u4e00-\u9fff.\-]', '_', filename)
        return filename.strip() or 'unnamed_file'

    def _validate_upload_id(self, upload_id: str):
        """校验 upload_id，防范路径穿越和任意字符注入"""
        if not upload_id or not isinstance(upload_id, str):
            raise ValueError("Invalid upload_id type")
        # 允许字母、数字、下划线、短横线、点号（支持文件哈希/大小组合作为后缀）
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", upload_id):
            raise ValueError("upload_id contains invalid characters")
        if len(upload_id) < 5 or len(upload_id) > 150:
            raise ValueError("upload_id length is out of range")

    def get_temp_upload_dir(self, upload_id: str) -> str:
        self._validate_upload_id(upload_id)
        temp_dir_abs = os.path.abspath(self.temp_dir)
        target_dir = os.path.join(temp_dir_abs, f"tmp_{upload_id}")
        target_dir_abs = os.path.abspath(target_dir)
        
        # 验证最终路径必须严格处于 temp_dir_abs 目录下
        if not target_dir_abs.startswith(temp_dir_abs + os.path.sep):
            raise ValueError("Path traversal detected in upload_id")
        return target_dir_abs

    def get_upload_file_path(self, filename: str) -> str:
        safe_name = self.secure_filename(filename)
        return os.path.join(self.upload_dir, safe_name)

    def save_chunk(self, upload_id: str, chunk_index: int, data: Union[bytes, memoryview]):
        """保存分片文件到临时目录"""
        temp_upload_dir = self.get_temp_upload_dir(upload_id)
        if not os.path.exists(temp_upload_dir):
            os.makedirs(temp_upload_dir)
        
        chunk_file_path = os.path.join(temp_upload_dir, str(chunk_index))
        with open(chunk_file_path, "wb") as f:
            f.write(data)

    def get_completed_chunks(self, upload_id: str) -> List[int]:
        """获取已成功上传的分片索引列表"""
        temp_upload_dir = self.get_temp_upload_dir(upload_id)
        completed_chunks = []
        if os.path.exists(temp_upload_dir):
            for fname in os.listdir(temp_upload_dir):
                if fname.isdigit():
                    completed_chunks.append(int(fname))
            completed_chunks.sort()
        return completed_chunks

    def merge_chunks(self, upload_id: str, filename: str, total_chunks: int) -> str:
        """同步合并文件分片，并在合并完成或失败后自动清理临时文件夹"""
        temp_upload_dir = self.get_temp_upload_dir(upload_id)
        file_path = self.get_upload_file_path(filename)
        
        try:
            for i in range(total_chunks):
                chunk_path = os.path.join(temp_upload_dir, str(i))
                if not os.path.exists(chunk_path):
                    raise FileNotFoundError(f"Chunk {i} is missing, cannot merge")
                    
            with open(file_path, "wb") as target_file:
                for i in range(total_chunks):
                    chunk_path = os.path.join(temp_upload_dir, str(i))
                    with open(chunk_path, "rb") as source_file:
                        shutil.copyfileobj(source_file, target_file, length=256*1024)
            return file_path
        finally:
            temp_dir_abs = os.path.abspath(self.temp_dir)
            if os.path.basename(temp_upload_dir).startswith("tmp_") and temp_upload_dir.startswith(temp_dir_abs):
                shutil.rmtree(temp_upload_dir, ignore_errors=True)

    def abort_upload(self, upload_id: str):
        """清理已中止上传的临时目录"""
        temp_upload_dir = self.get_temp_upload_dir(upload_id)
        temp_dir_abs = os.path.abspath(self.temp_dir)
        if os.path.basename(temp_upload_dir).startswith("tmp_") and temp_upload_dir.startswith(temp_dir_abs):
            shutil.rmtree(temp_upload_dir, ignore_errors=True)

    def cleanup_stale_uploads(self, timeout_hours: float = 2.0) -> int:
        """清理超过超时时间的孤儿临时上传目录"""
        now = time.time()
        timeout_seconds = timeout_hours * 3600
        cleaned = 0
        try:
            if not os.path.exists(self.temp_dir):
                return 0
            for dirname in os.listdir(self.temp_dir):
                if not dirname.startswith("tmp_"):
                    continue
                dirpath = os.path.join(self.temp_dir, dirname)
                if not os.path.isdir(dirpath):
                    continue
                try:
                    mtime = os.path.getmtime(dirpath)
                    if now - mtime > timeout_seconds:
                        shutil.rmtree(dirpath, ignore_errors=True)
                        cleaned += 1
                        logger.info(f"Cleaned up stale temp upload: {dirname}")
                except OSError:
                    pass
        except Exception as e:
            logger.error(f"Error scanning temp uploads: {e}")
        return cleaned
