from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Company, Site, Department, Area, Workstation, Equipment, EquipmentAssignment, Employee, EmployeeWorkAssignment, AuditEvent, CanvasObject
from app.core.security import csrf_protect, require_permission, audit as audit_change

router = APIRouter(prefix="/api/v1", tags=["enterprise"], dependencies=[Depends(csrf_protect)])
KINDS = {"site": Site, "department": Department, "area": Area, "workstation": Workstation}
PARENTS = {"site": None, "department": ("site", "site_id"), "area": ("department", "department_id"), "workstation": ("area", "area_id")}

class EntityInput(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None
    parent_id: UUID | None = None
    parent_kind: str | None = None
class EntityPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = None
class CompanyInput(EntityInput): pass
class CompanyPatch(EntityPatch):
    allow_multiple_positions: bool | None = None
    allow_multiple_qualifications: bool | None = None
class EquipmentInput(EntityInput): pass
class MoveInput(BaseModel):
    parent_id: UUID | None = None
    parent_kind: str | None = None
class AssignmentInput(BaseModel):
    site_id: UUID | None = None
    department_id: UUID | None = None
    area_id: UUID | None = None
    workstation_id: UUID | None = None
    valid_from: datetime | None = None
class CanvasObjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None
    object_type: str = Field(default="custom", min_length=1, max_length=80)
    parent_id: UUID | None
class CanvasObjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = None
    object_type: str | None = Field(default=None, min_length=1, max_length=80)
    parent_id: UUID | None = None
    x: float | None = Field(default=None, ge=-100000, le=100000)
    y: float | None = Field(default=None, ge=-100000, le=100000)
    width: float | None = Field(default=None, ge=40, le=10000)
    height: float | None = Field(default=None, ge=40, le=10000)
    rotation: float | None = Field(default=None, ge=-36000, le=36000)
    placed: bool | None = None
    locked: bool | None = None


def audit(db: Session, tenant_id: UUID, kind: str, entity_id: UUID, action: str, before=None, after=None):
    db.info["tenant_id"] = tenant_id
    audit_change(db, kind, entity_id, action, before, after)
def data(obj):
    result={"id": str(obj.id), "name": obj.name, "description": obj.description, "archived_at": obj.archived_at.isoformat() if obj.archived_at else None, "created_at": obj.created_at.isoformat() if obj.created_at else None, "updated_at": obj.updated_at.isoformat() if obj.updated_at else None}
    if isinstance(obj,Company):result.update(allow_multiple_positions=obj.allow_multiple_positions,allow_multiple_qualifications=obj.allow_multiple_qualifications)
    return result
def company_or_404(db, cid):
    row=db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==db.info.get("tenant_id")))
    if not row: raise HTTPException(404,"Company not found")
    return row

