"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, DragEvent as ReactDragEvent, FormEvent, PointerEvent as ReactPointerEvent } from "react";
import Link from "next/link";
import type { Locale } from "@/i18n/messages";
import { api } from "@/lib/api";
import { setupPath } from "@/lib/routes";
import { canvasObjectParents, canvasObjectRole, isAllowedCanvasParent, isCanvasRootType } from "@/lib/canvas-object-rules";

type Company = { id: string; name: string };
type CanvasObject = {
  id: string;
  name: string;
  description: string | null;
  object_type: string;
  parent_id: string | null;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  placed: boolean;
  locked: boolean;
};
type View = { scale: number; x: number; y: number; rotation: number; grid: boolean };
type Geometry = Pick<CanvasObject, "x" | "y" | "width" | "height" | "rotation">;
type CanvasSnapshot = CanvasObject[];
type HistoryEntry = { before: CanvasSnapshot; after: CanvasSnapshot };
type ExportFormat = "json" | "svg" | "png";
type ExportScope = "all" | "location";
type PrintScope = "all" | "each" | "location";
type DragState = {
  pointerId: number;
  mode: "move" | "resize" | "pan" | "rotate";
  objectId?: string;
  handle?: string;
  startX: number;
  startY: number;
  geometry?: Geometry;
  view?: View;
};
type SaveFileHandle = { createWritable(): Promise<{ write(data: Blob | string): Promise<void>; close(): Promise<void> }> };
type SavePickerWindow = Window & {
  showSaveFilePicker?: (options: {
    suggestedName: string;
    types: { description: string; accept: Record<string, string[]> }[];
  }) => Promise<SaveFileHandle>;
};

function topLevelLocations(objects: CanvasObject[]) {
  const parents = canvasObjectParents(objects);
  return objects.filter((object) => !parents.has(object.id));
}

function objectBounds(object: CanvasObject) {
  const angle = object.rotation * Math.PI / 180;
  const halfWidth = (Math.abs(Math.cos(angle)) * object.width + Math.abs(Math.sin(angle)) * object.height) / 2;
  const halfHeight = (Math.abs(Math.sin(angle)) * object.width + Math.abs(Math.cos(angle)) * object.height) / 2;
  const centerX = object.x + object.width / 2;
  const centerY = object.y + object.height / 2;
  return { left: centerX - halfWidth, right: centerX + halfWidth, top: centerY - halfHeight, bottom: centerY + halfHeight };
}

function objectsAtLocation(objects: CanvasObject[], location: CanvasObject) {
  const parents = canvasObjectParents(objects);
  const descendants = new Set([location.id]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const [id, parent] of parents) {
      if (descendants.has(parent.id) && !descendants.has(id)) {
        descendants.add(id);
        changed = true;
      }
    }
  }
  return objects.filter((object) => descendants.has(object.id));
}

function escapeXml(value: string) {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
  })[character] ?? character);
}

function fitCanvasLabel(value: string, availableWidth: number, fontSize: number) {
  const maxCharacters = Math.floor(availableWidth / (fontSize * 0.8));
  if (value.length <= maxCharacters) return value;
  return maxCharacters > 1 ? `${value.slice(0, maxCharacters - 1)}…` : "";
}

function wrapCanvasLabel(value: string, maxCharacters: number, maxLines: number) {
  const lines: string[] = [];
  let remaining = value.trim();
  while (remaining && lines.length < maxLines) {
    if (remaining.length <= maxCharacters) {
      lines.push(remaining);
      remaining = "";
      break;
    }
    let breakAt = remaining.lastIndexOf(" ", maxCharacters);
    if (breakAt < maxCharacters * 0.45) breakAt = maxCharacters;
    lines.push(remaining.slice(0, breakAt).trimEnd());
    remaining = remaining.slice(breakAt).trimStart();
  }
  if (remaining && lines.length) lines[lines.length - 1] = `${lines[lines.length - 1].slice(0, Math.max(0, maxCharacters - 1))}…`;
  return lines;
}

