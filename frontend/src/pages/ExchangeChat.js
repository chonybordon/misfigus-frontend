import React, { useState, useEffect, useRef, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Send, Lock } from 'lucide-react';

// Reputation badge component
const ReputationBadge = ({ status, t }) => {
  const config = {
    trusted: { color: 'bg-green-100 text-green-800', icon: '🟢', label: t('reputation.trusted') },
    under_review: { color: 'bg-yellow-100 text-yellow-800', icon: '🟡', label: t('reputation.underReview') },
    restricted: { color: 'bg-red-100 text-red-800', icon: '🔴', label: t('reputation.restricted') }
  };
  const c = config[status] || config.trusted;
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
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useContext(AuthContext);

  useEffect(() => {
    fetchData();
  }, [exchangeId]);

  useEffect(() => {
    scrollToBottom();
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
      toast.error(error.response?.data?.detail || t('common.error'));
      navigate(-1);
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
            {(exchange?.partner?.display_name || 'U')[0].toUpperCase()}
          </div>
          <div>
            <p className="font-semibold">
              {exchange?.partner?.display_name || t('app.defaultUser')}
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
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isSystem = msg.is_system;
          const isMe = msg.sender_id === user?.id;

          if (isSystem) {
            return (
              <div key={msg.id} className="flex justify-center">
                <div className="bg-gray-200 text-gray-600 px-4 py-2 rounded-full text-sm">
                  {msg.content}
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
