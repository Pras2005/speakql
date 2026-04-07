import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format, parseISO } from 'date-fns';
import { ArrowLeft, Calendar, Check, Clock, Copy, Database, Edit2 } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiClient } from '@/lib/api';
import { authStorage } from '@/lib/auth';
import type { QueryHistoryItem, UserDatabase } from '@/lib/types';

type GroupedQueries = Record<string, QueryHistoryItem[]>;
type FilterMode = 'all' | 'success' | 'error';

export default function QueryHistoryPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const dbIdParam = searchParams.get('dbId');

  const [selectedDbId, setSelectedDbId] = useState<number>(dbIdParam ? Number(dbIdParam) : 0);
  const [databases, setDatabases] = useState<UserDatabase[]>([]);
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  useEffect(() => {
    if (!authStorage.isAuthenticated()) {
      navigate('/login');
      return;
    }

    void fetchDatabases();
  }, [navigate]);

  useEffect(() => {
    if (dbIdParam && Number(dbIdParam) !== selectedDbId) {
      setSelectedDbId(Number(dbIdParam));
    }
  }, [dbIdParam, selectedDbId]);

  useEffect(() => {
    if (selectedDbId === 0) {
      return;
    }

    if (dbIdParam !== selectedDbId.toString()) {
      setSearchParams({ dbId: selectedDbId.toString() });
    }

    void fetchQueryHistory(selectedDbId);
  }, [dbIdParam, selectedDbId, setSearchParams]);

  const fetchDatabases = async () => {
    try {
      const response = await apiClient.getDatabases();
      const nextDatabases = response.data;
      setDatabases(nextDatabases);

      if (selectedDbId === 0 && nextDatabases.length > 0 && !dbIdParam) {
        setSelectedDbId(nextDatabases[0].id);
      }
    } catch (error) {
      console.error('Error fetching databases:', error);
    }
  };

  const fetchQueryHistory = async (dbId: number) => {
    try {
      setLoading(true);
      const response = await apiClient.getQueryHistory(dbId);
      const sortedHistory = [...response.data].sort(
        (a, b) => new Date(b.executed_at).getTime() - new Date(a.executed_at).getTime(),
      );
      setQueryHistory(sortedHistory);
    } catch (error) {
      console.error('Error fetching query history:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, index: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleDatabaseChange = (value: string) => {
    setSelectedDbId(Number(value));
  };

  const handleReRun = (query: QueryHistoryItem) => {
    sessionStorage.setItem(
      'reRunQuery',
      JSON.stringify({
        prompt: query.original_prompt ?? '',
        raw_sql: query.executed_sql || query.generated_sql || '',
        db_id: selectedDbId,
      }),
    );
    navigate('/chat');
  };

  const groupQueriesByDate = (items: QueryHistoryItem[]): GroupedQueries => {
    return items.reduce<GroupedQueries>((groups, query) => {
      const dateKey = new Date(query.executed_at).toLocaleDateString();
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(query);
      return groups;
    }, {});
  };

  const formatTime = (timestamp: string) => {
    try {
      return format(parseISO(timestamp), 'h:mm a');
    } catch {
      return timestamp;
    }
  };

  const formatDateLabel = (dateStr: string) => {
    const today = new Date().toLocaleDateString();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toLocaleDateString();

    if (dateStr === today) return 'Today';
    if (dateStr === yesterdayStr) return 'Yesterday';
    return dateStr;
  };

  const getStatus = (query: QueryHistoryItem) => (query.success ? 'success' : 'error');
  const getSql = (query: QueryHistoryItem) => query.executed_sql || query.generated_sql || '-- No SQL recorded';
  const isVisibleForFilter = (query: QueryHistoryItem, filter: FilterMode) => {
    if (filter === 'all') return true;
    return filter === 'success' ? query.success : !query.success;
  };

  const groupedQueries = useMemo(() => groupQueriesByDate(queryHistory), [queryHistory]);

  const statusBadge = (status: 'success' | 'error') => {
    const isSuccess = status === 'success';
    return (
      <span
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
          isSuccess ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}
      >
        {isSuccess ? 'success' : 'error'}
      </span>
    );
  };

  const renderQuerySection = (filter: FilterMode) => (
    <>
      {Object.entries(groupedQueries).map(([date, queries]) => {
        const filteredQueries = queries.filter((query) => isVisibleForFilter(query, filter));
        if (filteredQueries.length === 0) {
          return null;
        }

        return (
          <div key={date}>
            <h2 className="mb-3 flex items-center text-lg font-semibold text-gray-700">
              <Calendar size={18} className="mr-2 text-indigo-500" />
              {formatDateLabel(date)}
            </h2>
            <div className="space-y-4">
              {filteredQueries.map((query, idx) => {
                const sql = getSql(query);
                const status = getStatus(query);
                const copyKey = `${filter}-${query.id}-${idx}`;

                return (
                  <Card
                    key={query.id}
                    className="overflow-hidden bg-white shadow-md transition-shadow duration-300 hover:shadow-lg"
                  >
                    <CardHeader className="border-b border-gray-200 bg-gray-50 px-4 py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Clock size={16} className="text-gray-500" />
                          <span className="text-sm text-gray-600">{formatTime(query.executed_at)}</span>
                          {statusBadge(status)}
                          <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs uppercase tracking-wide text-gray-700">
                            {query.event_type}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 gap-1 text-gray-600 hover:bg-gray-200"
                            onClick={() => handleReRun(query)}
                          >
                            <Edit2 size={14} />
                            <span className="text-xs">Edit in Chat</span>
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 w-8 rounded-full hover:bg-gray-200"
                            onClick={() => copyToClipboard(sql, copyKey)}
                          >
                            {copiedIndex === copyKey ? <Check size={16} /> : <Copy size={16} />}
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <SyntaxHighlighter
                        language="sql"
                        style={oneDark}
                        customStyle={{
                          margin: '0',
                          padding: '1rem',
                          borderRadius: '0',
                          fontSize: '0.875rem',
                          lineHeight: '1.5',
                        }}
                      >
                        {sql}
                      </SyntaxHighlighter>

                      {query.original_prompt && (
                        <div className="border-t border-indigo-100 bg-indigo-50 px-4 py-3">
                          <p className="text-sm text-gray-700">
                            <span className="font-medium">Prompt:</span> {query.original_prompt}
                          </p>
                        </div>
                      )}

                      {query.error_message && (
                        <div className="border-t border-red-100 bg-red-50 px-4 py-3">
                          <p className="text-sm text-red-700">
                            <span className="font-medium">Error:</span> {query.error_message}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        );
      })}
    </>
  );

  return (
    <div className="flex h-full flex-col bg-gradient-to-br from-indigo-100 to-white">
      <div className="p-6">
        <div className="mb-6 flex items-center">
          <Button variant="ghost" className="mr-2" onClick={() => navigate('/')}>
            <ArrowLeft size={20} />
          </Button>
          <h1 className="mr-4 text-3xl font-bold">Query History</h1>

          <div className="ml-auto">
            <Select value={selectedDbId.toString()} onValueChange={handleDatabaseChange}>
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Select database" />
              </SelectTrigger>
              <SelectContent>
                {databases.map((db) => (
                  <SelectItem key={db.id} value={db.id.toString()}>
                    {db.db_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500" />
          </div>
        ) : databases.length === 0 ? (
          <Card className="bg-white shadow-md">
            <CardContent className="pt-6">
              <div className="py-10 text-center">
                <Database className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">No databases found</h3>
                <p className="mt-1 text-sm text-gray-500">You do not have access to any databases yet.</p>
                <Button className="mt-4" onClick={() => navigate('/')}>
                  Go to Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : queryHistory.length === 0 ? (
          <Card className="bg-white shadow-md">
            <CardContent className="pt-6">
              <div className="py-10 text-center">
                <Database className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">No query history</h3>
                <p className="mt-1 text-sm text-gray-500">
                  There is no query history for this database yet.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Tabs defaultValue="all" className="w-full">
              <TabsList className="mb-4">
                <TabsTrigger value="all">All Events</TabsTrigger>
                <TabsTrigger value="success">Successful</TabsTrigger>
                <TabsTrigger value="error">Failed</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-6">
                {renderQuerySection('all')}
              </TabsContent>

              <TabsContent value="success" className="space-y-6">
                {renderQuerySection('success')}
              </TabsContent>

              <TabsContent value="error" className="space-y-6">
                {renderQuerySection('error')}
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>
    </div>
  );
}
