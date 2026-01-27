import React, { useState, useEffect, useRef, useContext, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Send, Lock } from 'lucide-react';

// Polling interval in milliseconds
const POLL_INTERVAL = 2000;

// Helper to get display name with i18n fallback
const getDisplayName = (user, t) => {
  if (!user) return t('profile.noName');
  return user.display_name || t('profile.noName');
};

// Reputation badge component
const ReputationBadge = ({ status, t }) => {
  const config = {
    new: { color: 'bg-blue-100 text-blue-800', icon: '🔵', label: t('reputation.new') },
    trusted: { color: 'bg-green-100 text-green-800', icon: '🟢', label: t('reputation.trusted') },
    under_review: { color: 'bg-yellow-100 text-yellow-800', icon: '🟡', label: t('reputation.underReview') },
    restricted: { color: 'bg-red-100 text-red-800', icon: '🔴', label: t('reputation.restricted') }
  };
  const c = config[status] || config.new;  // Default to "new" instead of "trusted"
  return (
    <Badge className={c.color}>
      <span className="mr-1">{c.icon}</span>
      {c.label}
    </Badge>
  );
};

export const ExchangeChat = () => {
  const { exchangeId } = useParams();
  const [exchange, setExchange] = useState(null);
  const [chatData, setChatData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const isAtBottomRef = useRef(true);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useContext(AuthContext);

  // Check if user is scrolled to bottom
  const checkIfAtBottom = useCallback(() => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
      // Consider "at bottom" if within 100px of the bottom
      isAtBottomRef.current = scrollHeight - scrollTop - clientHeight < 100;
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [exchangeId]);

  // Polling for new messages
  useEffect(() => {
    if (loading) return; // Don't poll until initial load is complete
    
    const pollMessages = async () => {
      try {
        const chatRes = await api.get(`/exchanges/${exchangeId}/chat`);
        const newMessages = chatRes.data.messages || [];
        
        // Only update if there are new messages
        setMessages(prevMessages => {
          // Create a Set of existing message IDs for O(1) lookup
          const existingIds = new Set(prevMessages.map(m => m.id));
          
          // Find messages that don't exist yet
          const messagesToAdd = newMessages.filter(m => !existingIds.has(m.id));
          
          if (messagesToAdd.length > 0) {
            // Check if at bottom before adding new messages
            checkIfAtBottom();
            return [...prevMessages, ...messagesToAdd];
          }
          
          return prevMessages;
        });
        
        // Update chat data (for read-only status changes)
        setChatData(chatRes.data);
      } catch (error) {
        // Silently fail on poll errors - don't spam user with toasts
        console.error('Failed to poll messages:', error);
      }
    };

    const intervalId = setInterval(pollMessages, POLL_INTERVAL);
    
    // Cleanup: stop polling when component unmounts or exchangeId changes
    return () => clearInterval(intervalId);
  }, [exchangeId, loading, checkIfAtBottom]);

  // Auto-scroll when new messages arrive (only if user was at bottom)
  useEffect(() => {
    if (isAtBottomRef.current) {
      scrollToBottom();
    }
  }, [messages]);

  const fetchData = async () => {
    try {
      const [exchangeRes, chatRes] = await Promise.all([
        api.get(`/exchanges/${exchangeId}`),
        api.get(`/exchanges/${exchangeId}/chat`)
      ]);
      setExchange(exchangeRes.data);
      setChatData(chatRes.data);
      setMessages(chatRes.data.messages || []);
    } catch (error) {
      // Don't show raw backend error - use generic message
      toast.error(t('common.error'));
      // Navigate explicitly to exchange details, never use navigate(-1)
      navigate(`/exchanges/${exchangeId}`);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const response = await api.post(`/exchanges/${exchangeId}/chat/messages`, {
        content: newMessage.trim()
      });
      setMessages([...messages, response.data]);
      setNewMessage('');
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  const isReadOnly = chatData?.is_read_only;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b p-4 flex items-center gap-4 sticky top-0 z-10">
        <Button
          variant="outline"
          size="icon"
          onClick={() => navigate(`/exchanges/${exchangeId}`)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex items-center gap-3 flex-1">
          <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
            {getDisplayName(exchange?.partner, t)[0].toUpperCase()}
          </div>
          <div>
            <p className="font-semibold">
              {getDisplayName(exchange?.partner, t)}
            </p>
            <ReputationBadge status={exchange?.partner?.reputation_status} t={t} />
          </div>
        </div>
        {isReadOnly && (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Lock className="h-3 w-3" />
            {t('chat.readOnly')}
          </Badge>
        )}
      </div>

      {/* Messages */}
      <div 
        ref={messagesContainerRef}
        onScroll={checkIfAtBottom}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.map((msg) => {
          const isSystem = msg.is_system;
          const isMe = msg.sender_id === user?.id;

          if (isSystem) {
            // Translate system message keys
            const systemMessageKeys = {
              'SYSTEM_EXCHANGE_STARTED': t('system.exchangeStarted'),
              'SYSTEM_EXCHANGE_COMPLETED': t('system.exchangeCompleted'),
              'SYSTEM_EXCHANGE_FAILED': t('system.exchangeFailed')
            };
            const displayContent = systemMessageKeys[msg.content] || msg.content;
            
            return (
              <div key={msg.id} className="flex justify-center">
                <div className="bg-gray-200 text-gray-600 px-4 py-2 rounded-full text-sm">
                  {displayContent}
                </div>
              </div>
            );
          }

          return (
            <div 
              key={msg.id} 
              className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[70%] px-4 py-2 rounded-2xl ${
                  isMe 
                    ? 'bg-primary text-primary-foreground rounded-br-none' 
                    : 'bg-white border rounded-bl-none'
                }`}
              >
                <p className="text-sm">{msg.content}</p>
                <p className={`text-xs mt-1 ${isMe ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      {!isReadOnly ? (
        <form onSubmit={handleSend} className="bg-white border-t p-4 flex gap-2">
          <Input
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={t('chat.placeholder')}
            className="flex-1"
            disabled={sending}
          />
          <Button type="submit" disabled={!newMessage.trim() || sending}>
            <Send className="h-5 w-5" />
          </Button>
        </form>
      ) : (
        <div className="bg-gray-100 border-t p-4 text-center text-sm text-muted-foreground">
          <Lock className="h-4 w-4 inline mr-2" />
          {t('chat.chatClosed')}
        </div>
      )}
    </div>
  );
};

export default ExchangeChat;