def canvas_object_data(row: CanvasObject):
    return {
        "id": str(row.id),
        "name": row.name,
        "description": row.description,
        "object_type": row.object_type,
        "parent_id": str(row.parent_id) if row.parent_id else None,
        "x": row.x,
        "y": row.y,
        "width": row.width,
        "height": row.height,
        "rotation": row.rotation,
        "placed": row.placed,
        "locked": row.locked,
        "archived_at": row.archived_at.isoformat() if row.archived_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


CANVAS_ALLOWED_CHILDREN = {
    "enterprise": {"shop", "plot", "box", "warehouse", "building", "room", "work_area", "workstation", "person"},
    "building": {"shop", "plot", "box", "warehouse", "room", "work_area", "office", "workstation", "person"},
    "shop": {"plot", "box", "work_area", "room", "workstation", "warehouse", "person"},
    "plot": {"box", "work_area", "room", "workstation", "warehouse", "person"},
    "box": {"work_area", "room", "workstation", "warehouse_area", "person"},
    "warehouse": {"warehouse_area", "work_area", "workstation", "room", "person"},
    "work_area": {"workstation", "post", "station", "person"},
    "room": {"building", "work_area", "workstation", "person"},
    "office": set(),
    "warehouse_area": set(),
    "workstation": {"person"},
    "post": {"person"},
    "station": {"person"},
    "person": set(),
}
CANVAS_ROLE_ALIASES = {
    "company": "enterprise", "firma": "enterprise", "site": "enterprise", "factory": "enterprise",
    "plant": "enterprise", "werk": "enterprise", "unternehmen": "enterprise", "предприятие": "enterprise",
    "завод": "enterprise", "площадка": "enterprise", "house": "building", "gebäude": "building",
    "здание": "building", "дом": "building", "apartment": "room", "квартира": "room", "raum": "room",
    "комната": "room", "büro": "office", "офис": "office", "workshop": "shop", "werkhalle": "shop",
    "цех": "shop", "area": "plot", "bereich": "plot", "участок": "plot", "bay": "box", "бокс": "box",
    "lager": "warehouse", "склад": "warehouse", "work area": "work_area", "arbeitsbereich": "work_area",
    "рабочая зона": "work_area", "arbeitsplatz": "workstation", "рабочее место": "workstation",
    "warehouse area": "warehouse_area", "lagerbereich": "warehouse_area", "складская зона": "warehouse_area",
    "пост": "post", "stationen": "station", "станция": "station", "employee": "person",
    "mitarbeiter": "person", "персона": "person", "сотрудник": "person",
}


def canvas_role(object_type: str) -> str | None:
    normalized = object_type.strip().lower()
    return normalized if normalized in CANVAS_ALLOWED_CHILDREN else CANVAS_ROLE_ALIASES.get(normalized)


def validate_canvas_parent(db: Session, tenant_id: UUID, child_type: str, parent_id: UUID | None, child_id: UUID | None = None):
    child_role = canvas_role(child_type)
    if child_role is None:
        raise HTTPException(422, "Unknown canvas object type")
    if child_role == "enterprise":
        if parent_id is not None:
            raise HTTPException(422, "Enterprise / plant must be a root object")
        duplicate_query = select(CanvasObject).where(
            CanvasObject.tenant_id == tenant_id,
            CanvasObject.archived_at.is_(None),
        )
        if child_id is not None:
            duplicate_query = duplicate_query.where(CanvasObject.id != child_id)
        if any(canvas_role(item.object_type) == "enterprise" for item in db.scalars(duplicate_query).all()):
            raise HTTPException(409, "Only one active enterprise / plant root is allowed")
        return
    if parent_id is None:
        raise HTTPException(422, "Choose the object that will contain this object")
    parent = db.scalar(select(CanvasObject).where(CanvasObject.id == parent_id, CanvasObject.tenant_id == tenant_id))
    if parent is None:
        raise HTTPException(404, "Canvas parent object not found")
    if parent.archived_at:
        raise HTTPException(409, "Cannot place an object inside an archived parent")
    parent_role = canvas_role(parent.object_type)
    if parent_role is None or child_role not in CANVAS_ALLOWED_CHILDREN[parent_role]:
        raise HTTPException(422, "This object type is not allowed inside the selected parent")
    current = parent
    visited = set()
    while current is not None:
        if current.id == child_id:
            raise HTTPException(422, "Canvas object hierarchy cannot contain a cycle")
        if current.id in visited:
            raise HTTPException(409, "Existing canvas object hierarchy contains a cycle")
        visited.add(current.id)
        current = db.scalar(select(CanvasObject).where(
            CanvasObject.id == current.parent_id,
            CanvasObject.tenant_id == tenant_id,
        )) if current.parent_id else None

def canvas_object_or_404(db: Session, tenant_id: UUID, object_id: UUID):
    row = db.scalar(select(CanvasObject).where(CanvasObject.id == object_id, CanvasObject.tenant_id == tenant_id))
    if not row:
        raise HTTPException(404, "Canvas object not found")
    return row

@router.get("/companies/{company_id}/canvas-objects", dependencies=[Depends(require_permission("structure:read"))])
def list_canvas_objects(company_id: UUID, db: Session = Depends(get_db)):
    company = company_or_404(db, company_id)
    rows = db.scalars(
        select(CanvasObject)
        .where(CanvasObject.tenant_id == company.tenant_id, CanvasObject.archived_at.is_(None))
        .order_by(CanvasObject.created_at, CanvasObject.id)
    ).all()
    return [canvas_object_data(row) for row in rows]

@router.post("/companies/{company_id}/canvas-objects", status_code=201, dependencies=[Depends(require_permission("structure:write"))])
def create_canvas_object(company_id: UUID, payload: CanvasObjectInput, db: Session = Depends(get_db)):
    company = company_or_404(db, company_id)
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, "Name must not be empty")
    object_type = payload.object_type.strip()
    if not object_type:
        raise HTTPException(422, "Object type must not be empty")
    validate_canvas_parent(db, company.tenant_id, object_type, payload.parent_id)
    row = CanvasObject(tenant_id=company.tenant_id, name=name, description=payload.description, object_type=object_type, parent_id=payload.parent_id)
    db.add(row)
    db.flush()
    audit(db, company.tenant_id, "canvas_object", row.id, "create", after=canvas_object_data(row))
    db.commit()
    db.refresh(row)
    return canvas_object_data(row)

