import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, MessageCircle, CheckCircle, XCircle, Clock, AlertTriangle, Mail } from 'lucide-react';

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

// Exchange status badge
const ExchangeStatusBadge = ({ status, t }) => {
  const config = {
    pending: { color: 'bg-blue-100 text-blue-800', icon: <Clock className="h-3 w-3" />, label: t('exchange.statusPending') },
    completed: { color: 'bg-green-100 text-green-800', icon: <CheckCircle className="h-3 w-3" />, label: t('exchange.statusCompleted') },
    failed: { color: 'bg-red-100 text-red-800', icon: <XCircle className="h-3 w-3" />, label: t('exchange.statusFailed') },
    expired: { color: 'bg-gray-100 text-gray-800', icon: <AlertTriangle className="h-3 w-3" />, label: t('exchange.statusExpired') }
  };
  const c = config[status] || config.pending;
  return (
    <Badge className={`${c.color} flex items-center gap-1`}>
      {c.icon}
      {c.label}
    </Badge>
  );
};

// Failure reasons - Split into MINOR (no reputation impact) and SERIOUS
const FAILURE_REASONS_MINOR = [
  { value: 'schedule_conflict', labelKey: 'exchange.reasonScheduleConflict' },
  { value: 'personal_issue', labelKey: 'exchange.reasonPersonalIssue' },
  { value: 'moved_away', labelKey: 'exchange.reasonMovedAway' },
  { value: 'lost_stickers', labelKey: 'exchange.reasonLostStickers' }
];

const FAILURE_REASONS_SERIOUS = [
  { value: 'no_show', labelKey: 'exchange.reasonNoShow' },
  { value: 'cancelled_no_notice', labelKey: 'exchange.reasonCancelledNoNotice' },
  { value: 'attempted_sale', labelKey: 'exchange.reasonAttemptedSale' },
  { value: 'inappropriate', labelKey: 'exchange.reasonInappropriate' },
  { value: 'wrong_stickers', labelKey: 'exchange.reasonWrongStickers' }
];

