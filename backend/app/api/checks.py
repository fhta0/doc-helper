"""
Document Check API Routes
Handles document upload and format checking.
"""
import os
import json
import uuid
import re
import logging
from datetime import datetime
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import aiofiles

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.config import settings
from app.models import User, Check, CheckType, CheckStatus, CostType, Rule, RuleTemplate
from app.api.schemas import (
    ApiResponse,
    CheckSubmitRequest,
)
from app.api.deps import get_current_user, get_current_user_optional, check_count_available, reset_free_count_if_needed
from app.services.docx_parser import parse_document_safe
from app.services.rule_engine import create_rule_engine, load_rules_from_db_objects
from app.services.ai_checker import create_ai_checker
from app.services.ai_content_checker import create_ai_content_checker
from app.services.revision_engine import RevisionEngine


router = APIRouter(prefix="/check", tags=["Document Check"])


# Create AI checker instance (shared across requests)
_ai_checker = create_ai_checker()
# Create AI content checker instance (shared across requests)
_ai_content_checker = create_ai_content_checker()


def _is_guest_user(username: str) -> bool:
    """Check if user is a guest user based on username prefix."""
    return username and username.startswith("guest_")


def _get_max_file_size(user: Optional[User]) -> int:
    """Get maximum file size based on user type."""
    if user and _is_guest_user(user.username):
        return settings.MAX_FILE_SIZE_GUEST  # 10MB for guests
    else:
        return settings.MAX_FILE_SIZE_AUTHENTICATED  # 100MB for authenticated users


