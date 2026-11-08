"use client";

import { useEffect, useState } from "react";
import type { Locale } from "@/i18n/messages";
import { api } from "@/lib/api";
import { canvasObjectParents, canvasObjectRole, isCanvasRootType } from "@/lib/canvas-object-rules";

type CanvasObject = {
  id: string;
  name: string;
  description: string | null;
  kind: "site" | "department" | "area" | "workstation" | "equipment" | "employee";
  object_type: string;
  parent_id: string | null;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  placed: boolean;
};
type TreeNode = { id: string; name: string; kind: string; placed?: boolean; children?: TreeNode[] };

const words: Record<Locale, Record<string, string>> = {
  ru: {
    title: "Структура и связи",
    loading: "Загрузка структуры…",
    empty: "Структура предприятия пока не создана.",
    site: "Площадка",
    department: "Подразделение",
    area: "Участок",
    equipment: "Оборудование",
    employee: "Сотрудник",
    company: "Предприятие",
    enterprise: "Предприятие / завод",
    building: "Здание",
    shop: "Цех",
    plot: "Участок",
    warehouse: "Склад",
    box: "Бокс",
    work_area: "Рабочая зона",
    room: "Комната",
    office: "Офис",
    workstation: "Рабочее место",
    warehouse_area: "Складская зона",
    post: "Пост",
    station: "Станция",
    person: "Персона",
    unassigned: "Не задан родительский объект",
    explanation: "Связи задаются явно при создании объектов и проверяются по допустимой вложенности типов.",
  },
  de: {
    title: "Struktur und Verbindungen",
    loading: "Struktur wird geladen…",
    empty: "Die Unternehmensstruktur wurde noch nicht erstellt.",
    site: "Standort",
    department: "Abteilung",
    area: "Bereich",
    workstation: "Arbeitsplatz",
    equipment: "Ausrüstung",
    employee: "Mitarbeiter",
    company: "Unternehmen",
    enterprise: "Unternehmen / Werk",
    building: "Gebäude",
    shop: "Werkhalle",
    plot: "Bereich",
    warehouse: "Lager",
    box: "Box",
    work_area: "Arbeitsbereich",
    room: "Raum",
    office: "Büro",
    warehouse_area: "Lagerbereich",
    post: "Arbeitsplatz",
    station: "Station",
    person: "Person",
    unassigned: "Kein übergeordnetes Objekt zugeordnet",
    explanation: "Beziehungen werden beim Erstellen festgelegt und anhand der zulässigen Objekttypen geprüft.",
  },
  en: {
    title: "Structure and relationships",
    loading: "Loading structure…",
    empty: "The enterprise structure has not been created yet.",
    site: "Site",
    department: "Department",
    area: "Area",
    workstation: "Workstation",
    equipment: "Equipment",
    employee: "Employee",
    company: "Enterprise",
    enterprise: "Enterprise / plant",
    building: "Building",
    shop: "Shop",
    plot: "Section",
    warehouse: "Warehouse",
    box: "Bay",
    work_area: "Work area",
    room: "Room",
    office: "Office",
    warehouse_area: "Warehouse area",
    post: "Post",
    station: "Station",
    person: "Person",
    unassigned: "No parent object assigned",
    explanation: "Relationships are selected when objects are created and validated against the allowed type hierarchy.",
  },
};

function StructureBranch({ node, labels }: { node: TreeNode; labels: Record<string, string> }) {
  const children = node.children ?? [];
  return (
    <li className={`structure-tree-node structure-tree-${node.kind}`} role="treeitem">
      {children.length ? <details open>
        <summary className="structure-tree-card">
          <span className="structure-tree-type">{labels[node.kind] ?? node.kind}</span>
          <strong>{node.name}{node.placed === false ? " · —" : ""}</strong>
        </summary>
        <ul role="group">
          {children.map((child) => <StructureBranch key={`${child.kind}-${child.id}`} node={child} labels={labels} />)}
        </ul>
      </details> : <div className="structure-tree-card">
        <span className="structure-tree-type">{labels[node.kind] ?? node.kind}</span>
        <strong>{node.name}{node.placed === false ? " · —" : ""}</strong>
      </div>}
    </li>
  );
}

export function EnterpriseStructureTree({ locale }: { locale: Locale }) {
  const t = words[locale];
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const companies = await api<{ id: string; name: string }[]>("/api/v1/companies");
        const company = companies[0];
        if (!company) {
          if (active) setTree([]);
          return;
        }
        const objects = await api<CanvasObject[]>(`/api/v1/companies/${company.id}/canvas-objects`);
        const children = new Map<string, CanvasObject[]>();
        const parents = canvasObjectParents(objects);
        for (const object of objects) {
          const parentId = parents.get(object.id)?.id;
          const key = parentId ?? "enterprise-root";
          children.set(key, [...(children.get(key) ?? []), object]);
        }
        const toTreeNode = (object: CanvasObject): TreeNode => ({
          id: object.id,
          name: object.name,
          kind: canvasObjectRole(object.object_type) ?? object.object_type,
          placed: object.placed,
          children: (children.get(object.id) ?? []).map(toTreeNode),
        });
        const rootObjects = objects.filter((object) => isCanvasRootType(object.object_type));
        const unassigned = objects.filter((object) => !isCanvasRootType(object.object_type) && !parents.has(object.id));
        const rootChildren = rootObjects.map(toTreeNode);
        if (unassigned.length) {
          rootChildren.push({
            id: "unassigned-objects",
            name: t.unassigned,
            kind: "unassigned",
            children: unassigned.map(toTreeNode),
          });
        }
        if (active) setTree([{ id: company.id, name: company.name, kind: "company", children: rootChildren }]);
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : t.empty);
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [t.empty]);

  return (
    <section className="enterprise-structure-tree" aria-labelledby="enterprise-tree-title">
      <header>
        <span className="floor-index">STRUCTURE / DATA</span>
        <h2 id="enterprise-tree-title">{t.title}</h2>
        <p>{t.explanation}</p>
      </header>
      {loading ? <p>{t.loading}</p> : error ? <p role="alert">{error}</p> : tree.length ? (
        <ul className="enterprise-tree-root" role="tree" aria-label={t.title}>
          {tree.map((node) => <StructureBranch key={node.id} node={node} labels={t} />)}
        </ul>
      ) : <p>{t.empty}</p>}
    </section>
  );
}
