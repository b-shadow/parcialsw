import { PointerEvent, useEffect, useMemo, useRef, useState } from "react";
import * as joint from "@joint/core";

import type { UmlClassDetail, UmlRelationship } from "../types/uml";

type UmlTool = "select" | "class" | "association" | "inheritance" | "associationClass";

type JointUmlCanvasProps = {
  classes: UmlClassDetail[];
  relationships: UmlRelationship[];
  activeTool: UmlTool;
  pendingSourceId: string;
  selectedClassId: string | null;
  selectedRelationshipId: string | null;
  isDark: boolean;
  onClassClick: (classId: string) => void;
  onRelationshipClick: (relationshipId: string) => void;
  onClassMove: (classId: string, position: { x: number; y: number }) => void;
  onClassRename: (classId: string, name: string) => void;
};

const CLASS_WIDTH = 290;
const HEADER_HEIGHT = 34;
const ROW_HEIGHT = 22;
const CANVAS_WIDTH = 4200;
const CANVAS_HEIGHT = 3000;
const MIN_ZOOM = 0.35;
const MAX_ZOOM = 2.2;

type Viewport = {
  x: number;
  y: number;
  scale: number;
};

function visibilitySymbol(visibility: string) {
  return visibility === "private" ? "-" : "+";
}

function classHeight(umlClass: UmlClassDetail) {
  const attributeRows = Math.max(1, umlClass.attributes.length);
  const methodRows = Math.max(1, umlClass.methods.length);
  return HEADER_HEIGHT + attributeRows * ROW_HEIGHT + methodRows * ROW_HEIGHT + 26;
}

function classAttrs(umlClass: UmlClassDetail, isDark: boolean, selected: boolean) {
  const attributeText = (umlClass.attributes.length > 0 ? umlClass.attributes : [{ visibility: "private", name: "id", data_type: "Long" }])
    .map((attribute) => `${visibilitySymbol(attribute.visibility)}  ${attribute.name}: ${attribute.data_type}`)
    .join("\n");
  const methodText = (umlClass.methods.length > 0 ? umlClass.methods : [{ visibility: "public", name: "validar", return_type: "boolean" }])
    .map((method) => `${visibilitySymbol(method.visibility)}  ${method.name}(): ${method.return_type ?? "void"}`)
    .join("\n");
  const attributeRows = Math.max(1, umlClass.attributes.length);
  const methodSeparatorY = HEADER_HEIGHT + attributeRows * ROW_HEIGHT + 12;
  const lineColor = selected ? "#0f172a" : "#64748b";
  return {
    body: {
      width: CLASS_WIDTH,
      height: classHeight(umlClass),
      fill: isDark ? "#0f172a" : "#fff8ee",
      stroke: lineColor,
      strokeWidth: selected ? 2 : 1
    },
    header: {
      width: CLASS_WIDTH,
      height: HEADER_HEIGHT,
      fill: isDark ? "#111827" : "#fff2df",
      stroke: lineColor,
      strokeWidth: 1
    },
    name: {
      text: umlClass.name,
      x: CLASS_WIDTH / 2,
      y: 22,
      textAnchor: "middle",
      fontSize: 13,
      fontWeight: 700,
      fill: isDark ? "#f8fafc" : "#111827",
      cursor: "text"
    },
    attrSeparator: {
      x1: 0,
      x2: CLASS_WIDTH,
      y1: HEADER_HEIGHT,
      y2: HEADER_HEIGHT,
      stroke: isDark ? "#475569" : "#94a3b8",
      strokeWidth: 1
    },
    methodSeparator: {
      x1: 0,
      x2: CLASS_WIDTH,
      y1: methodSeparatorY,
      y2: methodSeparatorY,
      stroke: isDark ? "#475569" : "#94a3b8",
      strokeWidth: 1
    },
    attributes: {
      text: attributeText,
      x: 20,
      y: HEADER_HEIGHT + 24,
      fontFamily: "Consolas, ui-monospace, monospace",
      fontSize: 13,
      lineHeight: "18px",
      fill: isDark ? "#e2e8f0" : "#7c2d12"
    },
    methods: {
      text: methodText,
      x: 20,
      y: methodSeparatorY + 24,
      fontFamily: "Consolas, ui-monospace, monospace",
      fontSize: 13,
      lineHeight: "18px",
      fill: isDark ? "#e2e8f0" : "#166534"
    }
  };
}

