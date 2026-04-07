import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Database,
  Key,
  Link,
  RefreshCw,
  Table,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { apiClient, getErrorMessage } from '@/lib/api';
import { authStorage } from '@/lib/auth';
import type { SchemaTableData, SchemaVisualization, UserDatabase } from '@/lib/types';
import { cn } from '@/lib/utils';
import ERDiagramView from './ERDiagram';

export default function SchemaVisualizationPage() {
  const navigate = useNavigate();

  const [schemaData, setSchemaData] = useState<SchemaVisualization | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDbId, setSelectedDbId] = useState(0);
  const [databases, setDatabases] = useState<UserDatabase[]>([]);
  const [zoom, setZoom] = useState(1);
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState<'visualization' | 'erdiagram' | 'raw'>('visualization');

  const selectedDatabase = useMemo(
    () => databases.find((db) => db.id === selectedDbId) ?? null,
    [databases, selectedDbId],
  );

  const toggleTableExpansion = (tableName: string) => {
    setExpandedTables((prev) => ({
      ...prev,
      [tableName]: !prev[tableName],
    }));
  };

  const expandAllTables = () => {
    if (!schemaData) return;

    const allExpanded = Object.keys(schemaData.tables).reduce<Record<string, boolean>>((acc, tableName) => {
      acc[tableName] = true;
      return acc;
    }, {});

    setExpandedTables(allExpanded);
  };

  const collapseAllTables = () => {
    setExpandedTables({});
  };

  const fetchSchemaData = useCallback(async (dbId: number) => {
    if (!dbId) return;

    try {
      setLoading(true);
      setError(null);

      const data = await apiClient.getSchema(dbId);
      if (!data?.tables) {
        setError('Invalid schema data structure');
        return;
      }

      setSchemaData(data);

      const firstTable = Object.keys(data.tables)[0];
      if (firstTable) {
        setExpandedTables({ [firstTable]: true });
      }
    } catch (err) {
      console.error('Error fetching schema:', err);
      setError(`Failed to load schema data: ${getErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDatabases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await apiClient.getDatabases();
      setDatabases(res.data);

      if (selectedDbId === 0 && res.data.length > 0) {
        setSelectedDbId(res.data[0].id);
      } else if (res.data.length === 0) {
        setError('No databases available');
      }
    } catch (err) {
      console.error('Error fetching databases:', err);
      setError(`Failed to load databases: ${getErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  }, [selectedDbId]);

  useEffect(() => {
    if (!authStorage.isAuthenticated()) {
      navigate('/login');
      return;
    }

    void fetchDatabases();
  }, [fetchDatabases, navigate]);

  useEffect(() => {
    if (selectedDbId !== 0) {
      void fetchSchemaData(selectedDbId);
    }
  }, [fetchSchemaData, selectedDbId]);

  const handleDbChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const dbId = Number(event.target.value);
    setSelectedDbId(dbId);
    setSchemaData(null);
    setExpandedTables({});
  };

  const handleRefresh = () => {
    if (selectedDbId !== 0) {
      void fetchSchemaData(selectedDbId);
    }
  };

  const getOrganizedTables = useCallback(() => {
    if (!schemaData) return [] as string[][];

    const tablesWithIncomingFKs = new Set<string>();

    Object.values(schemaData.tables).forEach((tableData) => {
      (tableData.structure?.foreign_keys || []).forEach((fk) => {
        tablesWithIncomingFKs.add(fk.referred_table);
      });
    });

    const levels: string[][] = [];
    const topLevelTables = Object.keys(schemaData.tables).filter((tableName) => !tablesWithIncomingFKs.has(tableName));

    if (topLevelTables.length > 0) {
      levels.push(topLevelTables);
    }

    let remainingTables = Object.keys(schemaData.tables).filter((tableName) => !topLevelTables.includes(tableName));

    while (remainingTables.length > 0) {
      const currentLevel: string[] = [];
      const stillRemaining: string[] = [];

      for (const tableName of remainingTables) {
        const tableData = schemaData.tables[tableName];
        const allReferredTablesProcessed = (tableData.structure?.foreign_keys || []).every((fk) =>
          levels.flat().includes(fk.referred_table),
        );

        if (allReferredTablesProcessed) {
          currentLevel.push(tableName);
        } else {
          stillRemaining.push(tableName);
        }
      }

      if (currentLevel.length > 0) {
        levels.push(currentLevel);
      } else {
        levels.push(stillRemaining);
        break;
      }

      remainingTables = stillRemaining;
    }

    return levels;
  }, [schemaData]);

  const renderTable = (tableName: string) => {
    if (!schemaData) return null;

    const tableData = schemaData.tables[tableName] as SchemaTableData;
    const isExpanded = expandedTables[tableName] || false;

    if (!tableData.structure) {
      return (
        <div key={tableName} className="rounded-lg border border-red-700 bg-gray-800 p-4">
          <h3 className="font-bold text-red-300">{tableName}</h3>
          <p className="mt-2 text-sm text-red-200">{tableData.error || 'Table metadata unavailable'}</p>
        </div>
      );
    }

    const foreignKeys = tableData.structure.foreign_keys || [];
    const sampleData = tableData.sample_data || [];

    const isForeignKey = (columnName: string) =>
      foreignKeys.some((fk) => (fk.constrained_columns || []).includes(columnName));

    const getRelationshipDetails = (columnName: string) => {
      const fk = foreignKeys.find((currentFk) => (currentFk.constrained_columns || []).includes(columnName));
      if (!fk) return null;

      return {
        referencedTable: fk.referred_table,
        referencedColumn: fk.referred_columns?.[0],
      };
    };

    return (
      <div
        key={tableName}
        className={cn(
          'rounded-lg border shadow-lg transition-all duration-200',
          isExpanded ? 'border-indigo-500 bg-gray-800' : 'border-gray-600 bg-gray-750 hover:border-indigo-400',
        )}
      >
        <div
          className={cn(
            'flex cursor-pointer items-center justify-between p-4',
            isExpanded ? 'border-b border-gray-700' : '',
          )}
          onClick={() => toggleTableExpansion(tableName)}
        >
          <div className="flex items-center">
            <div className="mr-3 rounded-lg bg-indigo-950 p-2">
              <Table className="h-5 w-5 text-indigo-300" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-indigo-200">{tableName}</h3>
              <p className="text-xs text-gray-400">
                {tableData.structure.columns.length} columns • {sampleData.length} sample rows
              </p>
            </div>
          </div>

          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-indigo-300" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </div>

        {isExpanded && (
          <div className="p-4">
            {foreignKeys.length > 0 && (
              <div className="mb-4 rounded-lg border border-indigo-900 bg-indigo-950 bg-opacity-30 p-3">
                <h4 className="mb-2 text-sm font-semibold text-indigo-300">Relationships</h4>
                <div className="space-y-2">
                  {foreignKeys.map((fk, idx) => (
                    <div key={`${tableName}-fk-${idx}`} className="flex items-center text-sm">
                      <span className="font-medium text-indigo-400">{fk.constrained_columns?.[0]}</span>
                      <ArrowRight className="mx-2 h-4 w-4 text-indigo-500" />
                      <span className="text-green-400">
                        {fk.referred_table}.{fk.referred_columns?.[0]}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mb-4">
              <h4 className="mb-2 text-sm font-semibold text-gray-300">Columns</h4>
              <div className="max-h-64 space-y-1 overflow-y-auto pr-1">
                {tableData.structure.columns.map((column) => (
                  <div
                    key={column.name}
                    className={cn(
                      'flex items-center justify-between rounded p-2',
                      column.primary_key
                        ? 'border-l-4 border-green-600 bg-green-900 bg-opacity-20'
                        : isForeignKey(column.name)
                          ? 'border-l-4 border-indigo-600 bg-indigo-900 bg-opacity-20'
                          : 'border-l-4 border-gray-600 bg-gray-750',
                    )}
                  >
                    <div className="flex items-center">
                      {column.primary_key ? (
                        <Key className="mr-2 h-4 w-4 text-green-400" />
                      ) : isForeignKey(column.name) ? (
                        <Link className="mr-2 h-4 w-4 text-indigo-400" />
                      ) : null}

                      <span className="font-medium text-gray-200">{column.name}</span>

                      {column.primary_key && (
                        <span className="ml-2 rounded bg-green-900 px-1.5 py-0.5 text-xs text-green-300">PK</span>
                      )}

                      {isForeignKey(column.name) && (
                        <span className="ml-2 rounded bg-indigo-900 px-1.5 py-0.5 text-xs text-indigo-300">FK</span>
                      )}

                      {!column.nullable && !column.primary_key && !isForeignKey(column.name) && (
                        <span className="ml-2 rounded bg-gray-700 px-1.5 py-0.5 text-xs text-gray-300">NOT NULL</span>
                      )}
                    </div>

                    <div className="flex items-center">
                      <span className="text-sm text-gray-400">{column.type}</span>

                      {isForeignKey(column.name) && (
                        <div className="ml-3 flex items-center text-xs text-indigo-300">
                          <ArrowRight className="mx-1 h-3 w-3" />
                          {(() => {
                            const rel = getRelationshipDetails(column.name);
                            return rel ? `${rel.referencedTable}.${rel.referencedColumn}` : '';
                          })()}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {sampleData.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold text-gray-300">Sample Data</h4>
                <div className="overflow-x-auto rounded-lg border border-gray-700">
                  <table className="w-full table-auto">
                    <thead>
                      <tr className="bg-gray-800">
                        {Object.keys(sampleData[0]).map((key) => (
                          <th
                            key={key}
                            className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-400"
                          >
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sampleData.map((row, idx) => (
                        <tr key={`${tableName}-row-${idx}`} className={idx % 2 === 0 ? 'bg-gray-750' : 'bg-gray-800'}>
                          {Object.values(row).map((value, valueIdx) => (
                            <td key={`${tableName}-row-${idx}-col-${valueIdx}`} className="whitespace-nowrap px-3 py-2 text-sm text-gray-300">
                              {String(value)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const organizedTables = getOrganizedTables();
  return (
    <div className="flex h-screen flex-col bg-gray-900 text-gray-200">
      <header className="flex items-center justify-between border-b border-gray-700 bg-gray-800 px-6 py-4 shadow-md">
        <div className="flex items-center">
          <div className="mr-3 rounded-full bg-indigo-900 p-2">
            <Database className="h-6 w-6 text-indigo-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-indigo-300">SpeakQL Schema Visualization</h1>
            {selectedDatabase && (
              <p className="text-sm text-gray-400">
                Database: <span className="text-indigo-300">{selectedDatabase.db_name}</span>
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <select
            value={selectedDbId}
            onChange={handleDbChange}
            className="rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="0" disabled>
              Select Database
            </option>
            {databases.map((db) => (
              <option key={db.id} value={db.id}>
                {db.db_name}
              </option>
            ))}
          </select>

          <div className="flex gap-2">
            <Button
              onClick={handleRefresh}
              disabled={loading || selectedDbId === 0}
              className="bg-gray-700 hover:bg-gray-600"
              title="Refresh Schema"
            >
              <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
            </Button>

            <Button onClick={() => setZoom((prev) => Math.min(prev + 0.1, 1.5))} className="bg-gray-700 hover:bg-gray-600" title="Zoom In">
              <ZoomIn className="h-5 w-5" />
            </Button>

            <Button onClick={() => setZoom(1)} className="bg-gray-700 text-xs hover:bg-gray-600" title="Reset Zoom">
              {zoom.toFixed(1)}x
            </Button>

            <Button onClick={() => setZoom((prev) => Math.max(prev - 0.1, 0.6))} className="bg-gray-700 hover:bg-gray-600" title="Zoom Out">
              <ZoomOut className="h-5 w-5" />
            </Button>

            <Button size="sm" className="bg-gray-700 text-gray-300 hover:bg-indigo-500" onClick={() => navigate('/chat')}>
              DB.Chat
            </Button>
          </div>
        </div>
      </header>

      <div className="border-b border-gray-700 bg-gray-800 px-6">
        <div className="flex">
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'visualization' ? 'border-b-2 border-indigo-500 text-indigo-300' : 'text-gray-400 hover:text-gray-200'
            }`}
            onClick={() => setActiveTab('visualization')}
          >
            Visualization
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'erdiagram' ? 'border-b-2 border-indigo-500 text-indigo-300' : 'text-gray-400 hover:text-gray-200'
            }`}
            onClick={() => setActiveTab('erdiagram')}
          >
            ER Diagram
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'raw' ? 'border-b-2 border-indigo-500 text-indigo-300' : 'text-gray-400 hover:text-gray-200'
            }`}
            onClick={() => setActiveTab('raw')}
          >
            Raw JSON
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-red-700 bg-red-950/40 p-4 text-red-200">
            {error}
          </div>
        )}

        {activeTab === 'visualization' && (
          <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }} className="space-y-6">
            <div className="flex gap-2">
              <Button onClick={expandAllTables} className="bg-gray-700 hover:bg-gray-600">
                Expand All
              </Button>
              <Button onClick={collapseAllTables} className="bg-gray-700 hover:bg-gray-600">
                Collapse All
              </Button>
            </div>

            {organizedTables.map((level, levelIndex) => (
              <div key={`level-${levelIndex}`} className="grid gap-4 lg:grid-cols-2">
                {level.map((tableName) => renderTable(tableName))}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'erdiagram' && schemaData && (
          <ERDiagramView
            schemaData={schemaData}
            zoom={zoom}
            loading={loading}
            expandedTables={expandedTables}
            toggleTableExpansion={toggleTableExpansion}
          />
        )}

        {activeTab === 'raw' && schemaData && (
          <pre className="overflow-auto rounded-lg border border-gray-700 bg-gray-800 p-4 text-sm text-gray-300">
            {JSON.stringify(schemaData, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
