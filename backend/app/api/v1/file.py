import os
import hashlib
import time
import json
import base64
import hmac
import requests
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query
from app.api.v1.deps import get_current_user, require_login
from app.db import SessionLocal, SysFile
from app.boot import APIException, logger
from app.boot.config import qiniu_config

router = APIRouter(prefix="/files", tags=["文件服务"])

# 上传目录绝对路径
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "public", "uploads")

def upload_to_qiniu(content: bytes, filename: str, mime_type: str, key: str) -> bool:
    """上传文件内容到七牛云"""
    if not qiniu_config.is_configured:
        return False
        
    access_key = qiniu_config.access_key
    secret_key = qiniu_config.secret_key
    bucket = qiniu_config.bucket
    upload_endpoint = qiniu_config.upload_endpoint
    
    deadline = int(time.time()) + qiniu_config.token_expire
    policy = {
        "scope": bucket,
        "deadline": deadline
    }
    json_policy = json.dumps(policy, separators=(',', ':'))
    
    encoded_policy = base64.urlsafe_b64encode(json_policy.encode('utf-8')).decode('utf-8')
    
    sign = hmac.new(secret_key.encode('utf-8'), encoded_policy.encode('utf-8'), hashlib.sha1).digest()
    encoded_sign = base64.urlsafe_b64encode(sign).decode('utf-8')
    
    token = f"{access_key}:{encoded_sign}:{encoded_policy}"
    
    files = {
        "file": (filename, content, mime_type)
    }
    data = {
        "token": token,
        "key": key
    }
    
    try:
        response = requests.post(upload_endpoint, data=data, files=files, timeout=30)
        if response.status_code == 200:
            logger.info(f"Successfully uploaded {filename} to Qiniu key {key}")
            return True
        else:
            logger.error(f"Failed to upload to Qiniu: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error uploading to Qiniu: {e}")
        return False