@router.patch("/companies/{company_id}/canvas-objects/{object_id}", dependencies=[Depends(require_permission("structure:write"))])
def patch_canvas_object(company_id: UUID, object_id: UUID, payload: CanvasObjectPatch, db: Session = Depends(get_db)):
    company = company_or_404(db, company_id)
    row = canvas_object_or_404(db, company.tenant_id, object_id)
    if row.archived_at:
        raise HTTPException(409, "Archived canvas objects cannot be edited")
    before = canvas_object_data(row)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        if changes["name"] is None:
            raise HTTPException(422, "Name must not be empty")
        changes["name"] = changes["name"].strip()
        if not changes["name"]:
            raise HTTPException(422, "Name must not be empty")
    if "object_type" in changes:
        if changes["object_type"] is None or not changes["object_type"].strip():
            raise HTTPException(422, "Object type must not be empty")
        changes["object_type"] = changes["object_type"].strip()
    relationship_changed = (
        ("parent_id" in changes and changes["parent_id"] != row.parent_id)
        or ("object_type" in changes and changes["object_type"] != row.object_type)
    )
    if relationship_changed:
        validate_canvas_parent(
            db,
            company.tenant_id,
            changes.get("object_type", row.object_type),
            changes.get("parent_id", row.parent_id),
            row.id,
        )
    for key, value in changes.items():
        if value is not None or key == "description":
            setattr(row, key, value)
    audit(db, company.tenant_id, "canvas_object", row.id, "update", before=before, after=canvas_object_data(row))
    db.commit()
    db.refresh(row)
    return canvas_object_data(row)

@router.get("/companies/{company_id}/canvas-objects/trash", dependencies=[Depends(require_permission("structure:read"))])
def list_canvas_object_trash(company_id: UUID, db: Session = Depends(get_db)):
    company = company_or_404(db, company_id)
    rows = db.scalars(
        select(CanvasObject)
        .where(CanvasObject.tenant_id == company.tenant_id, CanvasObject.archived_at.is_not(None))
        .order_by(CanvasObject.archived_at.desc(), CanvasObject.name)
    ).all()
    return [canvas_object_data(row) for row in rows]

@router.post("/companies/{company_id}/canvas-objects/{object_id}/archive", dependencies=[Depends(require_permission("structure:write"))])
def archive_canvas_object(company_id: UUID, object_id: UUID, db: Session = Depends(get_db)):
    company = company_or_404(db, company_id)
    row = canvas_object_or_404(db, company.tenant_id, object_id)
    if row.archived_at:
        return canvas_object_data(row)
    active_child = db.scalar(select(CanvasObject.id).where(
        CanvasObject.tenant_id == company.tenant_id,
        CanvasObject.parent_id == row.id,
        CanvasObject.archived_at.is_(None),
    ).limit(1))
    if active_child:
        raise HTTPException(409, "Move or archive child objects before archiving this object")
    before = canvas_object_data(row)
    row.archived_at = datetime.now(timezone.utc)
    audit(db, company.tenant_id, "canvas_object", row.id, "archive", before=before, after=canvas_object_data(row))
    db.commit()
    db.refresh(row)
    return canvas_object_data(row)

@router.post("/companies/{company_id}/canvas-objects/{object_id}/restore", dependencies=[Depends(require_permission("structure:write"))])
def restore_canvas_object(company_id: UUID, object_id: UUID, db: Session = Depends(get_db)):
    company = company_or_404(db, company_id)
    row = canvas_object_or_404(db, company.tenant_id, object_id)
    if row.archived_at is None:
        raise HTTPException(409, "Canvas object is already active")
    if row.parent_id:
        parent = db.scalar(select(CanvasObject).where(
            CanvasObject.id == row.parent_id,
            CanvasObject.tenant_id == company.tenant_id,
        ))
        if parent is None or parent.archived_at:
            raise HTTPException(409, "Restore the parent object before restoring this object")
    validate_canvas_parent(db, company.tenant_id, row.object_type, row.parent_id, row.id)
    before = canvas_object_data(row)
    row.archived_at = None
    audit(db, company.tenant_id, "canvas_object", row.id, "restore", before=before, after=canvas_object_data(row))
    db.commit()
    db.refresh(row)
    return canvas_object_data(row)

@router.post("/companies/{company_id}/canvas-objects/{object_id}/purge", status_code=204, dependencies=[Depends(require_permission("structure:write"))])
def purge_canvas_object(company_id: UUID, object_id: UUID, db: Session = Depends(get_db)):
    company = company_or_404(db, company_id)
    row = canvas_object_or_404(db, company.tenant_id, object_id)
    if row.archived_at is None:
        raise HTTPException(409, "Archive the canvas object before permanently deleting it")
    child = db.scalar(select(CanvasObject.id).where(
        CanvasObject.tenant_id == company.tenant_id,
        CanvasObject.parent_id == row.id,
    ).limit(1))
    if child:
        raise HTTPException(409, "Move or permanently delete child objects before deleting this object")
    before = canvas_object_data(row)
    audit(db, company.tenant_id, "canvas_object", row.id, "purge", before=before)
    db.delete(row)
    db.commit()
    return None