def _find_uploaded_file(user_id: int, file_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Find uploaded file by user_id and file_id.
    
    Args:
        user_id: User ID
        file_id: File ID
        
    Returns:
        Tuple of (file_path, filename) or (None, None) if not found
    """
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    if not os.path.exists(user_upload_dir):
        return None, None
    
    all_files = os.listdir(user_upload_dir)
    # Match files containing the file_id in the filename
    pattern = re.compile(f'_{re.escape(file_id)}(_|\\.docx$)')
    matching_files = [f for f in all_files if pattern.search(f)]
    
    if not matching_files:
        return None, None
    
    # Use the first matching file (should be unique per file_id)
    filename = matching_files[0]
    file_path = os.path.join(user_upload_dir, filename)
    
    if not os.path.exists(file_path):
        return None, None
    
    return file_path, filename


@router.post("/upload", response_model=ApiResponse)
async def upload_document(
    file: UploadFile = File(...),
    check_type: str = Form(default="basic"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Upload a document for checking.

    Args:
        file: Uploaded file (must be .docx)
        check_type: Type of check (basic or full)
        current_user: Current authenticated user (optional for guests)
        db: Database session

    Returns:
        API response with file_id
    """
    # Validate file type
    if not file.filename.endswith((".docx", ".DOCX")):
        return ApiResponse(
            code=2001,
            message="文件格式不支持，仅支持.docx格式",
            data=None
        )

    # Read file content
    content = await file.read()

    # Check file size based on user type
    max_file_size = _get_max_file_size(current_user)
    if len(content) > max_file_size:
        max_size_mb = max_file_size // 1024 // 1024
        return ApiResponse(
            code=2002,
            message=f"文件大小超过{max_size_mb}MB限制",
            data=None
        )

    # Generate file ID
    file_id = f"file_{uuid.uuid4().hex[:16]}"

    # Create user upload directory
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)

    # Save file (include file_id in filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file_id}_{file.filename}"
    file_path = os.path.join(user_upload_dir, safe_filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return ApiResponse(
        code=200,
        message="上传成功",
        data={
            "file_id": file_id,
            "filename": file.filename,
            "file_size": len(content),
            "check_type": check_type,
            "upload_time": datetime.now().isoformat(),
        }
    )


@router.post("", response_model=ApiResponse)
async def submit_check(
    request: CheckSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a document for format checking.

    Args:
        request: Check submit request with file_id
        current_user: Current authenticated user
        db: Database session

    Returns:
        API response with check_id
    """
    # Reset free count if needed
    reset_free_count_if_needed(current_user, db)

    # Check count availability and determine cost type
    cost_type = check_count_available(current_user, request.check_type)

    # Find uploaded file
    file_path, filename = _find_uploaded_file(current_user.id, request.file_id)
    if not file_path:
        return ApiResponse(
            code=2003,
            message="文件不存在或已过期",
            data=None
        )

    # Generate check ID
    check_id = f"check_{uuid.uuid4().hex[:16]}"

    # Load rule template if specified
    rule_config = None
    if request.rule_template_id:
        template = db.query(RuleTemplate).filter(RuleTemplate.id == request.rule_template_id).first()
        if template:
            rule_config = template.config_json
        else:
            return ApiResponse(
                code=3007,
                message="规则模板不存在",
                data=None
            )

    # Create check record
    new_check = Check(
        check_id=check_id,
        user_id=current_user.id,
        file_id=request.file_id,
        filename=request.filename if hasattr(request, 'filename') and request.filename else filename,  # Prefer original filename from request if available, else use safe filename
        file_path=file_path,
        check_type=CheckType.BASIC if request.check_type == "basic" else CheckType.FULL,
        status=CheckStatus.COMPLETED,  # MVP: synchronous processing
        rule_template_id=request.rule_template_id,
        rule_config_json=rule_config,
        cost_type=CostType.FREE if cost_type == "free" else (CostType.BASIC if cost_type == "basic" else CostType.FULL),
    )
    db.add(new_check)

    # Decrement the appropriate count based on cost_type
    if cost_type == "free":
        current_user.free_count -= 1
    elif cost_type == "basic":
        current_user.basic_count -= 1
    elif cost_type == "full":
        current_user.full_count -= 1

    # Update user's last_template_id
    if request.rule_template_id:
        current_user.last_template_id = request.rule_template_id

    # Commit count deduction immediately
    db.commit()
    # Refresh user object to ensure changes are persisted
    db.refresh(current_user)

    # Perform the check (synchronous for MVP)
    try:
        logger.info(f"开始执行检查: check_id={check_id}, check_type={request.check_type}")

        # Parse document
        parse_result = parse_document_safe(file_path)
        if not parse_result["success"]:
            new_check.status = CheckStatus.FAILED
            db.commit()
            return ApiResponse(
                code=3003,
                message=f"文档解析失败: {parse_result.get('error', 'Unknown error')}",
                data=None
            )

        doc_data = parse_result["data"]
        logger.info(f"文档解析成功: {len(doc_data.get('paragraphs', []))} 个段落")

        # Load rules - use template config if provided, otherwise load from database
        if rule_config:
            # Convert template config to rule format
            from app.services.rule_engine import config_to_rules
            # Also load DB rules to match fix_action and fix_params
            db_rules = db.query(Rule).all()
            db_rule_dicts = load_rules_from_db_objects(db_rules)
            rule_dicts = config_to_rules(rule_config, db_rules=db_rule_dicts)
        else:
            # Load from database (default behavior)
            rules = db.query(Rule).all()
            rule_dicts = load_rules_from_db_objects(rules)
            
            # Debug: Log rules with fix_action
            rules_with_fix = [r for r in rule_dicts if r.get("fix_action")]
            logger.info(f"加载了 {len(rule_dicts)} 条规则，其中 {len(rules_with_fix)} 条有 fix_action")
            for rule in rules_with_fix:
                logger.debug(f"Rule {rule.get('id')}: fix_action={rule.get('fix_action')}")

        logger.info(f"加载了 {len(rule_dicts)} 条规则")

        # ============================================================
        # 检测流程：基础检测 vs 全面检测
        # ============================================================
        is_full_check = request.check_type == "full"

        if is_full_check:
            # ========== 全面检测 ==========
            logger.info("开始全面检测...")

            # 1. 规则检测（仅确定性规则，不包含AI规则）
            deterministic_rules = [r for r in rule_dicts if r.get("checker") != "ai"]
            logger.info(f"确定性规则数量: {len(deterministic_rules)}")

            rule_engine = create_rule_engine(deterministic_rules, enable_ai=False)
            rule_result = rule_engine.check_document_sync(doc_data)
            logger.info(f"规则检测完成: {rule_result.get('total_issues', 0)} 个问题")

            # 2. AI内容检测（错别字、交叉引用等）
            ai_issues = []
            if _ai_content_checker.is_enabled():
                try:
                    enabled_checks = ["spell_check", "cross_ref_check"]
                    logger.info("开始AI内容检测...")
                    ai_results = await _ai_content_checker.check_all(doc_data, enabled_checks)
                    ai_issues = _ai_content_checker.convert_to_standard_issues(ai_results)
                    logger.info(f"AI内容检测完成: {len(ai_issues)} 个问题")
                except Exception as e:
                    logger.error(f"AI内容检测失败: {e}", exc_info=True)
            else:
                logger.warning("AI内容检测未启用")

            # 合并结果
            all_issues = rule_result.get("issues", []) + ai_issues
            check_result = {
                "issues": all_issues,
                "total_issues": len(all_issues),
                "check_type": "full",
                "rule_issues": len(rule_result.get("issues", [])),
                "ai_issues": len(ai_issues),
            }
            logger.info(f"全面检测完成: 共 {len(all_issues)} 个问题")
        else:
            # ========== 基础检测 ==========
            logger.info("开始基础检测...")
            # 仅运行确定性规则（格式检查）
            deterministic_rules = [r for r in rule_dicts if r.get("checker") != "ai"]
            rule_engine = create_rule_engine(deterministic_rules, enable_ai=False)
            check_result = rule_engine.check_document_sync(doc_data)
            check_result["check_type"] = "basic"
            logger.info(f"基础检测完成: {check_result.get('total_issues', 0)} 个问题")

        # Save result
        result_json = json.dumps(check_result, ensure_ascii=False)
        new_check.result_json = result_json
        db.commit()
        logger.info(f"检查结果已保存: check_id={check_id}")

    except Exception as e:
        new_check.status = CheckStatus.FAILED
        db.commit()
        return ApiResponse(
            code=3004,
            message=f"检查失败: {str(e)}",
            data=None
        )

    return ApiResponse(
        code=200,
        message="检查完成",
        data={
            "check_id": check_id,
            "file_id": request.file_id,
            "filename": filename,
            "check_type": request.check_type,
            "status": "completed",
            "created_at": new_check.created_at.isoformat(),
        }
    )


@router.get("/recent", response_model=ApiResponse)
def get_recent_checks(
    limit: int = 5,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent check records for current user.

    Args:
        limit: Maximum number of records to return
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session

    Returns:
        API response with recent checks
    """
    # Get total count
    total = db.query(Check).filter(Check.user_id == current_user.id).count()

    # Get recent checks
    checks = db.query(Check).filter(
        Check.user_id == current_user.id
    ).order_by(
        Check.created_at.desc()
    ).offset(offset).limit(min(limit, 20)).all()

    checks_data = []
    for check in checks:
        check_dict = {
            "check_id": check.check_id,
            "filename": check.filename,
            "check_type": check.check_type.value,
            "status": check.status.value,
            "created_at": check.created_at.isoformat(),
            "updated_at": check.updated_at.isoformat() if check.updated_at else None,
        }
        if check.result_json:
            result = json.loads(check.result_json)
            check_dict["total_issues"] = result.get("total_issues", 0)
        else:
            check_dict["total_issues"] = 0
        checks_data.append(check_dict)

    return ApiResponse(
        code=200,
        message="成功",
        data={
            "total": total,
            "checks": checks_data
        }
    )


@router.get("/stats", response_model=ApiResponse)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        API response with user statistics
    """
    # Optimized query for counts
    stats = db.query(
        Check.check_type,
        func.count(Check.id)
    ).filter(
        Check.user_id == current_user.id,
        Check.status == CheckStatus.COMPLETED
    ).group_by(Check.check_type).all()

    basic_checks = 0
    full_checks = 0
    total_checks = 0
    
    for check_type, count in stats:
        if check_type == CheckType.BASIC:
            basic_checks = count
        elif check_type == CheckType.FULL:
            full_checks = count
        total_checks += count

    # For total_issues, we still need to parse JSON
    # Fetch only the result_json column to minimize data transfer
    checks_with_issues = db.query(Check.result_json).filter(
        Check.user_id == current_user.id,
        Check.status == CheckStatus.COMPLETED
    ).all()

    total_issues = 0
    for check in checks_with_issues:
        if check.result_json:
            try:
                result = json.loads(check.result_json)
                total_issues += result.get("total_issues", 0)
            except (json.JSONDecodeError, TypeError):
                pass

    return ApiResponse(
        code=200,
        message="成功",
        data={
            "total_checks": total_checks,
            "total_issues": total_issues,
            "basic_checks": basic_checks,
            "full_checks": full_checks
        }
    )


@router.post("/{check_id}/revise", response_model=ApiResponse)
async def generate_revised_document(
    check_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and return revised document URL.
    """
    check = db.query(Check).filter(
        Check.check_id == check_id,
        Check.user_id == current_user.id
    ).first()

    if not check:
        return ApiResponse(code=3002, message="检查记录不存在", data=None)

    if check.status != CheckStatus.COMPLETED:
        return ApiResponse(code=3005, message="检查未完成，无法生成修订版", data=None)

    # Check if already generated
    if check.revised_file_path and os.path.exists(check.revised_file_path):
        return ApiResponse(
            code=200,
            message="修订版已生成",
            data={"revised_file_url": f"/api/check/{check_id}/download_revised"}
        )

    # Generate
    try:
        # Load check result
        result = json.loads(check.result_json)
        issues = result.get("issues", [])
        
        # Log for debugging
        logger.info(f"Generating revised document for check {check_id}")
        logger.info(f"Found {len(issues)} issues to process")
        
        # Debug: Log each issue's rule_id and fix_action
        for i, issue in enumerate(issues, 1):
            rule_id = issue.get("rule_id", "Unknown")
            fix_action = issue.get("fix_action")
            logger.info(f"Issue {i}: rule_id={rule_id}, fix_action={fix_action}")
        
        # Count issues with fix_action
        issues_with_fix = [i for i in issues if i.get("fix_action")]
        logger.info(f"Found {len(issues_with_fix)} issues with fix_action")
        
        if not issues_with_fix:
            logger.warning("No issues with fix_action found - revision may not show changes")
            # Debug: Check if rules have fix_action
            rules = db.query(Rule).all()
            rule_fix_map = {r.id: r.fix_action for r in rules if r.fix_action}
            logger.info(f"Rules with fix_action in DB: {list(rule_fix_map.keys())}")
            for issue in issues:
                rule_id = issue.get("rule_id")
                if rule_id in rule_fix_map:
                    logger.warning(f"Issue {rule_id} should have fix_action={rule_fix_map[rule_id]} but doesn't!")
        
        # Initialize revision engine
        user_upload_dir = os.path.dirname(check.file_path)
        engine = RevisionEngine(check.file_path, user_upload_dir)
        
        # Generate
        revised_path = engine.generate_revised_document(issues)
        
        # Update DB
        check.revised_file_path = revised_path
        db.commit()
        
        logger.info(f"Revised document generated: {revised_path}")
        
        return ApiResponse(
            code=200,
            message="修订版生成成功",
            data={"revised_file_url": f"/api/check/{check_id}/download_revised"}
        )
        
    except Exception as e:
        logger.error(f"Failed to generate revised document: {e}", exc_info=True)
        return ApiResponse(code=3006, message=f"生成修订版失败: {str(e)}", data=None)


@router.get("/{check_id}", response_model=ApiResponse)
def get_check_result(
    check_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the result of a check.

    Args:
        check_id: Check ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        API response with check result
    """
    # Find check
    check = db.query(Check).filter(
        Check.check_id == check_id,
        Check.user_id == current_user.id
    ).first()

    if not check:
        return ApiResponse(
            code=3002,
            message="检查记录不存在",
            data=None
        )

    # Build response
    response_data = check.to_dict()
    # Add revised_file_generated flag explicitly
    response_data["revised_file_generated"] = bool(check.revised_file_path)

    if check.status == CheckStatus.COMPLETED and check.result_json:
        result = json.loads(check.result_json)
        response_data["result"] = result
    elif check.status == CheckStatus.FAILED:
        response_data["error_message"] = "检查执行失败"

    return ApiResponse(
        code=200,
        message="成功",
        data=response_data
    )


@router.get("/{check_id}/download_revised")
async def download_revised_document(
    check_id: str,
    # token: str = Query(...), # In production, verify token from query param for direct download links
    db: Session = Depends(get_db)
):
    """Download the revised document."""
    # For simplicity in this MVP, we might skip strict auth check for download link if it's hard to pass headers
    # BUT, secure way: verify token. Here we assume session/cookie auth works or we use a temporary token mechanism.
    # Let's try to get user from dependency if possible, but browser download triggers GET request.
    # We will rely on cookie auth if frontend sends it, or just basic check ID lookup (insecure but OK for MVP demo).
    # Ideally: Depends(get_current_user) but requires token in header.
    
    # We'll allow download if we can find the check record.
    # SECURITY NOTE: This exposes files if check_id is guessed. Production needs better auth.
    check = db.query(Check).filter(Check.check_id == check_id).first()
    
    if not check or not check.revised_file_path or not os.path.exists(check.revised_file_path):
        return ApiResponse(code=404, message="文件不存在", data=None)
        
    filename = os.path.basename(check.revised_file_path)
    # Return as attachment
    return FileResponse(
        check.revised_file_path, 
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