const UmlClassShape = joint.dia.Element.define(
  "case.UmlClass",
  {
    attrs: classAttrs(
      {
        id: "",
        diagram_id: "",
        name: "",
        visibility: "public",
        element_type: "class",
        stereotype: null,
        description: null,
        metadata_json: {},
        attributes: [],
        methods: [],
        visual: null
      },
      false,
      false
    )
  },
  {
    markup: [
      { tagName: "rect", selector: "body" },
      { tagName: "rect", selector: "header" },
      { tagName: "line", selector: "attrSeparator" },
      { tagName: "line", selector: "methodSeparator" },
      { tagName: "text", selector: "name" },
      { tagName: "text", selector: "attributes" },
      { tagName: "text", selector: "methods" }
    ]
  }
);

const jointCellNamespace = {
  ...joint.shapes,
  case: {
    UmlClass: UmlClassShape
  }
};

function relationshipLabel(relationship: UmlRelationship) {
  return [relationship.source_cardinality, relationship.label, relationship.target_cardinality].filter(Boolean).join("  ");
}

function linkAttrs(relationship: UmlRelationship, isDark: boolean, selected: boolean) {
  const stroke = relationship.relationship_type === "inheritance" ? "#1d4ed8" : "#0f766e";
  const dashed = relationship.relationship_type === "dependency" || relationship.relationship_type === "implementation";
  return {
    line: {
      stroke,
      strokeWidth: selected ? 3 : 2,
      strokeDasharray: dashed ? "8 6" : undefined,
      targetMarker:
        relationship.relationship_type === "inheritance"
          ? { type: "path", d: "M 10 -5 0 0 10 5 z", fill: isDark ? "#0f172a" : "#f8fafc", stroke }
          : { type: "path", d: "M 10 -5 0 0 10 5", fill: "none", stroke }
    }
  };
}

function classPosition(umlClass: UmlClassDetail, index: number, transientPositions: Record<string, { x: number; y: number }>) {
  return {
    x: transientPositions[umlClass.id]?.x ?? umlClass.visual?.position_x ?? 80 + index * 320,
    y: transientPositions[umlClass.id]?.y ?? umlClass.visual?.position_y ?? 90 + (index % 3) * 210
  };
}

function clampZoom(scale: number) {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, scale));
}

function squaredDistance(source: { x: number; y: number }, target: { x: number; y: number }) {
  return (source.x - target.x) ** 2 + (source.y - target.y) ** 2;
}

function closestConnectionPoints(
  source: { x: number; y: number; width: number; height: number },
  target: { x: number; y: number; width: number; height: number }
) {
  const sourcePorts = [
    { x: source.x + source.width / 2, y: source.y },
    { x: source.x + source.width, y: source.y + source.height / 2 },
    { x: source.x + source.width / 2, y: source.y + source.height },
    { x: source.x, y: source.y + source.height / 2 }
  ];
  const targetPorts = [
    { x: target.x + target.width / 2, y: target.y },
    { x: target.x + target.width, y: target.y + target.height / 2 },
    { x: target.x + target.width / 2, y: target.y + target.height },
    { x: target.x, y: target.y + target.height / 2 }
  ];
  let best = {
    source: sourcePorts[0],
    target: targetPorts[0],
    distance: Number.POSITIVE_INFINITY
  };

  for (const sourcePort of sourcePorts) {
    for (const targetPort of targetPorts) {
      const distance = squaredDistance(sourcePort, targetPort);
      if (distance < best.distance) {
        best = { source: sourcePort, target: targetPort, distance };
      }
    }
  }

  return best;
}