def get_node(db, tenant_id, kind, node_id):
    model=KINDS[kind]
    row=db.scalar(select(model).where(model.id==node_id, model.tenant_id==tenant_id))
    if not row: raise HTTPException(404,"Structure element not found")
    return row

def validate_parent(db, tenant_id, kind, parent_id):
    spec=PARENTS[kind]
    if spec is None:
        if parent_id is not None: raise HTTPException(422,"A site belongs directly to the company")
        return {}
    if parent_id is None: raise HTTPException(422,"parent_id is required")
    parent_kind, field=spec
    parent=get_node(db,tenant_id,parent_kind,parent_id)
    if parent.archived_at: raise HTTPException(409,"Cannot add an element below an archived parent")
    return {field: parent.id}

def validate_workspace_location(db, tenant_id, parent_kind, parent_id, allow_workstation=False):
    if parent_kind is None and parent_id is None:
        return {"site_id": None, "department_id": None, "area_id": None, "workstation_id": None}
    allowed={"site","department","area"}|({"workstation"} if allow_workstation else set())
    if parent_kind not in allowed or parent_id is None:
        raise HTTPException(422,"Choose a valid active location")
    parent=get_node(db,tenant_id,parent_kind,parent_id)
    if parent.archived_at: raise HTTPException(409,"Cannot place a workstation inside an archived location")
    return {"site_id":parent.id if parent_kind=="site" else None,"department_id":parent.id if parent_kind=="department" else None,"area_id":parent.id if parent_kind=="area" else None,"workstation_id":parent.id if parent_kind=="workstation" else None}

def node_children(db, tenant_id, kind, row):
    if kind=="site": kids=[("department", x) for x in db.scalars(select(Department).where(Department.tenant_id==tenant_id, Department.site_id==row.id, Department.archived_at.is_(None))).all()]
    elif kind=="department": kids=[("area", x) for x in db.scalars(select(Area).where(Area.tenant_id==tenant_id, Area.department_id==row.id, Area.archived_at.is_(None))).all()]
    else: kids=[]
    if kind in {"site","department","area"}:
        field={"site":"site_id","department":"department_id","area":"area_id"}[kind]
        kids.extend(("workstation",x) for x in db.scalars(select(Workstation).where(Workstation.tenant_id==tenant_id,getattr(Workstation,field)==row.id,Workstation.archived_at.is_(None))).all())
    field={"site":"site_id","department":"department_id","area":"area_id","workstation":"workstation_id"}.get(kind)
    if field:
        assigns=db.scalars(select(EquipmentAssignment).where(EquipmentAssignment.tenant_id==tenant_id,getattr(EquipmentAssignment,field)==row.id,EquipmentAssignment.valid_to.is_(None))).all()
        for a in assigns:
            e=db.scalar(select(Equipment).where(Equipment.id==a.equipment_id, Equipment.tenant_id==tenant_id, Equipment.archived_at.is_(None)))
            if e: kids.append(("equipment",e))
    employee_field={"site":"site_id","department":"department_id","area":"area_id","workstation":"workstation_id"}.get(kind)
    if employee_field:
        filters=[EmployeeWorkAssignment.tenant_id==tenant_id,EmployeeWorkAssignment.valid_to.is_(None),getattr(EmployeeWorkAssignment,employee_field)==row.id]
        if kind=="site":filters.extend((EmployeeWorkAssignment.department_id.is_(None),EmployeeWorkAssignment.area_id.is_(None),EmployeeWorkAssignment.workstation_id.is_(None)))
        placements=db.scalars(select(EmployeeWorkAssignment).where(*filters)).all()
        for placement in placements:
            person=db.scalar(select(Employee).where(Employee.id==placement.employee_id,Employee.tenant_id==tenant_id,Employee.is_active.is_(True),Employee.archived_at.is_(None)))
            if person:kids.append(("employee",person))
    return [{**({"id":str(x.id),"name":x.full_name,"full_name":x.full_name,"employee_number":x.employee_number} if isinstance(x,Employee) else data(x)),"kind":k,"children":node_children(db,tenant_id,k,x)} for k,x in kids]

@router.get("/companies",dependencies=[Depends(require_permission("structure:read"))])
def list_companies(db:Session=Depends(get_db)):
    return [data(x) for x in db.scalars(select(Company).where(Company.tenant_id==db.info.get("tenant_id"),Company.archived_at.is_(None)).order_by(Company.name)).all()]