const copy: Record<Locale, Record<string, string>> = {
  ru: {
    title: "Визуальный конструктор",
    subtitle: "Создавайте объекты, размещайте их и изменяйте на плане.",
    canvas: "Рабочая область",
    tray: "Новые объекты",
    trayHint: "Перетащите объект на план",
    add: "Добавить объект",
    first: "Создайте первый объект",
    firstHint: "Укажите тип, название и описание объекта. Размеры задаются в метрах.",
    name: "Название",
    description: "Описание",
    save: "Создать",
    cancel: "Отмена",
    type: "Тип объекта",
    enterprise: "Предприятие / завод",
    building: "Здание",
    shop: "Цех",
    plot: "Участок",
    box: "Бокс",
    warehouse: "Склад",
    workArea: "Рабочая зона",
    room: "Комната",
    office: "Офис",
    workstation: "Рабочее место",
    warehouse_area: "Складская зона",
    post: "Пост",
    station: "Станция",
    person: "Персона",
    custom: "Объект",
    edit: "Редактировать объект",
    pin: "Закрепить размер и положение",
    unpin: "Открепить объект",
    width: "Длина, м",
    height: "Ширина, м",
    x: "Координата X, м",
    y: "Координата Y, м",
    area: "Площадь",
    totalArea: "Общая площадь",
    meterUnit: "м",
    meters: "м²",
    rotation: "Поворот, °",
    rotateLeft: "Повернуть на 15° против часовой стрелки",
    rotateRight: "Повернуть на 15° по часовой стрелке",
    resetRotation: "Сбросить поворот",
    rotationValue: "Угол поворота объекта",
    details: "Подробнее",
    noSelection: "Объект не выбран",
    selectHint: "Выберите объект на полотне, чтобы увидеть его параметры.",
    objectDetails: "Подробная информация об объекте",
    saveChanges: "Сохранить изменения",
    locked: "Закрепить размер и положение",
    saveCanvas: "Сохранить план",
    savingCanvas: "Сохранение…",
    exportTitle: "Сохранить план на компьютере",
    printTitle: "Печать плана",
    printObjects: "Объекты",
    printObjectCount: "Всего объектов",
    printType: "Тип",
    printDimensions: "Размер, м",
    printArea: "Площадь",
    printCoordinates: "Координаты X / Y",
    printRotation: "Поворот",
    printDescription: "Описание",
    printStatus: "Состояние",
    printLocked: "Закреплён",
    printFree: "Не закреплён",
    exportFormat: "Формат файла",
    exportArea: "Что сохранить",
    wholePlan: "Весь план",
    eachLocation: "Каждую локацию на отдельной странице",
    oneLocation: "Одну локацию",
    chooseLocation: "Выберите локацию",
    saveFile: "Сохранить файл",
    saveDatabase: "Сохранить в базе",
    print: "Печать",
    printNow: "Открыть печать",
    saveFileHint: "Выберите папку в диалоге сохранения. Если браузер не поддерживает выбор папки, файл появится в загрузках.",
    printHint: "Можно напечатать весь план, каждую верхнюю локацию на отдельной странице или только выбранную локацию со вложенными объектами.",
    jsonFormat: "JSON — данные и размеры объектов",
    svgFormat: "SVG — векторный план",
    pngFormat: "PNG — изображение плана",
    exportCanceled: "Сохранение отменено",
    undo: "Отменить действие",
    redo: "Повторить действие",
    structureTitle: "Структура и связи",
    structureEmpty: "Структура предприятия пока не создана.",
    compass: "Компас: повернуть план на 90°",
    compassNorth: "Север сверху",
    compassEast: "Восток сверху",
    compassSouth: "Юг сверху",
    compassWest: "Запад сверху",
    unitHint: "Шаг сетки — 1 м; стены и углы объектов автоматически совмещаются.",
    trash: "Корзина",
    trashHint: "Перетащите объект сюда или выберите его и нажмите «В корзину».",
    emptyTrash: "Корзина пуста",
    restore: "Восстановить",
    delete: "Удалить навсегда",
    empty: "Очистить корзину",
    confirmDelete: "Удалить этот объект навсегда?",
    confirmEmpty: "Безвозвратно удалить все объекты из корзины?",
    saved: "Сохранено",
    error: "Не удалось выполнить действие",
    duplicateRoot: "На плане может быть только один корневой объект «Предприятие / завод».",
    parent: "Разместить внутри объекта",
    chooseParent: "Выберите объект-контейнер",
    rootObject: "Предприятие / завод — корневой объект.",
    noAvailableParents: "Нет подходящего объекта-контейнера. Сначала создайте объект разрешённого типа.",
    noCompany: "Сначала настройте предприятие",
    setup: "Открыть настройку предприятия",
    place: "Разместить",
    moveToTrash: "В корзину",
    rotate: "Поворот",
    zoomOut: "Уменьшить",
    zoomIn: "Увеличить",
    reset: "Сбросить вид",
    grid: "Сетка",
  },
  de: {
    title: "Visueller Konstruktor",
    subtitle: "Erstellen und bearbeiten Sie Objekte direkt im Plan.",
    canvas: "Arbeitsbereich",
    tray: "Neue Objekte",
    trayHint: "Objekt auf den Plan ziehen",
    add: "Objekt hinzufügen",
    first: "Erstes Objekt erstellen",
    firstHint: "Wählen Sie den Objekttyp und geben Sie Name und Beschreibung an. Maße werden in Metern festgelegt.",
    name: "Name",
    description: "Beschreibung",
    save: "Erstellen",
    cancel: "Abbrechen",
    type: "Objekttyp",
    enterprise: "Unternehmen / Werk",
    building: "Gebäude",
    shop: "Werkhalle",
    plot: "Bereich",
    box: "Box",
    warehouse: "Lager",
    workArea: "Arbeitsbereich",
    room: "Raum",
    office: "Büro",
    workstation: "Arbeitsplatz",
    warehouse_area: "Lagerbereich",
    post: "Arbeitsplatz",
    station: "Station",
    person: "Person",
    custom: "Objekt",
    edit: "Objekt bearbeiten",
    pin: "Größe und Position fixieren",
    unpin: "Objekt lösen",
    width: "Länge, m",
    height: "Breite, m",
    x: "Koordinate X, m",
    y: "Koordinate Y, m",
    area: "Fläche",
    totalArea: "Gesamtfläche",
    meterUnit: "m",
    meters: "m²",
    rotation: "Drehung, °",
    rotateLeft: "Um 15° gegen den Uhrzeigersinn drehen",
    rotateRight: "Um 15° im Uhrzeigersinn drehen",
    resetRotation: "Drehung zurücksetzen",
    rotationValue: "Objektdrehung",
    details: "Details",
    noSelection: "Kein Objekt ausgewählt",
    selectHint: "Wählen Sie ein Objekt im Plan, um seine Eigenschaften anzuzeigen.",
    objectDetails: "Objektdetails",
    saveChanges: "Änderungen speichern",
    locked: "Größe und Position fixieren",
    saveCanvas: "Plan speichern",
    savingCanvas: "Speichern…",
    exportTitle: "Plan auf dem Computer speichern",
    printTitle: "Plan drucken",
    printObjects: "Objekte",
    printObjectCount: "Objekte insgesamt",
    printType: "Typ",
    printDimensions: "Maße, m",
    printArea: "Fläche",
    printCoordinates: "Koordinaten X / Y",
    printRotation: "Drehung",
    printDescription: "Beschreibung",
    printStatus: "Status",
    printLocked: "Fixiert",
    printFree: "Nicht fixiert",
    exportFormat: "Dateiformat",
    exportArea: "Was soll gespeichert werden?",
    wholePlan: "Gesamter Plan",
    eachLocation: "Jeden Bereich auf einer eigenen Seite",
    oneLocation: "Ein Bereich",
    chooseLocation: "Bereich auswählen",
    saveFile: "Datei speichern",
    saveDatabase: "In der Datenbank speichern",
    print: "Drucken",
    printNow: "Druckdialog öffnen",
    saveFileHint: "Wählen Sie den Ordner im Speicherdialog. Wenn der Browser die Ordnerauswahl nicht unterstützt, wird die Datei heruntergeladen.",
    printHint: "Drucken Sie den gesamten Plan, jeden obersten Bereich auf einer eigenen Seite oder nur einen ausgewählten Bereich mit seinen Objekten.",
    jsonFormat: "JSON — Objektdaten und Maße",
    svgFormat: "SVG — Vektorplan",
    pngFormat: "PNG — Planbild",
    exportCanceled: "Speichern abgebrochen",
    undo: "Aktion rückgängig machen",
    redo: "Aktion wiederholen",
    structureTitle: "Struktur und Verbindungen",
    structureEmpty: "Die Unternehmensstruktur wurde noch nicht erstellt.",
    compass: "Kompass: Plan um 90° drehen",
    compassNorth: "Norden oben",
    compassEast: "Osten oben",
    compassSouth: "Süden oben",
    compassWest: "Westen oben",
    unitHint: "Rasterabstand 1 m; Objektkanten und Ecken rasten automatisch ein.",
    trash: "Papierkorb",
    trashHint: "Objekt hierher ziehen oder auswählen und „In Papierkorb“ wählen.",
    emptyTrash: "Der Papierkorb ist leer",
    restore: "Wiederherstellen",
    delete: "Endgültig löschen",
    empty: "Papierkorb leeren",
    confirmDelete: "Dieses Objekt endgültig löschen?",
    confirmEmpty: "Alle Objekte im Papierkorb endgültig löschen?",
    saved: "Gespeichert",
    error: "Aktion fehlgeschlagen",
    duplicateRoot: "Der Plan kann nur ein Wurzelelement „Unternehmen / Werk“ enthalten.",
    parent: "Innerhalb des Objekts platzieren",
    chooseParent: "Containerobjekt auswählen",
    rootObject: "Unternehmen / Werk ist das Wurzelelement.",
    noAvailableParents: "Kein passendes Containerobjekt. Erstellen Sie zuerst ein Objekt eines zulässigen Typs.",
    noCompany: "Richten Sie zuerst das Unternehmen ein",
    setup: "Unternehmen einrichten",
    place: "Platzieren",
    moveToTrash: "In Papierkorb",
    rotate: "Drehen",
    zoomOut: "Verkleinern",
    zoomIn: "Vergrößern",
    reset: "Ansicht zurücksetzen",
    grid: "Raster",
  },
  en: {
    title: "Visual builder",
    subtitle: "Create objects and arrange or resize them on the plan.",
    canvas: "Workspace",
    tray: "New objects",
    trayHint: "Drag an object onto the plan",
    add: "Add object",
    first: "Create your first object",
    firstHint: "Choose an object type, then enter a name and description. Dimensions are set in metres.",
    name: "Name",
    description: "Description",
    save: "Create",
    cancel: "Cancel",
    type: "Object type",
    enterprise: "Enterprise / plant",
    building: "Building",
    shop: "Shop",
    plot: "Section",
    box: "Bay",
    warehouse: "Warehouse",
    workArea: "Work area",
    room: "Room",
    office: "Office",
    workstation: "Workstation",
    warehouse_area: "Warehouse area",
    post: "Post",
    station: "Station",
    person: "Person",
    custom: "Object",
    edit: "Edit object",
    pin: "Lock size and position",
    unpin: "Unlock object",
    width: "Length, m",
    height: "Width, m",
    x: "X coordinate, m",
    y: "Y coordinate, m",
    area: "Area",
    totalArea: "Total area",
    meterUnit: "m",
    meters: "m²",
    rotation: "Rotation, °",
    rotateLeft: "Rotate 15° counterclockwise",
    rotateRight: "Rotate 15° clockwise",
    resetRotation: "Reset rotation",
    rotationValue: "Object rotation",
    details: "Details",
    noSelection: "No object selected",
    selectHint: "Select an object on the plan to see its information.",
    objectDetails: "Object details",
    saveChanges: "Save changes",
    locked: "Lock size and position",
    saveCanvas: "Save plan",
    savingCanvas: "Saving…",
    exportTitle: "Save plan to your computer",
    printTitle: "Print plan",
    printObjects: "Objects",
    printObjectCount: "Total objects",
    printType: "Type",
    printDimensions: "Size, m",
    printArea: "Area",
    printCoordinates: "Coordinates X / Y",
    printRotation: "Rotation",
    printDescription: "Description",
    printStatus: "Status",
    printLocked: "Locked",
    printFree: "Not locked",
    exportFormat: "File format",
    exportArea: "What to save",
    wholePlan: "Entire plan",
    eachLocation: "Each location on a separate page",
    oneLocation: "One location",
    chooseLocation: "Choose a location",
    saveFile: "Save file",
    saveDatabase: "Save to database",
    print: "Print",
    printNow: "Open print dialog",
    saveFileHint: "Choose a folder in the save dialog. If your browser does not support folder selection, the file will be downloaded.",
    printHint: "Print the entire plan, each top-level location on its own page, or one selected location with its nested objects.",
    jsonFormat: "JSON — object data and dimensions",
    svgFormat: "SVG — vector plan",
    pngFormat: "PNG — plan image",
    exportCanceled: "Save canceled",
    undo: "Undo action",
    redo: "Redo action",
    structureTitle: "Structure and relationships",
    structureEmpty: "The enterprise structure has not been created yet.",
    compass: "Compass: rotate plan 90°",
    compassNorth: "North up",
    compassEast: "East up",
    compassSouth: "South up",
    compassWest: "West up",
    unitHint: "Grid spacing is 1 m; object edges and corners snap together automatically.",
    trash: "Recycle bin",
    trashHint: "Drag an object here, or select it and choose “Move to recycle bin”.",
    emptyTrash: "The recycle bin is empty",
    restore: "Restore",
    delete: "Delete permanently",
    empty: "Empty recycle bin",
    confirmDelete: "Permanently delete this object?",
    confirmEmpty: "Permanently delete all objects in the recycle bin?",
    saved: "Saved",
    error: "Action failed",
    duplicateRoot: "The plan can contain only one root object: Enterprise / plant.",
    parent: "Place inside object",
    chooseParent: "Choose a container object",
    rootObject: "Enterprise / plant is the root object.",
    noAvailableParents: "No compatible container object. Create an object of an allowed type first.",
    noCompany: "Set up the enterprise first",
    setup: "Open enterprise setup",
    place: "Place",
    moveToTrash: "Move to recycle bin",
    rotate: "Rotate",
    zoomOut: "Zoom out",
    zoomIn: "Zoom in",
    reset: "Reset view",
    grid: "Grid",
  },
};