export function JointUmlCanvas({
  classes,
  relationships,
  activeTool,
  pendingSourceId,
  selectedClassId,
  selectedRelationshipId,
  isDark,
  onClassClick,
  onRelationshipClick,
  onClassMove,
  onClassRename
}: JointUmlCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const paperHostRef = useRef<HTMLDivElement | null>(null);
  const graphRef = useRef<joint.dia.Graph | null>(null);
  const paperRef = useRef<joint.dia.Paper | null>(null);
  const dragRef = useRef<{
    classId: string;
    offsetX: number;
    offsetY: number;
    position: { x: number; y: number };
    moved: boolean;
  } | null>(null);
  const panRef = useRef<{
    startClientX: number;
    startClientY: number;
    startX: number;
    startY: number;
  } | null>(null);
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, scale: 1 });
  const viewportRef = useRef<Viewport>({ x: 0, y: 0, scale: 1 });
  const [transientPositions, setTransientPositions] = useState<Record<string, { x: number; y: number }>>({});
  const classById = useMemo(() => new Map(classes.map((umlClass) => [umlClass.id, umlClass])), [classes]);
  const classByIdRef = useRef(classById);
  const callbacksRef = useRef({ onClassClick, onRelationshipClick, onClassMove, onClassRename });

  useEffect(() => {
    classByIdRef.current = classById;
    callbacksRef.current = { onClassClick, onRelationshipClick, onClassMove, onClassRename };
  }, [classById, onClassClick, onClassMove, onClassRename, onRelationshipClick]);

  useEffect(() => {
    viewportRef.current = viewport;
  }, [viewport]);

  useEffect(() => {
    if (!containerRef.current || !paperHostRef.current) {
      return;
    }
    paperHostRef.current.replaceChildren();
    const graph = new joint.dia.Graph({}, { cellNamespace: jointCellNamespace });
    const paperWidth = Math.max(containerRef.current.clientWidth || 0, 900);
    let paper: joint.dia.Paper;
    try {
      paper = new joint.dia.Paper({
        model: graph,
        width: paperWidth,
        height: 620,
        gridSize: 24,
        drawGrid: { name: "dot", args: { color: isDark ? "#64748b" : "#94a3b8", thickness: 1 } },
        background: { color: isDark ? "#111827" : "#f8fafc" },
        cellViewNamespace: jointCellNamespace,
        defaultLink: () => new joint.shapes.standard.Link(),
        interactive: { linkMove: false, labelMove: false },
        async: false
      });
    } catch {
      graphRef.current = null;
      paperRef.current = null;
      return () => {
        graph.clear();
        paperHostRef.current?.replaceChildren();
      };
    }
    paperHostRef.current.appendChild(paper.el);
    graphRef.current = graph;
    paperRef.current = paper;

    paper.on("element:pointerclick", (elementView: joint.dia.ElementView) => {
      callbacksRef.current.onClassClick(String(elementView.model.id));
    });
    paper.on("link:pointerclick", (linkView: joint.dia.LinkView) => {
      const relationshipId = linkView.model.get("relationshipId");
      if (relationshipId) {
        callbacksRef.current.onRelationshipClick(String(relationshipId));
      }
    });
    paper.on("element:pointerdblclick", (elementView: joint.dia.ElementView) => {
      const umlClass = classByIdRef.current.get(String(elementView.model.id));
      const nextName = window.prompt("Nombre de clase", umlClass?.name ?? "");
      if (nextName?.trim()) {
        callbacksRef.current.onClassRename(String(elementView.model.id), nextName.trim());
      }
    });
    paper.on("element:pointerup", (elementView: joint.dia.ElementView) => {
      const position = elementView.model.position();
      callbacksRef.current.onClassMove(String(elementView.model.id), position);
    });

    return () => {
      paper.remove();
      graph.clear();
      paperHostRef.current?.replaceChildren();
      graphRef.current = null;
      paperRef.current = null;
    };
  }, [isDark]);

  useEffect(() => {
    const graph = graphRef.current;
    const paper = paperRef.current;
    if (!graph || !paper) {
      return;
    }
    graph.clear();

    const elements = classes.map((umlClass, index) => {
      const element = new UmlClassShape({
        id: umlClass.id,
        position: {
          x: umlClass.visual?.position_x ?? 80 + index * 320,
          y: umlClass.visual?.position_y ?? 90 + (index % 3) * 210
        },
        size: { width: CLASS_WIDTH, height: classHeight(umlClass) },
        attrs: classAttrs(umlClass, isDark, selectedClassId === umlClass.id || pendingSourceId === umlClass.id)
      });
      return element;
    });

    const anchorElements: joint.dia.Element[] = [];
    const links = relationships.flatMap((relationship) => {
      const sourceClass = classById.get(relationship.source_class_id);
      const targetClass = classById.get(relationship.target_class_id);
      if (!sourceClass || !targetClass) {
        return [];
      }
      const link = new joint.shapes.standard.Link({
        source: { id: relationship.source_class_id },
        target: { id: relationship.target_class_id },
        attrs: linkAttrs(relationship, isDark, selectedRelationshipId === relationship.id),
        relationshipId: relationship.id,
        router: { name: "normal" },
        connector: { name: "normal" }
      });
      const label = relationshipLabel(relationship);
      if (label) {
        link.labels([
          {
            position: 0.5,
            attrs: {
              rect: { fill: isDark ? "#0f172a" : "#ffffff", stroke: "transparent", rx: 3, ry: 3 },
              text: { text: label, fill: isDark ? "#e2e8f0" : "#0f172a", fontSize: 12, fontWeight: 600 }
            }
          }
        ]);
      }
      const associationClassId: string | undefined =
        typeof relationship.metadata_json?.association_class_id === "string"
          ? relationship.metadata_json.association_class_id
          : undefined;
      const associationClass = associationClassId ? classById.get(associationClassId) : null;
      if (!associationClass) {
        return [link];
      }
      const sourcePosition = {
        x: sourceClass.visual?.position_x ?? 80,
        y: sourceClass.visual?.position_y ?? 90
      };
      const targetPosition = {
        x: targetClass.visual?.position_x ?? 400,
        y: targetClass.visual?.position_y ?? 90
      };
      const anchor = new joint.shapes.standard.Circle({
        id: `association-anchor-${relationship.id}`,
        position: {
          x: (sourcePosition.x + targetPosition.x + CLASS_WIDTH) / 2,
          y: (sourcePosition.y + targetPosition.y + HEADER_HEIGHT) / 2
        },
        size: { width: 1, height: 1 },
        attrs: { body: { fill: "transparent", stroke: "transparent" } }
      });
      anchorElements.push(anchor);
      const dashed = new joint.shapes.standard.Link({
        source: { id: associationClassId },
        target: { id: anchor.id },
        attrs: {
          line: {
            stroke: isDark ? "#94a3b8" : "#64748b",
            strokeWidth: 2,
            strokeDasharray: "8 6",
            targetMarker: { type: "path", d: "" }
          }
        },
        router: { name: "normal" },
        connector: { name: "normal" }
      });
      return [link, dashed];
    });

    graph.addCells([...elements, ...anchorElements, ...links]);
    paper.setDimensions(Math.max(containerRef.current?.clientWidth || 0, 900), 620);
    paper.translate(viewport.x, viewport.y);
    paper.scale(viewport.scale, viewport.scale);
    paper.render();
    paper.updateViews();
  }, [classById, classes, isDark, pendingSourceId, relationships, selectedClassId, selectedRelationshipId, viewport.scale, viewport.x, viewport.y]);

  function screenToWorld(clientX: number, clientY: number) {
    const rect = containerRef.current?.getBoundingClientRect();
    const left = rect?.left ?? 0;
    const top = rect?.top ?? 0;
    return {
      x: (clientX - left - viewport.x) / viewport.scale,
      y: (clientY - top - viewport.y) / viewport.scale
    };
  }

  function zoomAt(clientX: number, clientY: number, nextScale: number) {
    setViewport((current) => {
      const rect = containerRef.current?.getBoundingClientRect();
      const left = rect?.left ?? 0;
      const top = rect?.top ?? 0;
      const scale = clampZoom(nextScale);
      const worldX = (clientX - left - current.x) / current.scale;
      const worldY = (clientY - top - current.y) / current.scale;
      return {
        scale,
        x: clientX - left - worldX * scale,
        y: clientY - top - worldY * scale
      };
    });
  }

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }
    const canvasElement = element;

    function handleNativeWheel(event: WheelEvent) {
      event.preventDefault();
      const currentViewport = viewportRef.current;
      const factor = event.deltaY > 0 ? 0.9 : 1.1;
      const nextScale = clampZoom(currentViewport.scale * factor);
      const rect = canvasElement.getBoundingClientRect();
      const worldX = (event.clientX - rect.left - currentViewport.x) / currentViewport.scale;
      const worldY = (event.clientY - rect.top - currentViewport.y) / currentViewport.scale;
      setViewport({
        scale: nextScale,
        x: event.clientX - rect.left - worldX * nextScale,
        y: event.clientY - rect.top - worldY * nextScale
      });
    }

    canvasElement.addEventListener("wheel", handleNativeWheel, { passive: false });
    return () => canvasElement.removeEventListener("wheel", handleNativeWheel);
  }, []);

  function zoomAtCenter(nextScale: number) {
    const rect = containerRef.current?.getBoundingClientRect();
    zoomAt((rect?.left ?? 0) + (rect?.width ?? 320) / 2, (rect?.top ?? 0) + (rect?.height ?? 240) / 2, nextScale);
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>, umlClass: UmlClassDetail, index: number) {
    if (activeTool !== "select") {
      return;
    }
    const position = classPosition(umlClass, index, transientPositions);
    const worldPointer = screenToWorld(event.clientX, event.clientY);
    dragRef.current = {
      classId: umlClass.id,
      offsetX: worldPointer.x - position.x,
      offsetY: worldPointer.y - position.y,
      position,
      moved: false
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    const drag = dragRef.current;
    if (!drag) {
      return;
    }
    const worldPointer = screenToWorld(event.clientX, event.clientY);
    const nextPosition = {
      x: Math.max(24, worldPointer.x - drag.offsetX),
      y: Math.max(24, worldPointer.y - drag.offsetY)
    };
    drag.moved = true;
    drag.position = nextPosition;
    setTransientPositions((current) => ({ ...current, [drag.classId]: nextPosition }));
  }

  function handlePointerUp(event: PointerEvent<HTMLDivElement>, umlClass: UmlClassDetail, index: number) {
    const drag = dragRef.current;
    if (!drag || drag.classId !== umlClass.id) {
      onClassClick(umlClass.id);
      return;
    }
    event.currentTarget.releasePointerCapture(event.pointerId);
    dragRef.current = null;
    if (drag.moved) {
      onClassMove(umlClass.id, drag.position);
      return;
    }
    onClassClick(umlClass.id);
  }

  function handleCanvasPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) {
      return;
    }
    panRef.current = {
      startClientX: event.clientX,
      startClientY: event.clientY,
      startX: viewport.x,
      startY: viewport.y
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handleCanvasPointerMove(event: PointerEvent<HTMLDivElement>) {
    const pan = panRef.current;
    if (!pan) {
      return;
    }
    setViewport((current) => ({
      ...current,
      x: pan.startX + event.clientX - pan.startClientX,
      y: pan.startY + event.clientY - pan.startClientY
    }));
  }

  function handleCanvasPointerUp(event: PointerEvent<HTMLDivElement>) {
    if (!panRef.current) {
      return;
    }
    panRef.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }

  function renderRelationship(relationship: UmlRelationship) {
    const sourceIndex = classes.findIndex((umlClass) => umlClass.id === relationship.source_class_id);
    const targetIndex = classes.findIndex((umlClass) => umlClass.id === relationship.target_class_id);
    const sourceClass = sourceIndex >= 0 ? classes[sourceIndex] : null;
    const targetClass = targetIndex >= 0 ? classes[targetIndex] : null;
    if (!sourceClass || !targetClass) {
      return null;
    }
    const sourcePosition = classPosition(sourceClass, sourceIndex, transientPositions);
    const targetPosition = classPosition(targetClass, targetIndex, transientPositions);
    const sourceHeight = classHeight(sourceClass);
    const targetHeight = classHeight(targetClass);
    const connection = closestConnectionPoints(
      { x: sourcePosition.x, y: sourcePosition.y, width: CLASS_WIDTH, height: sourceHeight },
      { x: targetPosition.x, y: targetPosition.y, width: CLASS_WIDTH, height: targetHeight }
    );
    const x1 = connection.source.x;
    const y1 = connection.source.y;
    const x2 = connection.target.x;
    const y2 = connection.target.y;
    const selected = selectedRelationshipId === relationship.id;
    const stroke = relationship.relationship_type === "inheritance" ? "#1d4ed8" : "#0f766e";
    const label = relationshipLabel(relationship);
    const associationClassId =
      typeof relationship.metadata_json?.association_class_id === "string"
        ? relationship.metadata_json.association_class_id
        : "";
    const associationIndex = classes.findIndex((umlClass) => umlClass.id === associationClassId);
    const associationClass = associationIndex >= 0 ? classes[associationIndex] : null;
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;
    const associationPosition = associationClass ? classPosition(associationClass, associationIndex, transientPositions) : null;

    return (
      <g key={relationship.id}>
        <line
          className="cursor-pointer"
          markerEnd={relationship.relationship_type === "inheritance" ? "url(#uml-generalization)" : "url(#uml-association)"}
          onClick={(event) => {
            event.stopPropagation();
            onRelationshipClick(relationship.id);
          }}
          pointerEvents="visibleStroke"
          stroke={stroke}
          strokeDasharray={relationship.relationship_type === "dependency" || relationship.relationship_type === "implementation" ? "8 6" : undefined}
          strokeWidth={selected ? 3 : 2}
          x1={x1}
          x2={x2}
          y1={y1}
          y2={y2}
        />
        {label && (
          <text
            fill={isDark ? "#e2e8f0" : "#0f172a"}
            fontSize="12"
            fontWeight="600"
            textAnchor="middle"
            x={midX}
            y={midY - 8}
          >
            {label}
          </text>
        )}
        {associationClass && associationPosition && (
          <line
            pointerEvents="none"
            stroke={isDark ? "#94a3b8" : "#64748b"}
            strokeDasharray="8 6"
            strokeWidth={2}
            x1={associationPosition.x + CLASS_WIDTH / 2}
            x2={midX}
            y1={associationPosition.y}
            y2={midY}
          />
        )}
      </g>
    );
  }

  return (
    <div
      className="joint-uml-canvas relative h-[620px] cursor-grab overflow-hidden active:cursor-grabbing"
      onPointerDown={handleCanvasPointerDown}
      onPointerMove={handleCanvasPointerMove}
      onPointerUp={handleCanvasPointerUp}
      ref={containerRef}
      style={{
        backgroundColor: isDark ? "#111827" : "#f8fafc",
        backgroundImage: `radial-gradient(${isDark ? "#64748b" : "#94a3b8"} 1px, transparent 1px)`,
        backgroundPosition: `${viewport.x}px ${viewport.y}px`,
        backgroundSize: `${24 * viewport.scale}px ${24 * viewport.scale}px`
      }}
    >
      <div className="pointer-events-none absolute inset-0 z-0 opacity-0" ref={paperHostRef} />
      <div
        className="pointer-events-none absolute left-0 top-0 z-10"
        style={{
          height: CANVAS_HEIGHT,
          transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})`,
          transformOrigin: "0 0",
          width: CANVAS_WIDTH
        }}
      >
        <svg className="pointer-events-none absolute inset-0 h-full w-full overflow-visible">
          <defs>
            <marker id="uml-association" markerHeight="8" markerWidth="8" orient="auto" refX="8" refY="4">
              <path d="M 0 0 L 8 4 L 0 8" fill="none" stroke="#0f766e" strokeWidth="1.8" />
            </marker>
            <marker id="uml-generalization" markerHeight="12" markerWidth="12" orient="auto" refX="12" refY="6">
              <path d="M 12 6 L 0 0 L 0 12 Z" fill={isDark ? "#111827" : "#f8fafc"} stroke="#1d4ed8" strokeWidth="1.8" />
            </marker>
          </defs>
          {relationships.map(renderRelationship)}
        </svg>
        {classes.map((umlClass, index) => {
          const position = classPosition(umlClass, index, transientPositions);
          const selected = selectedClassId === umlClass.id || pendingSourceId === umlClass.id;
          const attributes =
            umlClass.attributes.length > 0 ? umlClass.attributes : [{ visibility: "private", name: "id", data_type: "Long" }];
          const methods =
            umlClass.methods.length > 0 ? umlClass.methods : [{ visibility: "public", name: "validar", return_type: "boolean" }];
          return (
            <div
              className={`pointer-events-auto absolute select-none overflow-hidden rounded-sm border font-mono text-sm shadow-sm ${
                selected
                  ? "border-slate-950 ring-2 ring-slate-950 dark:border-slate-200 dark:ring-slate-200"
                  : "border-slate-500 dark:border-slate-500"
              } ${isDark ? "bg-slate-950 text-slate-100" : "bg-orange-50 text-slate-950"}`}
              key={umlClass.id}
              onPointerDown={(event) => handlePointerDown(event, umlClass, index)}
              onPointerMove={handlePointerMove}
              onPointerUp={(event) => handlePointerUp(event, umlClass, index)}
              style={{
                left: position.x,
                top: position.y,
                width: CLASS_WIDTH,
                minHeight: classHeight(umlClass)
              }}
            >
              <input
                className={`h-[34px] w-full border-0 border-b px-3 text-center font-sans text-sm font-bold outline-none ${
                  isDark
                    ? "border-slate-700 bg-slate-900 text-slate-100"
                    : "border-slate-400 bg-orange-100 text-slate-950"
                }`}
                onChange={(event) => onClassRename(umlClass.id, event.target.value)}
                onPointerDown={(event) => event.stopPropagation()}
                value={umlClass.name}
              />
              <div className={`min-h-[46px] whitespace-pre-line border-b px-5 py-3 ${isDark ? "border-slate-700" : "border-slate-300"}`}>
                {attributes.map((attribute, itemIndex) => (
                  <div className={isDark ? "text-slate-200" : "text-orange-900"} key={`${attribute.name}-${itemIndex}`}>
                    {visibilitySymbol(attribute.visibility)}&nbsp; {attribute.name}: {attribute.data_type}
                  </div>
                ))}
              </div>
              <div className="min-h-[46px] whitespace-pre-line px-5 py-3">
                {methods.map((method, itemIndex) => (
                  <div className={isDark ? "text-slate-200" : "text-green-800"} key={`${method.name}-${itemIndex}`}>
                    {visibilitySymbol(method.visibility)}&nbsp; {method.name}(): {method.return_type ?? "void"}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      <div className="absolute bottom-4 left-4 z-30 flex overflow-hidden rounded-md border border-slate-300 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-950">
        <button
          className="h-9 w-10 border-r border-slate-300 text-lg font-semibold text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-100 dark:hover:bg-slate-800"
          onClick={() => zoomAtCenter(viewport.scale * 1.15)}
          type="button"
        >
          +
        </button>
        <button
          className="h-9 w-10 border-r border-slate-300 text-lg font-semibold text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-100 dark:hover:bg-slate-800"
          onClick={() => zoomAtCenter(viewport.scale / 1.15)}
          type="button"
        >
          -
        </button>
        <button
          className="h-9 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          onClick={() => setViewport({ x: 0, y: 0, scale: 1 })}
          type="button"
        >
          100%
        </button>
      </div>
    </div>
  );
}