export const Exchanges = () => {
  const { albumId } = useParams();
  const [exchanges, setExchanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchExchanges();
  }, [albumId]);

  const fetchExchanges = async () => {
    try {
      const response = await api.get(`/albums/${albumId}/exchanges`);
      setExchanges(response.data);
    } catch (error) {
      // Empty result is NOT an error - don't show error toast for 404 or empty
      // Only show toast for actual errors (500, network, etc.)
      if (error.response?.status >= 500) {
        toast.error(t('common.error'));
      }
      // For 404 or any other case, just show empty state
    } finally {
      setLoading(false);
    }
  };

  // Check if user has any new/unseen exchanges or unread messages
  const hasNewExchanges = exchanges.some(ex => ex.is_new && ex.status === 'pending');
  const hasUnreadMessages = exchanges.some(ex => ex.has_unread && ex.status === 'pending');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern pb-20">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate(`/albums/${albumId}`)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('exchange.myExchanges')}</h1>
          {(hasNewExchanges || hasUnreadMessages) && (
            <Badge className="bg-red-500 text-white animate-pulse flex items-center gap-1">
              <Mail className="h-3 w-3" />
              {hasNewExchanges ? t('exchange.newExchange') : t('exchange.hasNewMessage')}
            </Badge>
          )}
        </div>

        {exchanges.length === 0 ? (
          <div className="text-center py-20">
            <MessageCircle className="h-24 w-24 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-2xl font-bold mb-2">{t('exchange.noExchangesInArea')}</h2>
            <p className="text-muted-foreground mb-6">{t('exchange.noExchangesHint')}</p>
            <Button onClick={() => navigate(`/albums/${albumId}/matches`)}>
              {t('exchange.findMatches')}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {exchanges.map((exchange) => (
              <Card 
                key={exchange.id}
                className={`cursor-pointer hover:shadow-lg transition-all ${
                  exchange.has_unread && exchange.status === 'pending' 
                    ? 'border-2 border-primary' 
                    : ''
                }`}
                onClick={() => navigate(`/exchanges/${exchange.id}`)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-12 w-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold relative">
                        {(exchange.partner?.display_name || 'U')[0].toUpperCase()}
                        {/* Unread indicator dot */}
                        {exchange.has_unread && exchange.status === 'pending' && (
                          <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full flex items-center justify-center text-[10px] text-white font-bold">
                            {exchange.unread_count > 9 ? '9+' : exchange.unread_count}
                          </span>
                        )}
                      </div>
                      <div>
                        <p className="font-semibold">
                          {exchange.partner?.display_name || t('app.defaultUser')}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <ReputationBadge status={exchange.partner?.reputation_status} t={t} />
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <ExchangeStatusBadge status={exchange.status} t={t} />
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(exchange.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export const ExchangeDetail = () => {
  const { exchangeId } = useParams();
  const [exchange, setExchange] = useState(null);
  const [loading, setLoading] = useState(true);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmType, setConfirmType] = useState(null); // 'success' or 'failure'
  const [failureReason, setFailureReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchExchange();
  }, [exchangeId]);

  const fetchExchange = async () => {
    try {
      const response = await api.get(`/exchanges/${exchangeId}`);
      setExchange(response.data);
    } catch (error) {
      // Don't show raw backend error
      toast.error(t('common.error'));
      // Navigate to albums if exchange not found (don't use navigate(-1))
      navigate('/albums');
    } finally {
      setLoading(false);
    }
  };
  
  // Get proper back navigation path
  const getBackPath = () => {
    if (exchange?.album_id) {
      return `/albums/${exchange.album_id}/exchanges`;
    }
    return '/albums';
  };

  const handleConfirm = async () => {
    if (confirmType === 'failure' && !failureReason) {
      toast.error(t('exchange.selectReason'));
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/exchanges/${exchangeId}/confirm`, {
        confirmed: confirmType === 'success',
        failure_reason: confirmType === 'failure' ? failureReason : null
      });
      toast.success(t('exchange.confirmationSaved'));
      setConfirmDialogOpen(false);
      fetchExchange();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const hasUserConfirmed = () => {
    if (!exchange) return false;
    return exchange.is_user_a ? exchange.user_a_confirmed !== null : exchange.user_b_confirmed !== null;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  if (!exchange) return null;

  const myOffers = exchange.is_user_a ? exchange.user_a_offers_details : exchange.user_b_offers_details;
  const theirOffers = exchange.is_user_a ? exchange.user_b_offers_details : exchange.user_a_offers_details;

  return (
    <div className="min-h-screen sticker-album-pattern pb-20">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-6">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate(getBackPath())}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-black tracking-tight text-primary">{t('exchange.details')}</h1>
          </div>
          <ExchangeStatusBadge status={exchange.status} t={t} />
        </div>

        {/* Partner Info */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-xl">
                {(exchange.partner?.display_name || 'U')[0].toUpperCase()}
              </div>
              <div>
                <p className="text-xl font-semibold">
                  {exchange.partner?.display_name || t('app.defaultUser')}
                </p>
                <ReputationBadge status={exchange.partner?.reputation_status} t={t} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stickers Exchange Summary */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">{t('exchange.youGive')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {myOffers?.map((sticker) => (
                  <div key={sticker.id} className="text-sm bg-amber-50 p-2 rounded">
                    N° {sticker.number} - {sticker.name}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">{t('exchange.youReceive')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {theirOffers?.map((sticker) => (
                  <div key={sticker.id} className="text-sm bg-green-50 p-2 rounded">
                    N° {sticker.number} - {sticker.name}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chat Button */}
        <Button 
          className="w-full mb-4"
          onClick={() => navigate(`/exchanges/${exchangeId}/chat`)}
        >
          <MessageCircle className="h-5 w-5 mr-2" />
          {exchange.status === 'pending' ? t('exchange.openChat') : t('exchange.viewChat')}
        </Button>

        {/* Confirmation Actions (only for pending exchanges) */}
        {exchange.status === 'pending' && !hasUserConfirmed() && (
          <Card className="border-2 border-dashed">
            <CardHeader>
              <CardTitle>{t('exchange.confirmTitle')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                {t('exchange.confirmDescription')}
              </p>
              <div className="flex gap-4">
                <Button 
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  onClick={() => { setConfirmType('success'); setConfirmDialogOpen(true); }}
                >
                  <CheckCircle className="h-5 w-5 mr-2" />
                  {t('exchange.confirmSuccess')}
                </Button>
                <Button 
                  variant="destructive"
                  className="flex-1"
                  onClick={() => { setConfirmType('failure'); setConfirmDialogOpen(true); }}
                >
                  <XCircle className="h-5 w-5 mr-2" />
                  {t('exchange.confirmFailure')}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Already Confirmed Message */}
        {hasUserConfirmed() && (
          <Card className="bg-muted">
            <CardContent className="p-4 text-center">
              <CheckCircle className="h-8 w-8 mx-auto text-green-600 mb-2" />
              <p className="font-semibold">{t('exchange.alreadyConfirmed')}</p>
            </CardContent>
          </Card>
        )}

        {/* Confirmation Dialog */}
        <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {confirmType === 'success' ? t('exchange.confirmSuccessTitle') : t('exchange.confirmFailureTitle')}
              </DialogTitle>
              <DialogDescription>
                {confirmType === 'success' 
                  ? t('exchange.confirmSuccessDesc')
                  : t('exchange.confirmFailureDesc')
                }
              </DialogDescription>
            </DialogHeader>

            {confirmType === 'failure' && (
              <div className="space-y-3">
                <p className="text-sm font-semibold">{t('exchange.selectReasonLabel')}</p>
                
                {/* Minor issues - No reputation impact */}
                <p className="text-xs text-muted-foreground font-medium mt-2">{t('exchange.minorIssuesTitle')}</p>
                {FAILURE_REASONS_MINOR.map((reason) => (
                  <div 
                    key={reason.value}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      failureReason === reason.value 
                        ? 'border-amber-500 bg-amber-50' 
                        : 'hover:border-gray-400'
                    }`}
                    onClick={() => setFailureReason(reason.value)}
                  >
                    <p className="text-sm">{t(reason.labelKey)}</p>
                  </div>
                ))}
                
                {/* Serious issues - Affects reputation */}
                <p className="text-xs text-muted-foreground font-medium mt-3">{t('exchange.seriousIssuesTitle')}</p>
                {FAILURE_REASONS_SERIOUS.map((reason) => (
                  <div 
                    key={reason.value}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      failureReason === reason.value 
                        ? 'border-red-500 bg-red-50' 
                        : 'hover:border-gray-400'
                    }`}
                    onClick={() => setFailureReason(reason.value)}
                  >
                    <p className="text-sm">{t(reason.labelKey)}</p>
                  </div>
                ))}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setConfirmDialogOpen(false)}>
                {t('common.cancel')}
              </Button>
              <Button 
                onClick={handleConfirm}
                disabled={submitting || (confirmType === 'failure' && !failureReason)}
                className={confirmType === 'success' ? 'bg-green-600 hover:bg-green-700' : ''}
                variant={confirmType === 'failure' ? 'destructive' : 'default'}
              >
                {submitting ? t('common.loading') : t('common.confirm')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Exchanges;