@router.get("/companies/archived",dependencies=[Depends(require_permission("structure:write"))])
def list_archived_companies(db:Session=Depends(get_db)):
    return [data(x) for x in db.scalars(select(Company).where(Company.tenant_id==db.info.get("tenant_id"),Company.archived_at.is_not(None)).order_by(Company.name)).all()]
@router.post("/companies/{company_id}/restore",dependencies=[Depends(require_permission("structure:write"))])
def restore_company(company_id:UUID,db:Session=Depends(get_db)):
    row=company_or_404(db,company_id)
    if row.archived_at is None: raise HTTPException(409,"Company is already active")
    before=data(row); row.archived_at=None
    audit(db,row.tenant_id,"company",row.id,"restore",before=before,after=data(row)); db.commit(); db.refresh(row)
    return data(row)
@router.get("/companies/{company_id}/archive",dependencies=[Depends(require_permission("structure:write"))])
def list_structure_archive(company_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id);rows=[]
    for kind,model in KINDS.items():
        rows.extend([{**data(x),"kind":kind} for x in db.scalars(select(model).where(model.tenant_id==c.tenant_id,model.archived_at.is_not(None))).all()])
    rows.extend([{**data(x),"kind":"equipment"} for x in db.scalars(select(Equipment).where(Equipment.tenant_id==c.tenant_id,Equipment.archived_at.is_not(None))).all()])
    rows.sort(key=lambda x:(x.get("archived_at") or "",x["name"]))
    return rows
@router.post("/companies",status_code=201,dependencies=[Depends(require_permission("platform:company:create"))])
def create_company(payload:CompanyInput,db:Session=Depends(get_db)):
    row_id=uuid4(); row=Company(id=row_id,tenant_id=row_id,name=payload.name.strip(),description=payload.description)
    db.add(row); db.flush(); audit(db,row.tenant_id,"company",row.id,"create",after=data(row)); db.commit(); db.refresh(row); return data(row)
@router.get("/companies/{company_id}/structure",dependencies=[Depends(require_permission("structure:read"))])
def structure(company_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id)
    sites=db.scalars(select(Site).where(Site.tenant_id==c.tenant_id,Site.archived_at.is_(None)).order_by(Site.name)).all()
    tree=[{**data(s),"kind":"site","children":node_children(db,c.tenant_id,"site",s)} for s in sites]
    root_workstations=db.scalars(select(Workstation).where(Workstation.tenant_id==c.tenant_id,Workstation.site_id.is_(None),Workstation.department_id.is_(None),Workstation.area_id.is_(None),Workstation.archived_at.is_(None)).order_by(Workstation.name)).all()
    root_assignments=db.scalars(select(EquipmentAssignment).where(EquipmentAssignment.tenant_id==c.tenant_id,EquipmentAssignment.site_id.is_(None),EquipmentAssignment.department_id.is_(None),EquipmentAssignment.area_id.is_(None),EquipmentAssignment.workstation_id.is_(None),EquipmentAssignment.valid_to.is_(None))).all()
    root_equipment=[]
    for assignment in root_assignments:
        equipment=db.scalar(select(Equipment).where(Equipment.id==assignment.equipment_id,Equipment.tenant_id==c.tenant_id,Equipment.archived_at.is_(None)))
        if equipment:root_equipment.append({**data(equipment),"kind":"equipment","children":[]})
    root_people=db.scalars(select(Employee).join(EmployeeWorkAssignment,EmployeeWorkAssignment.employee_id==Employee.id).where(Employee.tenant_id==c.tenant_id,EmployeeWorkAssignment.tenant_id==c.tenant_id,EmployeeWorkAssignment.site_id.is_(None),EmployeeWorkAssignment.department_id.is_(None),EmployeeWorkAssignment.area_id.is_(None),EmployeeWorkAssignment.workstation_id.is_(None),EmployeeWorkAssignment.valid_to.is_(None),Employee.is_active.is_(True),Employee.archived_at.is_(None))).all()
    unassigned=db.scalars(select(Equipment).where(Equipment.tenant_id==c.tenant_id,Equipment.archived_at.is_(None),~select(EquipmentAssignment.id).where(EquipmentAssignment.tenant_id==c.tenant_id,EquipmentAssignment.equipment_id==Equipment.id,EquipmentAssignment.valid_to.is_(None)).exists()).order_by(Equipment.name)).all()
    return {"company":{**data(c),"allow_multiple_positions":c.allow_multiple_positions,"allow_multiple_qualifications":c.allow_multiple_qualifications},"tree":tree,"root_workstations":[{**data(x),"kind":"workstation","children":node_children(db,c.tenant_id,"workstation",x)} for x in root_workstations],"root_equipment":root_equipment,"root_people":[{"id":str(p.id),"name":p.full_name,"full_name":p.full_name,"employee_number":p.employee_number,"kind":"employee","children":[]} for p in root_people],"unassigned_equipment":[{**data(e),"kind":"equipment","children":[]} for e in unassigned]}
