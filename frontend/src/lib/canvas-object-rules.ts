export type CanvasStructureObject = {
  id: string;
  object_type: string;
  parent_id?: string | null;
};

const allowedChildren: Record<string, readonly string[]> = {
  enterprise: ["shop", "plot", "box", "warehouse", "building", "room", "work_area", "workstation", "person"],
  building: ["shop", "plot", "box", "warehouse", "room", "work_area", "office", "workstation", "person"],
  shop: ["plot", "box", "work_area", "room", "workstation", "warehouse", "person"],
  plot: ["box", "work_area", "room", "workstation", "warehouse", "person"],
  box: ["work_area", "room", "workstation", "warehouse_area", "person"],
  warehouse: ["warehouse_area", "work_area", "workstation", "room", "person"],
  work_area: ["workstation", "post", "station", "person"],
  room: ["building", "work_area", "workstation", "person"],
  workstation: ["person"],
  post: ["person"],
  station: ["person"],
  person: [],
};

const roleAliases: Record<string, string> = {
  company: "enterprise",
  firma: "enterprise",
  site: "enterprise",
  factory: "enterprise",
  plant: "enterprise",
  werk: "enterprise",
  unternehmen: "enterprise",
  предприятие: "enterprise",
  завод: "enterprise",
  площадка: "enterprise",
  building: "building",
  house: "building",
  gebäude: "building",
  здание: "building",
  дом: "building",
  apartment: "room",
  квартира: "room",
  room: "room",
  raum: "room",
  комната: "room",
  office: "office",
  büro: "office",
  офис: "office",
  shop: "shop",
  workshop: "shop",
  werkhalle: "shop",
  цех: "shop",
  plot: "plot",
  area: "plot",
  bereich: "plot",
  участок: "plot",
  box: "box",
  bay: "box",
  бокс: "box",
  warehouse: "warehouse",
  lager: "warehouse",
  склад: "warehouse",
  work_area: "work_area",
  "work area": "work_area",
  arbeitsbereich: "work_area",
  "рабочая зона": "work_area",
  workstation: "workstation",
  arbeitsplatz: "workstation",
  "рабочее место": "workstation",
  warehouse_area: "warehouse_area",
  "warehouse area": "warehouse_area",
  lagerbereich: "warehouse_area",
  "складская зона": "warehouse_area",
  post: "post",
  пост: "post",
  station: "station",
  stationen: "station",
  станция: "station",
  person: "person",
  employee: "person",
  mitarbeiter: "person",
  персона: "person",
  сотрудник: "person",
};

export function canvasObjectRole(type: string) {
  const normalized = type.trim().toLowerCase();
  return allowedChildren[normalized] ? normalized : roleAliases[normalized] ?? null;
}

export function isAllowedCanvasParent(parentType: string, childType: string) {
  const parentRole = canvasObjectRole(parentType);
  const childRole = canvasObjectRole(childType);
  return parentRole !== null && childRole !== null && (allowedChildren[parentRole]?.includes(childRole) ?? false);
}

export function isCanvasRootType(type: string) {
  return canvasObjectRole(type) === "enterprise";
}

export function canvasObjectParents<T extends CanvasStructureObject>(objects: T[]) {
  const parents = new Map<string, T>();
  const byId = new Map(objects.map((object) => [object.id, object]));
  for (const child of objects) {
    if (isCanvasRootType(child.object_type) || !child.parent_id) continue;
    const parent = byId.get(child.parent_id);
    if (parent && isAllowedCanvasParent(parent.object_type, child.object_type)) parents.set(child.id, parent);
  }
  return parents;
}
