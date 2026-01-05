import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ArrowLeft, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

// Terms Acceptance Screen (for new users)
export const TermsAcceptance = ({ onAccepted }) => {
  const [terms, setTerms] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [scrolledToBottom, setScrolledToBottom] = useState(false);
  const { t, i18n } = useTranslation();

  useEffect(() => {
    fetchTerms();
  }, []);

  const fetchTerms = async () => {
    try {
      const response = await api.get(`/terms?language=${i18n.language}`);
      setTerms(response.data);
    } catch (error) {
      console.error('Failed to fetch terms:', error);
      // Use default terms from i18n
      setTerms({
        version: '1.0',
        content: t('terms.content')
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await api.post('/user/accept-terms', {
        version: terms.version
      });
      toast.success(t('terms.accepted'));
      onAccepted?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setAccepting(false);
    }
  };

  const handleScroll = (e) => {
    const element = e.target;
    const isAtBottom = Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) < 50;
    if (isAtBottom) {
      setScrolledToBottom(true);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 to-primary/10">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 to-primary/10 p-4 flex items-center justify-center">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-2xl">{t('terms.title')}</CardTitle>
          <p className="text-muted-foreground mt-2">{t('terms.subtitle')}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Terms Content */}
          <div 
            className="bg-muted/50 rounded-lg h-80 overflow-y-auto p-4 prose prose-sm max-w-none"
            onScroll={handleScroll}
          >
            <ReactMarkdown>{terms?.content || ''}</ReactMarkdown>
          </div>

          {/* Scroll Indicator */}
          {!scrolledToBottom && (
            <div className="flex items-center justify-center gap-2 text-amber-600 bg-amber-50 p-2 rounded-lg">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">{t('terms.scrollToRead')}</span>
            </div>
          )}

          {/* Version Badge */}
          <div className="flex justify-center">
            <Badge variant="secondary">
              {t('terms.version')}: {terms?.version}
            </Badge>
          </div>

          {/* Accept Button */}
          <Button
            onClick={handleAccept}
            disabled={!scrolledToBottom || accepting}
            className="w-full btn-primary"
            size="lg"
          >
            {accepting ? t('common.loading') : t('terms.accept')}
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            {t('terms.acceptDisclaimer')}
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

// Terms View Screen (for viewing accepted terms)
export const TermsView = () => {
  const [terms, setTerms] = useState(null);
  const [termsStatus, setTermsStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [termsRes, statusRes] = await Promise.all([
        api.get(`/terms?language=${i18n.language}`),
        api.get('/user/terms-status')
      ]);
      setTerms(termsRes.data);
      setTermsStatus(statusRes.data);
    } catch (error) {
      console.error('Failed to fetch terms data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern">
      <div className="max-w-2xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('terms.title')}</h1>
        </div>

        {/* Acceptance Status */}
        {termsStatus?.terms_accepted && (
          <Card className="mb-6 border-green-200 bg-green-50">
            <CardContent className="p-4 flex items-center gap-3">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-medium text-green-800">{t('terms.alreadyAccepted')}</p>
                <p className="text-sm text-green-700">
                  {t('profile.termsVersion')}: {termsStatus.terms_version} • {t('profile.termsAcceptedAt')}: {new Date(termsStatus.terms_accepted_at).toLocaleDateString()}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Terms Content */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {t('terms.fullTerms')}
              </CardTitle>
              <Badge variant="secondary">v{terms?.version}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{terms?.content || ''}</ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TermsView;
