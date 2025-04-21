import { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { motion } from 'framer-motion';
import axios from 'axios';
import { API_URL } from '@/constants';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  Check, 
  Download, 
  RefreshCw, 
  Copy, 
  Edit2, 
  Save, 
  Database, 
  ChevronDown, 
  ChevronUp, 
  Maximize2, 
  Minimize2,
  MessageSquare,
  Plus,
  Trash2,
  Settings,
  ChevronLeft,
  ChevronRight,
  Clock,
  GripVertical,
  Send,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import useAuth from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';

// Add global style for scrollbars
const GlobalStyles = () => {
  useEffect(() => {
    // Add custom scrollbar styles
    const style = document.createElement('style');
    style.textContent = `
      /* Custom scrollbar styles */
      ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }
      ::-webkit-scrollbar-track {
        background: #1e1e2e;
      }
      ::-webkit-scrollbar-thumb {
        background: #3f3f5a;
        border-radius: 4px;
      }
      ::-webkit-scrollbar-thumb:hover {
        background: #555;
      }
      ::-webkit-scrollbar-corner {
        background: #1e1e2e;
      }
      
      /* Set color scheme for modern browsers */
      html {
        color-scheme: dark;
      }
    `;
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);
  
  return null;
};

type QueryResponse = {
  raw_sql: string;
  confirmation_required: boolean;
  message: string;
  result?: any;
  status?: string;
  error?: any;
  timestamp?: string;
};

type UserDatabaseType = {
  host: string;
  port: string;
  db_user: string;
  db_password: string;
  db_name: string;
};

type DatabasesType = {
  id: number;
  user_id: number;
  host: string;
  port: number;
  db_user: string;
  db_name: string;
  created_at: string;
};

type QueryHistoryItem = {
  id: number;
  user_database_id: number;
  original_prompt: string;
  generated_sql: string;
  success: boolean;
  error_message?: string;
  executed_at: string;
};

type ConversationType = {
  id: string;
  title: string;
  prompts: string[];
  responses: QueryResponse[];
  timestamp: string;
};

const token = localStorage.getItem('token');

export default function ChatbotPage() {
  // State for current chat
  const [input, setInput] = useState('');
  const [prompts, setPrompts] = useState<string[]>([]);
  const [rawSQL, setRawSQL] = useState('');
  const [responses, setResponses] = useState<QueryResponse[]>([]);
  
  // Database configuration states
  const [dbConfig, setDbConfig] = useState<UserDatabaseType>({
    host: '',
    port: '',
    db_user: '',
    db_password: '',
    db_name: '',
  });
  const [loading, setLoading] = useState(false);
  const [databases, setDatabases] = useState<DatabasesType[]>([]);
  const [selectedDbId, setSelectedDbId] = useState<number>(0);
  
  // History and UI states
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([]);
  const [conversations, setConversations] = useState<ConversationType[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [isEditingSql, setIsEditingSql] = useState(false);
  const [editedSql, setEditedSql] = useState('');
  const [editingSqlIndex, setEditingSqlIndex] = useState<number | null>(null);
  const [isChatExpanded, setIsChatExpanded] = useState(true);
  const [chatHeight, setChatHeight] = useState('500px');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'chat' | 'history'>('chat');
  
  // Pagination for query history
  const [historyPage, setHistoryPage] = useState(0);
  const HISTORY_ITEMS_PER_PAGE = 10;
  
  // New state for resizable sidebar
  const [sidebarWidth, setSidebarWidth] = useState(256); // Default width in pixels
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const resizerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { requestLogout } = useAuth();
  const navigate = useNavigate();

  // Function to scroll to bottom
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const toggleChatSize = () => {
    setIsChatExpanded(!isChatExpanded);
    setChatHeight(isChatExpanded ? '500px' : '80vh');
  };

  // Handle sidebar resizing
  useEffect(() => {
    const handleMouseDown = (e: MouseEvent) => {
      e.preventDefault();
      setIsResizing(true);
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      // Calculate new width based on mouse position
      const newWidth = e.clientX;
      
      // Set min and max constraints
      if (newWidth >= 180 && newWidth <= 500) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    // Add event listener to the resizer element
    const resizer = resizerRef.current;
    if (resizer) {
      resizer.addEventListener('mousedown', handleMouseDown);
    }

    // Cleanup
    return () => {
      if (resizer) {
        resizer.removeEventListener('mousedown', handleMouseDown);
      }
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // Auto-resize textarea based on content
  const autoResizeTextarea = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  useEffect(() => {
    autoResizeTextarea();
  }, [input]);

  // Generate a unique ID for new conversations
  const generateId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  };

  // Create a new conversation
  const createNewConversation = () => {
    const newId = generateId();
    const newConversation = {
      id: newId,
      title: 'New Conversation',
      prompts: [],
      responses: [],
      timestamp: new Date().toISOString(),
    };
    
    setConversations([newConversation, ...conversations]);
    setActiveConversationId(newId);
    setPrompts([]);
    setResponses([]);
    setRawSQL('');
  };

  // Load a conversation from history
  const loadConversation = (id: string) => {
    const conversation = conversations.find(c => c.id === id);
    if (conversation) {
      setActiveConversationId(id);
      setPrompts(conversation.prompts);
      setResponses(conversation.responses);
      setRawSQL('');
      setIsEditingSql(false);
      setEditingSqlIndex(null);
      setEditedSql('');
    }
  };

  // Delete a conversation
  const deleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      const updatedConversations = conversations.filter(c => c.id !== id);
      setConversations(updatedConversations);
      
      if (activeConversationId === id) {
        if (updatedConversations.length > 0) {
          loadConversation(updatedConversations[0].id);
        } else {
          createNewConversation();
        }
      }
    }
  };

  // Update conversation title based on first prompt
  const updateConversationTitle = (id: string, prompt: string) => {
    setConversations(prevConversations => 
      prevConversations.map(conv => 
        conv.id === id 
          ? { 
              ...conv, 
              title: prompt.length > 30 ? prompt.substring(0, 30) + '...' : prompt 
            } 
          : conv
      )
    );
  };

  // Fetch query history for a specific database
  const fetchQueryHistory = async (dbId: number) => {
    if (!dbId) return;
    
    try {
      setIsHistoryLoading(true);
      const res = await axios.get(`${API_URL}/query-history/${dbId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setQueryHistory(res.data);
      setHistoryPage(0); // Reset to first page when fetching new history
    } catch (error) {
      console.error("Error fetching query history:", error);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  // Get paginated query history
  const getPaginatedHistory = () => {
    const startIndex = historyPage * HISTORY_ITEMS_PER_PAGE;
    return queryHistory.slice(startIndex, startIndex + HISTORY_ITEMS_PER_PAGE);
  };

  // Navigation for history pagination
  const goToPreviousHistoryPage = () => {
    if (historyPage > 0) {
      setHistoryPage(historyPage - 1);
    }
  };

  const goToNextHistoryPage = () => {
    if ((historyPage + 1) * HISTORY_ITEMS_PER_PAGE < queryHistory.length) {
      setHistoryPage(historyPage + 1);
    }
  };

  // Database operations
  const requestDeleteDatabase = async (id: number) => {
    try {
      setLoading(true);
      await axios.delete(`${API_URL}/databases/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      await requestGetDatabases();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const requestGetDatabases = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_URL}/get_databases`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setDatabases(res.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const requestAddDatabase = async () => {
    try {
      setLoading(true);
      await axios.post(`${API_URL}/databases`, dbConfig, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      await requestGetDatabases();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
      setDbConfig({
        host: '',
        port: '',
        db_user: '',
        db_password: '',
        db_name: '',
      });
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    // Optional: Auto-submit the suggestion
    setTimeout(() => {
      requestGenerateQuery(suggestion);
    }, 100);
  };

  // Chat operations
  const requestGenerateQuery = async (promptText?: string) => {
    const textToSend = promptText || input;
    try {
      if (!textToSend.trim()) return;
      setLoading(true);
      
      // Create a new conversation if none is active
      if (!activeConversationId) {
        createNewConversation();
      }
      
      // Update local state
      const newPrompts = [...prompts, textToSend];
      setPrompts(newPrompts);

      const res = await axios.post(
        `${API_URL}/agent/generate-sql`,
        {
          prompt: textToSend,
          db_id: selectedDbId,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      setRawSQL(res.data.raw_sql);

      const response = {
        ...res.data,
        timestamp: new Date().toISOString(),
      };
      
      const newResponses = [...responses, response];
      setResponses(newResponses);
      
      // Update conversation in state
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.id === activeConversationId 
            ? { 
                ...conv, 
                prompts: newPrompts, 
                responses: newResponses,
                timestamp: new Date().toISOString()
              } 
            : conv
        )
      );
      
      // Update conversation title if this is the first message
      if (prompts.length === 0 && activeConversationId) {
        updateConversationTitle(activeConversationId, textToSend);
      }

      // Refresh query history if we're in history view
      if (viewMode === 'history') {
        fetchQueryHistory(selectedDbId);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setInput('');
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  const requestExecuteSQL = async (sql = rawSQL) => {
    try {
      setLoading(true);
      
      // Create a new conversation if none is active
      if (!activeConversationId) {
        createNewConversation();
      }
      
      const newPrompts = [...prompts, 'Execute SQL'];
      setPrompts(newPrompts);

      const res = await axios.post(
        `${API_URL}/agent/execute-sql`,
        {
          raw_sql: sql || rawSQL,
          db_id: selectedDbId,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      // Create a successful response object with the query results
      const successResponse: QueryResponse = {
        raw_sql: sql || rawSQL,
        confirmation_required: false,
        message: 'Query executed successfully',
        result: res.data.result,
        status: res.data.status,
        error: res.data.error,
        timestamp: new Date().toISOString(),
      };

      const newResponses = [...responses, successResponse];
      setResponses(newResponses);
      
      // Update conversation in state
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.id === activeConversationId 
            ? { 
                ...conv, 
                prompts: newPrompts, 
                responses: newResponses,
                timestamp: new Date().toISOString()
              } 
            : conv
        )
      );

      // Refresh query history if we're in history view
      if (viewMode === 'history') {
        fetchQueryHistory(selectedDbId);
      }
    } catch (error) {
      console.error(error);
      // Handle failed execution
      const errorResponse: QueryResponse = {
        raw_sql: sql || rawSQL,
        confirmation_required: false,
        message: `Error executing query: ${
          error instanceof Error ? error.message : 'Unknown error'
        }`,
        status: 'error',
        timestamp: new Date().toISOString(),
      };
      
      const newResponses = [...responses, errorResponse];
      setResponses(newResponses);
      
      // Update conversation in state
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.id === activeConversationId 
            ? { 
                ...conv, 
                prompts: [...prompts, 'Execute SQL'], 
                responses: newResponses,
                timestamp: new Date().toISOString()
              } 
            : conv
        )
      );
    } finally {
      setRawSQL('');
      setIsEditingSql(false);
      setEditingSqlIndex(null);
      setEditedSql('');
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  // Utility functions
  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const startEditingSql = (sql: string, index: number) => {
    setEditedSql(sql);
    setIsEditingSql(true);
    setEditingSqlIndex(index);
  };

  const saveEditedSql = (index: number) => {
    // Update the response with edited SQL
    const updatedResponses = [...responses];
    if (index < updatedResponses.length) {
      updatedResponses[index] = {
        ...updatedResponses[index],
        raw_sql: editedSql,
      };
      setResponses(updatedResponses);
      
      // Update conversation in state
      if (activeConversationId) {
        setConversations(prevConversations => 
          prevConversations.map(conv => 
            conv.id === activeConversationId 
              ? { ...conv, responses: updatedResponses } 
              : conv
          )
        );
      }
    }

    // Update rawSQL if this is the last SQL being edited
    if (index === responses.length - 1) {
      setRawSQL(editedSql);
    }

    // Exit edit mode
    setIsEditingSql(false);
    setEditingSqlIndex(null);
    setEditedSql('');
  };

  const exportResultsAsCSV = (result: any[]) => {
    if (!result || result.length === 0) return;

    const headers = Object.keys(result[0]);
    const csvRows = [
      headers.join(','),
      ...result.map((row) =>
        headers
          .map((header) => (typeof row[header] === 'string' ? `"${row[header]}"` : row[header]))
          .join(','),
      ),
    ];

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `query_results_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const clearConversation = () => {
    if (window.confirm('Are you sure you want to clear the conversation?')) {
      setPrompts([]);
      setResponses([]);
      setRawSQL('');
      setIsEditingSql(false);
      setEditingSqlIndex(null);
      setEditedSql('');
      
      // Update conversation in state if active
      if (activeConversationId) {
        setConversations(prevConversations => 
          prevConversations.map(conv => 
            conv.id === activeConversationId 
              ? { 
                  ...conv, 
                  prompts: [], 
                  responses: [],
                  timestamp: new Date().toISOString()
                } 
              : conv
          )
        );
      }
    }
  };

  // Toggle between chat and history views
  const toggleViewMode = (mode: 'chat' | 'history') => {
    setViewMode(mode);
    if (mode === 'history' && selectedDbId) {
      fetchQueryHistory(selectedDbId);
    }
  };

  // Helper function to render query results as a table
  const renderQueryResults = (result: any) => {
    if (!result || !Array.isArray(result) || result.length === 0) {
      return <p className="text-gray-400 italic">No results returned</p>;
    }

    // Extract column headers from the first result object
    const headers = Object.keys(result[0]);

    return (
      <div className="mt-3 rounded-lg border border-gray-700">
        <div className="flex justify-between items-center p-2 bg-gray-800 border-b border-gray-700">
          <span className="font-medium text-gray-300">Query Results ({result.length} rows)</span>
          <Button
            size="sm"
            variant="outline"
            className="text-xs flex items-center gap-1 bg-gray-700 text-gray-300 hover:bg-gray-600 border-gray-600"
            onClick={() => exportResultsAsCSV(result)}
          >
            <Download size={14} /> Export CSV
          </Button>
        </div>
        <div className="overflow-x-auto max-h-96">
          <table className="min-w-full bg-gray-900">
            <thead className="bg-gray-800 sticky top-0">
              <tr>
                {headers.map((header, idx) => (
                  <th
                    key={idx}
                    className="py-2 px-4 border-b border-gray-700 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.map((row: any, rowIdx: number) => (
                <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-gray-900' : 'bg-gray-800'}>
                  {headers.map((header, colIdx) => (
                    <td
                      key={`${rowIdx}-${colIdx}`}
                      className="py-2 px-4 border-b border-gray-700 text-sm text-gray-300"
                    >
                      {String(row[header] !== null ? row[header] : 'null')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch (e) {
      return dateString;
    }
  };

  // Initialize with a new conversation if none exists
  useEffect(() => {
    if (conversations.length === 0) {
      createNewConversation();
    } else if (!activeConversationId) {
      setActiveConversationId(conversations[0].id);
      setPrompts(conversations[0].prompts);
      setResponses(conversations[0].responses);
    }
  }, [conversations]);

  useEffect(() => {
    scrollToBottom();
  }, [prompts, responses]);

  // Fetch databases on component mount
  useEffect(() => {
    requestGetDatabases();
    
    // Load conversations from localStorage or backend in a real app
    // For this example, we'll just create a sample conversation
    if (conversations.length === 0) {
      createNewConversation();
    }
  }, []);

  // Fetch query history when selectedDbId changes and we're in history view
  useEffect(() => {
    if (selectedDbId && viewMode === 'history') {
      fetchQueryHistory(selectedDbId);
    }
  }, [selectedDbId, viewMode]);

  return (
    <>
      <GlobalStyles />
      <div className="flex h-screen w-screen bg-gray-900">
        {/* Sidebar with dynamic width */}
        {isSidebarOpen && (
          <div 
            ref={sidebarRef}
            className="bg-gray-800 border-r border-gray-700 flex flex-col overflow-hidden"
            style={{ 
              width: `${sidebarWidth}px`, 
              transition: isResizing ? 'none' : 'width 0.2s ease-in-out',
              minWidth: '180px',
              maxWidth: '500px'
            }}
          >
            <div className="p-4 border-b border-gray-700">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-200 flex items-center">
                  <Database className="text-indigo-300 w-5 h-5 mr-2" />
                  SpeakQL
                </h2>
              </div>
            </div>
            
            <div className="flex border-b border-gray-700">
              <button
                className={`flex-1 p-3 text-center ${viewMode === 'chat' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-700'}`}
                onClick={() => toggleViewMode('chat')}
              >
                <MessageSquare size={16} className="inline-block mr-2" />
                Chat
              </button>
              <button
                className={`flex-1 p-3 text-center ${viewMode === 'history' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-700'}`}
                onClick={() => toggleViewMode('history')}
              >
                <Clock size={16} className="inline-block mr-2" />
                History
              </button>
            </div>
            
            {viewMode === 'chat' ? (
              <>
                <div className="p-3 border-b border-gray-700">
                  <Button 
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                    onClick={createNewConversation}
                  >
                    <Plus size={16} className="mr-2" />
                    New Chat
                  </Button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-2">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      onClick={() => loadConversation(conv.id)}
                      className={`flex justify-between items-center p-3 mb-1 rounded-lg cursor-pointer transition-colors ${
                        activeConversationId === conv.id 
                          ? 'bg-gray-700 text-white' 
                          : 'text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="truncate font-medium">
                          {conv.title || 'New Conversation'}
                        </div>
                        <div className="text-xs text-gray-400 truncate">
                          {formatDate(conv.timestamp)}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 rounded-full text-gray-400 hover:text-gray-200 hover:bg-gray-600"
                        onClick={(e) => deleteConversation(conv.id, e)}
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  ))}
                </div>
                
                <div className="p-3 border-t border-gray-700">
                  <Button 
                    className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300"
                    onClick={clearConversation}
                  >
                    <RefreshCw size={16} className="mr-2" />
                    Clear Current Chat
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex flex-col h-full">
                <div className="flex-1 overflow-y-auto p-2">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2 px-2">
                    Query History
                  </h3>
                  
                  {isHistoryLoading ? (
                    <div className="flex justify-center items-center h-32">
                      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
                    </div>
                  ) : getPaginatedHistory().length === 0 ? (
                    <div className="text-center text-gray-400 py-8">
                      <p>No query history found</p>
                      {!selectedDbId && <p className="text-sm mt-2">Select a database to view history</p>}
                    </div>
                  ) : (
                    getPaginatedHistory().map((item) => (
                      <div
                        key={item.id}
                        className="p-3 mb-2 bg-gray-700 rounded-lg"
                      >
                        <div className="mb-2">
                          <SyntaxHighlighter
                            language="sql"
                            style={oneDark}
                            customStyle={{
                              padding: '0.75rem',
                              borderRadius: '0.5rem',
                              fontSize: '0.75rem',
                              lineHeight: '1.4',
                              maxHeight: '150px',
                              overflow: 'auto'
                            }}
                          >
                            {item.generated_sql}
                          </SyntaxHighlighter>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className={`px-2 py-1 rounded-full ${item.success ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                            {item.success ? 'Success' : 'Failed'}
                          </span>
                          <span className="text-gray-400">{formatDate(item.executed_at)}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                
                {/* Pagination controls */}
                {queryHistory.length > HISTORY_ITEMS_PER_PAGE && (
                  <div className="p-3 border-t border-gray-700 flex justify-between items-center">
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-gray-300 border-gray-600 hover:bg-gray-700"
                      onClick={goToPreviousHistoryPage}
                      disabled={historyPage === 0}
                    >
                      <ChevronsLeft size={16} className="mr-1" /> Previous
                    </Button>
                    
                    <span className="text-sm text-gray-400">
                      Page {historyPage + 1} of {Math.ceil(queryHistory.length / HISTORY_ITEMS_PER_PAGE)}
                    </span>
                    
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-gray-300 border-gray-600 hover:bg-gray-700"
                      onClick={goToNextHistoryPage}
                      disabled={(historyPage + 1) * HISTORY_ITEMS_PER_PAGE >= queryHistory.length}
                    >
                      Next <ChevronsRight size={16} className="ml-1" />
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        {/* Resizer handle */}
        {isSidebarOpen && (
          <div 
            ref={resizerRef}
            className={`w-1 cursor-col-resize hover:bg-indigo-500 active:bg-indigo-600 flex items-center justify-center ${isResizing ? 'bg-indigo-500' : 'bg-gray-600'}`}
            title="Drag to resize"
            style={{ cursor: 'col-resize' }}
          >
            <div className="h-8 flex items-center justify-center">
              <GripVertical size={12} className="text-gray-400" />
            </div>
          </div>
        )}

        {/* Main content area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="px-6 py-4 shadow-md bg-gray-800 z-10 flex justify-between items-center border-b border-gray-700">
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="sm"
                className="mr-4 h-10 w-10 rounded-full text-gray-400 hover:text-gray-200 hover:bg-gray-700"
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              >
                {isSidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
              </Button>
              
              <h1 className="text-4xl font-bold text-indigo-300 flex items-center">
                <div className="bg-indigo-900 p-2 rounded-full mr-3">
                  <Database className="text-indigo-300 w-6 h-6" />
                </div>
                SpeakQL
                <span className="text-lg text-gray-400 italic font-medium mx-4">
                  {selectedDbId !== 0 && databases.find((db) => db.id === selectedDbId)?.db_name
                    ? `(${databases.find((db) => db.id === selectedDbId)?.db_name})`
                    : '(No database selected)'}
                </span>
              </h1>
            </div>

            <div className="flex gap-4">
              {/* Main Dropdown Menu for Actions */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-4 py-2">
                    <Settings size={18} className="mr-2" />
                    Settings
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="space-y-2 bg-gray-800 border-gray-700">
                  {/* Configure DB Button */}
                  <DropdownMenuItem onClick={(e) => e.preventDefault()} className="text-gray-300 hover:bg-gray-700 focus:bg-gray-700">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                          Configure DB
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="space-y-4 bg-gray-800 border-gray-700">
                        <DialogHeader>
                          <DialogTitle className="text-gray-200">Database Configuration</DialogTitle>
                        </DialogHeader>
                        <Input
                          placeholder="Host"
                          value={dbConfig.host}
                          onChange={(e) => setDbConfig({ ...dbConfig, host: e.target.value })}
                          className="bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500"
                        />
                        <Input
                          placeholder="Port"
                          value={dbConfig.port}
                          onChange={(e) => setDbConfig({ ...dbConfig, port: e.target.value })}
                          className="bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500"
                        />
                        <Input
                          placeholder="User"
                          value={dbConfig.db_user}
                          onChange={(e) => setDbConfig({ ...dbConfig, db_user: e.target.value })}
                          className="bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500"
                        />
                        <Input
                          placeholder="Password"
                          type="password"
                          value={dbConfig.db_password}
                          onChange={(e) => setDbConfig({ ...dbConfig, db_password: e.target.value })}
                          className="bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500"
                        />
                        <Input
                          placeholder="Database Name"
                          value={dbConfig.db_name}
                          onChange={(e) => setDbConfig({ ...dbConfig, db_name: e.target.value })}
                          className="bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500"
                        />

                        <Button
                          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                          onClick={requestAddDatabase}
                          disabled={loading}
                        >
                          {loading ? 'Adding...' : 'Add database'}
                        </Button>
                      </DialogContent>
                    </Dialog>
                  </DropdownMenuItem>

                  {/* View Databases Button */}
                  <DropdownMenuItem onClick={(e) => e.preventDefault()} className="text-gray-300 hover:bg-gray-700 focus:bg-gray-700">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button className="w-full bg-gray-700 hover:bg-gray-600 text-gray-200">
                          View Databases
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="space-y-4 bg-gray-800 border-gray-700">
                        <DialogHeader>
                          <DialogTitle className="text-gray-200">Connected Databases</DialogTitle>
                        </DialogHeader>
                        <ul className="space-y-2">
                          {databases.length === 0 ? (
                            <p className="text-gray-400">No databases found.</p>
                          ) : (
                            databases.map((db) => (
                              <li
                                key={db.id}
                                className="flex items-center justify-between bg-gray-700 px-4 py-2 rounded-lg shadow-sm"
                              >
                                <div className="flex items-center gap-2">
                                  <div className="text-gray-200">
                                    <strong>{db.db_name}</strong> — {db.host}:{db.port}
                                  </div>
                                  {selectedDbId === db.id && (
                                    <span className="text-sm text-gray-400 italic">(selected)</span>
                                  )}
                                </div>

                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    className="bg-green-600 hover:bg-green-700 text-white px-3"
                                    onClick={() => {
                                      setSelectedDbId(db.id);
                                    }}
                                  >
                                    Select
                                  </Button>
                                  <Button
                                    size="sm"
                                    className="bg-red-600 hover:bg-red-700 text-white px-3"
                                    onClick={() => requestDeleteDatabase(db.id)}
                                    disabled={loading}
                                  >
                                    {loading ? 'Deleting...' : 'Delete'}
                                  </Button>
                                </div>
                              </li>
                            ))
                          )}
                        </ul>
                      </DialogContent>
                    </Dialog>
                  </DropdownMenuItem>

                  {/* View Schema Button */}
                  <DropdownMenuItem onClick={(e) => e.preventDefault()} className="text-gray-300 hover:bg-gray-700 focus:bg-gray-700">
                    <Button
                      className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300"
                      onClick={() => navigate('/schemas')}
                    >
                      View Schema
                    </Button>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              
              <Button
                className="bg-red-600 hover:bg-red-700 text-white rounded-lg px-4 py-2"
                onClick={requestLogout}
              >
                Log Out
              </Button>
            </div>
          </header>

          {/* Main chat area */}
          <div className="flex-1 overflow-y-auto p-6 bg-gray-900">
            <div className="max-w-4xl mx-auto">
              {prompts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="bg-gray-800 p-8 rounded-2xl shadow-lg max-w-lg">
                    <Database className="w-16 h-16 text-indigo-400 mx-auto mb-6" />
                    <h3 className="text-2xl font-bold text-gray-200 mb-4">SpeakQL Assistant</h3>
                    <p className="text-gray-400 mb-6">
                      Ask me questions about your database or request SQL queries. I can help you explore your data and generate SQL code.
                    </p>
                    <div className="grid grid-cols-1 gap-3 text-sm text-gray-300">
                      <button 
                        className="bg-gray-700 p-3 rounded-lg hover:bg-gray-600 cursor-pointer text-left"
                        onClick={() => handleSuggestionClick("Show all databases")}
                      >
                        "Show all databases"
                      </button>
                      <button 
                        className="bg-gray-700 p-3 rounded-lg hover:bg-gray-600 cursor-pointer text-left"
                        onClick={() => handleSuggestionClick("Find all tables in the current database")}
                      >
                        "Find all tables in the current database"
                      </button>
                      <button 
                        className="bg-gray-700 p-3 rounded-lg hover:bg-gray-600 cursor-pointer text-left"
                        onClick={() => handleSuggestionClick("What's the schema of this database?")}
                      >
                        "What's the schema of this database?"
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {prompts.map((prompt, index) => (
                    <div key={`conversation-${index}`} className="space-y-6">
                      {/* User message */}
                      <div className="flex items-start">
                        <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold mr-4 flex-shrink-0">
                          U
                        </div>
                        <div className="flex-1 px-4 py-3 rounded-lg bg-gray-800 text-gray-200 shadow">
                          {prompt}
                        </div>
                      </div>

                      {/* Assistant message */}
                      {responses[index] && (
                        <div className="flex items-start">
                          <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white mr-4 flex-shrink-0">
                            <Database className="w-4 h-4 text-indigo-300" />
                          </div>
                          <div className="flex-1 px-4 py-3 rounded-lg bg-gray-800 text-gray-200 shadow">
                            {/* SQL code block */}
                            {responses[index].raw_sql && (
                              <div className="mb-4 relative group">
                                {isEditingSql && editingSqlIndex === index ? (
                                  <div className="mb-2">
                                    <Textarea
                                      value={editedSql}
                                      onChange={(e) => setEditedSql(e.target.value)}
                                      className="font-mono text-sm border-2 border-indigo-600 focus:border-indigo-500 rounded-md p-3 w-full h-48 bg-gray-700 text-gray-200"
                                      placeholder="Edit SQL here..."
                                    />
                                    <div className="flex justify-end gap-2 mt-2">
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        className="text-gray-300 border-gray-600 hover:bg-gray-700"
                                        onClick={() => {
                                          setIsEditingSql(false);
                                          setEditingSqlIndex(null);
                                          setEditedSql('');
                                        }}
                                      >
                                        Cancel
                                      </Button>
                                      <Button
                                        size="sm"
                                        className="bg-green-600 hover:bg-green-700 text-white"
                                        onClick={() => saveEditedSql(index)}
                                      >
                                        <Save size={16} className="mr-1" /> Save Changes
                                      </Button>
                                    </div>
                                  </div>
                                ) : (
                                  <>
                                    <div className="absolute top-2 right-2 z-10 flex gap-1">
                                      <Button
                                        size="sm"
                                        variant="ghost"
                                        className="h-8 w-8 rounded-full bg-gray-900 bg-opacity-50 hover:bg-opacity-70 text-white"
                                        onClick={() => startEditingSql(responses[index].raw_sql, index)}
                                      >
                                        <Edit2 size={16} />
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="ghost"
                                        className="h-8 w-8 rounded-full bg-gray-900 bg-opacity-50 hover:bg-opacity-70 text-white"
                                        onClick={() => copyToClipboard(responses[index].raw_sql, index)}
                                      >
                                        {copiedIndex === index ? <Check size={16} /> : <Copy size={16} />}
                                      </Button>
                                    </div>
                                    <SyntaxHighlighter
                                      language="sql"
                                      style={oneDark}
                                      customStyle={{
                                        padding: '1rem',
                                        borderRadius: '0.75rem',
                                        marginBottom: '0.5rem',
                                        fontSize: '0.875rem',
                                        lineHeight: '1.5',
                                      }}
                                    >
                                      {responses[index].raw_sql}
                                    </SyntaxHighlighter>
                                  </>
                                )}
                              </div>
                            )}

                            <p className="text-gray-300 mb-2">{responses[index].message}</p>

                            {/* Display result data as a table if available */}
                            {responses[index].result &&
                              Array.isArray(responses[index].result) &&
                              renderQueryResults(responses[index].result)}

                            {/* Display status if available */}
                            {responses[index].status && (
                              <p
                                className={`text-sm mt-2 ${
                                  responses[index].status === 'success'
                                    ? 'text-green-500'
                                    : 'text-red-500'
                                }`}
                              >
                                Status: {responses[index].status}
                              </p>
                            )}

                            {/* Add "Execute This SQL" button for edited SQL */}
                            {index === responses.length - 1 &&
                              responses[index].raw_sql &&
                              !isEditingSql && (
                                <div className="mt-3">
                                  <Button
                                    size="sm"
                                    className="bg-indigo-600 hover:bg-indigo-700 text-white"
                                    onClick={() => requestExecuteSQL(responses[index].raw_sql)}
                                    disabled={loading}
                                  >
                                    Execute This SQL
                                  </Button>
                                </div>
                              )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* Input area */}
          <div className="p-4 border-t border-gray-700 bg-gray-800">
            <div className="max-w-4xl mx-auto">
              <div className="relative bg-gray-700 rounded-xl shadow-md border border-gray-600 overflow-hidden">
                <Textarea
                  ref={textareaRef}
                  placeholder={selectedDbId === 0 
                    ? "Select a database first..." 
                    : "Message SpeakQL..."}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      requestGenerateQuery();
                    }
                  }}
                  disabled={selectedDbId === 0 || loading}
                  className="w-full bg-gray-700 text-gray-200 placeholder-gray-400 rounded-xl px-4 py-3 pr-16 resize-none min-h-[56px] max-h-[200px] border-0 focus:ring-0 focus:outline-none"
                  rows={1}
                  style={{ overflow: input.length > 100 ? 'auto' : 'hidden' }}
                />
                
                <Button
                  onClick={() => requestGenerateQuery()}
                  className="absolute right-3 bottom-3 rounded-lg p-2 bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
                  disabled={selectedDbId === 0 || !input.trim() || loading}
                >
                  {loading ? (
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                  ) : (
                    <Send size={18} />
                  )}
                </Button>
              </div>
              
              <div className="text-xs text-gray-400 mt-2 text-center">
                Press Enter to send, Shift+Enter for new line
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