@router.patch("/companies/{company_id}",dependencies=[Depends(require_permission("structure:write"))])
def patch_company(company_id:UUID,payload:CompanyPatch,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id); before=data(c)
    for key,value in payload.model_dump(exclude_unset=True).items(): setattr(c,key,value.strip() if key=="name" and value else value)
    audit(db,c.tenant_id,"company",c.id,"update",before=before,after=data(c)); db.commit(); db.refresh(c); return data(c)

@router.post("/companies/{company_id}/archive",dependencies=[Depends(require_permission("structure:write"))])
def archive_company(company_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id)
    if c.archived_at:return data(c)
    has_sites=db.scalar(select(Site.id).where(Site.tenant_id==c.tenant_id,Site.archived_at.is_(None)).limit(1))
    has_equipment=db.scalar(select(Equipment.id).where(Equipment.tenant_id==c.tenant_id,Equipment.archived_at.is_(None)).limit(1))
    if has_sites or has_equipment:raise HTTPException(409,"Archive active structure elements and equipment first")
    before=data(c);c.archived_at=datetime.now(timezone.utc);audit(db,c.tenant_id,"company",c.id,"archive",before=before,after=data(c));db.commit();return data(c)

@router.post("/companies/{company_id}/nodes/{kind}",status_code=201,dependencies=[Depends(require_permission("structure:write"))])
def create_node(company_id:UUID,kind:str,payload:EntityInput,db:Session=Depends(get_db)):
    if kind not in KINDS: raise HTTPException(404,"Unsupported node type")
    c=company_or_404(db,company_id)
    if kind=="workstation":
        location_kind=payload.parent_kind or ("area" if payload.parent_id else None)
        parent=validate_workspace_location(db,c.tenant_id,location_kind,payload.parent_id)
        parent.pop("workstation_id",None)
    else: parent=validate_parent(db,c.tenant_id,kind,payload.parent_id)
    row=KINDS[kind](tenant_id=c.tenant_id,name=payload.name.strip(),description=payload.description,**parent)
    db.add(row); db.flush(); audit(db,c.tenant_id,kind,row.id,"create",after=data(row)); db.commit(); db.refresh(row); return {**data(row),"kind":kind,"children":[]}
@router.patch("/companies/{company_id}/nodes/{kind}/{node_id}",dependencies=[Depends(require_permission("structure:write"))])
def patch_node(company_id:UUID,kind:str,node_id:UUID,payload:EntityPatch,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id)
    if kind not in KINDS: raise HTTPException(404,"Unsupported node type")
    row=get_node(db,c.tenant_id,kind,node_id)
    if row.archived_at: raise HTTPException(409,"Archived elements cannot be edited")
    before=data(row)
    for key,value in payload.model_dump(exclude_unset=True).items(): setattr(row,key,value.strip() if key=="name" and value else value)
    audit(db,c.tenant_id,kind,row.id,"update",before=before,after=data(row)); db.commit(); db.refresh(row); return data(row)
@router.post("/companies/{company_id}/nodes/{kind}/{node_id}/move",dependencies=[Depends(require_permission("structure:write"))])
def move_node(company_id:UUID,kind:str,node_id:UUID,payload:MoveInput,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id)
    if kind not in KINDS or kind=="site": raise HTTPException(422,"Only departments, areas, and workstations can be moved")
    row=get_node(db,c.tenant_id,kind,node_id)
    if row.archived_at: raise HTTPException(409,"Archived elements cannot be moved")
    before=data(row)
    if kind=="workstation":
        location_kind=payload.parent_kind or ("area" if payload.parent_id else None)
        relation=validate_workspace_location(db,c.tenant_id,location_kind,payload.parent_id)
        row.site_id=relation["site_id"];row.department_id=relation["department_id"];row.area_id=relation["area_id"]
    else:
        relation=validate_parent(db,c.tenant_id,kind,payload.parent_id)
        if kind=="department": row.site_id=relation["site_id"]
        elif kind=="area": row.department_id=relation["department_id"]
    audit(db,c.tenant_id,kind,row.id,"move",before=before,after=data(row)); db.commit(); db.refresh(row); return data(row)