def delete_from_qiniu(key: str) -> bool:
    """从七牛云删除文件"""
    if not qiniu_config.is_configured:
        return False
        
    access_key = qiniu_config.access_key
    secret_key = qiniu_config.secret_key
    bucket = qiniu_config.bucket
    
    entry = f"{bucket}:{key}"
    encoded_entry = base64.urlsafe_b64encode(entry.encode('utf-8')).decode('utf-8')
    path = f"/delete/{encoded_entry}"
    
    signing_str = f"{path}\n"
    sign = hmac.new(secret_key.encode('utf-8'), signing_str.encode('utf-8'), hashlib.sha1).digest()
    encoded_sign = base64.urlsafe_b64encode(sign).decode('utf-8')
    token = f"{access_key}:{encoded_sign}"
    
    url = f"http://rs.qiniu.com{path}"
    headers = {
        "Authorization": f"QBox {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info(f"Successfully deleted key {key} from Qiniu")
            return True
        else:
            logger.error(f"Failed to delete from Qiniu: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error deleting from Qiniu: {e}")
        return False

def get_file_url(filepath: str) -> str:
    """根据 filepath 获取完整的 URL。支持本地和七牛。"""
    if filepath.startswith("public/uploads/"):
        filename = os.path.basename(filepath)
        return f"/uploads/{filename}"
    else:
        # 七牛云存储
        domain = qiniu_config.public_domain.rstrip("/") if qiniu_config.is_configured else "https://qiniu.muqiangyun.cn"
        return f"{domain}/{filepath}"

@router.post("/upload", summary="上传单个文件")
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(require_login)
):
    # 确保本地上传目录存在（虽然七牛启用时可能不用，但作为备用/以防万一）
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 读取内容以计算 MD5 哈希
    content = await file.read()
    file_size = len(content)
    md5_hash = hashlib.md5(content).hexdigest()
    
    # 检查数据库是否已存在该 MD5 的文件
    with SessionLocal() as db:
        existing = db.query(SysFile).filter(SysFile.hash_md5 == md5_hash).first()
        if existing:
            # 文件去重：如果已存在，直接返回已存在的文件信息
            return {
                "id": existing.id,
                "filename": file.filename, # 依然使用当前上传的文件名
                "filepath": existing.filepath,
                "url": get_file_url(existing.filepath),
                "file_size": existing.file_size,
                "mime_type": existing.mime_type,
                "hash_md5": existing.hash_md5,
                "duplicate": True
            }
            
    # 如果不存在，保存新文件
    # 为防止文件名冲突，使用 md5 命名，但保留原后缀
    ext = os.path.splitext(file.filename)[1]
    save_filename = f"{md5_hash}{ext}"
    
    if qiniu_config.is_configured:
        # 使用七牛云存储
        key = f"uploads/{save_filename}"
        success = upload_to_qiniu(content, file.filename, file.content_type or "application/octet-stream", key)
        if not success:
            raise APIException("上传文件到七牛云失败", code=500, status_code=500)
        rel_filepath = key
    else:
        # 回落本地存储
        save_path = os.path.join(UPLOAD_DIR, save_filename)
        try:
            with open(save_path, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise APIException("保存文件失败", code=500, status_code=500)
        rel_filepath = f"public/uploads/{save_filename}"
        
    # 保存数据库记录
    with SessionLocal() as db:
        db_file = SysFile(
            filename=file.filename,
            filepath=rel_filepath,
            file_size=file_size,
            mime_type=file.content_type,
            hash_md5=md5_hash,
            created_by=current_user.id
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {
            "id": db_file.id,
            "filename": db_file.filename,
            "filepath": db_file.filepath,
            "url": get_file_url(db_file.filepath),
            "file_size": db_file.file_size,
            "mime_type": db_file.mime_type,
            "hash_md5": db_file.hash_md5,
            "duplicate": False
        }

@router.get("", summary="文件列表")
async def list_files(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    filename: Optional[str] = Query(None),
    current_user = Depends(require_login)
):
    page = max(1, page)
    size = max(1, min(size, 100))
    
    with SessionLocal() as db:
        query = db.query(SysFile)
        if filename:
            query = query.filter(SysFile.filename.like(f"%{filename.strip()}%"))
            
        total = query.count()
        rows = query.order_by(SysFile.id.desc()).offset((page - 1) * size).limit(size).all()
        
        items = []
        for r in rows:
            items.append({
                "id": r.id,
                "filename": r.filename,
                "filepath": r.filepath,
                "url": get_file_url(r.filepath),
                "file_size": r.file_size,
                "mime_type": r.mime_type,
                "hash_md5": r.hash_md5,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
            
        return {
            "total": total,
            "items": items,
            "page": page,
            "size": size
        }

@router.delete("/{file_id}", summary="删除文件")
async def delete_file(
    file_id: int,
    current_user = Depends(require_login)
):
    with SessionLocal() as db:
        db_file = db.query(SysFile).filter(SysFile.id == file_id).first()
        if not db_file:
            raise APIException("文件不存在", code=404, status_code=404)
            
        # 物理文件是否还被其他记录引用（防止误删已合并的其他条目）
        other_ref = db.query(SysFile).filter(
            SysFile.filepath == db_file.filepath,
            SysFile.id != file_id
        ).first()
        
        try:
            db.delete(db_file)
            db.commit()
            
            # 如果没有其他记录引用该物理文件，则删除
            if not other_ref:
                if db_file.filepath.startswith("public/uploads/"):
                    # 删除本地物理文件
                    disk_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        db_file.filepath
                    )
                    if os.path.exists(disk_path):
                        os.remove(disk_path)
                elif qiniu_config.is_configured:
                    # 删除七牛云文件
                    delete_from_qiniu(db_file.filepath)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete file: {e}")
            raise APIException("删除文件失败", code=500, status_code=500)
            
        return {"success": True}
