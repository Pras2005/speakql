import { useCallback, useMemo } from 'react';
import { Database } from 'lucide-react';

import { cn } from '@/lib/utils';
import type { SchemaTableData, SchemaVisualization } from '@/lib/types';

interface ERRelationship {
  fromTable: string;
  fromColumn?: string;
  toTable: string;
  toColumn?: string;
  name?: string;
}

interface Position {
  x: number;
  y: number;
}

interface ERDiagramViewProps {
  schemaData: SchemaVisualization | null;
  zoom: number;
  loading: boolean;
  expandedTables: Record<string, boolean>;
  toggleTableExpansion: (tableName: string) => void;
}

export default function ERDiagramView({
  schemaData,
  zoom,
  loading,
  expandedTables,
  toggleTableExpansion,
}: ERDiagramViewProps) {
  const relationships = useMemo<ERRelationship[]>(() => {
    if (!schemaData?.tables) return [];

    const relations: ERRelationship[] = [];

    Object.entries(schemaData.tables).forEach(([tableName, tableData]) => {
      (tableData.structure?.foreign_keys || []).forEach((fk) => {
        relations.push({
          fromTable: tableName,
          fromColumn: fk.constrained_columns?.[0],
          toTable: fk.referred_table,
          toColumn: fk.referred_columns?.[0],
        });
      });
    });

    return relations;
  }, [schemaData]);

  const tablePositions = useMemo<Record<string, Position>>(() => {
    if (!schemaData?.tables) return {};

    const tableNames = Object.keys(schemaData.tables);
    const positions: Record<string, Position> = {};
    const cols = 3;
    const horizontalGap = 400;
    const verticalGap = 300;

    tableNames.forEach((tableName, index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;

      positions[tableName] = {
        x: 100 + col * horizontalGap,
        y: 100 + row * verticalGap,
      };
    });

    return positions;
  }, [schemaData]);

  const getPrimaryKeys = useCallback(
    (tableName: string) => {
      const columns = schemaData?.tables?.[tableName]?.structure?.columns || [];
      return columns.filter((column) => column.primary_key).map((column) => column.name);
    },
    [schemaData],
  );

  const svgDimensions = useMemo(() => {
    if (Object.keys(tablePositions).length === 0) {
      return { width: 1200, height: 800 };
    }

    let maxX = 0;
    let maxY = 0;

    Object.values(tablePositions).forEach((pos) => {
      maxX = Math.max(maxX, pos.x + 300);
      maxY = Math.max(maxY, pos.y + 200);
    });

    return {
      width: maxX + 100,
      height: maxY + 100,
    };
  }, [tablePositions]);

  const renderTableBox = (tableName: string, x: number, y: number) => {
    const tableData = schemaData?.tables[tableName] as SchemaTableData | undefined;
    if (!tableData?.structure) {
      return null;
    }

    const isExpanded = expandedTables[tableName] || false;
    const primaryKeys = getPrimaryKeys(tableName);
    const titleHeight = 40;
    const rowHeight = 25;
    const headerHeight = 30;

    let columnsToShow = tableData.structure.columns;
    if (!isExpanded) {
      const fkColumns = (tableData.structure.foreign_keys || []).flatMap((fk) => fk.constrained_columns || []);

      columnsToShow = tableData.structure.columns.filter(
        (column) => column.primary_key || fkColumns.includes(column.name),
      );

      if (columnsToShow.length < 3 && tableData.structure.columns.length >= 3) {
        columnsToShow = tableData.structure.columns.slice(0, 3);
      }
    }

    const tableHeight = titleHeight + headerHeight + columnsToShow.length * rowHeight;
    const tableWidth = 250;

    const isForeignKey = (columnName: string) =>
      (tableData.structure?.foreign_keys || []).some((fk) => (fk.constrained_columns || []).includes(columnName));

    return (
      <g key={tableName} transform={`translate(${x}, ${y})`}>
        <rect
          x="0"
          y="0"
          width={tableWidth}
          height={tableHeight}
          rx="6"
          ry="6"
          className={cn('fill-gray-800 stroke-2', isExpanded ? 'stroke-indigo-500' : 'stroke-gray-600')}
        />

        <rect
          x="0"
          y="0"
          width={tableWidth}
          height={titleHeight}
          rx="6"
          ry="6"
          className={cn('fill-indigo-900 fill-opacity-70', isExpanded ? 'stroke-indigo-500' : 'stroke-gray-600')}
        />

        <text
          x={tableWidth / 2}
          y={titleHeight / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          className="fill-indigo-200 font-bold text-lg"
        >
          {tableName}
        </text>

        <rect x="0" y={titleHeight} width={tableWidth} height={headerHeight} className="fill-gray-700 stroke-gray-600" />
        <line
          x1="0"
          y1={titleHeight + headerHeight}
          x2={tableWidth}
          y2={titleHeight + headerHeight}
          className="stroke-gray-600"
        />

        <text x={10} y={titleHeight + headerHeight / 2} dominantBaseline="middle" className="fill-gray-300 font-medium text-sm">
          Column
        </text>
        <text
          x={tableWidth - 10}
          y={titleHeight + headerHeight / 2}
          textAnchor="end"
          dominantBaseline="middle"
          className="fill-gray-300 font-medium text-sm"
        >
          Type
        </text>

        {columnsToShow.map((column, idx) => {
          const isPK = primaryKeys.includes(column.name);
          const isFK = isForeignKey(column.name);

          return (
            <g key={column.name} transform={`translate(0, ${titleHeight + headerHeight + idx * rowHeight})`}>
              <rect
                x="0"
                y="0"
                width={tableWidth}
                height={rowHeight}
                className={cn(
                  'fill-opacity-20 stroke-l-4',
                  isPK ? 'fill-green-900 stroke-green-600' : isFK ? 'fill-indigo-900 stroke-indigo-600' : 'fill-gray-750 stroke-none',
                )}
              />

              <text
                x={10}
                y={rowHeight / 2}
                dominantBaseline="middle"
                className={cn('font-medium', isPK ? 'fill-green-300' : isFK ? 'fill-indigo-300' : 'fill-gray-300')}
              >
                {isPK && 'PK '}
                {isFK && 'FK '}
                {column.name}
              </text>

              <text x={tableWidth - 10} y={rowHeight / 2} textAnchor="end" dominantBaseline="middle" className="fill-gray-400 text-sm">
                {column.type}
              </text>
            </g>
          );
        })}

        <g
          transform={`translate(${tableWidth - 20}, ${titleHeight - 20})`}
          className="cursor-pointer"
          onClick={() => toggleTableExpansion(tableName)}
        >
          <circle r="12" className="fill-gray-700 stroke-gray-600" />
          {isExpanded ? (
            <path d="M -5 0 L 0 5 L 5 0" className="stroke-indigo-300 stroke-2 fill-none" />
          ) : (
            <path d="M -5 0 L 0 -5 L 5 0" className="stroke-gray-400 stroke-2 fill-none" />
          )}
        </g>
      </g>
    );
  };

  const renderRelationships = () => {
    return relationships.map((rel, idx) => {
      const fromPos = tablePositions[rel.fromTable];
      const toPos = tablePositions[rel.toTable];

      if (!fromPos || !toPos) return null;

      const fromX = fromPos.x + 125;
      const fromY = fromPos.y + 40;
      const toX = toPos.x + 125;
      const toY = toPos.y + 40;
      const dx = toX - fromX;
      const dy = toY - fromY;
      const controlX1 = fromX + dx * 0.4;
      const controlY1 = fromY + dy * 0.1;
      const controlX2 = fromX + dx * 0.6;
      const controlY2 = fromY + dy * 0.9;

      return (
        <g key={`rel-${idx}`}>
          <path
            d={`M ${fromX},${fromY} C ${controlX1},${controlY1} ${controlX2},${controlY2} ${toX},${toY}`}
            className="stroke-indigo-500 stroke-2 fill-none"
            markerEnd="url(#arrowhead)"
          />

          <text x={(fromX + toX) / 2} y={(fromY + toY) / 2 - 10} textAnchor="middle" className="fill-indigo-300 text-xs">
            {rel.fromColumn} → {rel.toColumn}
          </text>
        </g>
      );
    });
  };

  return (
    <div className="relative">
      {loading ? (
        <div className="flex h-64 flex-col items-center justify-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500" />
          <p className="text-gray-400">Loading schema data...</p>
        </div>
      ) : !schemaData ? (
        <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-gray-700 bg-gray-800 bg-opacity-50">
          <Database className="mb-3 h-12 w-12 text-gray-500" />
          <p className="text-lg text-gray-400">No schema data available</p>
        </div>
      ) : (
        <div className="overflow-auto rounded-lg border border-gray-700 bg-gray-900 p-4" style={{ maxHeight: 'calc(100vh - 220px)' }}>
          <div className="mb-4 rounded-lg border border-gray-700 bg-gray-800 p-4">
            <h2 className="mb-2 text-lg font-bold text-indigo-300">ER Diagram</h2>
            <p className="text-sm text-gray-400">
              Showing {Object.keys(schemaData.tables).length} tables and {relationships.length} relationships
            </p>
          </div>

          <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
            <svg width={svgDimensions.width} height={svgDimensions.height} className="bg-gray-850">
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" className="fill-indigo-500" />
                </marker>
              </defs>

              {renderRelationships()}

              {Object.entries(tablePositions).map(([tableName, pos]) => renderTableBox(tableName, pos.x, pos.y))}
            </svg>
          </div>
        </div>
      )}
    </div>
  );
}