@router.post("/companies/{company_id}/nodes/{kind}/{node_id}/archive",dependencies=[Depends(require_permission("structure:write"))])
def archive_node(company_id:UUID,kind:str,node_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id)
    if kind not in KINDS: raise HTTPException(404,"Unsupported node type")
    row=get_node(db,c.tenant_id,kind,node_id)
    if row.archived_at:return data(row)
    if node_children(db,c.tenant_id,kind,row): raise HTTPException(409,"Archive active child elements first")
    before=data(row); row.archived_at=datetime.now(timezone.utc); audit(db,c.tenant_id,kind,row.id,"archive",before=before,after=data(row)); db.commit(); return data(row)
@router.post("/companies/{company_id}/archive/{kind}/{node_id}/restore",dependencies=[Depends(require_permission("structure:write"))])
def restore_archived_structure(company_id:UUID,kind:str,node_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id);model=Equipment if kind=="equipment" else KINDS.get(kind)
    if model is None:raise HTTPException(404,"Unsupported archive type")
    row=db.scalar(select(model).where(model.id==node_id,model.tenant_id==c.tenant_id))
    if not row:raise HTTPException(404,"Archived element not found")
    if row.archived_at is None:raise HTTPException(409,"Element is already active")
    before=data(row);row.archived_at=None;audit(db,c.tenant_id,kind,row.id,"restore",before=before,after=data(row));db.commit();return data(row)

@router.post("/companies/{company_id}/equipment",status_code=201,dependencies=[Depends(require_permission("structure:write"))])
def create_equipment(company_id:UUID,payload:EquipmentInput,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id); e=Equipment(tenant_id=c.tenant_id,name=payload.name.strip(),description=payload.description)
    location_kind=payload.parent_kind or ("workstation" if payload.parent_id else None)
    location=validate_workspace_location(db,c.tenant_id,location_kind,payload.parent_id,allow_workstation=True)
    db.add(e); db.flush(); audit(db,c.tenant_id,"equipment",e.id,"create",after=data(e))
    now=datetime.now(timezone.utc);a=EquipmentAssignment(tenant_id=c.tenant_id,equipment_id=e.id,valid_from=now,**location);db.add(a)
    audit(db,c.tenant_id,"equipment_assignment",a.id,"assign",after={"equipment_id":str(e.id),**{k:str(v) if v else None for k,v in location.items()},"valid_from":now.isoformat()})
    db.commit(); db.refresh(e); return data(e)
@router.get("/companies/{company_id}/equipment/{equipment_id}",dependencies=[Depends(require_permission("structure:read"))])
def equipment_detail(company_id:UUID,equipment_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id); e=db.scalar(select(Equipment).where(Equipment.id==equipment_id,Equipment.tenant_id==c.tenant_id))
    if not e: raise HTTPException(404,"Equipment not found")
    assignments=db.scalars(select(EquipmentAssignment).where(EquipmentAssignment.tenant_id==c.tenant_id,EquipmentAssignment.equipment_id==e.id).order_by(EquipmentAssignment.valid_from.desc())).all()
    return {**data(e),"kind":"equipment","assignments":[{"id":str(a.id),"site_id":str(a.site_id) if a.site_id else None,"department_id":str(a.department_id) if a.department_id else None,"area_id":str(a.area_id) if a.area_id else None,"workstation_id":str(a.workstation_id) if a.workstation_id else None,"valid_from":a.valid_from.isoformat(),"valid_to":a.valid_to.isoformat() if a.valid_to else None} for a in assignments]}
@router.post("/companies/{company_id}/equipment/{equipment_id}/assignments",status_code=201,dependencies=[Depends(require_permission("structure:write"))])
def assign_equipment(company_id:UUID,equipment_id:UUID,payload:AssignmentInput,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id); e=db.scalar(select(Equipment).where(Equipment.id==equipment_id,Equipment.tenant_id==c.tenant_id))
    if not e or e.archived_at: raise HTTPException(404,"Active equipment not found")
    location_values=(payload.site_id,payload.department_id,payload.area_id,payload.workstation_id)
    if sum(value is not None for value in location_values)>1:raise HTTPException(422,"Choose only one equipment location")
    location={"site_id":None,"department_id":None,"area_id":None,"workstation_id":None}
    for kind,key in (("site","site_id"),("department","department_id"),("area","area_id"),("workstation","workstation_id")):
        value=getattr(payload,key)
        if value is not None:
            row=get_node(db,c.tenant_id,kind,value)
            if row.archived_at:raise HTTPException(409,"Cannot place equipment inside an archived location")
            location[key]=row.id
    now=payload.valid_from or datetime.now(timezone.utc)
    current=db.scalar(select(EquipmentAssignment).where(EquipmentAssignment.tenant_id==c.tenant_id,EquipmentAssignment.equipment_id==e.id,EquipmentAssignment.valid_to.is_(None)).with_for_update())
    if current:
        if now<=current.valid_from: raise HTTPException(422,"New assignment must start after current assignment")
        old={"site_id":str(current.site_id) if current.site_id else None,"department_id":str(current.department_id) if current.department_id else None,"area_id":str(current.area_id) if current.area_id else None,"workstation_id":str(current.workstation_id) if current.workstation_id else None,"valid_from":current.valid_from.isoformat(),"valid_to":None}; current.valid_to=now
        audit(db,c.tenant_id,"equipment_assignment",current.id,"close",before=old,after={**old,"valid_to":now.isoformat()})
    new=EquipmentAssignment(tenant_id=c.tenant_id,equipment_id=e.id,valid_from=now,**location); db.add(new); db.flush()
    after={k:str(v) if v else None for k,v in location.items()};audit(db,c.tenant_id,"equipment_assignment",new.id,"assign",after=after); db.commit()
    return {"id":str(new.id),"equipment_id":str(e.id),**after,"valid_from":now.isoformat(),"valid_to":None}
