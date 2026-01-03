import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ArrowLeft, Send } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

export const Chat = () => {
  const { groupId, userId } = useParams();
  const [thread, setThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef(null);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const currentUserId = JSON.parse(localStorage.getItem('user'))?.id;

  useEffect(() => {
    fetchThread();
    const interval = setInterval(fetchThread, 5000);
    return () => clearInterval(interval);
  }, [groupId, userId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchThread = async () => {
    try {
      const response = await api.get(`/chat/threads/${userId}?group_id=${groupId}`);
      setThread(response.data.thread);
      setMessages(response.data.messages);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    try {
      await api.post(`/chat/messages?group_id=${groupId}&thread_id=${thread.id}`, {
        to_user_id: userId,
        text: text.trim(),
      });
      setNewMessage('');
      fetchThread();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSendMessage(newMessage);
  };

  const templates = [
    t('chat.templates.greeting'),
    t('chat.templates.thanks'),
    t('chat.templates.question'),
    t('chat.templates.meetup'),
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="bg-card border-b p-4">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <Button
            data-testid="back-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate(`/groups/${groupId}`)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-black tracking-tight text-primary">{t('chat.title')}</h1>
        </div>
      </div>

      <div className="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col">
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto space-y-4 mb-4"
          data-testid="messages-container"
        >
          {messages.map((message) => (
            <div
              key={message.id}
              data-testid={`message-${message.id}`}
              className={`flex ${message.from_user_id === currentUserId ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs md:max-w-md p-3 rounded-2xl ${
                  message.from_user_id === currentUserId
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                <p className="text-sm">{message.text}</p>
                <p className="text-xs opacity-70 mt-1">
                  {new Date(message.created_at).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="mb-4">
          <p className="text-xs text-muted-foreground mb-2">{t('chat.templates.greeting')}:</p>
          <div className="flex flex-wrap gap-2">
            {templates.map((template, idx) => (
              <Button
                key={idx}
                data-testid={`template-btn-${idx}`}
                size="sm"
                variant="outline"
                onClick={() => handleSendMessage(template)}
                className="text-xs"
              >
                {template}
              </Button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2" data-testid="message-form">
          <Input
            data-testid="message-input"
            placeholder={t('chat.placeholder')}
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            className="flex-1"
          />
          <Button
            data-testid="send-message-btn"
            type="submit"
            size="icon"
            className="btn-primary"
            disabled={!newMessage.trim()}
          >
            <Send className="h-5 w-5" />
          </Button>
        </form>
      </div>
    </div>
  );
};

export default Chat;
