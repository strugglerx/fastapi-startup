import os
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query
from app.api.v1.deps import get_current_user, require_login
from app.db import SessionLocal, SysFile
from app.boot import APIException, logger

router = APIRouter(prefix="/files", tags=["文件服务"])

# 上传目录绝对路径
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "public", "uploads")

@router.post("/upload", summary="上传单个文件")
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(require_login)
):
    # 确保上传目录存在
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
                "url": f"/uploads/{os.path.basename(existing.filepath)}",
                "file_size": existing.file_size,
                "mime_type": existing.mime_type,
                "hash_md5": existing.hash_md5,
                "duplicate": True
            }
            
    # 如果不存在，保存新文件
    # 为防止文件名冲突，使用 md5 命名，但保留原后缀
    ext = os.path.splitext(file.filename)[1]
    save_filename = f"{md5_hash}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_filename)
    
    try:
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise APIException("保存文件失败", code=500, status_code=500)
        
    # 保存数据库记录
    # filepath 存相对路径，方便后续支持 CDN 或 OSS
    rel_filepath = f"public/uploads/{save_filename}"
    
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
            "url": f"/uploads/{save_filename}",
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
                "url": f"/uploads/{os.path.basename(r.filepath)}",
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
            
            # 如果没有其他记录引用该物理文件，则删除磁盘上的物理文件
            if not other_ref:
                disk_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    db_file.filepath
                )
                if os.path.exists(disk_path):
                    os.remove(disk_path)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete file: {e}")
            raise APIException("删除文件失败", code=500, status_code=500)
            
        return {"success": True}
