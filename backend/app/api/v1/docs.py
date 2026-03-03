"""
文档 API 路由

提供学习文档的查询功能
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query

from app.core.logger import get_logger, info, warning
from app.models.schemas import DocItem, DocListResponse, DocDetailResponse
from app.services.data_service import data_service

router = APIRouter(prefix="/docs", tags=["学习文档"])
logger = get_logger(__name__)


@router.get(
    "",
    response_model=DocListResponse,
    summary="获取文档列表",
    description="获取所有学习文档列表"
)
async def list_docs(
    version_id: Optional[str] = Query(None, description="按版本ID筛选"),
    category: Optional[str] = Query(None, description="按分类筛选")
):
    """
    获取文档列表
    
    - **version_id**: 可选，按版本 ID 筛选
    - **category**: 可选，按分类筛选
    """
    info("Listing docs", extra={"version_id": version_id, "category": category})
    
    docs = data_service.get_docs(version_id)
    
    if category:
        docs = [d for d in docs if d.category == category]
    
    # 按 order 排序
    docs.sort(key=lambda x: x.order)
    
    return DocListResponse(
        docs=docs,
        total=len(docs),
        message=f"Found {len(docs)} documents"
    )


@router.get(
    "/{doc_id}",
    response_model=DocDetailResponse,
    summary="获取文档详情",
    description="根据文档 ID 获取详细信息"
)
async def get_doc(
    doc_id: str = Path(..., description="文档 ID")
):
    """获取文档详情"""
    info("Getting doc", extra={"doc_id": doc_id})
    
    doc = data_service.get_doc_by_id(doc_id)
    
    if not doc:
        warning(f"Document not found: {doc_id}")
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    return DocDetailResponse(
        data=doc,
        message=f"Document {doc_id} retrieved successfully"
    )


@router.get(
    "/by-version/{version_id}",
    response_model=DocListResponse,
    summary="按版本获取文档",
    description="根据版本 ID 获取相关文档"
)
async def get_docs_by_version(
    version_id: str = Path(..., description="版本 ID", pattern=r"^s\d{2}$")
):
    """根据版本 ID 获取文档"""
    info("Getting docs by version", extra={"version_id": version_id})
    
    docs = data_service.get_docs(version_id)
    
    return DocListResponse(
        docs=docs,
        total=len(docs),
        message=f"Found {len(docs)} documents for {version_id}"
    )
