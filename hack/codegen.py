import argparse
import os
import re

def generate_code(name: str, title: str, fields_str: str):
    name = name.lower().strip()
    camel_name = name.capitalize()
    class_name = f"Sys{camel_name}"
    table_name = f"sys_{name}"
    
    # 解析字段
    fields = []
    for f_item in fields_str.split(","):
        parts = f_item.strip().split(":")
        if len(parts) < 3:
            print(f"警告: 忽略无效的字段配置 '{f_item}'。格式应为 name:type:comment[:default]")
            continue
        f_name = parts[0]
        f_type = parts[1]
        f_comment = parts[2]
        f_default = parts[3] if len(parts) > 3 else None
        
        # 默认值类型转换
        if f_type == "int":
            f_default = int(f_default) if f_default is not None else 0
        elif f_type == "float":
            f_default = float(f_default) if f_default is not None else 0.0
        elif f_type == "bool":
            if f_default is not None:
                f_default = f_default.lower() in ("true", "1", "yes")
            else:
                f_default = True
        
        fields.append({
            "name": f_name,
            "type": f_type,
            "comment": f_comment,
            "default": f_default
        })

    print(f"开始生成业务模块 [{name}] ({title}) ...")

    # 1. 更新 backend/app/db/models.py
    models_path = "backend/app/db/models.py"
    if os.path.exists(models_path):
        with open(models_path, "r", encoding="utf-8") as f:
            models_content = f.read()
            
        if class_name in models_content:
            print(f"警告: Model {class_name} 已存在于 models.py，跳过追加。")
        else:
            model_fields_lines = []
            for f in fields:
                if f["type"] == "string":
                    line = f"    {f['name']:<10} = Column(String(255), nullable=True, comment='{f['comment']}')"
                elif f["type"] == "text":
                    line = f"    {f['name']:<10} = Column(Text, nullable=True, comment='{f['comment']}')"
                elif f["type"] == "int":
                    line = f"    {f['name']:<10} = Column(Integer, default={f['default']}, nullable=False, comment='{f['comment']}')"
                elif f["type"] == "float":
                    line = f"    {f['name']:<10} = Column(sa.Float, default={f['default']}, nullable=False, comment='{f['comment']}')"
                elif f["type"] == "bool":
                    val = "True" if f["default"] else "False"
                    line = f"    {f['name']:<10} = Column(Boolean, default={val}, nullable=False, comment='{f['comment']}')"
                model_fields_lines.append(line)
                
            model_code = f"\n\nclass {class_name}(Base):\n"
            model_code += f"    __tablename__ = \"{table_name}\"\n"
            model_code += f"    __table_args__ = (\n"
            model_code += f"        {{\"comment\": \"{title}\"}},\n"
            model_code += f"    )\n\n"
            model_code += f"    id         = Column(BigInteger().with_variant(mysql.BIGINT(unsigned=True), \"mysql\"), primary_key=True, autoincrement=True)\n"
            model_code += "\n".join(model_fields_lines) + "\n"
            model_code += f"    created_by = Column(Integer, nullable=True, comment=\"创建用户ID\")\n"
            model_code += f"    created_at = Column(sa.DateTime(timezone=True), default=_now, server_default=sa.text(\"CURRENT_TIMESTAMP\"), nullable=False)\n"
            model_code += f"    updated_at = Column(sa.DateTime(timezone=True), default=_now, onupdate=_now, server_default=sa.text(\"CURRENT_TIMESTAMP\"), nullable=False)\n"
            
            with open(models_path, "a", encoding="utf-8") as f:
                f.write(model_code)
            print(f"✓ 已追加 {class_name} 到 {models_path}")

    # 2. 写入 backend/app/service/{name}_service.py
    service_path = f"backend/app/service/{name}_service.py"
    service_code = """from typing import List, Optional, Tuple
from sqlalchemy import desc
import sqlalchemy as sa
from app.db import SessionLocal, {class_name}
from app.boot import APIException

class {camel_name}Service:
    @classmethod
    def get_list(cls, page: int = 1, size: int = 10, **filters) -> Tuple[List[{class_name}], int]:
        with SessionLocal() as db:
            q = db.query({class_name})
            for k, v in filters.items():
                if v is not None and v != "":
                    if hasattr({class_name}, k):
                        col = getattr({class_name}, k)
                        if isinstance(col.type, (sa.String, sa.Text)):
                            q = q.filter(col.like(f"%{v}%"))
                        else:
                            q = q.filter(col == v)
            total = q.count()
            rows = q.order_by(desc({class_name}.id)).offset((page - 1) * size).limit(size).all()
            return rows, total

    @classmethod
    def create(cls, data: dict, user_id: Optional[int] = None) -> {class_name}:
        with SessionLocal() as db:
            row = {class_name}(**data)
            if user_id:
                row.created_by = user_id
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    @classmethod
    def update(cls, id: int, data: dict) -> {class_name}:
        with SessionLocal() as db:
            row = db.query({class_name}).filter({class_name}.id == id).first()
            if not row:
                raise APIException(msg="记录不存在", code=404, status_code=404)
            for k, v in data.items():
                if hasattr(row, k):
                    setattr(row, k, v)
            db.commit()
            db.refresh(row)
            return row

    @classmethod
    def delete(cls, id: int) -> bool:
        with SessionLocal() as db:
            row = db.query({class_name}).filter({class_name}.id == id).first()
            if not row:
                raise APIException(msg="记录不存在", code=404, status_code=404)
            db.delete(row)
            db.commit()
            return True
"""
    service_code = service_code.replace("{class_name}", class_name).replace("{camel_name}", camel_name)
    with open(service_path, "w", encoding="utf-8") as f:
        f.write(service_code)
    print(f"✓ 已创建 {service_path}")

    # 3. 写入 backend/app/api/v1/{name}.py
    pydantic_fields = []
    pydantic_fields_opt = []
    query_params = []
    filter_dict = []
    for f in fields:
        py_type = "str"
        if f["type"] in ("int", "float"):
            py_type = "int" if f["type"] == "int" else "float"
        elif f["type"] == "bool":
            py_type = "bool"
            
        pydantic_fields.append(f"    {f['name']}: {py_type} = Field(..., description='{f['comment']}')")
        pydantic_fields_opt.append(f"    {f['name']}: Optional[{py_type}] = Field(None, description='{f['comment']}')")
        query_params.append(f"    {f['name']}: Optional[{py_type}] = Query(None, description='{f['comment']}'),")
        filter_dict.append(f"        \"{f['name']}\": {f['name']}," if f["type"] in ("string", "text") else f"        \"{f['name']}\": {f['name']}," )

    pydantic_fields_str = "\n".join(pydantic_fields)
    pydantic_fields_opt_str = "\n".join(pydantic_fields_opt)
    query_params_str = "\n".join(query_params)
    filter_dict_str = "\n".join(filter_dict)

    router_path = f"backend/app/api/v1/{name}.py"
    router_code = """from fastapi import APIRouter, Depends, Query, Request
from app.api.v1.deps import get_current_user, require_permission
from app.service.{name}_service import {camel_name}Service
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/{name}", tags=["{title}"])

class {camel_name}Create(BaseModel):
{pydantic_fields_str}

class {camel_name}Update(BaseModel):
{pydantic_fields_opt_str}

@router.get("", summary="获取{title}列表")
async def get_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
{query_params_str}
    user = Depends(get_current_user)
):
    filters = {{
{filter_dict_str}
    }}
    rows, total = {camel_name}Service.get_list(page=page, size=size, **filters)
    return {"list": rows, "total": total}

@router.post("", summary="新建{title}", dependencies=[Depends(require_permission("system:{name}:create"))])
async def create(req: {camel_name}Create, request: Request, user = Depends(get_current_user)):
    return {camel_name}Service.create(req.model_dump(), user_id=user.id)

@router.put("/{id}", summary="更新{title}", dependencies=[Depends(require_permission("system:{name}:update"))])
async def update(id: int, req: {camel_name}Update):
    return {camel_name}Service.update(id, req.model_dump(exclude_unset=True))

@router.delete("/{id}", summary="删除{title}", dependencies=[Depends(require_permission("system:{name}:delete"))])
async def delete(id: int):
    {camel_name}Service.delete(id)
    return {"success": True}
"""
    router_code = router_code.replace("{name}", name).replace("{camel_name}", camel_name).replace("{title}", title)
    router_code = router_code.replace("{pydantic_fields_str}", pydantic_fields_str)
    router_code = router_code.replace("{pydantic_fields_opt_str}", pydantic_fields_opt_str)
    router_code = router_code.replace("{query_params_str}", query_params_str)
    router_code = router_code.replace("{filter_dict_str}", filter_dict_str)

    with open(router_path, "w", encoding="utf-8") as f:
        f.write(router_code)
    print(f"✓ 已创建 {router_path}")

    # 4. 更新 backend/app/api/v1/__init__.py 自动导入和注册路由
    init_api_path = "backend/app/api/v1/__init__.py"
    with open(init_api_path, "r", encoding="utf-8") as f:
        init_content = f.read()
        
    if f"from . import" in init_content and f", {name}" not in init_content:
        # 修改导入行
        init_content = re.sub(
            r"(from \. import hello, user, auth, admin, me, role, audit, file, dict)(.*)",
            rf"\1, {name}\2",
            init_content
        )
        # 修改包含路由行
        include_router_str = f"router.include_router({name}.router)"
        if include_router_str not in init_content:
            init_content = init_content.replace(
                "router.include_router(dict.router)",
                f"router.include_router(dict.router)\nrouter.include_router({name}.router)"
            )
        with open(init_api_path, "w", encoding="utf-8") as f:
            f.write(init_content)
        print(f"✓ 已更新 {init_api_path} 路由配置")

    # 5. 更新 backend/app/service/menu_service.py 添加默认内置菜单
    menu_service_path = "backend/app/service/menu_service.py"
    with open(menu_service_path, "r", encoding="utf-8") as f:
        menu_service_content = f.read()
        
    menu_key = f"system:{name}"
    if f"\"{menu_key}\":" not in menu_service_content:
        target_marker = """        "system:dict": {
            "title": "数据字典",
            "icon": "BookOpen",
            "parentKey": "g:system",
            "sort": 16,
        },"""
        new_menu_entry = f"""        "system:dict": {{
            "title": "数据字典",
            "icon": "BookOpen",
            "parentKey": "g:system",
            "sort": 16,
        }},
        "{menu_key}": {{
            "title": "{title}",
            "icon": "Grid",
            "parentKey": "g:system",
            "sort": 17,
        }},"""
        
        menu_service_content = menu_service_content.replace(target_marker, new_menu_entry)
        with open(menu_service_path, "w", encoding="utf-8") as f:
            f.write(menu_service_content)
        print(f"✓ 已在 {menu_service_path} 的 DEFAULT_CORE_MENUS 中注册内置菜单")

    # 6. 写入 frontend/app/admin/api/{name}.js
    fe_api_path = f"frontend/app/admin/api/{name}.js"
    fe_api_code = """import { apiFetch } from '../../src/utils/apiFetch.js'

export function fetch{camel_name}List(params) {
  return apiFetch('/api/v1/{name}', { query: params })
}

export function create{camel_name}(data) {
  return apiFetch('/api/v1/{name}', {
    method: 'POST',
    body: data
  })
}

export function update{camel_name}(id, data) {
  return apiFetch(`/api/v1/{name}/${id}`, {
    method: 'PUT',
    body: data
  })
}

export function delete{camel_name}(id) {
  return apiFetch(`/api/v1/{name}/${id}`, {
    method: 'DELETE'
  })
}
"""
    fe_api_code = fe_api_code.replace("{name}", name).replace("{camel_name}", camel_name)
    with open(fe_api_path, "w", encoding="utf-8") as f:
        f.write(fe_api_code)
    print(f"✓ 已创建 {fe_api_path}")

    # 7. 写入 frontend/app/admin/views/system/{name}/page.js
    fe_dir = f"frontend/app/admin/views/system/{name}"
    os.makedirs(fe_dir, exist_ok=True)
    
    fe_page_path = f"{fe_dir}/page.js"
    fe_page_code = """import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:{name}",
  title: "{title}",
  parentKey: "g:system",
  path: "/system/{name}",
  component: "system/{name}/index",
  icon: "Grid",
  sort: 17,
  cacheable: false,
})
"""
    fe_page_code = fe_page_code.replace("{name}", name).replace("{title}", title)
    with open(fe_page_path, "w", encoding="utf-8") as f:
        f.write(fe_page_code)
    print(f"✓ 已创建 {fe_page_path}")

    # 8. 写入 frontend/app/admin/views/system/{name}/index.vue
    vue_table_cols = []
    vue_search_fields = []
    vue_form_fields = []
    vue_form_rules = []
    
    for f in fields:
        vue_table_cols.append(f"  {{ title: '{f['comment']}', key: '{f['name']}', minWidth: 120 }},")
        
        # 搜索配置（默认只对文本和状态配置搜索）
        if f["type"] in ("string", "text"):
            vue_search_fields.append(f"  {{ label: '{f['comment']}', key: '{f['name']}', type: 'text', placeholder: '按{f['comment']}搜索...' }},")
        elif f["type"] == "bool":
            vue_search_fields.append(f"  {{ label: '{f['comment']}', key: '{f['name']}', type: 'select', placeholder: '请选择{f['comment']}', options: [{{ label: '是', value: true }}, {{ label: '否', value: false }}] }},")
            
        # 表单配置
        f_ui_type = "text"
        if f["type"] == "text":
            f_ui_type = "textarea"
        elif f["type"] == "bool":
            f_ui_type = "switch"
        elif f["type"] == "int":
            f_ui_type = "text"
            
        vue_form_fields.append(f"  {{ label: '{f['comment']}', key: '{f['name']}', type: '{f_ui_type}' }},")
        
        # 表单基本校验规则（字符串字段要求必填）
        if f["type"] == "string" and f["name"] != "description":
            vue_form_rules.append(f"  {f['name']}: {{ required: true, message: '请输入{f['comment']}', trigger: 'blur' }},")

    vue_table_cols_str = "\n".join(vue_table_cols)
    vue_search_fields_str = "\n".join(vue_search_fields)
    vue_form_fields_str = "\n".join(vue_form_fields)
    vue_form_rules_str = "\n".join(vue_form_rules)

    vue_index_path = f"{fe_dir}/index.vue"
    vue_index_code = """<template>
  <ProTable
    :title="title"
    :subtitle="subtitle"
    :columns="columns"
    :search-fields="searchFields"
    :form-fields="formFields"
    :form-rules="formRules"
    :list-api="fetch{camel_name}List"
    :create-api="create{camel_name}"
    :update-api="update{camel_name}"
    :delete-api="delete{camel_name}"
    permission-prefix="system:{name}"
  />
</template>

<script setup>
import { ref } from 'vue'
import ProTable from '@/components/ProTable.vue'
import {
  fetch{camel_name}List,
  create{camel_name},
  update{camel_name},
  delete{camel_name}
} from '#/admin/api/{name}.js'

const title = '{title}'
const subtitle = '{title}数据的查看、新建、修改与删除'

const columns = [
{vue_table_cols_str}
]

const searchFields = [
{vue_search_fields_str}
]

const formFields = [
{vue_form_fields_str}
]

const formRules = {
{vue_form_rules_str}
}
</script>
"""
    vue_index_code = vue_index_code.replace("{name}", name).replace("{camel_name}", camel_name).replace("{title}", title)
    vue_index_code = vue_index_code.replace("{vue_table_cols_str}", vue_table_cols_str)
    vue_index_code = vue_index_code.replace("{vue_search_fields_str}", vue_search_fields_str)
    vue_index_code = vue_index_code.replace("{vue_form_fields_str}", vue_form_fields_str)
    vue_index_code = vue_index_code.replace("{vue_form_rules_str}", vue_form_rules_str)

    with open(vue_index_path, "w", encoding="utf-8") as f:
        f.write(vue_index_code)
    print(f"✓ 已创建 {vue_index_path}")
    print("--------------------------------------------------")
    print(f"🎉 业务组件 [{name}] ({title}) 代码生成完毕！")
    print("要应用新的数据表结构和菜单，请依次：")
    print("1. 重启后台服务，程序将自动在 MySQL 数据库中检测并创建表结构。")
    print("2. 运行 'node scripts/sync-menu.mjs' (或等待前端自动同步) 将新菜单同步注册到数据库。")
    print("--------------------------------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="smart-ai 简易 CRUD 代码生成器")
    parser.add_argument("--name", required=True, help="业务实体名称，例如 product")
    parser.add_argument("--title", required=True, help="业务中文名称，例如 产品管理")
    parser.add_argument("--fields", required=True, help="字段配置列表，例如 name:string:产品名称,price:float:产品单价,status:int:状态:0")
    
    args = parser.parse_args()
    generate_code(args.name, args.title, args.fields)