@router.post("/companies/{company_id}/equipment/{equipment_id}/assignments/close",dependencies=[Depends(require_permission("structure:write"))])
def close_assignment(company_id:UUID,equipment_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id)
    equipment=db.scalar(select(Equipment).where(Equipment.id==equipment_id,Equipment.tenant_id==c.tenant_id))
    if not equipment:raise HTTPException(404,"Equipment not found")
    current=db.scalar(select(EquipmentAssignment).where(EquipmentAssignment.tenant_id==c.tenant_id,EquipmentAssignment.equipment_id==equipment.id,EquipmentAssignment.valid_to.is_(None)).with_for_update())
    if not current:raise HTTPException(409,"Equipment has no active workstation assignment")
    now=datetime.now(timezone.utc)
    if now<=current.valid_from:raise HTTPException(409,"Assignment start time is not before the current time")
    before={"equipment_id":str(equipment.id),"site_id":str(current.site_id) if current.site_id else None,"department_id":str(current.department_id) if current.department_id else None,"area_id":str(current.area_id) if current.area_id else None,"workstation_id":str(current.workstation_id) if current.workstation_id else None,"valid_from":current.valid_from.isoformat(),"valid_to":None}
    current.valid_to=now
    after={**before,"valid_to":now.isoformat()}
    audit(db,c.tenant_id,"equipment_assignment",current.id,"unassign",before=before,after=after)
    db.commit()
    return {"id":str(current.id),"equipment_id":str(equipment.id),"workstation_id":str(current.workstation_id),"valid_from":current.valid_from.isoformat(),"valid_to":now.isoformat()}

@router.patch("/companies/{company_id}/equipment/{equipment_id}",dependencies=[Depends(require_permission("structure:write"))])
def patch_equipment(company_id:UUID,equipment_id:UUID,payload:EntityPatch,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id); e=db.scalar(select(Equipment).where(Equipment.id==equipment_id,Equipment.tenant_id==c.tenant_id))
    if not e: raise HTTPException(404,"Equipment not found")
    before=data(e)
    for key,value in payload.model_dump(exclude_unset=True).items(): setattr(e,key,value.strip() if key=="name" and value else value)
    audit(db,c.tenant_id,"equipment",e.id,"update",before=before,after=data(e)); db.commit(); db.refresh(e); return data(e)
@router.post("/companies/{company_id}/equipment/{equipment_id}/archive",dependencies=[Depends(require_permission("structure:write"))])
def archive_equipment(company_id:UUID,equipment_id:UUID,db:Session=Depends(get_db)):
    c=company_or_404(db,company_id); e=db.scalar(select(Equipment).where(Equipment.id==equipment_id,Equipment.tenant_id==c.tenant_id))
    if not e: raise HTTPException(404,"Equipment not found")
    active=db.scalar(select(EquipmentAssignment).where(EquipmentAssignment.tenant_id==c.tenant_id,EquipmentAssignment.equipment_id==e.id,EquipmentAssignment.valid_to.is_(None)).with_for_update())
    if active:
        now=datetime.now(timezone.utc)
        if now<=active.valid_from:raise HTTPException(409,"Equipment placement has just started; retry shortly")
        before={"site_id":str(active.site_id) if active.site_id else None,"department_id":str(active.department_id) if active.department_id else None,"area_id":str(active.area_id) if active.area_id else None,"workstation_id":str(active.workstation_id) if active.workstation_id else None,"valid_from":active.valid_from.isoformat(),"valid_to":None}
        active.valid_to=now;audit(db,c.tenant_id,"equipment_assignment",active.id,"close_for_archive",before=before,after={**before,"valid_to":now.isoformat()})
    before=data(e); e.archived_at=datetime.now(timezone.utc); audit(db,c.tenant_id,"equipment",e.id,"archive",before=before,after=data(e)); db.commit(); return data(e)