const initialView: View = { scale: 1, x: 0, y: 0, rotation: 0, grid: true };
const GRID_METERS = 40;
const CANVAS_WIDTH = 12000;
const CANVAS_HEIGHT = 8000;
const MIN_SIZE = GRID_METERS;
const MIN_VIEW_SCALE = 0.1;
const MAX_VIEW_SCALE = 5;
const ZOOM_STEP = 1.2;
const objectTypes = ["enterprise", "building", "shop", "plot", "box", "warehouse", "work_area", "room", "office", "workstation", "warehouse_area", "post", "station", "person"] as const;

export function EnterpriseCadCanvas({ locale }: { locale: Locale }) {
  const t = copy[locale];
  const [company, setCompany] = useState<Company | null>(null);
  const [objects, setObjects] = useState<CanvasObject[]>([]);
  const [trash, setTrash] = useState<CanvasObject[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingCanvas, setSavingCanvas] = useState(false);
  const [saveNotice, setSaveNotice] = useState("");
  const [history, setHistory] = useState<{ past: HistoryEntry[]; future: HistoryEntry[] }>({ past: [], future: [] });
  const [historyBusy, setHistoryBusy] = useState(false);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(false);
  const [trashOpen, setTrashOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [printOpen, setPrintOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>("svg");
  const [exportScope, setExportScope] = useState<ExportScope>("all");
  const [exportLocationId, setExportLocationId] = useState("");
  const [printScope, setPrintScope] = useState<PrintScope>("all");
  const [printLocationId, setPrintLocationId] = useState("");
  const [editing, setEditing] = useState<CanvasObject | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [objectType, setObjectType] = useState<string>("enterprise");
  const [parentId, setParentId] = useState("");
  const [lengthMeters, setLengthMeters] = useState(5);
  const [widthMeters, setWidthMeters] = useState(3);
  const [xMeters, setXMeters] = useState(0);
  const [yMeters, setYMeters] = useState(0);
  const [rotation, setRotation] = useState(0);
  const [editingLocked, setEditingLocked] = useState(false);
  const [view, setView] = useState<View>(initialView);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const viewportRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const historyRef = useRef(history);

  const refresh = useCallback(async (companyId: string) => {
    const [active, removed] = await Promise.all([
      api<CanvasObject[]>(`/api/v1/companies/${companyId}/canvas-objects`),
      api<CanvasObject[]>(`/api/v1/companies/${companyId}/canvas-objects/trash`),
    ]);
    setObjects(active);
    setTrash(removed);
  }, []);

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const companies = await api<Company[]>("/api/v1/companies");
        if (!active) return;
        const current = companies[0] ?? null;
        setCompany(current);
        if (current) await refresh(current.id);
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : t.error);
      } finally {
        if (active) setLoading(false);
      }
    }
    try {
      const saved = JSON.parse(localStorage.getItem("workflow-cad-view") || "null") as Partial<View> | null;
      if (saved) {
        setView({
          ...initialView,
          scale: typeof saved.scale === "number" && Number.isFinite(saved.scale) ? Math.max(MIN_VIEW_SCALE, Math.min(MAX_VIEW_SCALE, saved.scale)) : 1,
          x: typeof saved.x === "number" && Number.isFinite(saved.x) ? saved.x : 0,
          y: typeof saved.y === "number" && Number.isFinite(saved.y) ? saved.y : 0,
          rotation: typeof saved.rotation === "number" && Number.isFinite(saved.rotation) ? saved.rotation : 0,
          grid: typeof saved.grid === "boolean" ? saved.grid : initialView.grid,
        });
      }
    } catch (reason) {
      console.warn("Could not restore the visual builder view.", reason);
    }
    void initialize();
    return () => { active = false; };
  }, [refresh, t.error]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const observer = new ResizeObserver(([entry]) => {
      setViewportSize({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(viewport);
    return () => observer.disconnect();
  }, [loading]);

  useEffect(() => {
    localStorage.setItem("workflow-cad-view", JSON.stringify(view));
  }, [view]);

  const selected = useMemo(() => objects.find((object) => object.id === selectedId) ?? null, [objects, selectedId]);
  const placedObjects = useMemo(() => objects.filter((object) => object.placed), [objects]);
  const locations = useMemo(() => topLevelLocations(placedObjects), [placedObjects]);
  const objectParents = useMemo(() => canvasObjectParents(objects), [objects]);
  const parentCandidates = useMemo(() => {
    const descendants = new Set<string>();
    let changed = true;
    while (changed) {
      changed = false;
      for (const [childId, parent] of objectParents) {
        if ((parent.id === editing?.id || descendants.has(parent.id)) && !descendants.has(childId)) {
          descendants.add(childId);
          changed = true;
        }
      }
    }
    return objects.filter((candidate) =>
      candidate.id !== editing?.id &&
      !descendants.has(candidate.id) &&
      isAllowedCanvasParent(candidate.object_type, objectType),
    );
  }, [editing?.id, objectParents, objectType, objects]);
  function recordHistory(before: CanvasSnapshot, after: CanvasSnapshot) {
    const comparable = (items: CanvasSnapshot) => items.map(({ id, name, description, object_type, parent_id, x, y, width, height, rotation, placed, locked }) => ({
      id, name, description, object_type, parent_id, x, y, width, height, rotation, placed, locked,
    }));
    if (JSON.stringify(comparable(before)) === JSON.stringify(comparable(after))) return;
    const next = {
      past: [...historyRef.current.past, { before: before.map((item) => ({ ...item })), after: after.map((item) => ({ ...item })) }].slice(-100),
      future: [],
    };
    historyRef.current = next;
    setHistory(next);
  }

  async function applyHistorySnapshot(target: CanvasSnapshot) {
    if (!company) return;
    const targetById = new Map(target.map((item) => [item.id, item]));
    const currentById = new Map(objects.map((item) => [item.id, item]));
    const trashById = new Map(trash.map((item) => [item.id, item]));
    for (const current of objects) {
      if (targetById.has(current.id)) continue;
      await api(`/api/v1/companies/${company.id}/canvas-objects/${current.id}/archive`, { method: "POST" });
    }
    for (const desired of target) {
      const current = currentById.get(desired.id);
      if (!current) {
        if (!trashById.has(desired.id)) throw new Error(t.error);
        await api(`/api/v1/companies/${company.id}/canvas-objects/${desired.id}/restore`, { method: "POST" });
      }
      await api<CanvasObject>(`/api/v1/companies/${company.id}/canvas-objects/${desired.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: desired.name,
          description: desired.description,
          object_type: desired.object_type,
          parent_id: desired.parent_id,
          x: desired.x,
          y: desired.y,
          width: desired.width,
          height: desired.height,
          rotation: desired.rotation,
          placed: desired.placed,
          locked: desired.locked,
        }),
      });
    }
    await refresh(company.id);
  }

  async function moveHistory(direction: "undo" | "redo") {
    if (historyBusy || !company) return;
    const current = historyRef.current;
    const entry = direction === "undo" ? current.past[current.past.length - 1] : current.future[current.future.length - 1];
    if (!entry) return;
    setHistoryBusy(true);
    try {
      await applyHistorySnapshot(direction === "undo" ? entry.before : entry.after);
      const next = direction === "undo"
        ? { past: current.past.slice(0, -1), future: [...current.future, entry] }
        : { past: [...current.past, entry], future: current.future.slice(0, -1) };
      historyRef.current = next;
      setHistory(next);
      setSaveNotice("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
      await refresh(company.id);
    } finally {
      setHistoryBusy(false);
    }
  }

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey)) return;
      if (event.target instanceof HTMLElement && event.target.closest("input,textarea,select,[contenteditable=true]")) return;
      if (event.key.toLowerCase() === "z") {
        event.preventDefault();
        void moveHistory(event.shiftKey ? "redo" : "undo");
      } else if (event.key.toLowerCase() === "y") {
        event.preventDefault();
        void moveHistory("redo");
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [history, historyBusy, company, objects, trash]);

  const matrix = useMemo(() => {
    const angle = view.rotation * Math.PI / 180;
    const a = view.scale * Math.cos(angle);
    const b = view.scale * Math.sin(angle);
    const c = -b;
    const d = a;
    const e = viewportSize.width / 2 + view.x - a * CANVAS_WIDTH / 2 - c * CANVAS_HEIGHT / 2;
    const f = viewportSize.height / 2 + view.y - b * CANVAS_WIDTH / 2 - d * CANVAS_HEIGHT / 2;
    return `matrix(${a},${b},${c},${d},${e},${f})`;
  }, [view, viewportSize]);

  function toWorld(clientX: number, clientY: number) {
    const rect = viewportRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    const dx = clientX - rect.left - viewportSize.width / 2 - view.x;
    const dy = clientY - rect.top - viewportSize.height / 2 - view.y;
    const angle = view.rotation * Math.PI / 180;
    return {
      x: (Math.cos(angle) * dx + Math.sin(angle) * dy) / view.scale + CANVAS_WIDTH / 2,
      y: (-Math.sin(angle) * dx + Math.cos(angle) * dy) / view.scale + CANVAS_HEIGHT / 2,
    };
  }

  function startObjectDrag(event: ReactPointerEvent<HTMLElement>, object: CanvasObject, mode: "move" | "resize", handle?: string) {
    if (event.button !== 0 || object.locked) return;
    event.preventDefault();
    event.stopPropagation();
    setSaveNotice("");
    setSelectedId(object.id);
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = {
      pointerId: event.pointerId,
      mode,
      objectId: object.id,
      handle,
      startX: event.clientX,
      startY: event.clientY,
      geometry: { x: object.x, y: object.y, width: object.width, height: object.height, rotation: object.rotation },
    };
  }

  function startPan(event: ReactPointerEvent<HTMLDivElement>) {
    if (event.button !== 0 && event.button !== 2) return;
    if (event.target instanceof Element && event.target.closest(".cad-object,button")) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = {
      pointerId: event.pointerId,
      mode: event.button === 2 ? "rotate" : "pan",
      startX: event.clientX,
      startY: event.clientY,
      view,
    };
  }

  function updateDrag(event: ReactPointerEvent<HTMLElement>) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (drag.mode === "pan" && drag.view) {
      setView((current) => ({ ...current, x: drag.view!.x + dx, y: drag.view!.y + dy }));
      return;
    }
    if (drag.mode === "rotate" && drag.view) {
      setView((current) => ({ ...current, rotation: (drag.view!.rotation + dx * 0.35) % 360 }));
      return;
    }
    if (!drag.geometry || !drag.objectId) return;
    const angle = view.rotation * Math.PI / 180;
    const worldX = (Math.cos(angle) * dx + Math.sin(angle) * dy) / view.scale;
    const worldY = (-Math.sin(angle) * dx + Math.cos(angle) * dy) / view.scale;
    const origin = drag.geometry;
    let { x, y, width, height } = origin;
    const handle = drag.handle ?? "";
    if (drag.mode === "move") {
      x = Math.round((x + worldX) / GRID_METERS) * GRID_METERS;
      y = Math.round((y + worldY) / GRID_METERS) * GRID_METERS;
      const snapped = snapToNearbyEdges(drag.objectId, x, y, width, height);
      x = snapped.x;
      y = snapped.y;
    } else {
      const objectAngle = origin.rotation * Math.PI / 180;
      const combinedAngle = (view.rotation + origin.rotation) * Math.PI / 180;
      const localX = (Math.cos(combinedAngle) * dx + Math.sin(combinedAngle) * dy) / view.scale;
      const localY = (-Math.sin(combinedAngle) * dx + Math.cos(combinedAngle) * dy) / view.scale;
      if (handle.includes("w")) width = Math.max(MIN_SIZE, Math.round((origin.width - localX) / GRID_METERS) * GRID_METERS);
      if (handle.includes("e")) width = Math.max(MIN_SIZE, Math.round((origin.width + localX) / GRID_METERS) * GRID_METERS);
      if (handle.includes("n")) height = Math.max(MIN_SIZE, Math.round((origin.height - localY) / GRID_METERS) * GRID_METERS);
      if (handle.includes("s")) height = Math.max(MIN_SIZE, Math.round((origin.height + localY) / GRID_METERS) * GRID_METERS);
      const offsetX = handle.includes("w") ? (origin.width - width) / 2 : handle.includes("e") ? (width - origin.width) / 2 : 0;
      const offsetY = handle.includes("n") ? (origin.height - height) / 2 : handle.includes("s") ? (height - origin.height) / 2 : 0;
      const centerX = origin.x + origin.width / 2 + Math.cos(objectAngle) * offsetX - Math.sin(objectAngle) * offsetY;
      const centerY = origin.y + origin.height / 2 + Math.sin(objectAngle) * offsetX + Math.cos(objectAngle) * offsetY;
      x = Math.round((centerX - width / 2) / GRID_METERS) * GRID_METERS;
      y = Math.round((centerY - height / 2) / GRID_METERS) * GRID_METERS;
    }
    setObjects((items) => items.map((item) => item.id === drag.objectId ? { ...item, x, y, width, height } : item));
  }

  async function finishDrag(event: ReactPointerEvent<HTMLElement>) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    dragRef.current = null;
    if (drag.objectId && company) {
      const changed = objects.find((item) => item.id === drag.objectId);
      if (changed) {
        const geometry = {
          x: Math.round(changed.x / GRID_METERS) * GRID_METERS,
          y: Math.round(changed.y / GRID_METERS) * GRID_METERS,
          width: Math.max(MIN_SIZE, Math.round(changed.width / GRID_METERS) * GRID_METERS),
          height: Math.max(MIN_SIZE, Math.round(changed.height / GRID_METERS) * GRID_METERS),
        };
        const before = objects.map((item) => item.id === changed.id ? { ...item, ...drag.geometry } : item);
        const candidate = before.map((item) => item.id === changed.id ? { ...item, ...geometry, placed: true } : item);
        try {
          const updated = await api<CanvasObject>(`/api/v1/companies/${company.id}/canvas-objects/${changed.id}`, {
            method: "PATCH",
            body: JSON.stringify({
              ...geometry,
              placed: true,
            }),
          });
          const after = before.map((item) => item.id === updated.id ? updated : item);
          setObjects((items) => items.map((item) => item.id === updated.id ? updated : item));
          recordHistory(before, after);
        } catch (reason) {
          setError(reason instanceof Error ? reason.message : t.error);
          await refresh(company.id);
        }
      }
    }
  }

  function zoomAt(nextScale: number, clientX: number, clientY: number) {
    const rect = viewportRef.current?.getBoundingClientRect();
    if (!rect) return;
    const scale = Math.max(MIN_VIEW_SCALE, Math.min(MAX_VIEW_SCALE, nextScale));
    const px = clientX - rect.left - viewportSize.width / 2;
    const py = clientY - rect.top - viewportSize.height / 2;
    const ratio = scale / view.scale;
    setView((current) => ({ ...current, x: px - ratio * (px - current.x), y: py - ratio * (py - current.y), scale }));
  }

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const onWheel = (event: globalThis.WheelEvent) => {
      event.preventDefault();
      zoomAt(view.scale * (event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP), event.clientX, event.clientY);
    };
    viewport.addEventListener("wheel", onWheel, { passive: false });
    return () => viewport.removeEventListener("wheel", onWheel);
  }, [view, viewportSize]);

  function zoomToCenter(nextScale: number) {
    const rect = viewportRef.current?.getBoundingClientRect();
    if (rect) zoomAt(nextScale, rect.left + rect.width / 2, rect.top + rect.height / 2);
  }

  async function createObject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!company) return;
    if (isCanvasRootType(objectType) && objects.some((object) => isCanvasRootType(object.object_type))) {
      setError(t.duplicateRoot);
      return;
    }
    try {
      const created = await api<CanvasObject>(`/api/v1/companies/${company.id}/canvas-objects`, {
        method: "POST",
        body: JSON.stringify({ name, description, object_type: objectType, parent_id: isCanvasRootType(objectType) ? null : parentId }),
      });
      recordHistory(objects, [...objects, created]);
      setObjects((items) => [...items, created]);
      closeEditor();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
    }
  }

  function openCreate() {
    setEditing(null);
    setName("");
    setDescription("");
    const hasRoot = objects.some((object) => isCanvasRootType(object.object_type));
    setObjectType(hasRoot ? "building" : "enterprise");
    setParentId("");
    setLengthMeters(5);
    setWidthMeters(3);
    setXMeters(0);
    setYMeters(0);
    setRotation(0);
    setModal(true);
  }

  function openEdit(object: CanvasObject) {
    setEditing(object);
    setName(object.name);
    setDescription(object.description ?? "");
    setObjectType(object.object_type);
    setParentId(object.parent_id ?? objectParents.get(object.id)?.id ?? "");
    setLengthMeters(object.width / GRID_METERS);
    setWidthMeters(object.height / GRID_METERS);
    setXMeters(object.x / GRID_METERS);
    setYMeters(object.y / GRID_METERS);
    setRotation(object.rotation);
    setEditingLocked(object.locked);
    setModal(true);
  }

  function closeEditor() {
    setModal(false);
    setEditing(null);
  }

  async function saveEditedObject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    if (isCanvasRootType(objectType) && !isCanvasRootType(editing.object_type) && objects.some((object) => object.id !== editing.id && isCanvasRootType(object.object_type))) {
      setError(t.duplicateRoot);
      return;
    }
    const saved = await patchObject(editing.id, {
      name,
      description,
      object_type: objectType,
      parent_id: isCanvasRootType(objectType) ? null : parentId,
      x: Math.round(xMeters) * GRID_METERS,
      y: Math.round(yMeters) * GRID_METERS,
      width: Math.max(1, Math.round(lengthMeters)) * GRID_METERS,
      height: Math.max(1, Math.round(widthMeters)) * GRID_METERS,
      rotation,
      locked: editingLocked,
    });
    if (saved) closeEditor();
  }

  function typeLabel(value: string) {
    const role = canvasObjectRole(value) ?? value;
    return t[role === "work_area" ? "workArea" : role] ?? value;
  }

  function snapToNearbyEdges(id: string, x: number, y: number, width: number, height: number) {
    let snappedX = x;
    let snappedY = y;
    let bestX = GRID_METERS * 0.25;
    let bestY = GRID_METERS * 0.25;
    for (const other of objects) {
      if (other.id === id || !other.placed) continue;
      const verticalOverlap = y + height > other.y - GRID_METERS * 0.25 && y < other.y + other.height + GRID_METERS * 0.25;
      const horizontalOverlap = x + width > other.x - GRID_METERS * 0.25 && x < other.x + other.width + GRID_METERS * 0.25;
      if (verticalOverlap) {
        for (const candidate of [other.x - width, other.x + other.width]) {
          const distance = Math.abs(candidate - snappedX);
          if (distance < bestX) { bestX = distance; snappedX = candidate; }
        }
      }
      if (horizontalOverlap) {
        for (const candidate of [other.y - height, other.y + other.height]) {
          const distance = Math.abs(candidate - snappedY);
          if (distance < bestY) { bestY = distance; snappedY = candidate; }
        }
      }
    }
    return { x: snappedX, y: snappedY };
  }

  async function patchObject(id: string, changes: Partial<CanvasObject>) {
    if (!company) return false;
    setSaveNotice("");
    try {
      const updated = await api<CanvasObject>(`/api/v1/companies/${company.id}/canvas-objects/${id}`, {
        method: "PATCH",
        body: JSON.stringify(changes),
      });
      const before = objects;
      const after = objects.map((item) => item.id === id ? updated : item);
      recordHistory(before, after);
      setObjects((items) => items.map((item) => item.id === id ? updated : item));
      return true;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
      return false;
    }
  }

  async function saveCanvas() {
    if (!company || savingCanvas) return;
    setSavingCanvas(true);
    setSaveNotice("");
    try {
      const saved = await Promise.all(objects.map((object) => api<CanvasObject>(`/api/v1/companies/${company.id}/canvas-objects/${object.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: object.name,
          description: object.description,
          object_type: object.object_type,
          parent_id: object.parent_id,
          x: object.x,
          y: object.y,
          width: object.width,
          height: object.height,
          rotation: object.rotation,
          placed: object.placed,
          locked: object.locked,
        }),
      })));
      setObjects(saved);
      setSaveNotice(t.saved);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
    } finally {
      setSavingCanvas(false);
    }
  }

  function makePlanSvg(items: CanvasObject[], title: string) {
    if (!items.length) throw new Error(t.structureEmpty);
    const bounds = items.map(objectBounds);
    const padding = 40;
    const left = Math.min(...bounds.map((item) => item.left)) - padding;
    const top = Math.min(...bounds.map((item) => item.top)) - padding;
    const right = Math.max(...bounds.map((item) => item.right)) + padding;
    const bottom = Math.max(...bounds.map((item) => item.bottom)) + padding;
    const width = Math.max(1, right - left);
    const height = Math.max(1, bottom - top);
    const shapes = items.map((object) => {
      const x = object.x;
      const y = object.y;
      const textWidth = Math.max(0, object.width - 28);
      const safeName = escapeXml(fitCanvasLabel(object.name, textWidth, 18));
      const safeDescription = escapeXml(fitCanvasLabel(object.description ?? "", textWidth, 14));
      const safeType = escapeXml(typeLabel(object.object_type));
      const radius = object.object_type === "person" ? Math.min(18, object.width / 2, object.height / 2) : 6;
      const rotation = object.rotation ? ` transform="rotate(${object.rotation} ${x + object.width / 2} ${y + object.height / 2})"` : "";
      const textX = x + 14;
      return `<g${rotation}><rect x="${x}" y="${y}" width="${object.width}" height="${object.height}" rx="${radius}" fill="#f7faf8" stroke="#236e58" stroke-width="2"/><text x="${textX}" y="${y + 27}" fill="#326c56" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700">${safeType}</text><text x="${textX}" y="${y + 52}" fill="#172522" font-family="Segoe UI, sans-serif" font-size="18" font-weight="700">${safeName}</text>${safeDescription ? `<text x="${textX}" y="${y + 74}" fill="#55635d" font-family="Segoe UI, sans-serif" font-size="14">${safeDescription}</text>` : ""}</g>`;
    }).join("");
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="${left} ${top} ${width} ${height}" role="img" aria-label="${escapeXml(title)}"><rect x="${left}" y="${top}" width="${width}" height="${height}" fill="#ffffff"/>${shapes}</svg>`;
  }

  async function svgToPng(svg: string) {
    const source = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(source);
    try {
      const image = new Image();
      image.src = url;
      await new Promise<void>((resolve, reject) => {
        image.onload = () => resolve();
        image.onerror = () => reject(new Error(t.error));
      });
      const scale = Math.min(2, 8192 / image.width, 8192 / image.height);
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(image.width * scale));
      canvas.height = Math.max(1, Math.round(image.height * scale));
      const context = canvas.getContext("2d");
      if (!context) throw new Error(t.error);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      return await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error(t.error)), "image/png");
      });
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async function exportPlan() {
    const location = placedObjects.find((item) => item.id === exportLocationId);
    if (exportScope === "location" && !location) {
      setError(t.chooseLocation);
      return;
    }
    const selectedObjects = exportScope === "all" ? placedObjects : objectsAtLocation(placedObjects, location!);
    if (!selectedObjects.length) {
      setError(t.structureEmpty);
      return;
    }
    const extension = exportFormat;
    const mimeTypes: Record<ExportFormat, string> = { json: "application/json", svg: "image/svg+xml", png: "image/png" };
    const safeCompanyName = company?.name.replace(/[<>:"/\\|?*\x00-\x1f]/g, "-").trim() || "enterprise";
    const safeLocationName = location?.name.replace(/[<>:"/\\|?*\x00-\x1f]/g, "-").trim() || "location";
    const namePart = exportScope === "location" ? `-${safeLocationName}` : "";
    const filename = `${safeCompanyName}${namePart}-plan.${extension}`;
    const pickerWindow = window as SavePickerWindow;
    setError("");
    try {
      const fileHandle = pickerWindow.showSaveFilePicker
        ? await pickerWindow.showSaveFilePicker({
          suggestedName: filename,
          types: [{ description: extension.toUpperCase(), accept: { [mimeTypes[extension]]: [`.${extension}`] } }],
        })
        : null;
      const title = exportScope === "location" ? location!.name : company?.name ?? t.canvas;
      const svg = makePlanSvg(selectedObjects, title);
      let file: Blob;
      if (exportFormat === "svg") file = new Blob([svg], { type: mimeTypes.svg });
      else if (exportFormat === "png") file = await svgToPng(svg);
      else file = new Blob([JSON.stringify({
        format: "workflow-production-cad",
        version: 1,
        company,
        exportedAt: new Date().toISOString(),
        scope: exportScope,
        location: location ?? null,
        objects: selectedObjects,
      }, null, 2)], { type: mimeTypes.json });

      if (fileHandle) {
        const writable = await fileHandle.createWritable();
        await writable.write(file);
        await writable.close();
      } else {
        const url = URL.createObjectURL(file);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = filename;
        anchor.click();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
      setSaveNotice(t.saved);
      setExportOpen(false);
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      setError(reason instanceof Error ? reason.message : t.error);
    }
  }

  function printPlan() {
    let pages: { title: string; items: CanvasObject[] }[];
    if (printScope === "all") pages = [{ title: company?.name ?? t.canvas, items: placedObjects }];
    else if (printScope === "each") pages = locations.map((location) => ({
      title: location.name,
      items: objectsAtLocation(placedObjects, location),
    }));
    else {
      const location = placedObjects.find((item) => item.id === printLocationId);
      if (!location) {
        setError(t.chooseLocation);
        return;
      }
      pages = [{ title: location.name, items: objectsAtLocation(placedObjects, location) }];
    }
    if (!pages.length || pages.some((page) => page.items.length === 0)) {
      setError(t.structureEmpty);
      return;
    }
    const printWindow = window.open("", "_blank");
    if (!printWindow) {
      setError(t.error);
      return;
    }
    try {
      const formatNumber = (value: number) => Number(value.toFixed(2)).toString();
      const markup = pages.map(({ title, items }) => {
        const children = new Map<string, CanvasObject[]>();
        const parents = canvasObjectParents(items);
        for (const object of items) {
          const parent = parents.get(object.id);
          const key = parent?.id ?? "print-root";
          children.set(key, [...(children.get(key) ?? []), object]);
        }
        const renderBranch = (object: CanvasObject): string => {
          const length = object.width / GRID_METERS;
          const width = object.height / GRID_METERS;
          const nested = children.get(object.id) ?? [];
          return `<li><div class="tree-node"><div class="tree-name"><strong>${escapeXml(object.name)}</strong><small>${escapeXml(typeLabel(object.object_type))}</small></div><div class="tree-measure">${formatNumber(length)} × ${formatNumber(width)} ${t.meterUnit}<span>${formatNumber(length * width)} ${t.meters}</span></div></div>${nested.length ? `<ul>${nested.map(renderBranch).join("")}</ul>` : ""}</li>`;
        };
        const tree = (children.get("print-root") ?? []).map(renderBranch).join("");
        const details = `<section class="print-details"><h2>${escapeXml(t.printObjects)} <small>· ${escapeXml(t.printDimensions)} · ${escapeXml(t.printArea)}</small></h2><ul class="tree-root">${tree}</ul></section>`;
        return `<section class="print-page"><header><h1>${escapeXml(title)}</h1><p>${items.length} · ${escapeXml(t.printObjects)}</p></header><div class="print-content"><div class="print-plan">${makePlanSvg(items, title)}</div>${details}</div></section>`;
      }).join("");
      printWindow.document.open();
      printWindow.document.write(`<!doctype html><html><head><title>${escapeXml(t.printTitle)}</title><style>
        @page{size:A4 landscape;margin:8mm}*{box-sizing:border-box}html,body{margin:0;font:10px "Segoe UI",sans-serif;color:#172522}
        .print-page{width:281mm;height:194mm;page-break-after:always;break-after:page;display:grid;grid-template-rows:auto minmax(0,1fr);gap:3mm;overflow:hidden}
        .print-page:last-child{page-break-after:auto;break-after:auto}
        .print-page>header{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid #87978f;padding:0 0 2mm}
        h1{font-size:17px;margin:0}.print-page>header p{margin:0;color:#52645d}
        .print-content{display:grid;grid-template-columns:minmax(0,1fr) 88mm;gap:3mm;min-height:0}
        .print-plan{min-width:0;min-height:0;display:flex;justify-content:center;overflow:hidden;border:1px solid #aebbb4;padding:2mm}
        .print-plan svg{width:100%;height:100%;object-fit:contain}
        .print-details{min-width:0;overflow:hidden}.print-details h2{margin:0 0 2mm;font-size:11px}.print-details h2 small{font-size:8px;font-weight:400;color:#52645d}
        .tree-root,.tree-root ul{list-style:none;margin:0;padding:0}.tree-root ul{margin-left:3mm;padding-left:2mm;border-left:1px solid #aebbb4}
        .tree-root li{position:relative;margin:0;padding:0}.tree-root ul>li:before{content:"";position:absolute;left:-2mm;top:4mm;width:2mm;border-top:1px solid #aebbb4}
        .tree-node{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:2mm;padding:1mm 0;border-bottom:1px solid #d5ded9;break-inside:avoid}
        .tree-name{min-width:0;overflow-wrap:anywhere}.tree-name strong,.tree-name small{display:block}.tree-name strong{font-size:9px;line-height:1.15}.tree-name small{margin-top:.3mm;color:#52645d;font-size:7px}
        .tree-measure{text-align:right;white-space:nowrap;font-size:8px}.tree-measure span{display:block;margin-top:.3mm;color:#52645d;font-size:7px}
        </style></head><body>${markup}</body></html>`);
      printWindow.document.close();
      printWindow.focus();
      window.setTimeout(() => printWindow.print(), 250);
      setPrintOpen(false);
    } catch (reason) {
      printWindow.close();
      setError(reason instanceof Error ? reason.message : t.error);
    }
  }

  async function archiveObject(id: string) {
    if (!company) return;
    setSaveNotice("");
    try {
      const archived = await api<CanvasObject>(`/api/v1/companies/${company.id}/canvas-objects/${id}/archive`, { method: "POST" });
      recordHistory(objects, objects.filter((item) => item.id !== id));
      setObjects((items) => items.filter((item) => item.id !== id));
      setTrash((items) => [archived, ...items]);
      setSelectedId(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
    }
  }

  async function restoreObject(id: string) {
    if (!company) return;
    try {
      const restored = await api<CanvasObject>(`/api/v1/companies/${company.id}/canvas-objects/${id}/restore`, { method: "POST" });
      recordHistory(objects, [...objects, restored]);
      setTrash((items) => items.filter((item) => item.id !== id));
      setObjects((items) => [...items, restored]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
    }
  }

  async function purgeObject(id: string) {
    if (!company || !window.confirm(t.confirmDelete)) return;
    try {
      await api(`/api/v1/companies/${company.id}/canvas-objects/${id}/purge`, { method: "POST" });
      setTrash((items) => items.filter((item) => item.id !== id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
    }
  }

  async function emptyTrash() {
    if (!company || !trash.length || !window.confirm(t.confirmEmpty)) return;
    try {
      const byId = new Map(trash.map((item) => [item.id, item]));
      const depth = (item: CanvasObject) => {
        let current = item;
        const visited = new Set<string>();
        let result = 0;
        while (current.parent_id && byId.has(current.parent_id) && !visited.has(current.parent_id)) {
          visited.add(current.parent_id);
          current = byId.get(current.parent_id)!;
          result += 1;
        }
        return result;
      };
      for (const item of [...trash].sort((a, b) => depth(b) - depth(a))) {
        await api(`/api/v1/companies/${company.id}/canvas-objects/${item.id}/purge`, { method: "POST" });
      }
      setTrash([]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
      await refresh(company.id);
    }
  }

  function dragTrayObject(event: ReactDragEvent<HTMLElement>, object: CanvasObject) {
    event.dataTransfer.setData("application/workflow-canvas-object", object.id);
    event.dataTransfer.effectAllowed = "move";
  }

  async function dropOnCanvas(event: ReactDragEvent<HTMLDivElement>) {
    event.preventDefault();
    const id = event.dataTransfer.getData("application/workflow-canvas-object");
    const object = objects.find((item) => item.id === id);
    if (!object) return;
    const point = toWorld(event.clientX, event.clientY);
    const rawX = Math.round((point.x - object.width / 2) / GRID_METERS) * GRID_METERS;
    const rawY = Math.round((point.y - object.height / 2) / GRID_METERS) * GRID_METERS;
    const snapped = snapToNearbyEdges(id, rawX, rawY, object.width, object.height);
    await patchObject(id, { ...snapped, placed: true });
  }

  async function dropOnTrash(event: ReactDragEvent<HTMLElement>) {
    event.preventDefault();
    const id = event.dataTransfer.getData("application/workflow-canvas-object");
    if (objects.some((item) => item.id === id)) await archiveObject(id);
  }

  if (loading) return <section className="cad-loading">{t.title}…</section>;
  if (!company) return <section className="cad-no-company"><h2>{t.noCompany}</h2><Link className="sandbox-primary" href={setupPath(locale)}>{t.setup}</Link>{error && <p role="alert">{error}</p>}</section>;

  return (
    <section className="cad-editor sandbox-page" lang={locale}>
      <header className="cad-heading">
        <div>
          <div className="sandbox-kicker">{company.name}</div>
          <h1>{t.title}</h1>
          <p>{t.subtitle}</p>
        </div>
        <button type="button" className="sandbox-add" onClick={openCreate}><span>＋</span>{t.add}</button>
      </header>
      {error && <div className="sandbox-error" role="alert">{error}<button type="button" onClick={() => setError("")}>×</button></div>}
      <div className="cad-workspace">
        <aside className="cad-tray-panel">
          <section className="cad-object-summary" aria-label={selected ? selected.name : t.noSelection}>
            {selected ? <>
              <span className="floor-index">{typeLabel(selected.object_type)}</span>
              <strong>{selected.name}</strong>
              <span>{selected.width / GRID_METERS} × {selected.height / GRID_METERS} {t.meterUnit} · {(selected.width / GRID_METERS) * (selected.height / GRID_METERS)} {t.meters}</span>
              {selected.description && <p>{selected.description}</p>}
              <button type="button" className="sandbox-ghost" onClick={() => openEdit(selected)}>{t.details}</button>
            </> : <>
              <span className="floor-index">{t.objectDetails}</span>
              <strong>{t.noSelection}</strong>
              <p>{t.selectHint}</p>
            </>}
          </section>
          <section className="cad-tray">
            <header><span className="floor-index">01 / TRAY</span><h2>{t.tray}</h2><p>{t.trayHint}</p></header>
            <div className="cad-tray-items">
              {objects.filter((object) => !object.placed).map((object) => (
                <article key={object.id} className="cad-tray-object" draggable onDragStart={(event) => dragTrayObject(event, object)}>
                  <span className="cad-grip" aria-hidden="true">⠿</span><div><small>{typeLabel(object.object_type)}</small><strong>{object.name}</strong>{object.description && <small>{object.description}</small>}</div>
                  <button type="button" title={t.moveToTrash} aria-label={`${t.moveToTrash}: ${object.name}`} onClick={() => void archiveObject(object.id)}>×</button>
                </article>
              ))}
              {objects.every((object) => object.placed) && <p className="cad-empty-hint">{t.firstHint}</p>}
            </div>
          </section>
          <section className="cad-trash-drop" onDragOver={(event) => event.preventDefault()} onDrop={(event) => void dropOnTrash(event)}>
            <button type="button" onClick={() => setTrashOpen(true)}><span>▤</span>{t.trash}<small>{trash.length}</small></button>
            <p>{t.trashHint}</p>
          </section>
        </aside>
        <section className="cad-board">
          <header className="cad-board-header">
            <div><span className="floor-index">02 / PLAN</span><h2>{t.canvas}</h2></div>
            <div className="cad-tools">
              <button type="button" title={t.zoomOut} onClick={() => zoomToCenter(view.scale / ZOOM_STEP)}>−</button>
              <span>{Math.round(view.scale * 100)}%</span>
              <button type="button" title={t.zoomIn} onClick={() => zoomToCenter(view.scale * ZOOM_STEP)}>＋</button>
              {selected && <div className="cad-object-rotation" aria-label={`${t.rotationValue}: ${selected.rotation}°`}>
                <button type="button" title={t.rotateLeft} aria-label={t.rotateLeft} onClick={() => void patchObject(selected.id, { rotation: ((selected.rotation - 15) % 360 + 360) % 360 })}>↶ 15°</button>
                <button type="button" title={t.rotateRight} aria-label={t.rotateRight} onClick={() => void patchObject(selected.id, { rotation: ((selected.rotation + 15) % 360 + 360) % 360 })}>↷ 15°</button>
                <span title={t.rotationValue}>{selected.rotation}°</span>
                <button type="button" title={t.resetRotation} aria-label={t.resetRotation} onClick={() => void patchObject(selected.id, { rotation: 0 })}>0°</button>
              </div>}
              <button type="button" aria-pressed={view.grid} onClick={() => setView((current) => ({ ...current, grid: !current.grid }))}>{t.grid}</button>
              <button type="button" title={t.reset} onClick={() => setView({ ...initialView })}>↺</button>
              <button type="button" title={t.undo} aria-label={t.undo} disabled={historyBusy || history.past.length === 0} onClick={() => void moveHistory("undo")}>↶</button>
              <button type="button" title={t.redo} aria-label={t.redo} disabled={historyBusy || history.future.length === 0} onClick={() => void moveHistory("redo")}>↷</button>
              {saveNotice && <span className="cad-save-notice" role="status">{saveNotice}</span>}
              <button type="button" className="cad-save-button" disabled={!company} onClick={() => {
                const initialLocation = placedObjects.find((item) => item.id === selectedId)?.id ?? locations[0]?.id ?? "";
                setExportLocationId(initialLocation);
                setExportScope(selected && selected.placed ? "location" : "all");
                setExportOpen(true);
              }}>{t.saveCanvas}</button>
              <button type="button" className="cad-print-button" disabled={!placedObjects.length} onClick={() => {
                const initialLocation = placedObjects.find((item) => item.id === selectedId)?.id ?? locations[0]?.id ?? "";
                setPrintLocationId(initialLocation);
                setPrintScope("all");
                setPrintOpen(true);
              }}>{t.print}</button>
              <button
                type="button"
                className="cad-compass"
                title={[t.compassNorth, t.compassEast, t.compassSouth, t.compassWest][((Math.round(view.rotation / 90) % 4) + 4) % 4]}
                aria-label={t.compass}
                onClick={() => setView((current) => ({ ...current, rotation: (Math.round(current.rotation / 90 + 1) % 4) * 90 }))}
              >
                <span style={{ transform: `rotate(${view.rotation}deg)` }}>↑</span><strong>N</strong>
              </button>
            </div>
          </header>
          <div
            ref={viewportRef}
            className="cad-viewport"
            onPointerDown={startPan}
            onPointerMove={updateDrag}
            onPointerUp={(event) => void finishDrag(event)}
            onPointerCancel={(event) => void finishDrag(event)}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => void dropOnCanvas(event)}
            onContextMenu={(event) => event.preventDefault()}
          >
            <div className={`cad-world ${view.grid ? "with-grid" : ""}`} style={{ transform: matrix, width: CANVAS_WIDTH, height: CANVAS_HEIGHT }}>
              {objects.filter((object) => object.placed).map((object) => (
                  (() => {
                    const inverseScale = 1 / view.scale;
                    const screenWidth = object.width * view.scale;
                    const screenHeight = object.height * view.scale;
                    const showLabels = view.scale >= 0.25 && screenWidth >= 48 && screenHeight >= 26;
                    const canShowType = view.scale >= 0.5 && screenHeight >= 46;
                    const screenFontSize = Math.max(9, Math.min(18, 14 * view.scale, screenWidth * 0.14));
                    const fontSize = screenFontSize / view.scale;
                    const typeFontSize = Math.max(7, Math.min(12, 9 * view.scale, screenWidth * 0.1)) / view.scale;
                    const maxCharacters = Math.max(1, Math.floor((object.width - 24) / (fontSize * 0.62)));
                    const nameLines = wrapCanvasLabel(object.name, maxCharacters, 3);
                    const descriptionLines = view.scale >= 1.25 && screenHeight >= 88 && object.description
                      ? wrapCanvasLabel(object.description, maxCharacters, 2)
                      : [];
                    const nameStartY = 12 + (canShowType ? typeFontSize * 1.6 : 0) + fontSize;
                    return (
                  <article
                    key={object.id}
                    className={`cad-object cad-object-${object.object_type.replace(/[^a-z0-9_-]/gi, "-")} ${selectedId === object.id ? "selected" : ""} ${object.locked ? "locked" : ""}`}
                    style={{ left: object.x, top: object.y, width: object.width, height: object.height, transform: `rotate(${object.rotation}deg)`, "--cad-inverse-scale": inverseScale } as CSSProperties}
                  onPointerDown={(event) => startObjectDrag(event, object, "move")}
                  onPointerMove={updateDrag}
                  onPointerUp={(event) => void finishDrag(event)}
                  onPointerCancel={(event) => void finishDrag(event)}
                  onClick={() => setSelectedId(object.id)}
                  aria-label={object.name}
                >
                  <svg className="cad-object-outline" viewBox={`0 0 ${object.width} ${object.height}`} preserveAspectRatio="none" shapeRendering="geometricPrecision" textRendering="geometricPrecision" aria-hidden="true">
                    <defs>
                      <clipPath id={`cad-label-clip-${object.id}`}>
                        <rect x="8" y="8" width={Math.max(0, object.width - 16)} height={Math.max(0, object.height - 16)} rx={object.object_type === "person" ? Math.min(18, object.width / 2, object.height / 2) : 5} />
                      </clipPath>
                    </defs>
                    <rect
                      x="1"
                      y="1"
                      width={Math.max(0, object.width - 2)}
                      height={Math.max(0, object.height - 2)}
                      rx={object.object_type === "person" ? Math.min(18, object.width / 2, object.height / 2) : object.object_type === "work_area" ? 12 : 5}
                      fill="none"
                      stroke="var(--cad-object-stroke, var(--green))"
                      strokeWidth="2"
                      strokeDasharray={object.object_type === "box" ? "6 4" : undefined}
                      vectorEffect="non-scaling-stroke"
                    />
                    {showLabels && <g clipPath={`url(#cad-label-clip-${object.id})`} pointerEvents="none">
                      {canShowType && <text x="12" y={12 + typeFontSize} fill="var(--green)" fontFamily="var(--font-body)" fontSize={`calc(${typeFontSize}px * var(--ui-font-scale, 1))`} fontWeight="700">{typeLabel(object.object_type)}</text>}
                      <text x="12" y={nameStartY} fill="var(--ink)" fontFamily="var(--font-display)" fontSize={`calc(${fontSize}px * var(--ui-font-scale, 1))`} fontWeight="700">
                        {nameLines.map((line, index) => <tspan key={`${object.id}-name-${index}`} x="12" dy={index === 0 ? 0 : fontSize * 1.2}>{line}</tspan>)}
                      </text>
                      {descriptionLines.length > 0 && <text x="12" y={nameStartY + nameLines.length * fontSize * 1.2} fill="var(--muted)" fontFamily="var(--font-body)" fontSize={`calc(${typeFontSize}px * var(--ui-font-scale, 1))`}>
                        {descriptionLines.map((line, index) => <tspan key={`${object.id}-description-${index}`} x="12" dy={index === 0 ? 0 : typeFontSize * 1.2}>{line}</tspan>)}
                      </text>}
                    </g>}
                  </svg>
                </article>
                  );
                })()
              ))}
              <div className="cad-selection-controls" aria-label="Object controls">
                {objects.filter((object) => object.placed && object.id === selectedId).map((object) => (
                  <div
                    key={object.id}
                    className="cad-selection-object"
                    style={{ left: object.x, top: object.y, width: object.width, height: object.height, transform: `rotate(${object.rotation}deg)`, "--cad-inverse-scale": 1 / view.scale } as CSSProperties}
                  >
                    <div className="cad-object-actions" onPointerDown={(event) => event.stopPropagation()}>
                      <button type="button" title={t.edit} aria-label={`${t.edit}: ${object.name}`} onClick={() => openEdit(object)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 16.5-.8 4.3 4.3-.8L20 7.5 16.5 4 4 16.5Z"/><path d="m14.8 5.7 3.5 3.5"/></svg></button>
                      <button type="button" title={object.locked ? t.unpin : t.pin} aria-label={object.locked ? t.unpin : t.pin} aria-pressed={object.locked} onClick={() => void patchObject(object.id, { locked: !object.locked })}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 4 12 12"/><path d="m7 5 5-2 2 2-2 5"/><path d="m10 11-7 7 3 3 7-7"/><path d="m14 15 5 5"/></svg></button>
                      <button type="button" title={t.moveToTrash} aria-label={`${t.moveToTrash}: ${object.name}`} onClick={() => void archiveObject(object.id)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
                    </div>
                    {!object.locked && ["nw", "n", "ne", "e", "se", "s", "sw", "w"].map((handle) => (
                      <button key={handle} type="button" className={`cad-resize cad-resize-${handle}`} aria-label={`Resize ${handle}`} onPointerDown={(event) => startObjectDrag(event, object, "resize", handle)} onPointerMove={updateDrag} onPointerUp={(event) => void finishDrag(event)} onPointerCancel={(event) => void finishDrag(event)} />
                    ))}
                  </div>
                ))}
              </div>
              <span className="cad-scale-note">{t.unitHint}</span>
              {!objects.some((object) => object.placed) && <div className="cad-first-prompt"><span>＋</span><strong>{t.first}</strong><p>{t.firstHint}</p><button type="button" className="sandbox-primary" onClick={openCreate}>{t.add}</button></div>}
            </div>
          </div>
        </section>
      </div>
      {exportOpen && <div className="block-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setExportOpen(false); }}>
        <section className="block-modal cad-export-dialog" role="dialog" aria-modal="true" aria-labelledby="cad-export-title">
          <button type="button" className="modal-close" aria-label={t.cancel} onClick={() => setExportOpen(false)}>×</button>
          <span className="floor-index">CAD / EXPORT</span>
          <h2 id="cad-export-title">{t.exportTitle}</h2>
          <label>{t.exportFormat}
            <select value={exportFormat} onChange={(event) => setExportFormat(event.target.value as ExportFormat)}>
              <option value="svg">{t.svgFormat}</option>
              <option value="png">{t.pngFormat}</option>
              <option value="json">{t.jsonFormat}</option>
            </select>
          </label>
          <label>{t.exportArea}
            <select value={exportScope} onChange={(event) => setExportScope(event.target.value as ExportScope)}>
              <option value="all">{t.wholePlan}</option>
              <option value="location">{t.oneLocation}</option>
            </select>
          </label>
          {exportScope === "location" && <label>{t.chooseLocation}
            <select value={exportLocationId} onChange={(event) => setExportLocationId(event.target.value)}>
              {placedObjects.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
            </select>
          </label>}
          <p>{t.saveFileHint}</p>
          <div className="cad-export-actions">
            <button type="button" className="sandbox-primary" onClick={() => void exportPlan()}>{t.saveFile}</button>
            <button type="button" className="sandbox-ghost" disabled={savingCanvas} onClick={() => void saveCanvas()}>{savingCanvas ? t.savingCanvas : t.saveDatabase}</button>
          </div>
        </section>
      </div>}
      {printOpen && <div className="block-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setPrintOpen(false); }}>
        <section className="block-modal cad-export-dialog" role="dialog" aria-modal="true" aria-labelledby="cad-print-title">
          <button type="button" className="modal-close" aria-label={t.cancel} onClick={() => setPrintOpen(false)}>×</button>
          <span className="floor-index">CAD / PRINT</span>
          <h2 id="cad-print-title">{t.printTitle}</h2>
          <label>{t.exportArea}
            <select value={printScope} onChange={(event) => setPrintScope(event.target.value as PrintScope)}>
              <option value="all">{t.wholePlan}</option>
              <option value="each">{t.eachLocation}</option>
              <option value="location">{t.oneLocation}</option>
            </select>
          </label>
          {printScope === "location" && <label>{t.chooseLocation}
            <select value={printLocationId} onChange={(event) => setPrintLocationId(event.target.value)}>
              {placedObjects.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
            </select>
          </label>}
          <p>{t.printHint}</p>
          <div className="cad-export-actions">
            <button type="button" className="sandbox-primary" onClick={printPlan}>{t.printNow}</button>
            <button type="button" className="sandbox-ghost" onClick={() => setPrintOpen(false)}>{t.cancel}</button>
          </div>
        </section>
      </div>}
      {modal && <div className="block-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) closeEditor(); }}>
        <form className="block-modal cad-create-form" onSubmit={(event) => void (editing ? saveEditedObject(event) : createObject(event))}>
          <button type="button" className="modal-close" aria-label={t.cancel} onClick={closeEditor}>×</button>
          <span className="floor-index">CAD / OBJECT</span><h2>{editing ? t.objectDetails : t.add}</h2>
          <label>{t.type}<select value={objectType} onChange={(event) => {
            const nextType = event.target.value;
            setObjectType(nextType);
            if (isCanvasRootType(nextType) || (parentId && !isAllowedCanvasParent(objects.find((item) => item.id === parentId)?.object_type ?? "", nextType))) {
              setParentId("");
            }
          }}>{objectTypes.map((value) => <option key={value} value={value}>{t[value === "work_area" ? "workArea" : value as keyof typeof t]}</option>)}{editing && !objectTypes.some((value) => value === editing.object_type) && <option value={editing.object_type}>{typeLabel(editing.object_type)}</option>}</select></label>
          {isCanvasRootType(objectType) ? <p>{t.rootObject}</p> : <label>{t.parent}<select required value={parentId} onChange={(event) => setParentId(event.target.value)}>
            <option value="">{t.chooseParent}</option>
            {parentCandidates.map((candidate) => <option key={candidate.id} value={candidate.id}>{typeLabel(candidate.object_type)} · {candidate.name}</option>)}
          </select>{parentCandidates.length === 0 && <small>{t.noAvailableParents}</small>}</label>}
          <label>{t.name}<input required maxLength={180} value={name} onChange={(event) => setName(event.target.value)} autoFocus /></label>
          <label>{t.description}<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label>
          {editing && <div className="cad-dimensions">
            <label>{t.width}<input type="number" min="1" step="1" value={lengthMeters} onChange={(event) => setLengthMeters(Number(event.target.value))} /></label>
            <label>{t.height}<input type="number" min="1" step="1" value={widthMeters} onChange={(event) => setWidthMeters(Number(event.target.value))} /></label>
            <label>{t.x}<input type="number" step="0.25" value={xMeters} onChange={(event) => setXMeters(Number(event.target.value))} /></label>
            <label>{t.y}<input type="number" step="0.25" value={yMeters} onChange={(event) => setYMeters(Number(event.target.value))} /></label>
            <label>{t.rotation}<input type="number" step="15" value={rotation} onChange={(event) => setRotation(Number(event.target.value))} /></label>
            <p>{t.area}: <strong>{Math.max(1, lengthMeters) * Math.max(1, widthMeters)} {t.meters}</strong></p>
          </div>}
          {editing && <label className="cad-lock-field"><input type="checkbox" checked={editingLocked} onChange={(event) => setEditingLocked(event.target.checked)} />{t.locked}</label>}
          <div className="modal-actions"><button type="button" className="sandbox-ghost" onClick={closeEditor}>{t.cancel}</button><button type="submit" className="sandbox-primary">{editing ? t.saveChanges : t.save}</button></div>
        </form>
      </div>}
      {trashOpen && <div className="block-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setTrashOpen(false); }}>
        <section className="block-modal cad-trash-modal" role="dialog" aria-modal="true" aria-labelledby="cad-trash-title">
          <button type="button" className="modal-close" aria-label={t.cancel} onClick={() => setTrashOpen(false)}>×</button>
          <span className="floor-index">CAD / RECYCLE BIN</span><h2 id="cad-trash-title">{t.trash}</h2>
          {trash.length === 0 ? <p>{t.emptyTrash}</p> : <>
            <div className="cad-trash-items">{trash.map((object) => <article key={object.id}><span><strong>{object.name}</strong>{object.description && <small>{object.description}</small>}</span><button type="button" onClick={() => void restoreObject(object.id)}>{t.restore}</button><button type="button" className="danger" onClick={() => void purgeObject(object.id)}>{t.delete}</button></article>)}</div>
            <div className="modal-actions"><button type="button" className="sandbox-ghost" onClick={() => void emptyTrash()}>{t.empty}</button><button type="button" className="sandbox-primary" onClick={() => setTrashOpen(false)}>{t.cancel}</button></div>
          </>}
        </section>
      </div>}
    </section>
  );
}
